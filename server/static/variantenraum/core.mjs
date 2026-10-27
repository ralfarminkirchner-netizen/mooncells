/** Local proposal operations only. No storage, network, canonical mutation, or sync. */
export const STAGES = ['proposal', 'implementation', 'verification', 'humanAcceptance'];
const TABLES = ['sources', 'rooms', 'components', 'variants', 'relations', 'dissent'];
const clone = value => JSON.parse(JSON.stringify(value));
const text = value => typeof value === 'string' && value.trim().length > 0;
const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const list = value => Array.isArray(value) ? value : [];
const unique = values => [...new Set(values)];
export function canonicalJSON(value) {
  if (Array.isArray(value)) return '[' + value.map(canonicalJSON).join(',') + ']';
  if (object(value)) return '{' + Object.keys(value).sort().map(key => JSON.stringify(key) + ':' + canonicalJSON(value[key])).join(',') + '}';
  return JSON.stringify(value);
}
const equal = (left, right) => canonicalJSON(left) === canonicalJSON(right);
function receiptEvidenceError(receipt) {
  if (receipt.evidenceDisposition !== undefined && !['not-reviewed', 'reviewed-rejected', 'received'].includes(receipt.evidenceDisposition)) return 'Quittung: unbekannter Befundzustand.';
  if (receipt.evidenceSourceIds !== undefined && (!Array.isArray(receipt.evidenceSourceIds) || receipt.evidenceSourceIds.some(id => !text(id)))) return 'Quittung: ungültige Befundquellen.';
  for (const key of ['testRun', 'blockedBy', 'finding']) if (receipt[key] !== undefined && !text(receipt[key])) return 'Quittung: unbenannter Prüfbezug.';
  if (receipt.evidenceDisposition === 'reviewed-rejected' && (!text(receipt.blockedBy) || !text(receipt.finding) || (!list(receipt.evidenceSourceIds).length && !text(receipt.testRun)))) return 'Geprüfte Ablehnung braucht Verantwortlichen, Befund und Quelle oder Testlauf.';
  return null;
}

