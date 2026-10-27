import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash, webcrypto } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { canonicalJSON } from '../server/static/variantenraum/core.mjs';
import { digestJSON, verifySealed, mergeRundwegState, inspectHandoff, handoffsForVariant, dazwischenUrl, createRundwegClient } from '../server/static/variantenraum/rundweg-client.mjs';

const catalog = JSON.parse(await readFile(new URL('../server/static/variantenraum/catalog.json', import.meta.url)));
const copy = value => JSON.parse(JSON.stringify(value));
const seal = async value => ({ ...value, digest: await digestJSON(value) });
const operationId = 'c7203f7f-e0b6-43cd-99da-95aad76a6c35';
async function envelope() {
  const variant = copy(catalog.variants[0]);
  const hash = '#variante=' + variant.id + '&ansicht=room&vergleich=' + catalog.variants[1].id + '&filter=dissent&raum=room-dazwischen&raumfassung=' + variant.id + '&rueckweg=compare';
  const packet = await seal({ format: 'kintegrity.roundtrip.v1', operationId,
    source: { roomId: 'room-dazwischen', catalogRevision: catalog.revision, variantId: variant.id,
      variantDigest: await digestJSON(variant), variantSnapshot: variant },
    navigation: { hash }, returnUrl: '/variantenraum/index.html' + hash,
    target: { name: 'DAS DAZWISCHEN', revision: 'public-build' },
    mandate: { executor: 'Codex', role: 'Technische Ausführung', text: 'Diesen technischen Rundweg ausführen.', scope: 'Technischer Empfang; menschliche Annahme bleibt offen.' } });
  const receipt = await seal({ id: 'receipt-test', packetDigest: packet.digest,
    actor: { name: 'Codex', role: packet.mandate.role, mandate: packet.mandate.text, scope: packet.mandate.scope,
      identityBasis: 'configured-local-technical-executor' },
    transport: 'received', review: 'not-reviewed', humanAcceptance: 'open', finding: 'Öffentliche Zusammenfassungen empfangen.',
    targetRevision: packet.target.revision, returnUrl: packet.returnUrl });
  return { packet, receipt, withdrawn: false, adoption: null };
}
function storage() {
  const values = new Map();
  return { getItem: key => values.get(key) ?? null, setItem: (key, value) => values.set(key, value) };
}
const response = value => ({ ok: true, json: async () => value });

test('canonical digest sorts nested keys, preserves arrays and hashes Unicode as UTF-8', async () => {
  const a = { z: [{ ü: 'Öffentliche Quelle', a: '→' }], a: true };
  const b = { a: true, z: [{ a: '→', ü: 'Öffentliche Quelle' }] };
  assert.equal(await digestJSON(a), await digestJSON(b));
  assert.equal(await digestJSON(a), createHash('sha256').update(canonicalJSON(a), 'utf8').digest('hex'));
  assert.notEqual(await digestJSON(['a', 'b']), await digestJSON(['b', 'a']));
});

test('a sealed value detects changed content', async () => {
  const value = await seal({ finding: 'Empfangen' });
  assert.equal(await verifySealed(value), true);
  assert.equal(await verifySealed({ ...value, finding: 'Angenommen' }), false);
});

test('state adds a derived variant without changing a published variant or its stages', () => {
  const before = canonicalJSON(catalog);
  const derived = copy(catalog.variants[0]);
  derived.id = 'variant-client-derived'; derived.title += ' · mit quittiertem Rundweg'; derived.parentIds = [catalog.variants[0].id];
  const result = mergeRundwegState(catalog, { handoffs: [], variants: [derived] });
  assert.equal(result.variants.at(-1).id, derived.id);
  for (const key of ['proposal', 'implementation', 'verification', 'humanAcceptance', 'componentBindings', 'dissentIds']) {
    assert.deepEqual(result.variants.at(-1)[key], catalog.variants[0][key]);
  }
  assert.equal(canonicalJSON(catalog), before);
  const changed = copy(catalog.variants[0]); changed.title = 'Verdeckter Ersatz';
  assert.throws(() => mergeRundwegState(catalog, { handoffs: [], variants: [changed] }), /immutable/);
  assert.throws(() => mergeRundwegState(catalog, { handoffs: [], variants: [] }, [derived]), /catalog/);
});

test('matching technical receipt allows explicit derivation and preserves the exact return fragment', async () => {
  const entry = await envelope();
  assert.deepEqual(await inspectHandoff(entry, catalog), { validPacket: true, validReceipt: true, stale: false, canContinue: true, canAdopt: true });
  assert.equal(entry.packet.returnUrl, '/variantenraum/index.html' + entry.packet.navigation.hash);
  assert.equal(entry.receipt.humanAcceptance, 'open');
});

test('withdrawal keeps a receipt historical and prevents another derivation', async () => {
  const entry = await envelope(); entry.withdrawn = true;
  const checked = await inspectHandoff(entry, catalog);
  assert.equal(checked.validReceipt, true); assert.equal(checked.canAdopt, false); assert.equal(checked.canContinue, false);
  entry.adoption = { variantId: 'variant-already-derived' };
  assert.equal((await inspectHandoff(entry, catalog)).canAdopt, false);
});

test('an older catalog or modified source variant cannot receive a current derivation', async () => {
  const entry = await envelope();
  assert.equal((await inspectHandoff(entry, { ...catalog, revision: catalog.revision + '.new' })).canAdopt, false);
  const changed = copy(catalog); changed.variants[0].title += ' geändert';
  assert.equal((await inspectHandoff(entry, changed)).stale, true);
});

