/* Mooncells Oberfläche — Vanilla JS gegen die REST-API */
let G = { agents: [], works: [], worktrees: [], variants: [], edges: [], findings: [] };

const $ = (sel) => document.querySelector(sel);
const technicalDetails = (record) => `<details class="technical-details"><summary>Technische Details</summary><pre>${esc(JSON.stringify(record, null, 2))}</pre></details>`;
const esc = (s) => (s ?? "").replace(/[&<>"]/g,
  c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const agentOf = (id) => G.agents.find(a => a.id === id);
const agentLabel = (id) => {
  const a = agentOf(id);
  return a ? `${esc(a.handle)}${a.agent_type === "model" ? " 🤖" : " 🧑"}` : "Unbekannter Autor";
};
const variantOf = (id) => G.variants.find(v => v.id === id);
const variantLabel = (id) => {
  const v = variantOf(id);
  return v ? `${esc(workOf(G.worktrees.find(t => t.id === v.worktree_id)?.work_id)?.title || "Unbenanntes Werk")} / ${esc(v.label || "Unbenannte Variante")}` : "Nicht verfügbare Variante";
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
    throw new Error(r.status >= 500 ? "Der Dienst ist derzeit nicht verfügbar." : "Die Anfrage konnte nicht ausgeführt werden. Bitte Eingaben und Verknüpfungen prüfen.");
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
               : `<span class="err">${esc(r.peer)} ✗ Synchronisierung fehlgeschlagen</span>`).join(" · ")
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
    return `<option value="${v.id}">${w ? esc(w.title) + " / " : ""}${esc(v.label || "Unbenannte Variante")}</option>`;
  }).join("");
  document.querySelectorAll(".variant-select").forEach(s => { s.innerHTML = variantOpts; });

  // Befund-Ziel: Kanten oder Variantenpaare
  const edgeOpts = G.edges.map(e =>
    `<option value="edge:${e.id}">Kante: ${esc(e.edge_type)} ${variantLabel(e.from_variant_id)} → ${variantLabel(e.to_variant_id)}</option>`);
  const pairOpts = [];
  for (const e of G.edges)
    pairOpts.push(`<option value="pair:${e.from_variant_id},${e.to_variant_id}">Paar: ${variantLabel(e.from_variant_id)} ↔ ${variantLabel(e.to_variant_id)}</option>`);
  $("#finding-target").innerHTML = [...edgeOpts, ...pairOpts].join("");
  syncVariantSelect();
}

function syncVariantSelect() {
  // Werk und Worktree explizit auswählen; Ableitungen bleiben im selben Worktree.
  const form = $("#form-variant");
  const workId = form.work_id.value;
  const trees = G.worktrees.filter(t => t.work_id === workId);
  const selected = form.worktree_id.value;
  form.worktree_id.innerHTML = trees.map((t, index) =>
    `<option value="${t.id}">Worktree ${index + 1} · ${agentLabel(t.author_id)}</option>`).join("");
  if (trees.some(t => t.id === selected)) form.worktree_id.value = selected;
  syncDerivedSelect();
}

function syncDerivedSelect() {
  const form = $("#form-variant");
  const opts = G.variants.filter(v => v.worktree_id === form.worktree_id.value);
  form.derived_from.innerHTML =
    `<option value="">— Wurzel —</option>` +
    opts.map(v => `<option value="${v.id}">${esc(v.label || "Unbenannte Variante")}</option>`).join("");
}