/** Checks declared source bindings; does not attest to remote source contents. */
export function validateCatalog(catalog, {knownVariants = []} = {}) {
  const errors = [];
  const fail = message => errors.push(message);
  if (!object(catalog)) return {valid: false, errors: ['Katalog muss ein Objekt sein.']};
  if (catalog.schemaVersion !== 1) fail('Unbekannte Katalogversion.');
  for (const field of ['title', 'revision']) if (!text(catalog[field])) fail(`Katalog: ${field} fehlt.`);
  const indexes = {};
  const globalIds = new Set();
  for (const table of [...TABLES, 'receipts']) {
    if (table !== 'receipts' && !Array.isArray(catalog[table])) fail(`${table}: Liste fehlt.`);
    if (catalog[table] !== undefined && !Array.isArray(catalog[table])) fail(`${table}: ungültige Liste.`);
    indexes[table] = new Map();
    for (const row of list(catalog[table])) {
      if (!object(row) || !text(row.id)) { fail(`${table}: eindeutige Kennung fehlt.`); continue; }
      if (globalIds.has(row.id)) fail(`${table}: doppelte Kennung ${row.id}.`);
      globalIds.add(row.id); indexes[table].set(row.id, row);
    }
  }
  const reference = (table, id, label) => {
    if (!text(id) || !indexes[table].has(id)) fail(`${label}: unbekannter Bezug ${id ?? ''}.`);
  };
  for (const source of indexes.sources.values()) {
    if (!text(source.title)) fail('Quelle: Titel fehlt.');
    if (source.visibility !== 'public') fail('Dieser Katalog erlaubt nur ausdrücklich öffentliche Quellen.');
    if (!['verified', 'unverified', 'unknown'].includes(source.status)) fail('Quelle: Kenntnisstatus fehlt.');
    if (source.revision != null && !text(source.revision)) fail('Quelle: ungültiger Quellenstand.');
    if (source.contentHash != null && !/^[a-f0-9]{64}$/i.test(source.contentHash)) fail('Quelle: ungültige SHA256-Angabe.');
  }
  for (const room of indexes.rooms.values()) {
    if (!text(room.title) || !text(room.description)) fail('Raum: Name oder Beschreibung fehlt.');
    if (!['open', 'available'].includes(room.contributionStatus)) fail('Raum: Beitragszustand fehlt.');
    if (room.knowledgeStatus !== undefined && !['known', 'partial', 'unknown'].includes(room.knowledgeStatus)) fail('Raum: ungültiger Kenntnisstand.');
  }
  for (const component of indexes.components.values()) {
    if (!text(component.title) || !text(component.workIdentity)) fail('Bestandteil: Name oder Werkidentität fehlt.');
    if (component.roomId !== undefined) reference('rooms', component.roomId, 'Bestandteilraum');
  }
  const checkContext = (context, label) => {
    if (!object(context) || !text(context.question) || !Array.isArray(context.conditions)
        || context.conditions.some(condition => !text(condition))) fail(`${label}: Frage und ausdrückliche Bedingungen erforderlich.`);
  };
  const checkMandate = (mandate, label) => {
    if (!object(mandate) || !['status', 'actor', 'scope'].every(key => text(mandate[key]))) fail(`${label}: Mandat mit Status, Akteur und Umfang erforderlich.`);
  };
  for (const variant of indexes.variants.values()) {
    if (!text(variant.title)) fail('Gesamtvariante: Titel fehlt.');
    checkContext(variant.context, 'Gesamtvariante'); checkMandate(variant.mandate, 'Gesamtvariante');
    for (const stage of STAGES) {
      if (!object(variant[stage]) || !text(variant[stage].status) || !text(variant[stage].summary)) fail(`Gesamtvariante: getrennte Stufe ${stage} fehlt.`);
    }
    if (!Array.isArray(variant.parentIds) || !Array.isArray(variant.dissentIds) || !Array.isArray(variant.componentBindings)) fail('Gesamtvariante: Eltern, Einwände und Bestandteile müssen Listen sein.');
    for (const field of ['parentIds', 'dissentIds']) if (unique(list(variant[field])).length !== list(variant[field]).length) fail(`Gesamtvariante: ${field} enthält doppelte Bezüge.`);
    for (const id of list(variant.parentIds)) {
      reference('variants', id, 'Elternfassung');
      if (id === variant.id) fail('Gesamtvariante darf nicht von sich selbst abstammen.');
    }
    for (const id of list(variant.dissentIds)) reference('dissent', id, 'Einwand');
    const componentIds = new Set();
    for (const binding of list(variant.componentBindings)) {
      if (!object(binding)) { fail('Ungültige Komponentenbindung.'); continue; }
      reference('components', binding.componentId, 'Bestandteil');
      reference('sources', binding.sourceId, 'Komponentenquelle');
      reference('rooms', binding.roomId, 'Komponentenraum');
      if (componentIds.has(binding.componentId)) fail('Ein Bestandteil hat mehrere uneindeutige Bindungen.');
      componentIds.add(binding.componentId);
      if (!text(binding.role)) fail('Komponentenbindung: situationsbezogene Rolle fehlt.');
      if (binding.requiresRelationIds !== undefined && !Array.isArray(binding.requiresRelationIds)) fail('Komponentenabhängigkeiten müssen eine Liste sein.');
      for (const id of list(binding.requiresRelationIds)) reference('relations', id, 'Komponentenvoraussetzung');
      const component = indexes.components.get(binding.componentId);
      if (binding.workIdentity !== undefined && binding.workIdentity !== component?.workIdentity) fail('Falsche Werkgleichsetzung in Komponentenbindung.');
      if (!['pinned', 'unknown'].includes(binding.bindingStatus)) fail('Komponentenbindung muss festgelegt oder ausdrücklich unbekannt sein.');
      if (binding.bindingStatus === 'pinned') {
        const source = indexes.sources.get(binding.sourceId);
        if (!text(binding.revision) && !text(binding.contentHash)) fail('Festgelegte Komponentenbindung braucht Quellenstand oder Prüfsumme.');
        if (binding.revision != null && binding.revision !== source?.revision) fail('Komponentenstand stimmt nicht mit der Quelle überein.');
        if (binding.contentHash != null && binding.contentHash !== source?.contentHash) fail('Komponentenprüfsumme stimmt nicht mit der Quelle überein.');
      }
      if (binding.contentHash != null && !/^[a-f0-9]{64}$/i.test(binding.contentHash)) fail('Komponentenbindung: ungültige SHA256-Angabe.');
    }
    if (!object(variant.provenance) || !text(variant.provenance.kind) || !Array.isArray(variant.provenance.sourceVariantIds)) fail('Gesamtvariante: Herkunft fehlt.');
    else {
      if (unique(variant.provenance.sourceVariantIds).length !== variant.provenance.sourceVariantIds.length) fail('Herkunftsfassungen sind mehrfach belegt.');
      for (const id of variant.provenance.sourceVariantIds) reference('variants', id, 'Herkunftsfassung');
      for (const id of list(variant.provenance.componentIds)) reference('components', id, 'Herkunftsbestandteil');
    }
  }
  // Parent links form a DAG. Relationship links may deliberately express cycles.
  const visiting = new Set(), visited = new Set();
  function visit(id) {
    if (visiting.has(id)) { fail('Zyklische Variantenabstammung.'); return; }
    if (visited.has(id)) return;
    visiting.add(id);
    for (const parentId of list(indexes.variants.get(id)?.parentIds)) if (indexes.variants.has(parentId)) visit(parentId);
    visiting.delete(id); visited.add(id);
  }
  for (const id of indexes.variants.keys()) visit(id);
  for (const relation of indexes.relations.values()) {
    reference('variants', relation.fromVariantId, 'Beziehungsursprung');
    reference('variants', relation.toVariantId, 'Beziehungsziel');
    if (!text(relation.type) || !text(relation.summary)) fail('Beziehung braucht Art und Beschreibung.');
    if (relation.sourceIds !== undefined && !Array.isArray(relation.sourceIds)) fail('Beziehungsquellen müssen eine Liste sein.');
    for (const id of list(relation.sourceIds)) reference('sources', id, 'Beziehungsquelle');
    if (relation.compatibility !== undefined && !['unknown', 'blocked', 'compatible'].includes(relation.compatibility)) fail('Beziehung: ungültige lokale Verträglichkeitsangabe.');
    if (relation.dependsOnRelationIds !== undefined && !Array.isArray(relation.dependsOnRelationIds)) fail('Beziehungsabhängigkeiten müssen eine Liste sein.');
    for (const id of list(relation.dependsOnRelationIds)) reference('relations', id, 'Beziehungsabhängigkeit');
  }
  for (const dissent of indexes.dissent.values()) {
    if (!text(dissent.title) || !text(dissent.summary) || !text(dissent.status) || !Array.isArray(dissent.variantIds)) fail('Einwand braucht Beschreibung, Zustand und Fassungsbezüge.');
    for (const id of list(dissent.variantIds)) reference('variants', id, 'Einwandsfassung');
  }
  for (const receipt of indexes.receipts.values()) {
    reference('variants', receipt.variantId, 'Quittungsfassung');
    if (!text(receipt.operationId) || !object(receipt.request) || receipt.request.operationId !== receipt.operationId) fail('Quittung: genauer Versuch fehlt.');
    const variant = indexes.variants.get(receipt.variantId);
    if (receipt.request?.newVariantId !== receipt.variantId || variant?.provenance?.operationId !== receipt.operationId) fail('Quittung und abgeleitete Fassung gehören nicht zum selben Versuch.');
    const evidenceError = receiptEvidenceError(receipt);
    if (evidenceError) fail(evidenceError);
    for (const id of list(receipt.evidenceSourceIds)) reference('sources', id, 'Quittungsbefund');
  }
  if (new Set(list(catalog.receipts).map(receipt => receipt?.operationId)).size !== list(catalog.receipts).length) fail('Wiederholungskennung ist mehrfach belegt.');
  for (const known of knownVariants) {
    if (!equal(indexes.variants.get(known.id), known)) fail('Eine bekannte Gesamtvariante wurde verändert oder entfernt.');
  }
  return {valid: errors.length === 0, errors};
}

