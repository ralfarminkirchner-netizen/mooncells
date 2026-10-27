import { canonicalJSON, validateCatalog } from './core.mjs';

const clone = value => JSON.parse(JSON.stringify(value));
const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const digestPattern = /^[a-f0-9]{64}$/;

export async function digestJSON(value, cryptoImpl = globalThis.crypto) {
  const bytes = new TextEncoder().encode(canonicalJSON(value));
  const digest = await cryptoImpl.subtle.digest('SHA-256', bytes);
  return [...new Uint8Array(digest)].map(byte => byte.toString(16).padStart(2, '0')).join('');
}

export async function verifySealed(value) {
  if (!object(value) || !digestPattern.test(value.digest || '')) return false;
  const { digest, ...contents } = value;
  return await digestJSON(contents) === digest;
}

/** Adds only server-returned overall variants; published catalog rows stay immutable. */
export function mergeRundwegState(baseCatalog, remote, knownVariants = []) {
  if (!object(remote) || !Array.isArray(remote.variants) || !Array.isArray(remote.handoffs)) throw new Error('state');
  const next = clone(baseCatalog);
  const variants = new Map(next.variants.map(variant => [variant.id, variant]));
  for (const variant of remote.variants) {
    if (!object(variant) || typeof variant.id !== 'string') throw new Error('variant');
    if (variants.has(variant.id)) {
      if (canonicalJSON(variants.get(variant.id)) !== canonicalJSON(variant)) throw new Error('immutable');
    } else { variants.set(variant.id, clone(variant)); }
  }
  next.variants = [...variants.values()];
  if (!validateCatalog(next, { knownVariants: [...baseCatalog.variants, ...knownVariants] }).valid) throw new Error('catalog');
  return next;
}

export function handoffsForVariant(handoffs, variant) {
  return handoffs.filter(entry => entry?.packet?.source?.roomId === 'room-dazwischen' && (
    entry.packet.source.variantId === variant.id || entry.adoption?.variantId === variant.id ||
    (variant.roomReceipts || []).some(receipt => receipt.packetDigest === entry.packet.digest)
  ));
}

/** Integrity and local freshness checks; a digest is no proof of human authority. */
export async function inspectHandoff(entry, catalog) {
  const packet = entry?.packet;
  const source = packet?.source;
  const current = catalog.variants.find(variant => variant.id === source?.variantId);
  const mandate = packet?.mandate;
  const fragment = packet?.navigation?.hash;
  const validPacket = packet?.format === 'kintegrity.roundtrip.v1' && source?.roomId === 'room-dazwischen' &&
    object(source.variantSnapshot) && source.variantSnapshot.id === source.variantId &&
    mandate?.executor === 'Codex' && mandate.role === 'Technische Ausführung' &&
    typeof mandate.text === 'string' && !!mandate.text.trim() && typeof mandate.scope === 'string' && !!mandate.scope.trim() &&
    packet.target?.name === 'DAS DAZWISCHEN' && typeof packet.target.revision === 'string' &&
    typeof fragment === 'string' && fragment.startsWith('#') && fragment.length <= 8000 &&
    packet.returnUrl === '/variantenraum/index.html' + fragment && await verifySealed(packet) &&
    await digestJSON(source.variantSnapshot) === source.variantDigest;
  const stale = source?.catalogRevision !== catalog.revision || !current || await digestJSON(current) !== source?.variantDigest;
  const receipt = entry?.receipt;
  const validReceipt = !!receipt && await verifySealed(receipt) && receipt.packetDigest === packet?.digest &&
    receipt.actor?.name === 'Codex' && receipt.actor.role === mandate?.role &&
    receipt.actor.mandate === mandate?.text && receipt.actor.scope === mandate?.scope &&
    receipt.actor.identityBasis === 'configured-local-technical-executor' &&
    receipt.targetRevision === packet?.target?.revision && receipt.returnUrl === packet?.returnUrl &&
    receipt.transport === 'received' &&
    receipt.review === 'not-reviewed' && receipt.humanAcceptance === 'open';
  return {
    validPacket: !!validPacket, validReceipt, stale,
    canContinue: !!validPacket && !stale && !entry.withdrawn,
    canAdopt: !!validPacket && validReceipt && !stale && !entry.withdrawn && !entry.adoption,
  };
}

