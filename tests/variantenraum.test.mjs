import test from 'node:test';
import assert from 'node:assert/strict';
import {
  validateCatalog, compareVariants, createPartialAdoption, changeRole, canonicalJSON,
  assessCompatibility, assessBindingDependencies, classifyEntityConflict,
  createLocalDecision, advanceLocalDecision, recordLocalReceipt,
} from '../server/static/variantenraum/core.mjs';

const copy = value => JSON.parse(JSON.stringify(value));
const context = {question: 'Wie verbinden wir Werk und Quellen?', conditions: ['Nur lokaler Vorschlag']};
const mandate = {status: 'proposed', actor: 'Ada', seat: 'Werkstatt', scope: 'Vergleich eines Entwurfs'};
const stages = () => ({
  proposal: {status: 'observed', summary: 'Benannte Ausgangsidee'},
  implementation: {status: 'partial', summary: 'Nur ein Teil wurde umgesetzt'},
  verification: {status: 'unverified', summary: 'Prüfung bleibt offen'},
  humanAcceptance: {status: 'awaiting', summary: 'Keine Annahme erklärt'},
});
function fixture() {
  const binding = (componentId, sourceId, role, revision, contentHash) => ({
    componentId, sourceId, role, roomId: 'room-workshop',
    bindingStatus: revision ? 'pinned' : 'unknown', revision, contentHash,
    authors: ['Ada'], negotiationResponsibility: {actor: 'Ada', scope: 'Quellenbezug'},
  });
  return {
    schemaVersion: 1, title: 'Lokale Prüfbeispiele', revision: 'test-1',
    sources: [
      {id: 'src-a', title: 'Öffentliche Zusammenfassung A', visibility: 'public', status: 'unverified', revision: 'summary-a', contentHash: 'a'.repeat(64)},
      {id: 'src-b', title: 'Öffentliche Zusammenfassung B', visibility: 'public', status: 'unverified', revision: 'summary-b', contentHash: 'b'.repeat(64)},
      {id: 'src-unknown', title: 'Offener Beitrag', visibility: 'public', status: 'unknown', revision: null, contentHash: null},
    ],
    rooms: [
      {id: 'room-workshop', title: 'Werkstatt', description: 'Entwürfe vergleichen', contributionStatus: 'available', knowledgeStatus: 'partial'},
      {id: 'room-open', title: 'Offener Raum', description: 'Beitrag wird noch erbeten', contributionStatus: 'open', knowledgeStatus: 'unknown'},
    ],
    components: [
      {id: 'component-word', title: 'Wortwerk', workIdentity: 'work-word', roomId: 'room-workshop'},
      {id: 'component-time', title: 'Zeitspur', workIdentity: 'work-time', roomId: 'room-workshop'},
    ],
    variants: [
      {id: 'variant-a', title: 'Werknahe Fassung', parentIds: [], context: copy(context), mandate: copy(mandate), ...stages(),
        componentBindings: [binding('component-word', 'src-a', 'Träger', 'summary-a', 'a'.repeat(64)), binding('component-time', 'src-unknown', 'Zeuge', null, null)],
        dissentIds: [], provenance: {kind: 'inventory', sourceVariantIds: []},
        authors: ['Ada'], negotiationResponsibility: {actor: 'Ada', scope: 'Werkbezug'},
      },
      {id: 'variant-b', title: 'Quellennahe Fassung', parentIds: [], context: {...copy(context), conditions: ['Andere Fragestellung']},
        mandate: {...copy(mandate), scope: 'Alternativer Quellenbezug'}, ...stages(), proposal: {status: 'proposed', summary: 'Andere Gesamtidee'},
        componentBindings: [binding('component-word', 'src-b', 'Begleiter', 'summary-b', 'b'.repeat(64)), binding('component-time', 'src-unknown', 'Erzähler', null, null)],
        dissentIds: ['dissent-source'], provenance: {kind: 'proposal', sourceVariantIds: []},
      },
    ],
    relations: [{id: 'relation-a-b', fromVariantId: 'variant-a', toVariantId: 'variant-b', type: 'alternative', summary: 'Zwei Perspektiven bleiben offen', compatibility: 'unknown', dependsOnRelationIds: []}],
    dissent: [{id: 'dissent-source', title: 'Quellenverlust vermeiden', summary: 'Die Quelle braucht ihren eigenen Rückweg', status: 'open', variantIds: ['variant-b'], authors: ['Berta'], negotiationResponsibility: {actor: 'Berta', scope: 'Quellenrückweg'}}],
  };
}
const packageRequest = (overrides = {}) => ({
  operationId: 'attempt-one', newVariantId: 'variant-derived', title: 'Benannte Teilübernahme',
  sourceVariantId: 'variant-b', targetVariantId: 'variant-a', componentIds: ['component-word'],
  context: copy(context), mandate: copy(mandate), ...overrides,
});

