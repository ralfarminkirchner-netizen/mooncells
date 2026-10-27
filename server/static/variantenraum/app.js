import { validateCatalog, compareVariants } from './core.mjs';

const workspace = document.querySelector('#workspace');
const variantList = document.querySelector('#variant-list');
const notice = document.querySelector('#notice');
let catalog;
let state;
let indexes;
let navigationWarning = false;
const stages = [['proposal', 'Vorschlag'], ['implementation', 'Umsetzung'], ['verification', 'Prüfung'], ['humanAcceptance', 'Menschliche Annahme']];
const labels = {
  open: 'Offen', proposed: 'Vorgeschlagen', proposal: 'Vorgeschlagen', awaiting: 'Beitrag ausstehend',
  approved: 'Ausdrücklich bestätigt', accepted: 'Angenommen', confirmed: 'Bestätigt',
  implemented: 'Umgesetzt', available: 'Vorhanden', complete: 'Abgeschlossen', completed: 'Abgeschlossen',
  verified: 'Geprüft', tested: 'Geprüft', passed: 'Geprüft', documented: 'Dokumentiert',
  partial: 'Teilweise belegt', unknown: 'Noch ungeklärt', pending: 'Ausstehend', not_started: 'Noch offen',
  not_implemented: 'Noch nicht umgesetzt', not_verified: 'Noch nicht geprüft', not_accepted: 'Noch nicht angenommen',
  not_requested: 'Nicht angefragt', unverified: 'Ungeprüft', disputed: 'Strittig', unresolved: 'Offen',
  answered: 'Beantwortet', retained: 'Erhalten', historical: 'Historischer Beleg', withdrawn: 'Zurückgezogen',
  pinned: 'An eine Quellenfassung gebunden', public: 'Öffentlich', known: 'Belegt',
};
const technicalPattern = /(?:\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b|\b[0-9a-f]{7,64}\b|\/Volumes\/|\/Users\/|codex\/)/i;

function human(value, fallback = '') {
  if (typeof value !== 'string' || !value.trim() || technicalPattern.test(value)) return fallback;
  const trimmed = value.trim();
  if (indexes && [indexes.variants, indexes.rooms, indexes.components, indexes.sources, indexes.dissent].some(index => [...index.keys()].some(id => trimmed.includes(id)))) return fallback;
  return trimmed;
}
const name = (item, fallback) => human(item?.title || item?.name, fallback);
const summary = (item, fallback = '') => human(item?.summary || item?.description, fallback);
const list = value => Array.isArray(value) ? value : [];
const itemById = (kind, id) => indexes[kind].get(id);
const stage = (variant, key) => variant?.[key] && typeof variant[key] === 'object' ? variant[key] : { status: 'open' };
const statusText = value => labels[value] || 'Noch einzuordnen';
const isOpen = status => !['approved', 'accepted', 'confirmed', 'implemented', 'complete', 'completed', 'verified', 'tested', 'passed', 'answered'].includes(status);

function node(tag, attrs = {}, ...children) {
  const element = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value === null || value === undefined || value === false) continue;
    if (key.startsWith('on') && typeof value === 'function') element.addEventListener(key.slice(2).toLowerCase(), value);
    else element.setAttribute(key, String(value));
  }
  for (const child of children.flat(Infinity)) {
    if (child === null || child === undefined || child === false) continue;
    element.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return element;
}
const paragraph = (text, className) => node('p', { class: className }, text);
const button = (text, onClick, attrs = {}) => node('button', { type: 'button', onClick, ...attrs }, text);
const heading = (text, level = 3, attrs = {}) => node(`h${level}`, attrs, text);
function badge(status, text) { return node('span', { class: `badge${isOpen(status) ? ' pending' : ''}` }, text || statusText(status)); }
function technical(value) {
  return node('details', { class: 'technical' }, node('summary', {}, 'Technische Details'), node('pre', {}, JSON.stringify(value, null, 2)));
}
function announce(text) { notice.textContent = text; notice.hidden = !text; }
function safeUrl(value) {
  if (typeof value !== 'string') return null;
  try { const url = new URL(value); return url.protocol === 'https:' && !url.username && !url.password && human(url.href) ? url.href : null; } catch { return null; }
}

