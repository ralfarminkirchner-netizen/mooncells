"""Serverseitige Traversierungsmuster — die Query-Engine (v2).

Implementiert die Standardfragen aus docs/konzept.md §4 direkt auf dem Store,
ohne externe Graphdatenbank. Bei Migration auf eine DB bleibt diese Schicht
das stabile Interface (Queries werden dann nur schneller).
"""
from __future__ import annotations

from .store import JsonStore

VERDICT_WEIGHT = {"tragfähig": 1.0, "teilweise": 0.5, "nicht-tragfähig": -1.0}

PATTERNS = {
    "ancestors": "Abstammung: transitive Hülle derived_from rückwärts",
    "descendants": "Nachfahren: transitive Hülle derived_from vorwärts (Fan-out = Wirkung)",
    "remix-line": "Remix-Linie: remixt-aus-Pfade über Werkgrenzen hinweg",
    "contradiction-clusters": "Widerspruchs-Cluster: Zusammenhangskomponenten über 'widerspricht'",
    "findings-for": "Bewertungslage: alle Befunde zu einer Variante (optional gefiltert nach Aufgabe)",
    "fitness": "Fitness-Ranking: Befund-Aggregation pro Variante + Adoption (remixt-aus-In-Degree)",
    "provenance": "Provenienz-Kette: Abstammung mit Autoren & Zeitstempeln, plus berührende Kanten",
}


def _require_variant(store: JsonStore, variant_id: str) -> dict:
    v = store.get("variants", variant_id)
    if not v:
        raise ValueError(f"Variante '{variant_id}' unbekannt")
    return v


def ancestors(store: JsonStore, variant_id: str) -> dict:
    _require_variant(store, variant_id)
    by_id = {v["id"]: v for v in store.list("variants")}
    chain, cur, seen = [], variant_id, set()
    while cur and cur not in seen:
        seen.add(cur)
        v = by_id.get(cur)
        if not v:
            break
        chain.append(v)
        cur = v.get("derived_from")
    return {"chain": chain, "depth": len(chain) - 1}


def descendants(store: JsonStore, variant_id: str) -> dict:
    _require_variant(store, variant_id)
    children: dict[str, list] = {}
    for v in store.list("variants"):
        if v.get("derived_from"):
            children.setdefault(v["derived_from"], []).append(v)
    result, frontier, seen = [], [variant_id], {variant_id}
    while frontier:
        nxt = []
        for vid in frontier:
            for c in children.get(vid, []):
                if c["id"] not in seen:
                    seen.add(c["id"])
                    result.append(c)
                    nxt.append(c["id"])
        frontier = nxt
    return {"descendants": result, "fanout": len(result)}


def remix_line(store: JsonStore, variant_id: str) -> dict:
    """Alle Varianten, die mit dieser über remixt-aus verbunden sind
    (bidirektional, transitiv) — die Wanderung der Bausteine."""
    _require_variant(store, variant_id)
    edges = [e for e in store.list("edges") if e["edge_type"] == "remixt-aus"]
    adj: dict[str, set] = {}
    for e in edges:
        adj.setdefault(e["from_variant_id"], set()).add(e["to_variant_id"])
        adj.setdefault(e["to_variant_id"], set()).add(e["from_variant_id"])
    seen, frontier = {variant_id}, [variant_id]
    while frontier:
        nxt = [n for vid in frontier for n in adj.get(vid, set()) if n not in seen]
        seen.update(nxt)
        frontier = nxt
    involved = [e for e in edges
                if e["from_variant_id"] in seen or e["to_variant_id"] in seen]
    return {"variants": [v for v in store.list("variants") if v["id"] in seen],
            "edges": involved}


def contradiction_clusters(store: JsonStore) -> dict:
    """Zusammenhangskomponenten über 'widerspricht'-Kanten —
    die Positionen, die im echten Streit stehen."""
    edges = [e for e in store.list("edges") if e["edge_type"] == "widerspricht"]
    adj: dict[str, set] = {}
    for e in edges:
        adj.setdefault(e["from_variant_id"], set()).add(e["to_variant_id"])
        adj.setdefault(e["to_variant_id"], set()).add(e["from_variant_id"])
    clusters, seen = [], set()
    for start in adj:
        if start in seen:
            continue
        comp, frontier = {start}, [start]
        seen.add(start)
        while frontier:
            nxt = [n for vid in frontier for n in adj.get(vid, set()) if n not in seen]
            for n in nxt:
                seen.add(n)
            comp.update(nxt)
            frontier = nxt
        clusters.append(sorted(comp))
    by_id = {v["id"]: v for v in store.list("variants")}
    return {"clusters": [
        {"variants": [by_id.get(i, {"id": i, "label": "?"}) for i in c],
         "size": len(c)} for c in sorted(clusters, key=len, reverse=True)]}