test('offene Räume, unbekannte Bindungen und getrennte offene Stufen sind gültig', () => {
  const catalog = fixture();
  catalog.variants.push({...copy(catalog.variants[0]), id: 'variant-open', title: 'Offener Beitrag', componentBindings: []});
  assert.deepEqual(validateCatalog(catalog), {valid: true, errors: []});
  assert.equal(catalog.variants[0].componentBindings[1].bindingStatus, 'unknown');
});

test('globale Kennungen und alle referenziellen Pfade sind geprüft', async t => {
  const cases = {
    'globale Doppelung': c => {c.rooms[0].id = 'src-a';},
    'fehlende Quelle': c => {c.variants[0].componentBindings[0].sourceId = 'missing';},
    'fehlender Raum': c => {c.components[0].roomId = 'missing';},
    'fehlender Bestandteil': c => {c.variants[0].componentBindings[0].componentId = 'missing';},
    'fehlende Herkunft': c => {c.variants[0].provenance.sourceVariantIds = ['missing'];},
    'fehlender Herkunftsbestandteil': c => {c.variants[0].provenance.componentIds = ['missing'];},
    'fehlender Einwand': c => {c.variants[0].dissentIds = ['missing'];},
    'fehlende Einwandsfassung': c => {c.dissent[0].variantIds = ['missing'];},
    'fehlende Elternfassung': c => {c.variants[0].parentIds = ['missing'];},
    'fehlendes Beziehungsziel': c => {c.relations[0].toVariantId = 'missing';},
    'fehlende Voraussetzung': c => {c.relations[0].dependsOnRelationIds = ['missing'];},
    'fehlende Komponentenvoraussetzung': c => {c.variants[0].componentBindings[0].requiresRelationIds = ['missing'];},
    'doppelte Bindung': c => {c.variants[0].componentBindings.push(copy(c.variants[0].componentBindings[0]));},
    'doppelter Einwand': c => {c.variants[1].dissentIds.push('dissent-source');},
  };
  for (const [name, mutate] of Object.entries(cases)) await t.test(name, () => {
    const catalog = fixture(); mutate(catalog);
    assert.equal(validateCatalog(catalog).valid, false);
  });
});

test('festgelegte Bindung braucht genauen deklarierten Quellenstand oder Hash', () => {
  const catalog = fixture(), binding = catalog.variants[0].componentBindings[0];
  binding.revision = null; binding.contentHash = null;
  assert.equal(validateCatalog(catalog).valid, false);
  binding.revision = 'anderer-stand';
  assert.equal(validateCatalog(catalog).valid, false);
  binding.revision = 'summary-a';
  assert.equal(validateCatalog(catalog).valid, true);
  binding.contentHash = 'b'.repeat(64);
  assert.equal(validateCatalog(catalog).valid, false);
  binding.contentHash = 'kein-hash';
  assert.equal(validateCatalog(catalog).valid, false);
});