function renderWorks() {
  const host = $("#works");
  if (!G.works.length) { host.innerHTML = `<div class="empty">Noch keine Werke.</div>`; return; }
  host.innerHTML = G.works.map(w => {
    const trees = G.worktrees.filter(t => t.work_id === w.id);
    const vars = G.variants.filter(v => trees.some(t => t.id === v.worktree_id));
    return `<div class="work">
      <div class="work-head" data-work="${w.id}">
        <span class="title">${esc(w.title || "Unbenanntes Werk")}</span>
        <span class="badge type">${esc(w.work_type)}</span>
        <span class="badge">${trees.length} Worktrees · ${vars.length} Varianten</span>
        <span class="byline">${agentLabel(w.author_id)} · ${esc(w.created_at.slice(0, 10))}</span>
      </div>
      <div class="tree" id="tree-${w.id}">${trees.map((t, index) => `<section class="worktree"><h3>Worktree ${index + 1} · ${agentLabel(t.author_id)}</h3>${renderTree(vars.filter(v => v.worktree_id === t.id))}${technicalDetails(t)}</section>`).join("") || `<div class="empty">Noch kein Worktree verfügbar.</div>`}</div>${technicalDetails(w)}
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
        <span class="pill status-${esc(v.status || "entwurf")}" title="Status ändern" data-set-status="${v.id}" style="cursor:pointer">${esc(v.status || "entwurf")}</span>
        ${(v.tags || []).map(t => `<span class="badge">${esc(t)}</span>`).join("")}
        <span class="notes">${esc(v.notes || "")}</span>
      </div>
      ${v.content ? `<details class="variant-content"><summary>Varianteninhalt öffnen</summary><pre>${esc(v.content)}</pre></details>` : `<p class="sync-note">Kein Varianteninhalt hinterlegt.</p>`}
      ${technicalDetails(v)}
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
        ? (() => { const e = G.edges.find(e => e.id === f.target_edge_id); return e ? `${esc(e.edge_type)}: ${variantLabel(e.from_variant_id)} → ${variantLabel(e.to_variant_id)}` : "Nicht verfügbare Kante"; })()
        : f.target_finding_id ? "Befund über einen Befund" : (f.target_variant_ids || []).map(variantLabel).join(" ↔ ") || "Kein Ziel hinterlegt";
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
  if (d.tags) d.tags = d.tags.split(",").map(s => s.trim()).filter(Boolean);
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
  const wt = G.worktrees.find(t => t.id === d.worktree_id && t.work_id === d.work_id);
  if (!wt) throw new Error("Bitte einen verfügbaren Worktree wählen.");
  await post("/variants", {
    worktree_id: wt.id,
    derived_from: d.derived_from,
    label: d.label, notes: d.notes || "", content: d.content,
    status: d.status || "entwurf",
    tags: d.tags || [],
    author_id: d.author_id,
  });
});

$("#form-variant").worktree_id.addEventListener("change", syncDerivedSelect);

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

// ---------------------------------------------------- Status (delegiert)
$("#works").addEventListener("click", async (ev) => {
  const el = ev.target.closest("[data-set-status]");
  if (!el) return;
  const cur = G.variants.find(v => v.id === el.dataset.setStatus);
  const next = prompt("Neuer Status (entwurf / geprüft / grundformation / verworfen):",
                      cur?.status || "entwurf");
  if (!next) return;
  try {
    await post(`/variants/${el.dataset.setStatus}/status`, { status: next.trim() });
    toast(`Status → ${next.trim()}${next.trim() === "grundformation" ? " ✦ Kristallisiert!" : ""}`);
    await load();
  } catch (e) { toast("Fehler: " + e.message, false); }
});

// --------------------------------------------------------------- Queries
const NEEDS_VARIANT = new Set(["ancestors", "descendants", "remix-line",
                               "findings-for", "provenance"]);

(async () => {
  try {
    const patterns = await api("/patterns");
    $("#query-pattern").innerHTML = Object.entries(patterns)
      .map(([k, desc]) => `<option value="${k}">${k}</option>`).join("");
  } catch {}
})();

function renderQueryResult(res) {
  const vLabel = variantLabel;
  const fLine = (f) => `${esc(f.verdict)} · ${esc(f.criterion)} · Aufgabe „${esc(f.task)}" — ${esc(f.rationale)} (${agentLabel(f.author_id)})`;
  let html = `<strong>${esc(res.pattern)}</strong> — ${esc(res.description)}<br>`;
  if (res.chain) html += res.chain.map(v => `${vLabel(v.id)} <span class="sync-note">(${agentLabel(v.author_id)})</span>`).join(" ← ") + ` <span class="sync-note">(Tiefe ${res.depth})</span>`;
  if (res.descendants) html += `<span class="sync-note">Fan-out ${res.fanout}:</span> ` + res.descendants.map(v => vLabel(v.id)).join(", ");
  if (res.ranking) html += `<table><tr><th>Variante</th><th>Fitness</th><th>Adoption</th><th>Status</th></tr>` +
    res.ranking.map(r => `<tr><td>${vLabel(r.variant.id)}</td><td>${r.fitness}</td><td>${r.adoption}</td><td>${esc(r.status)}</td></tr>`).join("") + "</table>";
  if (res.clusters) html += res.clusters.map(c => `Cluster (${c.size}): ` + c.variants.map(v => vLabel(v.id)).join(", ")).join("<br>") || "Keine Widerspruchs-Kanten.";
  if (res.findings) html += `<span class="sync-note"> tragfähig ${res.summary["tragfähig"]} · teilweise ${res.summary["teilweise"]} · nicht ${res.summary["nicht-tragfähig"]}</span><br>` +
    res.findings.map(fLine).join("<br>");
  if (res.lineage) {
    html += res.lineage.map(v => `${vLabel(v.id)} <span class="sync-note">(${agentLabel(v.author_id)}, ${esc(v.created_at.slice(0, 10))})</span>`).join(" ← ");
    if (res.edges?.length) html += `<br><span class="sync-note">Kanten:</span> ` + res.edges.map(e => `<span class="pill ${esc(e.edge_type)}">${esc(e.edge_type)}</span> ${vLabel(e.from_variant_id)}→${vLabel(e.to_variant_id)}`).join(" · ");
  }
  if (res.variants && res.pattern === "remix-line")
    html += `<span class="sync-note">Remix-Verband (${res.variants.length}):</span> ` + res.variants.map(v => vLabel(v.id)).join(", ");
  $("#query-result").innerHTML = html;
}

$("#form-query").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const d = formData(ev.target);
  if (NEEDS_VARIANT.has(d.pattern) && !d.variant_id) {
    toast("Dieses Muster braucht eine Variante.", false);
    return;
  }
  try {
    const res = await post("/query", {
      pattern: d.pattern,
      variant_id: NEEDS_VARIANT.has(d.pattern) ? d.variant_id : null,
      task: d.task,
    });
    renderQueryResult(res);
  } catch (e) { toast("Query fehlgeschlagen: " + e.message, false); }
});

// --------------------------------------------------------------- Start
load().catch(e => toast("Laden fehlgeschlagen: " + e.message, false));