function assertCatalog(catalog, options) {
  const result = validateCatalog(catalog, options);
  if (!result.valid) throw new Error(result.errors.join(' '));
}
function getVariant(catalog, id) {
  const variant = catalog.variants.find(row => row.id === id);
  if (!variant) throw new Error('Die ausgewählte Gesamtvariante ist nicht vorhanden.');
  return variant;
}

export function compareVariants(catalog, leftId, rightId) {
  assertCatalog(catalog);
  const left = getVariant(catalog, leftId), right = getVariant(catalog, rightId);
  const before = new Map(left.componentBindings.map(binding => [binding.componentId, binding]));
  const after = new Map(right.componentBindings.map(binding => [binding.componentId, binding]));
  const components = unique([...before.keys(), ...after.keys()]).map(componentId => {
    const a = before.get(componentId) || null, b = after.get(componentId) || null;
    return {componentId, title: catalog.components.find(row => row.id === componentId).title,
      change: !a ? 'added' : !b ? 'removed' : equal(a, b) ? 'same' : 'changed', before: a, after: b};
  });
  const dissentIds = unique([...left.dissentIds, ...right.dissentIds]);
  return clone({left, right, contextChanged: !equal(left.context, right.context),
    mandateChanged: !equal(left.mandate, right.mandate), components,
    dissent: catalog.dissent.filter(row => dissentIds.includes(row.id)),
    dependencyReview: {left: assessBindingDependencies(catalog, left.componentBindings), right: assessBindingDependencies(catalog, right.componentBindings)},
    stages: Object.fromEntries(STAGES.map(stage => [stage, {before: left[stage], after: right[stage], changed: !equal(left[stage], right[stage])}]))});
}