test('Beziehungsquellen unterscheiden deklarierte Unkenntnis von ungültigen Quellenbezügen', () => {
  const catalog = fixture();
  catalog.relations[0].sourceIds = ['src-a', 'src-unknown'];
  assert.deepEqual(validateCatalog(catalog), {valid: true, errors: []});
  for (const sourceIds of [['src-a', 'missing'], 'src-a', [null]]) {
    catalog.relations[0].sourceIds = sourceIds;
    const result = validateCatalog(catalog);
    assert.equal(result.valid, false);
    assert.match(result.errors.join(' '), /Beziehungsquelle/);
    assert.throws(() => compareVariants(catalog, 'variant-a', 'variant-b'), /Beziehungsquelle/);
  }
  catalog.relations[0].sourceIds = [];
  assert.equal(validateCatalog(catalog).valid, true);
  delete catalog.relations[0].sourceIds;
  assert.equal(validateCatalog(catalog).valid, true);
});

test('keine implizite Umsetzung, Annahme oder private Quelle ersetzt fehlende Angaben', () => {
  const catalog = fixture();
  delete catalog.variants[0].humanAcceptance;
  assert.equal(validateCatalog(catalog).valid, false);
  catalog.variants[0].humanAcceptance = {status: 'open', summary: 'Offen'};
  catalog.sources[0].visibility = 'private';
  assert.equal(validateCatalog(catalog).valid, false);
});

test('Elternzyklen werden abgewiesen, beabsichtigte Beziehungszyklen bleiben möglich', () => {
  const catalog = fixture();
  catalog.relations.push({...copy(catalog.relations[0]), id: 'relation-b-a', fromVariantId: 'variant-b', toVariantId: 'variant-a'});
  assert.equal(validateCatalog(catalog).valid, true);
  catalog.variants[0].parentIds = ['variant-b']; catalog.variants[1].parentIds = ['variant-a'];
  assert.equal(validateCatalog(catalog).valid, false);
});

test('bekannte Gesamtvarianten dürfen auch an Notiz, Titel oder Status nicht verändert werden', () => {
  const known = fixture().variants;
  for (const field of ['note', 'title', 'humanAcceptance']) {
    const catalog = fixture();
    catalog.variants[0][field] = field === 'humanAcceptance' ? {status: 'accepted', summary: 'Unbelegte Änderung'} : 'Geändert';
    assert.equal(validateCatalog(catalog, {knownVariants: known}).valid, false);
  }
  const catalog = fixture(); catalog.variants.shift();
  assert.equal(validateCatalog(catalog, {knownVariants: known}).valid, false);
});

test('Vergleich trennt Kontext, Mandat, Rollen, Stufen und erhaltene Einwände', () => {
  const catalog = fixture(), before = copy(catalog);
  const comparison = compareVariants(catalog, 'variant-a', 'variant-b');
  assert.equal(comparison.contextChanged, true);
  assert.equal(comparison.mandateChanged, true);
  assert.deepEqual(comparison.components.map(row => row.change), ['changed', 'changed']);
  assert.equal(comparison.stages.proposal.changed, true);
  assert.equal(comparison.stages.implementation.changed, false);
  assert.equal(comparison.dissent[0].authors[0], 'Berta');
  assert.equal(comparison.dependencyReview.left.overall, 'unknown');
  comparison.left.title = 'Nur Ausgabekopie';
  assert.deepEqual(catalog, before);
});

test('Teilübernahme erzeugt neue Fassung, bewahrt Ursprünge und übernimmt nur Auswahl', () => {
  const catalog = fixture(), before = copy(catalog);
  const result = createPartialAdoption(catalog, packageRequest());
  assert.deepEqual(catalog, before);
  assert.deepEqual(result.catalog.variants.slice(0, 2), before.variants);
  assert.deepEqual(result.variant.parentIds, ['variant-a', 'variant-b']);
  assert.deepEqual(result.variant.provenance.componentIds, ['component-word']);
  assert.deepEqual(result.variant.componentBindings[0], before.variants[1].componentBindings[0]);
  assert.deepEqual(result.variant.componentBindings[1], before.variants[0].componentBindings[1]);
  assert.deepEqual(result.variant.dissentIds, ['dissent-source']);
  assert.deepEqual(result.catalog.dissent, before.dissent);
  assert.equal(result.variant.implementation.status, 'open');
  assert.equal(result.variant.verification.status, 'unverified');
  assert.equal(result.variant.humanAcceptance.status, 'awaiting');
  assert.equal(result.receipt.variantId, result.variant.id);
  assert.equal(validateCatalog(result.catalog, {knownVariants: before.variants}).valid, true);
});

