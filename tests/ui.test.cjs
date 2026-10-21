const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const source = fs.readFileSync(path.join(__dirname, '../server/static/app.js'), 'utf8');
function setup() {
  const hosts = Object.fromEntries(['#works', '#edges', '#findings'].map(k => [k, { innerHTML: '' }]));
  const select = (value = '') => ({ value, innerHTML: '' });
  hosts['#form-variant'] = { work_id: select('work-full-id'), worktree_id: select('tree-two-full-id'), derived_from: select() };
  const ctx = vm.createContext({ document: { querySelector: k => hosts[k] } });
  vm.runInContext(source.split('// --------------------------------------------------------------- Formulare')[0], ctx);
  vm.runInContext(`G = {
    agents: [{id:'author-full-id',handle:'Ralf',agent_type:'human'}],
    works: [{id:'work-full-id',title:'Mondphase',work_type:'song',author_id:'author-full-id',created_at:'2026-10-12'}],
    worktrees: ['tree-one-full-id','tree-two-full-id'].map(id => ({id,work_id:'work-full-id',author_id:'author-full-id'})),
    variants: [
      {id:'variant-one-full-id',worktree_id:'tree-one-full-id',label:'Original',derived_from:null,content:'<script>alert("x")</script>'},
      {id:'variant-two-full-id',worktree_id:'tree-two-full-id',label:'Remix',derived_from:null,content:'Zeile 1\\nZeile 2'},
      {id:'variant-child-full-id',worktree_id:'tree-two-full-id',label:'Weiterarbeit',derived_from:'variant-two-full-id'}
    ], edges:[], findings:[]
  };`, ctx);
  return { ctx, hosts };
}

test('all worktrees and their variants remain visible, including derivations', () => {
  const { ctx, hosts } = setup();
  vm.runInContext('renderWorks()', ctx);
  const html = hosts['#works'].innerHTML;
  assert.match(html, /2 Worktrees · 3 Varianten/);
  for (const label of ['Worktree 1', 'Worktree 2', 'Original', 'Remix', 'Weiterarbeit']) assert.ok(html.includes(label));
  assert.match(html, /class="vkids"/);
});

test('content is escaped and full identifiers appear only inside closed diagnostics', () => {
  const { ctx, hosts } = setup();
  vm.runInContext('renderWorks()', ctx);
  const html = hosts['#works'].innerHTML;
  assert.ok(!html.includes('<script>'));
  assert.ok(html.includes('&lt;script&gt;'));
  assert.match(html, /<details class="variant-content"><summary>Varianteninhalt öffnen/);
  assert.ok(!/<details[^>]*\bopen\b/.test(html));
  assert.ok(html.includes('variant-two-full-id'));
  const normal = html.replace(/<details class="technical-details">[\s\S]*?<\/details>/g, '').replace(/<[^>]+>/g, '');
  assert.ok(!normal.includes('full-id'));
  assert.match(normal, /Kein Varianteninhalt hinterlegt/);
});

test('chosen worktree is preserved and derivation options stay within it', () => {
  const { ctx, hosts } = setup();
  vm.runInContext('syncVariantSelect()', ctx);
  const form = hosts['#form-variant'];
  assert.equal(form.worktree_id.value, 'tree-two-full-id');
  assert.match(form.worktree_id.innerHTML, /Worktree 2 · Ralf/);
  assert.match(form.derived_from.innerHTML, /Remix/);
  assert.match(form.derived_from.innerHTML, /Weiterarbeit/);
  assert.ok(!form.derived_from.innerHTML.includes('Original'));
  form.worktree_id.value = 'tree-one-full-id';
  vm.runInContext('syncDerivedSelect()', ctx);
  assert.match(form.derived_from.innerHTML, /Original/);
  assert.ok(!form.derived_from.innerHTML.includes('Remix'));
});

test('meta findings and missing references render without leaking identifiers', () => {
  const { ctx, hosts } = setup();
  vm.runInContext(`G.findings = [
    {target_finding_id:'hidden-finding-id',criterion:'Verlässlichkeit',task:'Kalibrierung',verdict:'tragfähig',rationale:'Meta-Befund'},
    {target_edge_id:'hidden-edge-id',criterion:'Bezug',task:'Prüfung',verdict:'teilweise',rationale:'Fehlender Bezug'}
  ]; renderFindings()`, ctx);
  assert.match(hosts['#findings'].innerHTML, /Befund über einen Befund/);
  assert.match(hosts['#findings'].innerHTML, /Nicht verfügbare Kante/);
  assert.ok(!hosts['#findings'].innerHTML.includes('hidden-'));
  assert.equal(vm.runInContext('variantLabel("hidden-variant-id")', ctx), 'Nicht verfügbare Variante');
});