/** The caller must retain/export the returned catalog, including its receipt. */
export function applyContributionPackage(catalog, request) {
  assertCatalog(catalog);
  if (!object(request)) throw new Error('Beitragspaket fehlt.');
  const allowed = new Set(['kind', 'operationId', 'newVariantId', 'title', 'sourceVariantId', 'targetVariantId', 'componentIds', 'roleChanges', 'context', 'mandate', 'expectedWorkIdentities']);
  if (Object.keys(request).some(key => !allowed.has(key))) throw new Error('Unbekannte Paketfelder; Werkidentitäten dürfen nicht umgedeutet werden.');
  if (!['partial-adoption', 'role-change'].includes(request.kind)) throw new Error('Unbekannte Beitragsart.');
  for (const key of ['operationId', 'newVariantId', 'title', 'sourceVariantId', 'targetVariantId']) if (!text(request[key])) throw new Error('Beitragspaket braucht benannte Quelle, Ziel und neuen Versuch.');
  const previous = list(catalog.receipts).find(receipt => receipt.operationId === request.operationId);
  if (previous) {
    if (!equal(previous.request, request)) throw new Error('Diese Wiederholungskennung gehört zu anderem Paket, Kontext oder Mandat. Neuer Versuch erforderlich.');
    return {catalog: clone(catalog), variant: clone(getVariant(catalog, previous.variantId)), receipt: clone(previous), replayed: true};
  }
  if (catalog.variants.some(variant => variant.id === request.newVariantId)) throw new Error('Bekannte Gesamtvarianten dürfen nicht überschrieben werden.');
  const source = getVariant(catalog, request.sourceVariantId), target = getVariant(catalog, request.targetVariantId);
  if (request.expectedWorkIdentities !== undefined && !object(request.expectedWorkIdentities)) throw new Error('Werkidentitätsprüfung braucht eine ausdrückliche Zuordnung.');
  if (request.kind === 'partial-adoption' && request.roleChanges !== undefined) throw new Error('Teilübernahme und Rollenwechsel brauchen getrennte Versuche.');
  if (request.kind === 'role-change' && request.componentIds !== undefined) throw new Error('Rollenwechsel verwendet nur die ausdrücklich benannten Rollen.');
  for (const [componentId, identity] of Object.entries(request.expectedWorkIdentities || {})) {
    if (catalog.components.find(component => component.id === componentId)?.workIdentity !== identity) throw new Error('Falsche Werkgleichsetzung im Beitragspaket.');
  }
  let bindings = clone(target.componentBindings);
  let selected = [];
  if (request.kind === 'partial-adoption') {
    if (!Array.isArray(request.componentIds) || !request.componentIds.length || unique(request.componentIds).length !== request.componentIds.length) throw new Error('Teilübernahme braucht eine eindeutige ausdrückliche Auswahl.');
    selected = request.componentIds;
    for (const componentId of selected) {
      const binding = source.componentBindings.find(row => row.componentId === componentId);
      if (!binding) throw new Error('Der gewählte Bestandteil fehlt in der Quellfassung.');
      const index = bindings.findIndex(row => row.componentId === componentId);
      if (index < 0) bindings.push(clone(binding)); else bindings[index] = clone(binding);
    }
  } else {
    if (source.id !== target.id || !object(request.roleChanges) || !Object.keys(request.roleChanges).length) throw new Error('Rollenwechsel braucht dieselbe Ausgangsfassung und ausdrückliche Rollen.');
    for (const [componentId, role] of Object.entries(request.roleChanges)) {
      const binding = bindings.find(row => row.componentId === componentId);
      if (!binding || !text(role)) throw new Error('Rollenwechsel braucht vorhandenen Bestandteil und benannte Rolle.');
      binding.role = role;
    }
    selected = Object.keys(request.roleChanges);
  }
  const variant = {
    ...clone(target),
    id: request.newVariantId, title: request.title, parentIds: unique([target.id, source.id]),
    componentBindings: bindings, context: clone(request.context ?? null), mandate: clone(request.mandate ?? null),
    proposal: {status: 'proposed', summary: 'Lokal zusammengestellter Vorschlag mit ausdrücklicher Herkunft.'},
    implementation: {status: 'open', summary: 'Die Zusammenstellung belegt keine Umsetzung in den beteiligten Räumen.'},
    verification: {status: 'unverified', summary: 'Für diesen neuen Versuch ist eine eigene Prüfung offen.'},
    humanAcceptance: {status: 'awaiting', summary: 'Eine menschliche Annahme ist nicht erklärt.'},
    dissentIds: unique([...target.dissentIds, ...source.dissentIds]),
    provenance: {kind: request.kind, sourceVariantIds: unique([target.id, source.id]), operationId: request.operationId, componentIds: selected},
    dependencyReview: assessBindingDependencies(catalog, bindings),
  };
  const receipt = {id: 'receipt-' + request.operationId, operationId: request.operationId, request: clone(request), variantId: variant.id, evidenceDisposition: 'received'};
  const next = clone(catalog);
  next.variants.push(variant); next.receipts = [...list(next.receipts), receipt];
  assertCatalog(next, {knownVariants: catalog.variants});
  return {catalog: next, variant: clone(variant), receipt: clone(receipt), replayed: false};
}