function defaultState() {
  return { variant: catalog.variants[0].id, view: 'variant', room: '', roomVariant: '', other: catalog.variants[1]?.id || catalog.variants[0].id, filter: 'all', query: '', back: 'variant' };
}
function readState() {
  const fallback = defaultState();
  if (location.hash.length > 8000) { navigationWarning = true; return fallback; }
  const params = new URLSearchParams(location.hash.slice(1));
  const next = { ...fallback };
  const requestedVariant = params.get('variante');
  const requestedOther = params.get('vergleich');
  const requestedRoom = params.get('raum');
  if (requestedVariant && indexes.variants.has(requestedVariant)) next.variant = requestedVariant;
  else if (requestedVariant) navigationWarning = true;
  if (requestedOther && indexes.variants.has(requestedOther)) next.other = requestedOther;
  else if (requestedOther) navigationWarning = true;
  if (next.other === next.variant) next.other = catalog.variants.find(item => item.id !== next.variant)?.id || next.variant;
  const requestedView = params.get('ansicht');
  if (['variant', 'room', 'compare'].includes(requestedView)) next.view = requestedView;
  else if (requestedView) navigationWarning = true;
  if (requestedRoom && indexes.rooms.has(requestedRoom)) next.room = requestedRoom;
  else if (requestedRoom) navigationWarning = true;
  const requestedRoomVariant = params.get('raumfassung');
  if (requestedRoomVariant && indexes.variants.has(requestedRoomVariant)) next.roomVariant = requestedRoomVariant;
  else if (requestedRoomVariant) navigationWarning = true;
  if (next.view === 'room' && !next.room) { next.view = 'variant'; navigationWarning = true; }
  if (['all', 'open', 'dissent'].includes(params.get('filter'))) next.filter = params.get('filter');
  else if (params.has('filter')) navigationWarning = true;
  next.query = human((params.get('suche') || '').slice(0, 120));
  next.back = params.get('rueckweg') === 'compare' ? 'compare' : 'variant';
  return next;
}
function hashFor(value) {
  const params = new URLSearchParams({ variante: value.variant, ansicht: value.view, vergleich: value.other, filter: value.filter });
  if (value.room) params.set('raum', value.room);
  if (value.view === 'room' && value.roomVariant) params.set('raumfassung', value.roomVariant);
  if (value.query) params.set('suche', value.query);
  if (value.view === 'room') params.set('rueckweg', value.back);
  return `#${params.toString()}`;
}
function saveHash(replace = false) {
  const hash = hashFor(state);
  if (location.hash === hash) return;
  history[replace ? 'replaceState' : 'pushState'](null, '', hash);
}
function go(patch, { focus = true, replace = false } = {}) {
  state = { ...state, ...patch };
  if (state.other === state.variant) state.other = catalog.variants.find(item => item.id !== state.variant)?.id || state.variant;
  saveHash(replace);
  render();
  if (focus) document.querySelector('#work-title')?.focus();
}
function openRoom(id, variantId = state.variant) { go({ view: 'room', room: id, roomVariant: variantId, back: state.view === 'compare' ? 'compare' : 'variant' }); }
function returnFromRoom() {
  const room = state.room;
  go({ view: state.back }, { focus: false });
  const index = catalog.rooms.findIndex(item => item.id === room);
  (document.querySelector(`[data-room-index="${index}"]`) || document.querySelector('#work-title'))?.focus();
}
function onHistory() {
  if (!catalog) return;
  state = readState(); saveHash(true); render();
  if (navigationWarning) { announce('Ein Teil des gespeicherten Einstiegs war nicht verfügbar. Die gültige Auswahl ist geöffnet.'); navigationWarning = false; }
}