test('verlorene Antwort wird mit exportiertem Paket, Kontext und Mandat idempotent wiederholt', () => {
  const request = packageRequest();
  const first = createPartialAdoption(fixture(), request);
  const retained = copy(first.catalog); // persistierter Katalog; die erste Antwort kann verloren sein
  const reorderedRequest = Object.fromEntries(Object.entries(request).reverse());
  const retry = createPartialAdoption(retained, reorderedRequest);
  assert.equal(retry.replayed, true);
  assert.equal(retry.variant.id, first.variant.id);
  assert.equal(retry.catalog.variants.length, 3);
  assert.equal(retry.catalog.receipts.length, 1);
  assert.equal(canonicalJSON(retry.catalog), canonicalJSON(retained));
});

test('gleiche Wiederholungskennung mit anderem Paket, Kontext oder Mandat ist kein Retry', () => {
  const request = packageRequest(), first = createPartialAdoption(fixture(), request);
  for (const changes of [
    {componentIds: ['component-time']},
    {context: {...context, conditions: ['Neue Bedingung']}},
    {mandate: {...mandate, actor: 'Berta'}},
  ]) assert.throws(() => createPartialAdoption(first.catalog, {...request, ...changes}), /Neuer Versuch erforderlich/);
  const next = createPartialAdoption(first.catalog, {...request, operationId: 'attempt-two', newVariantId: 'variant-revised', context: {...context, conditions: ['Neue Bedingung']}});
  assert.equal(next.catalog.variants.length, 4);
  assert.deepEqual(next.variant.context.conditions, ['Neue Bedingung']);
});

test('falsche Werkgleichsetzung, stilles Überschreiben und ungenaue Auswahl scheitern atomar', () => {
  const catalog = fixture(), before = copy(catalog);
  for (const changes of [
    {expectedWorkIdentities: {'component-word': 'work-time'}},
    {workMapping: {'component-word': 'component-time'}},
    {newVariantId: 'variant-a'}, {componentIds: []},
    {componentIds: ['component-word', 'component-word']}, {componentIds: ['missing']},
    {context: {question: 'Fehlt', conditions: null}},
  ]) assert.throws(() => createPartialAdoption(catalog, packageRequest(changes)));
  catalog.variants[0].componentBindings[0].workIdentity = 'work-time';
  assert.equal(validateCatalog(catalog).valid, false);
  delete catalog.variants[0].componentBindings[0].workIdentity;
  assert.deepEqual(catalog, before);
});

test('Rollenwechsel ändert weder Werkidentität, Akteur, Urheber noch Verhandlungszuständigkeit', () => {
  const catalog = fixture();
  catalog.variants[0].dissentIds = ['dissent-source'];
  const before = copy(catalog);
  const result = changeRole(catalog, {
    operationId: 'role-one', newVariantId: 'variant-role', title: 'Andere situative Rolle',
    sourceVariantId: 'variant-a', targetVariantId: 'variant-a', roleChanges: {'component-word': 'Zeuge'},
    context: copy(context), mandate: copy(mandate), expectedWorkIdentities: {'component-word': 'work-word'},
  });
  const expectedBinding = {...before.variants[0].componentBindings[0], role: 'Zeuge'};
  assert.deepEqual(result.variant.componentBindings[0], expectedBinding);
  assert.deepEqual(result.catalog.components, before.components);
  assert.deepEqual(result.catalog.dissent, before.dissent);
  assert.deepEqual(result.variant.dissentIds, ['dissent-source']);
  assert.deepEqual(result.variant.authors, before.variants[0].authors);
  assert.deepEqual(result.variant.negotiationResponsibility, before.variants[0].negotiationResponsibility);
  assert.equal(result.variant.mandate.actor, 'Ada');
  assert.equal(result.variant.mandate.seat, 'Werkstatt');
  assert.deepEqual(catalog, before);
});