export function createPartialAdoption(catalog, request) {
  return applyContributionPackage(catalog, {...request, kind: 'partial-adoption'});
}
export function changeRole(catalog, request) {
  return applyContributionPackage(catalog, {...request, kind: 'role-change'});
}

/** Relationship evidence is local; no set of these checks proves whole-system compatibility. */
export function assessCompatibility(catalog) {
  assertCatalog(catalog);
  const byId = new Map(catalog.relations.map(relation => [relation.id, relation]));
  function dependencies(id, visited = new Set()) {
    if (visited.has(id)) return visited;
    visited.add(id);
    for (const dependency of list(byId.get(id)?.dependsOnRelationIds)) dependencies(dependency, visited);
    return visited;
  }
  return {overall: 'unknown', relations: catalog.relations.map(relation => {
    const reachable = [...dependencies(relation.id)];
    const blockedByRelationIds = reachable.filter(id => byId.get(id).compatibility === 'blocked');
    return {relationId: relation.id, status: blockedByRelationIds.length ? 'blocked' : 'unknown',
      declaredStatus: relation.compatibility ?? 'unknown', blockedByRelationIds,
      checkedRelationIds: reachable,
      dependencyInformation: reachable.every(id => Array.isArray(byId.get(id).dependsOnRelationIds)) ? 'declared' : 'unknown'};
  })};
}