def findings_for(store: JsonStore, variant_id: str, task: str | None = None) -> dict:
    _require_variant(store, variant_id)
    out = []
    for f in store.list("findings"):
        hit = (f.get("target_variant_ids") and variant_id in f["target_variant_ids"]) \
            or (f.get("target_edge_id") and variant_id in (
                (store.get("edges", f["target_edge_id"]) or {}).get("from_variant_id"),
                (store.get("edges", f["target_edge_id"]) or {}).get("to_variant_id")))
        if hit and (not task or f["task"] == task):
            out.append(f)
    by_verdict = {"tragfähig": 0, "teilweise": 0, "nicht-tragfähig": 0}
    for f in out:
        by_verdict[f["verdict"]] += 1
    return {"findings": sorted(out, key=lambda f: f["created_at"]),
            "summary": by_verdict}


def fitness(store: JsonStore, task: str | None = None) -> dict:
    """fitness(v) = Σ gewichtete Verdicts über Befunde (optional pro Aufgabe)
    + Adoption = In-Degree über remixt-aus (tatsächliche Wiederverwendung)."""
    adoption: dict[str, int] = {}
    for e in store.list("edges"):
        if e["edge_type"] == "remixt-aus":
            adoption[e["to_variant_id"]] = adoption.get(e["to_variant_id"], 0) + 1
    scores: dict[str, float] = {}
    for f in store.list("findings"):
        if task and f["task"] != task:
            continue
        ids = f.get("target_variant_ids") or []
        if not ids and f.get("target_edge_id"):
            e = store.get("edges", f["target_edge_id"]) or {}
            ids = [e.get("from_variant_id"), e.get("to_variant_id")]
        for vid in filter(None, ids):
            scores[vid] = scores.get(vid, 0.0) + VERDICT_WEIGHT[f["verdict"]]
    by_id = {v["id"]: v for v in store.list("variants")}
    ranking = [
        {"variant": v, "fitness": round(scores.get(v["id"], 0.0), 2),
         "adoption": adoption.get(v["id"], 0),
         "status": v.get("status", "entwurf")}
        for v in by_id.values()
    ]
    ranking.sort(key=lambda r: (r["fitness"], r["adoption"]), reverse=True)
    return {"task": task, "ranking": ranking}


def provenance(store: JsonStore, variant_id: str) -> dict:
    """Gemischte Kette: Abstammung mit Autoren/Zeit, plus alle typisierten
    Kanten und Befunde, die diese Variante berühren."""
    chain = ancestors(store, variant_id)["chain"]
    edges = [e for e in store.list("edges")
             if variant_id in (e["from_variant_id"], e["to_variant_id"])]
    f = findings_for(store, variant_id)
    return {"lineage": chain, "edges": edges, "findings": f["findings"],
            "summary": f["summary"]}


def run(store: JsonStore, pattern: str, variant_id: str | None = None,
        task: str | None = None) -> dict:
    needs_variant = {"ancestors", "descendants", "remix-line",
                     "findings-for", "provenance"}
    if pattern not in PATTERNS:
        raise ValueError(f"Unbekanntes Muster '{pattern}'. "
                         f"Möglich: {', '.join(PATTERNS)}")
    if pattern in needs_variant and not variant_id:
        raise ValueError(f"Muster '{pattern}' braucht variant_id")
    dispatch = {
        "ancestors": lambda: ancestors(store, variant_id),
        "descendants": lambda: descendants(store, variant_id),
        "remix-line": lambda: remix_line(store, variant_id),
        "contradiction-clusters": lambda: contradiction_clusters(store),
        "findings-for": lambda: findings_for(store, variant_id, task),
        "fitness": lambda: fitness(store, task),
        "provenance": lambda: provenance(store, variant_id),
    }
    return {"pattern": pattern, "description": PATTERNS[pattern],
            **dispatch[pattern]()}