function bindingsFor(variant, roomId) {
  return list(variant.componentBindings).filter(binding => !roomId || binding.roomId === roomId || itemById('components', binding.componentId)?.roomId === roomId);
}
function dissentFor(variant, roomId) {
  const selected = new Set(list(variant.dissentIds));
  return catalog.dissent.filter(item => (selected.has(item.id) || list(item.variantIds).includes(variant.id)) && (!roomId || list(item.roomIds).includes(roomId) || list(item.componentIds).some(id => itemById('components', id)?.roomId === roomId)));
}
function roomSources(room, bindings = []) {
  return [...new Set([...list(room.sourceIds), ...bindings.flatMap(binding => [binding.sourceId, ...list(itemById('components', binding.componentId)?.sourceIds)])])].filter(id => indexes.sources.has(id));
}
function sourcesView(ids) {
  const sources = [...new Set(ids)].map(id => itemById('sources', id)).filter(Boolean);
  if (!sources.length) return paragraph('Für diesen Beitrag ist noch keine zugängliche Quelle gebunden.', 'empty');
  return node('ul', { class: 'source-list' }, sources.map(source => {
    const url = safeUrl(source.url);
    return node('li', { class: 'source-item' }, node('strong', {}, name(source, 'Quelle ohne verständlichen Titel')),
      summary(source) && paragraph(summary(source)),
      source.status && badge(source.status),
      url && node('p', {}, node('a', { href: url, target: '_blank', rel: 'noopener noreferrer' }, 'Quelle in einem neuen Fenster öffnen ↗')),
      technical({ id: source.id, revision: source.revision, contentHash: source.contentHash, visibility: source.visibility, locator: source.locator, url: source.url }));
  }));
}
function dissentView(items, emptyText = 'Für diese Fassung ist hier kein Einwand verzeichnet. Das belegt keine Zustimmung.') {
  if (!items.length) return paragraph(emptyText, 'subtle');
  return node('div', {}, items.map(item => node('article', { class: 'dissent-item' }, heading(name(item, 'Offener Einwand'), 4),
    paragraph(summary(item, 'Die Begründung des Einwands fehlt noch.')),
    badge(item.status || 'open'),
    human(item.response) && paragraph(`Antwort: ${human(item.response)}`),
    list(item.sourceIds).length && sourcesView(item.sourceIds))));
}
function stageView(variant) {
  return node('div', { class: 'stage-grid' }, stages.map(([key, title]) => {
    const value = stage(variant, key);
    return node('section', { class: 'stage' }, heading(title, 3), badge(value.status || 'open'), paragraph(summary(value, 'Hier ist noch kein Befund festgehalten.')));
  }));
}
function conditionsView(variant) {
  const context = variant.context || {};
  const mandate = variant.mandate || {};
  return node('div', {},
    node('section', { class: 'quiet-panel' }, heading('Frage und Annahmen'), paragraph(human(context.question, 'Die leitende Frage ist noch offen.')),
      list(context.conditions).length ? node('ul', {}, context.conditions.map(item => node('li', {}, human(item, 'Eine Bedingung muss noch verständlich beschrieben werden.')))) : paragraph('Weitere Bedingungen sind noch nicht festgehalten.')),
    node('section', { class: 'quiet-panel' }, heading('Auftrag und Verantwortung'), badge(mandate.status || 'open'),
      paragraph(human(mandate.scope, 'Ein konkreter Auftrag ist noch zu klären.')),
      paragraph(human(mandate.actor, 'Eine verantwortliche Person oder Stelle ist noch nicht benannt.'))));
}
function relatedView(variant) {
  const relations = catalog.relations.filter(item => item.fromVariantId === variant.id || item.toVariantId === variant.id);
  if (!relations.length) return paragraph('Eine Ableitung zu weiteren Gesamtfassungen ist noch nicht verzeichnet.', 'subtle');
  return node('ul', { class: 'relation-list' }, relations.map(relation => {
    const otherId = relation.fromVariantId === variant.id ? relation.toVariantId : relation.fromVariantId;
    const other = itemById('variants', otherId);
    return node('li', {}, button(name(other, 'Verwandte Gesamtfassung'), () => go({ variant: otherId, view: 'variant' }), { class: 'text-button' }),
      paragraph(summary(relation, 'Eine Beziehung zwischen diesen Gesamtfassungen ist dokumentiert.')));
  }));
}