function diamond() {
  const catalog = fixture();
  const relation = (id, dependencies, compatibility = 'unknown') => ({id, fromVariantId: 'variant-a', toVariantId: 'variant-b', type: 'requires', summary: 'Beziehung ' + id, compatibility, dependsOnRelationIds: dependencies});
  catalog.relations = [
    relation('relation-origin', [], 'blocked'),
    relation('relation-left', ['relation-origin']), relation('relation-right', ['relation-origin']),
    relation('relation-diamond', ['relation-left', 'relation-right']), relation('relation-independent', []),
  ];
  catalog.variants[1].componentBindings[0].requiresRelationIds = ['relation-diamond'];
  return catalog;
}

test('gerichtete Diamond-Abhängigkeit vererbt Konfliktursprung einmal, ohne globale Sperre', () => {
  const catalog = diamond(), review = assessCompatibility(catalog);
  assert.equal(review.overall, 'unknown');
  assert.deepEqual(review.relations.find(row => row.relationId === 'relation-diamond').blockedByRelationIds, ['relation-origin']);
  assert.equal(review.relations.find(row => row.relationId === 'relation-independent').status, 'unknown');
  const adopted = createPartialAdoption(catalog, packageRequest());
  assert.deepEqual(adopted.variant.dependencyReview.conflictRelationIds, ['relation-origin']);
  assert.deepEqual(adopted.variant.dependencyReview.blockedComponentIds, ['component-word']);
  assert.equal(adopted.variant.dependencyReview.conflictRelations[0].summary, 'Beziehung relation-origin');
  assert.equal(adopted.variant.dependencyReview.overall, 'unknown');
  const independent = createPartialAdoption(catalog, packageRequest({componentIds: ['component-time']}));
  assert.equal(independent.variant.dependencyReview.status, 'unknown');
  assert.deepEqual(independent.variant.dependencyReview.blockedComponentIds, []);
});

test('fehlende Abhängigkeitsinformation und deklarierte Kompatibilität geben nichts frei', () => {
  const catalog = fixture();
  delete catalog.relations[0].dependsOnRelationIds;
  catalog.relations[0].compatibility = 'compatible';
  const relation = assessCompatibility(catalog).relations[0];
  assert.equal(relation.status, 'unknown');
  assert.equal(relation.declaredStatus, 'compatible');
  assert.equal(relation.dependencyInformation, 'unknown');
  const review = assessBindingDependencies(catalog, catalog.variants[0].componentBindings);
  assert.equal(review.overall, 'unknown');
  assert.deepEqual(review.unknownComponentIds, ['component-word', 'component-time']);
});

test('Nicht-Kantendaten an gleicher Identität erzeugen Inhaltskonflikt statt stiller Gleichsetzung', () => {
  const original = {id: 'same-work', notes: 'Quelle behalten', label: 'Werk', status: 'open'};
  assert.deepEqual(classifyEntityConflict(original, copy(original)), {status: 'same', changedFields: []});
  for (const field of ['notes', 'label', 'status']) {
    assert.deepEqual(classifyEntityConflict(original, {...original, [field]: 'Geändert'}), {status: 'content-conflict', changedFields: [field]});
  }
  assert.throws(() => classifyEntityConflict(original, {...original, id: 'other-work'}));
});