export function dazwischenUrl(entry, origin) {
  const operationId = entry?.packet?.operationId;
  if (typeof operationId !== 'string' || !/^[a-f0-9-]{36}$/i.test(operationId)) throw new Error('destination');
  const expected = new URL('/dazwischen/', origin);
  expected.searchParams.set('rundweg', operationId);
  if (entry.dazwischenUrl) {
    const supplied = new URL(entry.dazwischenUrl, origin);
    if (supplied.href !== expected.href) throw new Error('destination');
  }
  return expected.pathname + expected.search;
}

/** Stores public request intents only, so a lost POST response can replay exactly. */
export function createRundwegClient({ fetchImpl = globalThis.fetch, storage, cryptoImpl = globalThis.crypto, timeout = 8000 } = {}) {
  const storageKey = 'mooncells.rundweg.pending/1';
  let intents = [];
  try {
    const saved = JSON.parse(storage?.getItem(storageKey) || '[]');
    if (Array.isArray(saved)) intents = saved.filter(item => object(item) && typeof item.key === 'string' && object(item.body) && typeof item.body.operationId === 'string');
  } catch { /* Memory retry still works when session storage is unavailable. */ }
  function persist() { try { storage?.setItem(storageKey, JSON.stringify(intents)); } catch { /* No private payload is cached. */ } }
  function intent(kind, input) {
    const key = canonicalJSON({ kind, input });
    let item = intents.find(saved => saved.key === key);
    if (!item) { item = { key, body: { operationId: cryptoImpl.randomUUID(), ...input } }; intents.push(item); persist(); }
    return item;
  }
  function forgetWithdrawn(handoffs) {
    const withdrawn = new Set((Array.isArray(handoffs) ? handoffs : []).filter(entry => entry.withdrawn).map(entry => entry.packet?.operationId));
    intents = intents.filter(item => {
      if (withdrawn.has(item.body.operationId)) return false;
      try { return ![...withdrawn].some(op => JSON.parse(item.key).kind === 'adopt:' + op); } catch { return true; }
    });
    persist();
  }
  async function request(path, body) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeout);
    try {
      const response = await fetchImpl(path, { method: body === undefined ? 'GET' : 'POST', cache: 'no-store',
        credentials: 'same-origin', redirect: 'error', signal: controller.signal,
        headers: body === undefined ? {} : { 'Content-Type': 'application/json', 'X-Rundweg-Request': '1' },
        ...(body === undefined ? {} : { body: JSON.stringify(body) }) });
      if (!response.ok) throw new Error('request');
      return await response.json();
    } finally { clearTimeout(timer); }
  }
  async function mutation(path, item) {
    const result = await request(path, item.body);
    if (!object(result?.packet)) throw new Error('response');
    intents = intents.filter(saved => saved !== item); persist();
    return result;
  }
  const operationPath = entry => '/api/rundweg/handoffs/' + encodeURIComponent(entry.packet.operationId);
  return {
    async state() { const result = await request('/api/rundweg/state'); forgetWithdrawn(result.handoffs); return result; },
    async handoff({ catalogRevision, variant, navigation }) {
      const input = { catalogRevision, variantId: variant.id, roomId: 'room-dazwischen', navigation,
        expectedVariantDigest: await digestJSON(variant, cryptoImpl) };
      return mutation('/api/rundweg/handoffs', intent('handoff', input));
    },
    adopt: entry => mutation(operationPath(entry) + '/adopt', intent('adopt:' + entry.packet.operationId, {
      receiptDigest: entry.receipt.digest, expectedVariantDigest: entry.packet.source.variantDigest,
    })),
    async withdraw(entry) { const result = await request(operationPath(entry) + '/withdraw', {}); forgetWithdrawn([result]); return result; },
  };
}