function renderVariantTabs() {
  variantList.replaceChildren(...catalog.variants.map(variant => button([
    node('strong', {}, name(variant, 'Gesamtfassung ohne Titel')),
    node('span', { class: 'variant-summary' }, summary(variant, summary(stage(variant, 'proposal'), 'Eine eigenständige Fassung des Gesamtentwurfs.'))),
    node('span', { class: 'variant-action' }, variant.id === state.variant ? 'Geöffnete Fassung' : 'Fassung erkunden →'),
  ], () => go({ variant: variant.id, view: 'variant' }), { class: 'variant-button', 'aria-pressed': variant.id === state.variant })));
}
function exportButton(text, type) { return button(text, () => download(type)); }
function shareButton() {
  return button('Link kopieren', async () => {
    try { await navigator.clipboard.writeText(location.href); announce('Der Link zur aktuellen Auswahl ist kopiert.'); }
    catch { announce('Der Link konnte nicht kopiert werden. Die Adressleiste enthält die aktuelle Auswahl und den Rückweg.'); }
  });
}
function workHeader(variant, { compare = false } = {}) {
  return node('div', { class: 'work-head' }, node('div', {}, paragraph(compare ? 'Gesamtfassungen vergleichen' : 'Gewählte Gesamtfassung', 'work-label'),
    heading(name(variant, 'Gesamtfassung'), 2, { id: 'work-title', tabindex: '-1' }),
    paragraph(summary(variant, summary(stage(variant, 'proposal'), 'Ein gemeinsamer Entwurf mit getrennten Quellen und Zuständigkeiten.')))),
    node('div', { class: 'actions' }, !compare && button('Mit einer Fassung vergleichen', () => go({ view: 'compare' }), { class: 'primary' }),
      exportButton(compare ? 'Vergleich als JSON exportieren' : 'Variante als JSON exportieren', compare ? 'comparison' : 'variant'), shareButton()));
}
function roomMatches(room, variant) {
  const text = `${name(room, '')} ${summary(room)} ${human(room.contribution)}`.toLocaleLowerCase('de');
  if (state.query && !text.includes(state.query.toLocaleLowerCase('de'))) return false;
  if (state.filter === 'open') return room.contributionStatus !== 'available';
  if (state.filter === 'dissent') return dissentFor(variant, room.id).some(item => isOpen(item.status));
  return true;
}
function renderRoomList(container, variant) {
  const rooms = catalog.rooms.filter(room => roomMatches(room, variant));
  container.replaceChildren(paragraph(`${rooms.length} von ${catalog.rooms.length} Räumen`, 'room-count'));
  if (!rooms.length) {
    container.append(node('div', { class: 'empty' }, paragraph('Zu dieser Auswahl ist kein Raum verzeichnet.'), button('Alle Räume zeigen', () => go({ filter: 'all', query: '' }, { focus: false }))));
    return;
  }
  container.append(node('ul', { class: 'room-list' }, rooms.map(room => node('li', {}, button([
    node('span', {}, node('strong', {}, name(room, 'Eigenständiger Raum')),
      node('small', {}, summary(room, 'Der Beitrag dieses Raums ist noch zu beschreiben.')),
      node('small', {}, room.contributionStatus === 'available' ? 'Beitrag im Katalog vorhanden' : 'Beitrag des Raums noch offen')),
    node('span', { 'aria-hidden': 'true' }, '↗'),
  ], () => openRoom(room.id), { class: 'room-row', 'data-room-index': catalog.rooms.indexOf(room) })))));
}
function roomDirectory(variant) {
  const results = node('div', { id: 'room-results' });
  const search = node('input', { type: 'search', value: state.query, placeholder: 'Raum oder Beitrag finden', maxlength: 120 });
  const filter = node('select', {}, [['all', 'Alle Räume'], ['open', 'Beitrag noch offen'], ['dissent', 'Mit offenem Einwand']].map(([value, label]) => node('option', { value, selected: state.filter === value }, label)));
  search.addEventListener('input', () => { state.query = search.value; saveHash(true); renderRoomList(results, variant); });
  filter.addEventListener('change', () => { state.filter = filter.value; saveHash(); renderRoomList(results, variant); });
  renderRoomList(results, variant);
  return node('section', {}, heading('Von der Fassung in die Räume'), paragraph('Jeder Raum behält seine eigene Herkunft. Öffne einen Beitrag, seine Quellen und die noch fehlenden Nachweise.', 'subtle'),
    node('div', { class: 'toolbar' }, node('label', { class: 'field' }, 'Räume durchsuchen', search), node('label', { class: 'field' }, 'Beiträge eingrenzen', filter)), results);
}
function variantView(variant) {
  return [workHeader(variant), stageView(variant), node('div', { class: 'content-grid' }, roomDirectory(variant), node('aside', {}, conditionsView(variant),
    node('section', { class: 'quiet-panel' }, heading('Offener Dissens'), dissentView(dissentFor(variant))),
    node('section', { class: 'quiet-panel' }, heading('Verwandte Gesamtfassungen'), relatedView(variant)))),
    technical({ catalogRevision: catalog.revision, variant, note: 'Beziehungen dieses Katalogs beschreiben Gesamtfassungen. Sie erzeugen keine kanonischen Werkbeziehungen.' })];
}
function bindingView(binding) {
  const component = itemById('components', binding.componentId);
  return node('article', { class: 'binding' }, heading(name(component, 'Beitrag zur Gesamtfassung'), 4),
    paragraph(summary(component, 'Der Beitrag muss noch verständlich beschrieben werden.')),
    paragraph(`Rolle in dieser Fassung: ${human(binding.role, 'noch zu klären')}`),
    badge(binding.bindingStatus || 'unknown'),
    technical({ componentId: binding.componentId, sourceId: binding.sourceId, revision: binding.revision, contentHash: binding.contentHash, roomId: binding.roomId }));
}
function roomView(variant) {
  const room = itemById('rooms', state.room);
  const bindings = bindingsFor(variant, room.id);
  const openDissent = dissentFor(variant, room.id);
  return [button(`← Zurück ${state.back === 'compare' ? 'zum Vergleich' : 'zur Gesamtfassung'}`, returnFromRoom, { class: 'text-button back-button' }),
    node('article', { class: 'room-detail' }, paragraph(name(variant, 'Gewählte Gesamtfassung'), 'work-label'),
      heading(name(room, 'Eigenständiger Raum'), 2, { id: 'work-title', tabindex: '-1' }), paragraph(summary(room, 'Die Eigenart dieses Raums ist noch zu beschreiben.'), 'lead'),
      node('div', { class: 'content-grid' }, node('div', {},
        heading('Beitrag dieses Raums'), badge(room.contributionStatus || 'open'), paragraph(human(room.contribution, 'Ein tatsächlicher Beitrag des verantwortlichen Raums steht noch aus.')),
        paragraph(human(room.knowledge, room.knowledgeStatus === 'known' ? 'Der erfasste Stand ist mit Quellen verbunden.' : 'Die Übersicht kennt diesen Raum nur teilweise; sein eigener Beitrag bleibt erforderlich.'), 'subtle'),
        heading('Bindung an diese Gesamtfassung'), bindings.length ? bindings.map(bindingView) : paragraph('In dieser Gesamtfassung ist kein konkreter Beitrag dieses Raums gebunden.', 'empty'),
        heading('Quellen und Herkunft'), sourcesView(roomSources(room, bindings))),
        node('aside', {}, node('section', { class: 'quiet-panel' }, heading('Einwände und offene Fragen'), dissentView(openDissent)),
          node('section', { class: 'quiet-panel' }, heading('Rückweg'), paragraph('Die gewählte Gesamtfassung, der Vergleich und die Eingrenzung bleiben beim Zurückgehen und Neuladen erhalten.'), shareButton()),
          conditionsView(variant))), technical({ room, selectedVariantId: variant.id, componentBindings: bindings }))];
}
function selectVariant(selected, onChange) {
  const select = node('select', {}, catalog.variants.map(variant => node('option', { value: variant.id, selected: variant.id === selected }, name(variant, 'Gesamtfassung'))));
  select.addEventListener('change', () => onChange(select.value));
  return select;
}
function compareRow(title, left, right, leftName, rightName, changed) {
  return node('section', { class: 'compare-row' }, heading(title), changed !== undefined && badge(changed ? 'pending' : 'verified', changed ? 'Unterschied dokumentiert' : 'Gleicher dokumentierter Stand'),
    node('div', { class: 'compare-pair' }, node('div', { class: 'compare-cell' }, paragraph(leftName, 'mobile-label'), left), node('div', { class: 'compare-cell' }, paragraph(rightName, 'mobile-label'), right)));
}
function contextCell(variant) {
  return node('div', {}, paragraph(human(variant.context?.question, 'Leitende Frage noch offen.')),
    node('ul', {}, list(variant.context?.conditions).map(text => node('li', {}, human(text, 'Bedingung noch ungeklärt.')))));
}
function mandateCell(variant) {
  return node('div', {}, badge(variant.mandate?.status || 'open'), paragraph(human(variant.mandate?.scope, 'Konkreter Auftrag noch offen.')), paragraph(human(variant.mandate?.actor, 'Verantwortung noch zu benennen.')));
}
function dependencyCell(review) {
  const conflicts = list(review?.conflictRelations);
  const blocked = list(review?.blockedComponentIds).map(id => itemById('components', id)).filter(Boolean);
  return node('div', {}, badge('open', 'Gesamtverträglichkeit offen'),
    review?.status === 'blocked' && paragraph('Für die untersuchten Bindungen bleibt ein Konflikt offen.'),
    conflicts.map(item => paragraph(summary(item, 'Eine vererbte Konfliktbedingung ist noch zu klären.'))),
    blocked.length && node('ul', {}, blocked.map(item => node('li', {}, name(item, 'Betroffener Beitrag')))),
    paragraph('Dieser Befund betrifft die gebundenen Beiträge. Eine vollständige Verträglichkeit des Gesamtgefüges und eine menschliche Annahme bleiben offen.', 'subtle'));
}
function comparisonBinding(binding, component, variantId) {
  if (!binding) return paragraph('In dieser Fassung nicht übernommen.');
  const source = itemById('sources', binding.sourceId);
  const room = itemById('rooms', binding.roomId || component?.roomId);
  return node('div', { class: 'compare-binding' }, paragraph(`Rolle: ${human(binding.role, 'noch zu klären')}`),
    paragraph(`Quelle: ${name(source, 'noch nicht gebunden')}`), summary(source) && paragraph(summary(source)), badge(binding.bindingStatus || 'unknown'),
    room && button(`Beitrag: ${name(room, 'Eigenständiger Raum')}`, () => openRoom(room.id, variantId), { class: 'text-button' }));
}
function compareView(variant) {
  const other = itemById('variants', state.other);
  const comparison = compareVariants(catalog, variant.id, other.id);
  const leftName = name(variant, 'Erste Fassung');
  const rightName = name(other, 'Zweite Fassung');
  const rows = [];
  rows.push(compareRow('Frage und Annahmen', contextCell(variant), contextCell(other), leftName, rightName, comparison.contextChanged));
  rows.push(compareRow('Auftrag und Verantwortung', mandateCell(variant), mandateCell(other), leftName, rightName, comparison.mandateChanged));
  rows.push(compareRow('Herkunft und Ableitungen', relatedView(variant), relatedView(other), leftName, rightName));
  rows.push(compareRow('Abhängigkeiten und offene Konflikte', dependencyCell(comparison.dependencyReview?.left), dependencyCell(comparison.dependencyReview?.right), leftName, rightName));
  for (const [key, title] of stages) {
    const left = stage(variant, key); const right = stage(other, key);
    rows.push(compareRow(title, node('div', {}, badge(left.status || 'open'), paragraph(summary(left, 'Kein Befund festgehalten.'))),
      node('div', {}, badge(right.status || 'open'), paragraph(summary(right, 'Kein Befund festgehalten.'))), leftName, rightName, comparison.stages?.[key]?.changed));
  }
  for (const entry of comparison.components) {
    const component = itemById('components', entry.componentId);
    const changeText = { same: 'Gleiche Bindung und Rolle', added: 'In der zweiten Fassung hinzugefügt', removed: 'In der zweiten Fassung nicht übernommen', changed: 'Bindung oder Rolle verändert' }[entry.change] || 'Unterschied noch einzuordnen';
    const row = compareRow(name(component, human(entry.title, 'Beitrag zur Gesamtfassung')), comparisonBinding(entry.before, component, variant.id), comparisonBinding(entry.after, component, other.id), leftName, rightName);
    row.insertBefore(badge(entry.change === 'same' ? 'verified' : 'pending', changeText), row.lastChild);
    rows.push(row);
  }
  rows.push(compareRow('Erhaltener Dissens', dissentView(dissentFor(variant)), dissentView(dissentFor(other)), leftName, rightName));
  return [button('← Zurück zur gewählten Gesamtfassung', () => go({ view: 'variant' }), { class: 'text-button back-button' }), workHeader(variant, { compare: true }),
    paragraph('Der Vergleich beschreibt Quellenbindungen, Rollen, Annahmen und Befunde. Eine Teilübernahme behauptet keine Zustimmung zu den übrigen Beiträgen.', 'comparison-intro'),
    node('div', { class: 'comparison-controls' }, node('label', { class: 'field' }, 'Erste Fassung', selectVariant(state.variant, id => go({ variant: id }, { focus: false }))),
      node('label', { class: 'field' }, 'Zweite Fassung', selectVariant(state.other, id => go({ other: id }, { focus: false }))),
      button('Fassungen tauschen', () => go({ variant: state.other, other: state.variant }, { focus: false }))),
    node('div', { class: 'compare-heads' }, node('div', {}, heading(leftName), paragraph('Erste Fassung')), node('div', {}, heading(rightName), paragraph('Zweite Fassung'))), rows,
    technical({ catalogRevision: catalog.revision, leftVariantId: variant.id, rightVariantId: other.id, comparison })];
}
function render() {
  const variant = itemById('variants', state.variant);
  renderVariantTabs();
  workspace.setAttribute('aria-busy', 'false');
  workspace.replaceChildren(...(state.view === 'room' ? roomView(itemById('variants', state.roomVariant) || variant) : state.view === 'compare' ? compareView(variant) : variantView(variant)).flat(Infinity));
  document.title = `${state.view === 'room' ? name(itemById('rooms', state.room), 'Raumbeitrag') : state.view === 'compare' ? 'Fassungen vergleichen' : name(variant, 'Gesamtfassung')} · Mooncells`;
}
function download(type) {
  try {
    const variant = itemById('variants', state.variant);
    let output;
    if (type === 'comparison') {
      output = { format: 'mooncells.comparison-export/1', catalog, selection: { leftVariantId: state.variant, rightVariantId: state.other }, comparison: compareVariants(catalog, state.variant, state.other) };
    } else {
      const componentIds = new Set(list(variant.componentBindings).map(item => item.componentId));
      const components = catalog.components.filter(item => componentIds.has(item.id));
      const sourceIds = new Set([...list(variant.componentBindings).map(item => item.sourceId), ...components.flatMap(item => list(item.sourceIds))]);
      output = { format: 'mooncells.variant-export/1', catalogRevision: catalog.revision, selectedVariantId: variant.id, variant, components, sources: catalog.sources.filter(item => sourceIds.has(item.id)), rooms: catalog.rooms.filter(item => bindingsFor(variant, item.id).length), dissent: dissentFor(variant), relations: catalog.relations.filter(item => item.fromVariantId === variant.id || item.toVariantId === variant.id), catalog };
    }
    const url = URL.createObjectURL(new Blob([JSON.stringify(output, null, 2) + '\n'], { type: 'application/json' }));
    const link = node('a', { href: url, download: type === 'comparison' ? 'mooncells-vergleich.json' : 'mooncells-variante.json' });
    document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    announce(type === 'comparison' ? 'Der Vergleich wurde mit dem vollständigen Katalog und beiden Quellenbindungen zum Export bereitgestellt.' : 'Die Variante wurde mit ihren Quellenbindungen und erhaltenen Einwänden zum Export bereitgestellt.');
  } catch { announce('Der Export konnte nicht erstellt werden. Die aktuelle Auswahl bleibt erhalten.'); }
}
async function load() {
  try {
    const response = await fetch('./catalog.json', { cache: 'no-store' });
    if (!response.ok) throw new Error('catalog');
    const data = await response.json();
    const result = validateCatalog(data);
    if (!result.valid || !list(data.variants).length) throw new Error('catalog');
    catalog = data;
    indexes = Object.fromEntries(['variants', 'rooms', 'components', 'sources', 'dissent'].map(kind => [kind, new Map(catalog[kind].map(item => [item.id, item]))]));
    document.querySelector('#catalog-note').textContent = `${catalog.variants.length} Gesamtfassungen · ${catalog.rooms.length} eigenständige Räume`;
    state = readState(); saveHash(true); render();
    if (navigationWarning) { announce('Ein Teil des gespeicherten Einstiegs war nicht verfügbar. Die gültige Auswahl ist geöffnet.'); navigationWarning = false; }
  } catch {
    catalog = null;
    variantList.replaceChildren();
    document.querySelector('#catalog-note').textContent = 'Der gemeinsame Einstieg ist gerade nicht verfügbar.';
    workspace.setAttribute('aria-busy', 'false');
    workspace.replaceChildren(node('div', { class: 'empty' }, heading('Der Variantenraum konnte nicht geöffnet werden.', 2), paragraph('Der Katalog fehlt oder kann nicht sicher gelesen werden. Lade ihn erneut, um mit einer belegten Fassung zu beginnen.'), button('Erneut versuchen', load)));
  }
}
window.addEventListener('hashchange', onHistory);
window.addEventListener('popstate', onHistory);
document.querySelector('.skip-link').addEventListener('click', event => { event.preventDefault(); document.querySelector('#inhalt').focus(); });
load();