/** Carries scoped conflict origins forward; absence of evidence never means clearance. */
export function assessBindingDependencies(catalog, bindings) {
  const review = assessCompatibility(catalog);
  const byId = new Map(review.relations.map(relation => [relation.relationId, relation]));
  const conflictRelationIds = [], blockedComponentIds = [], unknownComponentIds = [];
  for (const binding of bindings) {
    const requirements = binding.requiresRelationIds;
    if (!Array.isArray(requirements)) { unknownComponentIds.push(binding.componentId); continue; }
    const origins = [];
    for (const id of requirements) {
      const relation = byId.get(id);
      if (!relation) throw new Error('Unbekannte Beziehungsvoraussetzung.');
      origins.push(...relation.blockedByRelationIds);
    }
    if (origins.length) blockedComponentIds.push(binding.componentId);
    // A complete dependency list is still not implementation/acceptance evidence.
    unknownComponentIds.push(binding.componentId);
    conflictRelationIds.push(...origins);
  }
  return {scope: 'variant-bindings-only', overall: 'unknown', status: blockedComponentIds.length ? 'blocked' : 'unknown',
    conflictRelationIds: unique(conflictRelationIds), conflictRelations: clone(catalog.relations.filter(row => conflictRelationIds.includes(row.id))),
    blockedComponentIds: unique(blockedComponentIds), unknownComponentIds: unique(unknownComponentIds)};
}

/** Matching identity is insufficient for content equality, including notes and labels. */
export function classifyEntityConflict(before, after) {
  if (!object(before) || !object(after) || !text(before.id) || before.id !== after.id) throw new Error('Inhaltsvergleich braucht dieselbe ausdrücklich gebundene Identität.');
  const changedFields = unique([...Object.keys(before), ...Object.keys(after)]).filter(key => !equal(before[key], after[key]));
  return {status: changedFields.length ? 'content-conflict' : 'same', changedFields};
}

function assertDecisionState(state) {
  if (!object(state) || !text(state.scopeId) || !text(state.actor) || !Number.isSafeInteger(state.epoch) || state.epoch < 0
      || !text(state.status) || !Array.isArray(state.history) || !Array.isArray(state.receipts)) throw new Error('Lokale Entscheidung braucht eigenen Bereich, Akteur, Epoche und Historie.');
}

/** Epochs order decisions only inside this one local actor/scope; they are not distributed clocks. */
export function createLocalDecision({scopeId, actor, status = 'open'}) {
  const state = {scopeId, actor, epoch: 0, status, history: [], receipts: []};
  assertDecisionState(state);
  return state;
}

export function advanceLocalDecision(state, {status}) {
  assertDecisionState(state);
  if (!text(status) || state.epoch === Number.MAX_SAFE_INTEGER) throw new Error('Lokale Entscheidung braucht einen benannten neuen Zustand.');
  return {...clone(state), epoch: state.epoch + 1, status,
    history: [...clone(state.history), {epoch: state.epoch, status: state.status}]};
}

/** A receipt records an acknowledgement, never human acceptance. Late receipts remain history. */
export function recordLocalReceipt(state, receipt) {
  assertDecisionState(state);
  if (!object(receipt) || !text(receipt.id) || !text(receipt.operationId) || receipt.scopeId !== state.scopeId || receipt.actor !== state.actor
      || !Number.isSafeInteger(receipt.decisionEpoch) || receipt.decisionEpoch < 0 || receipt.decisionEpoch > state.epoch) throw new Error('Quittung gehört nicht zu einem bekannten lokalen Entscheidungsbereich.');
  const evidenceError = receiptEvidenceError(receipt);
  if (evidenceError) throw new Error(evidenceError);
  const previous = state.receipts.find(row => row.receipt.id === receipt.id);
  if (previous) {
    if (!equal(previous.receipt, receipt)) throw new Error('Quittungskennung wurde für andere Angaben wiederverwendet.');
    return {state: clone(state), receipt: clone(previous), replayed: true};
  }
  const recorded = {receipt: clone(receipt), late: receipt.decisionEpoch < state.epoch};
  return {state: {...clone(state), receipts: [...clone(state.receipts), recorded]}, receipt: recorded, replayed: false};
}