test('a newly sealed receipt still needs the exact packet, actor mandate, target, return and open acceptance', async () => {
  const original = await envelope();
  const mutations = [
    receipt => { receipt.packetDigest = 'a'.repeat(64); },
    receipt => { receipt.actor.name = 'Andere Ausführung'; },
    receipt => { receipt.actor.role = 'Menschliche Entscheidung'; },
    receipt => { receipt.actor.mandate = 'Anderer Auftrag'; },
    receipt => { receipt.actor.scope = 'Fachliche Annahme'; },
    receipt => { receipt.targetRevision = 'other-build'; },
    receipt => { receipt.returnUrl = '/andere-auswahl'; },
    receipt => { receipt.humanAcceptance = 'accepted'; },
    receipt => { receipt.review = 'reviewed-rejected'; },
  ];
  for (const mutate of mutations) {
    const entry = copy(original); const { digest, ...receipt } = entry.receipt;
    mutate(receipt); entry.receipt = await seal(receipt);
    assert.equal((await inspectHandoff(entry, catalog)).canAdopt, false);
  }
});

test('a packet with another snapshot identity or destination is not a valid source packet', async () => {
  const original = await envelope();
  for (const mutate of [packet => { packet.source.variantSnapshot.id = 'another-work'; }, packet => { packet.returnUrl = 'https://other.example/'; }, packet => { packet.mandate.executor = 'Other'; }, packet => { packet.format = 'other'; }]) {
    const entry = copy(original); const { digest, ...packet } = entry.packet;
    mutate(packet); entry.packet = await seal(packet);
    assert.equal((await inspectHandoff(entry, catalog)).validPacket, false);
  }
});

test('receipt association follows the exact source or inherited packet, not a title', async () => {
  const entry = await envelope();
  assert.equal(handoffsForVariant([entry], catalog.variants[0]).length, 1);
  assert.equal(handoffsForVariant([entry], { id: 'other', title: catalog.variants[0].title }).length, 0);
  assert.equal(handoffsForVariant([entry], { id: 'derived', roomReceipts: [{ packetDigest: entry.packet.digest }] }).length, 1);
});

test('the browser opens only the same-origin broker DAZ route for this operation', async () => {
  const entry = await envelope();
  assert.equal(dazwischenUrl(entry, 'http://localhost:1234'), '/dazwischen/?rundweg=' + operationId);
  for (const value of ['https://other.example/dazwischen/?rundweg=' + operationId, '/dazwischen/?rundweg=other', '/dazwischen/../admin']) {
    assert.throws(() => dazwischenUrl({ ...entry, dazwischenUrl: value }, 'http://localhost:1234'), /destination/);
  }
});

test('a lost handoff response replays the same persisted public intent after client reload', async () => {
  const saved = storage(); const requests = [];
  const fetchImpl = async (path, options) => { requests.push({ path, options, body: JSON.parse(options.body) }); if (requests.length === 1) throw new Error('lost response'); return response({ packet: { operationId: requests.at(-1).body.operationId } }); };
  const input = { catalogRevision: catalog.revision, variant: catalog.variants[0], navigation: { hash: '#variante=' + catalog.variants[0].id } };
  await assert.rejects(createRundwegClient({ storage: saved, fetchImpl, cryptoImpl: webcrypto }).handoff(input));
  await createRundwegClient({ storage: saved, fetchImpl, cryptoImpl: webcrypto }).handoff(input);
  assert.deepEqual(requests[0].body, requests[1].body);
  assert.deepEqual(requests[0].options.headers, { 'Content-Type': 'application/json', 'X-Rundweg-Request': '1' });
  assert.equal(requests[0].options.redirect, 'error');
  assert.equal('variantSnapshot' in requests[0].body, false);
  assert.equal('summary' in requests[0].body, false);
  await createRundwegClient({ storage: saved, fetchImpl, cryptoImpl: webcrypto }).handoff({ ...input, navigation: { hash: input.navigation.hash + '&filter=open' } });
  assert.notEqual(requests[1].body.operationId, requests[2].body.operationId);
});

test('a lost adoption response replays its operation without creating a new adoption intent', async () => {
  const saved = storage(); const bodies = []; const entry = await envelope();
  const fetchImpl = async (_path, options) => { bodies.push(JSON.parse(options.body)); if (bodies.length === 1) throw new Error('lost'); return response({ packet: entry.packet, adoption: { variantId: 'variant-derived' } }); };
  await assert.rejects(createRundwegClient({ storage: saved, fetchImpl, cryptoImpl: webcrypto }).adopt(entry));
  await createRundwegClient({ storage: saved, fetchImpl, cryptoImpl: webcrypto }).adopt(entry);
  assert.deepEqual(bodies[0], bodies[1]);
  assert.equal(bodies[1].receiptDigest, entry.receipt.digest);
  assert.equal(bodies[1].expectedVariantDigest, entry.packet.source.variantDigest);
});

test('a confirmed withdrawal frees a lost public handoff intent for an explicit new attempt', async () => {
  const saved = storage(); const bodies = [];
  const fetchImpl = async (path, options) => {
    if (options.method === 'GET') return response({ variants: [], handoffs: [{ packet: { operationId: bodies[0].operationId }, withdrawn: true }] });
    bodies.push(JSON.parse(options.body));
    if (bodies.length === 1) throw new Error('lost response');
    return response({ packet: { operationId: bodies.at(-1).operationId } });
  };
  const input = { catalogRevision: catalog.revision, variant: catalog.variants[0], navigation: { hash: '#variante=' + catalog.variants[0].id } };
  const client = createRundwegClient({ storage: saved, fetchImpl, cryptoImpl: webcrypto });
  await assert.rejects(client.handoff(input));
  await client.state();
  await createRundwegClient({ storage: saved, fetchImpl, cryptoImpl: webcrypto }).handoff(input);
  assert.notEqual(bodies[0].operationId, bodies[1].operationId);
});