test('späte Quittung nach lokalem Rückzug bleibt Historie und reaktiviert keine Annahme', () => {
  const initial = createLocalDecision({scopeId: 'local-review', actor: 'Ada', status: 'open'});
  const accepted = advanceLocalDecision(initial, {status: 'accepted'});
  const withdrawn = advanceLocalDecision(accepted, {status: 'withdrawn'});
  const receipt = {id: 'ack-one', operationId: 'attempt-one', scopeId: 'local-review', actor: 'Ada', decisionEpoch: 1};
  const late = recordLocalReceipt(withdrawn, receipt);
  assert.equal(late.receipt.late, true);
  assert.equal(late.state.status, 'withdrawn');
  assert.equal(late.state.epoch, 2);
  assert.equal(withdrawn.receipts.length, 0);
  assert.equal(late.state.history[1].status, 'accepted');
  const retry = recordLocalReceipt(late.state, copy(receipt));
  assert.equal(retry.replayed, true);
  assert.equal(retry.state.receipts.length, 1);
  assert.equal(retry.state.status, 'withdrawn');
});

test('Quittung ist nur Empfang; Epochen haben keine Ordnung zwischen Räumen oder Akteuren', () => {
  const state = createLocalDecision({scopeId: 'workshop', actor: 'Ada'});
  const receipt = {id: 'ack', operationId: 'attempt', scopeId: 'workshop', actor: 'Ada', decisionEpoch: 0};
  assert.equal(recordLocalReceipt(state, receipt).state.status, 'open');
  for (const changes of [{scopeId: 'archive'}, {actor: 'Werkstatt-Sitz'}, {decisionEpoch: 1}]) assert.throws(() => recordLocalReceipt(state, {...receipt, ...changes}));
  const anotherRoom = createLocalDecision({scopeId: 'archive', actor: 'Ada', status: 'open'});
  assert.equal(anotherRoom.status, 'open');
});

test('fehlerhafte Quittung wird als ungültiger Katalog gemeldet', () => {
  const catalog = fixture(); catalog.receipts = [null];
  assert.equal(validateCatalog(catalog).valid, false);
  const result = createPartialAdoption(fixture(), packageRequest());
  result.catalog.receipts[0].variantId = 'variant-a';
  assert.equal(validateCatalog(result.catalog).valid, false);
});

test('ungeprüft und geprüft verworfen bleiben mit verantwortlichem Befund unterscheidbar', () => {
  const state = createLocalDecision({scopeId: 'workshop', actor: 'Ada'});
  const receipt = {id: 'review-ack', operationId: 'attempt', scopeId: 'workshop', actor: 'Ada', decisionEpoch: 0};
  const unreviewed = recordLocalReceipt(state, {...receipt, evidenceDisposition: 'not-reviewed'});
  assert.equal(unreviewed.receipt.receipt.evidenceDisposition, 'not-reviewed');
  assert.throws(() => recordLocalReceipt(state, {...receipt, evidenceDisposition: 'reviewed-rejected'}), /Verantwortlichen, Befund/);
  const reviewed = {...receipt, evidenceDisposition: 'reviewed-rejected', blockedBy: 'Berta', finding: 'Quellenrückweg fehlt', testRun: 'Lokaler Rückwegtest'};
  const rejected = recordLocalReceipt(state, reviewed);
  assert.equal(rejected.state.status, 'open');
  assert.equal(rejected.receipt.receipt.blockedBy, 'Berta');
  assert.equal(rejected.receipt.receipt.finding, 'Quellenrückweg fehlt');
  assert.equal(rejected.receipt.receipt.testRun, 'Lokaler Rückwegtest');
  assert.throws(() => recordLocalReceipt(rejected.state, {...reviewed, finding: 'Anderer Befund'}), /wiederverwendet/);
  const result = createPartialAdoption(fixture(), packageRequest());
  assert.equal(result.receipt.evidenceDisposition, 'received');
  Object.assign(result.catalog.receipts[0], {evidenceDisposition: 'reviewed-rejected', blockedBy: 'Berta', finding: 'Quellenrückweg fehlt', evidenceSourceIds: ['missing']});
  assert.equal(validateCatalog(result.catalog).valid, false);
  result.catalog.receipts[0].evidenceSourceIds = ['src-a'];
  assert.equal(validateCatalog(result.catalog).valid, true);
});
