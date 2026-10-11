/* Mooncells Oberfläche — Vanilla JS gegen die REST-API */
let G = { agents: [], works: [], worktrees: [], variants: [], edges: [], findings: [] };

const $ = (sel) => document.querySelector(sel);
const short = (id) => (id ? id.slice(0, 8) + "…" : "—");
const esc = (s) => (s ?? "").replace(/[&<>"]/g,
  c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const agentOf = (id) => G.agents.find(a => a.id === id);
const agentLabel = (id) => {
  const a = agentOf(id);
  return a ? `${esc(a.handle)}${a.agent_type === "model" ? " 🤖" : " 🧑"}` : short(id);
};
const variantOf = (id) => G.variants.find(v => v.id === id);
const variantLabel = (id) => {
  const v = variantOf(id);
  return v ? `${esc(v.label)} <span class="mono">${short(id)}</span>` : short(id);
};
const workOf = (id) => G.works.find(w => w.id === id);

// ---------------------------------------------------------------- Flash
function toast(msg, ok = true) {
  const el = document.createElement("div");
  el.className = "toast " + (ok ? "ok" : "err");
  el.textContent = msg;
  $("#flash").appendChild(el);
  setTimeout(() => el.remove(), ok ? 3500 : 7000);
}

// ---------------------------------------------------------------- API
async function api(path, opts = {}) {
  const r = await fetch("/api" + path, {
    headers: { "Content-Type": "application/json" }, ...opts,
  });
  if (!r.ok) {
    let detail = r.statusText;
    try { detail = (await r.json()).detail || detail; } catch {}
    throw new Error(`${r.status}: ${detail}`);
  }
  return r.json();
}
const post = (path, data) => api(path, { method: "POST", body: JSON.stringify(data) });

// --------------------------------------------------------------- Laden
let PEERS = [], SYNCLOG = [];

async function load() {
  G = await api("/graph");
  renderAll();
  loadPeers();
}

async function loadPeers() {
  try {
    PEERS = await api("/peers");
    SYNCLOG = await api("/autosync-log");
  } catch { PEERS = []; SYNCLOG = []; }
  renderPeers();
}

function renderPeers() {
  const host = $("#peers");
  host.innerHTML = PEERS.length
    ? `<div class="peer-list">` + PEERS.map(p =>
        `<span class="peer-chip">${esc(p.url)}
           <button data-del-peer="${p.id}" title="Peer entfernen">✕</button></span>`).join("") + `</div>`
    : `<div class="empty">Keine Peers — Auto-Sync inaktiv.</div>`;
  host.querySelectorAll("[data-del-peer]").forEach(btn =>
    btn.addEventListener("click", async () => {
      try {
        await api("/peers/" + btn.dataset.delPeer, { method: "DELETE" });
        toast("Peer entfernt.");
        await loadPeers();
      } catch (e) { toast("Fehler: " + e.message, false); }
    }));
  const logHost = $("#autosync-log");
  logHost.innerHTML = SYNCLOG.length
    ? `<div class="sync-note">Letzte Auto-Sync-Läufe:<br>` +
      SYNCLOG.slice(-5).reverse().map(l =>
        esc(l.at.slice(11, 19)) + " — " + l.results.map(r =>
          r.ok ? `<span class="ok">${esc(r.peer)} ✓ (+${r.added})</span>`
               : `<span class="err">${esc(r.peer)} ✗ ${esc(r.error || r.status)}</span>`).join(" · ")
      ).join("<br>") + `</div>`
    : "";
}

// --------------------------------------------------------------- Render
function renderAll() { renderSelects(); renderWorks(); renderEdges(); renderFindings(); }

function renderSelects() {
  const agentOpts = G.agents.map(a =>
    `<option value="${a.id}">${esc(a.handle)} (${a.agent_type})</option>`).join("");
  document.querySelectorAll(".agent-select").forEach(s => { s.innerHTML = agentOpts; });

  const workOpts = G.works.map(w =>
    `<option value="${w.id}">${esc(w.title)} [${esc(w.work_type)}]</option>`).join("");
  document.querySelectorAll(".work-select").forEach(s => { s.innerHTML = workOpts; });

  const variantOpts = G.variants.map(v => {
    const w = workOf((G.worktrees.find(t => t.id === v.worktree_id) || {}).work_id);
    return `<option value="${v.id}">${w ? esc(w.title) + " / " : ""}${esc(v.label)} (${short(v.id)})</option>`;
  }).join("");
  document.querySelectorAll(".variant-select").forEach(s => { s.innerHTML = variantOpts; });

  // Befund-Ziel: Kanten oder Variantenpaare
  const edgeOpts = G.edges.map(e =>
    `<option value="edge:${e.id}">Kante: ${esc(e.edge_type)} ${short(e.from_variant_id)}→${short(e.to_variant_id)}</option>`);
  const pairOpts = [];
  for (const e of G.edges)
    pairOpts.push(`<option value="pair:${e.from_variant_id},${e.to_variant_id}">Paar: ${short(e.from_variant_id)} ↔ ${short(e.to_variant_id)}</option>`);
  $("#finding-target").innerHTML = [...edgeOpts, ...pairOpts].join("");
  syncVariantSelect();
}

function syncVariantSelect() {
  // Variante-anlegen: derived_from auf Varianten des gewählten Werks einschränken
  const form = $("#form-variant");
  const workId = form.work_id.value;
  const wt = G.worktrees.find(t => t.work_id === workId);
  const opts = G.variants.filter(v => v.worktree_id === (wt && wt.id));
  form.derived_from.innerHTML =
    `<option value="">— Wurzel —</option>` +
    opts.map(v => `<option value="${v.id}">${esc(v.label)} (${short(v.id)})</option>`).join("");
}

function renderWorks() {
  const host = $("#works");
  if (!G.works.length) { host.innerHTML = `<div class="empty">Noch keine Werke.</div>`; return; }
  host.innerHTML = G.works.map(w => {
    const wt = G.worktrees.find(t => t.work_id === w.id);
    const vars = G.variants.filter(v => v.worktree_id === (wt && wt.id));
    return `<div class="work">
      <div class="work-head" data-work="${w.id}">
        <span class="title">${esc(w.title)}</span>
        <span class="badge type">${esc(w.work_type)}</span>
        <span class="badge">${vars.length} Varianten</span>
        <span class="byline">${agentLabel(w.author_id)} · ${esc(w.created_at.slice(0, 10))} · <span class="mono">${short(w.id)}</span></span>
      </div>
      <div class="tree" id="tree-${w.id}">${renderTree(vars)}</div>
    </div>`;
  }).join("");
}

function renderTree(vars) {
  if (!vars.length) return `<div class="empty">Keine Varianten — lege die Wurzel an.</div>`;
  const kids = {};
  const roots = [];
  for (const v of vars) {
    if (v.derived_from && vars.some(p => p.id === v.derived_from)) {
      (kids[v.derived_from] ||= []).push(v);
    } else {
      roots.push(v); // Wurzel oder Vorgänger nicht in Auswahl → als Stamm anzeigen
    }
  }
  const node = (v) => `<div class="vnode">
      <div class="vrow">
        <span class="label">${esc(v.label)}</span>
        ${v.derived_from === null ? `<span class="root-tag">WURZEL</span>` : ""}
        <span class="vid">${short(v.id)}</span>
        <span class="notes">${esc(v.notes || "")}</span>
      </div>
      ${(kids[v.id] || []).length ? `<div class="vkids">${kids[v.id].map(node).join("")}</div>` : ""}
    </div>`;
  return roots.map(node).join("");
}

function renderEdges() {
  const host = $("#edges");
  if (!G.edges.length) { host.innerHTML = `<div class="empty">Noch keine Kanten.</div>`; return; }
  host.innerHTML = `<table><tr><th>Typ</th><th>Von</th><th>Nach</th><th>Notiz</th><th>Autor</th></tr>` +
    G.edges.map(e => `<tr>
      <td><span class="pill ${esc(e.edge_type)}">${esc(e.edge_type)}</span></td>
      <td>${variantLabel(e.from_variant_id)}</td>
      <td>${variantLabel(e.to_variant_id)}</td>
      <td>${esc(e.note || "")}</td>
      <td>${agentLabel(e.author_id)}</td>
    </tr>`).join("") + "</table>";
}

function renderFindings() {
  const host = $("#findings");
  if (!G.findings.length) { host.innerHTML = `<div class="empty">Noch keine Befunde.</div>`; return; }
  host.innerHTML = `<table><tr><th>Ziel</th><th>Kriterium</th><th>Aufgabe</th><th>Ergebnis</th><th>Begründung</th><th>Autor</th></tr>` +
    G.findings.map(f => {
      const target = f.target_edge_id
        ? `Kante <span class="mono">${short(f.target_edge_id)}</span>`
        : `Paar <span class="mono">${short(f.target_variant_ids[0])} ↔ ${short(f.target_variant_ids[1])}</span>`;
      return `<tr>
        <td>${target}</td><td>${esc(f.criterion)}</td><td>${esc(f.task)}</td>
        <td><span class="pill ${esc(f.verdict)}">${esc(f.verdict)}</span></td>
        <td>${esc(f.rationale)}</td><td>${agentLabel(f.author_id)}</td>
      </tr>`;
    }).join("") + "</table>";
}

// --------------------------------------------------------------- Formulare
function formData(form) {
  const d = Object.fromEntries(new FormData(form).entries());
  for (const k of Object.keys(d)) if (d[k] === "") d[k] = null;
  return d;
}

function wireForm(id, handler) {
  $(id).addEventListener("submit", async (ev) => {
    ev.preventDefault();
    try { await handler(formData(ev.target)); ev.target.reset(); renderSelects(); await load(); }
    catch (e) { toast("Fehler: " + e.message, false); }
  });
}

wireForm("#form-agent", d => post("/agents", d));

wireForm("#form-work", d => post("/works", d));

wireForm("#form-variant", async d => {
  const wt = G.worktrees.find(t => t.work_id === d.work_id);
  await post("/variants", {
    worktree_id: wt.id,
    derived_from: d.derived_from,
    label: d.label, notes: d.notes || "", content: d.content,
    author_id: d.author_id,
  });
});

wireForm("#form-edge", d => post("/edges", d));

wireForm("#form-finding", d => {
  const [kind, rest] = d.target.split(":");
  const payload = {
    criterion: d.criterion, task: d.task, verdict: d.verdict,
    rationale: d.rationale || "", author_id: d.author_id,
    target_edge_id: kind === "edge" ? rest : null,
    target_variant_ids: kind === "pair" ? rest.split(",") : null,
  };
  return post("/findings", payload);
});

$("#form-variant").work_id.addEventListener("change", syncVariantSelect);

// --------------------------------------------------------------- Peers
wireForm("#form-peer", async d => {
  await post("/peers", { url: d.url });
  toast(`Peer registriert: ${d.url} — jeder Schreibzugriff wird jetzt automatisch gepusht.`);
  await loadPeers();
});

// -------------------------------------------------------- Export / Import
$("#btn-export").addEventListener("click", async () => {
  const doc = await api("/export");
  const blob = new Blob([JSON.stringify(doc, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `mooncells-export-${new Date().toISOString().slice(0, 19)}.json`;
  a.click();
  URL.revokeObjectURL(a.href);
  toast("Export erstellt (Mooncells Document Format v1).");
});

$("#import-file").addEventListener("change", async (ev) => {
  const file = ev.target.files[0];
  if (!file) return;
  try {
    const doc = JSON.parse(await file.text());
    const res = await post("/import", doc);
    const parts = Object.entries(res.report)
      .map(([k, v]) => `${k}: +${v.added}/~${v.skipped}`).join("  ");
    toast(`Import OK — ${parts}`);
    await load();
  } catch (e) { toast("Import fehlgeschlagen: " + e.message, false); }
  ev.target.value = "";
});

$("#btn-sync").addEventListener("click", async () => {
  const peer = prompt("Peer-Instanz-URL:", "http://127.0.0.1:8401");
  if (!peer) return;
  try {
    const res = await post("/sync", { peer });
    const fmt = (r) => Object.entries(r)
      .map(([k, v]) => `${k} +${v.added}/~${v.skipped}`).join("  ");
    toast(`Sync mit ${res.peer} OK\nHin → ${fmt(res.pushed.report)}\nHer ← ${fmt(res.pulled_report)}`);
    await load();
  } catch (e) { toast("Sync fehlgeschlagen: " + e.message, false); }
});

$("#btn-refresh").addEventListener("click", load);

// --------------------------------------------------------------- Start
load().catch(e => toast("Laden fehlgeschlagen: " + e.message, false));
