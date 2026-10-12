"""JSON-Datei-Storage mit append-only-Semantik und UUID-Dedupe-Merge.

Struktur der State-Datei:
    {
      "agents": [...], "works": [...], "worktrees": [...],
      "variants": [...], "edges": [...], "findings": [...]
    }

Alle Schreibzugriffe gehen über dieselbe Datei (atomar via tmp+rename).
Später kann diese Klasse 1:1 durch eine Datenbank-Implementierung desselben
Interfaces ersetzt werden, ohne die API-Schicht anzufassen.
"""
from __future__ import annotations

import json
import os
import threading
import uuid
from typing import Any, Optional

COLLECTIONS = ["agents", "works", "worktrees", "variants", "edges", "findings",
               "peers"]


def new_uuid() -> str:
    return str(uuid.uuid4())


class JsonStore:
    def __init__(self, path: str):
        self.path = path
        self._lock = threading.RLock()
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self._state: dict[str, dict[str, dict]] = {
                coll: {e["id"]: e for e in raw.get(coll, [])}
                for coll in COLLECTIONS
            }
        else:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            self._state = {coll: {} for coll in COLLECTIONS}
            self._save()

    # ------------------------------------------------------------ I/O

    def _save(self) -> None:
        """Atomar schreiben: erst tmp, dann rename — kein halber Zustand."""
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(
                {coll: list(self._state[coll].values()) for coll in COLLECTIONS},
                f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.path)

    # ------------------------------------------------------- Generisch

    def list(self, coll: str) -> list[dict]:
        with self._lock:
            return list(self._state[coll].values())

    def get(self, coll: str, entity_id: str) -> Optional[dict]:
        with self._lock:
            return self._state[coll].get(entity_id)

    def add(self, coll: str, entity: dict) -> dict:
        """Append-only insert. Existierende UUID → Fehler (kein Überschreiben)."""
        with self._lock:
            if entity["id"] in self._state[coll]:
                raise ValueError(f"{coll}:{entity['id']} existiert bereits")
            self._state[coll][entity["id"]] = entity
            self._save()
            return entity

    def find_by(self, coll: str, field: str, value: Any) -> list[dict]:
        with self._lock:
            return [e for e in self._state[coll].values() if e.get(field) == value]

    def ensure_source_space(self, work: dict, worktree: dict, variant: dict) -> dict:
        """Quellenraum atomar anlegen oder über seine belegte Identität finden.

        Ein Wiederaufruf ändert weder Inhalt noch Herkunft einer Quellfassung.
        Drei Entitäten werden mit einem einzigen atomaren Save veröffentlicht.
        """
        identity = tuple(work["source_ref"][k] for k in ("system", "kind", "source_id"))
        with self._lock:
            for existing in self._state["works"].values():
                ref = existing.get("source_ref") or {}
                if tuple(ref.get(k) for k in ("system", "kind", "source_id")) != identity:
                    continue
                trees = [t for t in self._state["worktrees"].values()
                         if t["work_id"] == existing["id"]]
                tree_ids = {t["id"] for t in trees}
                roots = [v for v in self._state["variants"].values()
                         if v["worktree_id"] in tree_ids and v.get("derived_from") is None
                         and tuple((v.get("source_ref") or {}).get(k)
                                   for k in ("system", "kind", "source_id")) == identity]
                if not roots:
                    raise ValueError("Bestehender Quellenraum hat keine belegte Quellfassung")
                root = roots[0]
                tree = next(t for t in trees if t["id"] == root["worktree_id"])
                return {"work": existing, "worktree": tree, "variant": root, "created": False}
            additions = [("works", work), ("worktrees", worktree), ("variants", variant)]
            for coll, entity in additions:
                self._state[coll][entity["id"]] = entity
            try:
                self._save()
            except Exception:
                for coll, entity in additions:
                    del self._state[coll][entity["id"]]
                raise
            return {"work": work, "worktree": worktree, "variant": variant, "created": True}

    def delete(self, coll: str, entity_id: str) -> bool:
        """Löschen nur für Konfigurations-Collections (z. B. peers) — die
        Kerndaten (agents…findings) bleiben append-only."""
        with self._lock:
            if entity_id not in self._state[coll]:
                return False
            del self._state[coll][entity_id]
            self._save()
            return True

    def update_fields(self, coll: str, entity_id: str, fields: dict) -> Optional[dict]:
        """Selektives Update einzelner Felder — v2 nur für `variant.status`
        zugelassen; alle anderen Kern-Felder bleiben append-only."""
        with self._lock:
            e = self._state[coll].get(entity_id)
            if e is None:
                return None
            e.update(fields)
            self._save()
            return e

    # ----------------------------------------------------- Document I/O

    def export_document(self, instance_id: str, exported_by: str,
                        work_ids: Optional[list[str]] = None,
                        since: Optional[str] = None) -> dict:
        """Export im Mooncells Document Format, optional gefiltert."""
        with self._lock:

            def filt(coll: str, rows: list[dict]) -> list[dict]:
                out = rows
                if coll in ("works",) and work_ids:
                    out = [e for e in out if e["id"] in work_ids]
                if since:
                    out = [e for e in out if e.get("created_at", "") >= since]
                return out

            # Gefilterter Export erfasst Varianten/Edges/Findings nur, wenn
            # ihr Werk (bzw. deren Worktree) im Scope liegt.
            works = filt("works", list(self._state["works"].values()))
            if work_ids is not None:
                wt_ids = {w["id"] for w in self._state["worktrees"].values()
                          if w["work_id"] in set(work_ids)}
                variants = [v for v in self._state["variants"].values()
                            if v["worktree_id"] in wt_ids]
                v_ids = {v["id"] for v in variants}
                edges = [e for e in self._state["edges"].values()
                         if e["from_variant_id"] in v_ids or e["to_variant_id"] in v_ids]
                e_ids = {e["id"] for e in edges}
                findings = [f for f in self._state["findings"].values()
                            if f.get("target_edge_id") in e_ids
                            or any(x in v_ids for x in (f.get("target_variant_ids") or []))]
                worktrees = [w for w in self._state["worktrees"].values()
                             if w["work_id"] in set(work_ids)]
                agent_ids = ({w["author_id"] for w in works}
                             | {v["author_id"] for v in variants}
                             | {e["author_id"] for e in edges}
                             | {f["author_id"] for f in findings})
                agents = [a for a in self._state["agents"].values()
                          if a["id"] in agent_ids]
            else:
                agents = filt("agents", list(self._state["agents"].values()))
                worktrees = filt("worktrees", list(self._state["worktrees"].values()))
                variants = filt("variants", list(self._state["variants"].values()))
                edges = filt("edges", list(self._state["edges"].values()))
                findings = filt("findings", list(self._state["findings"].values()))

        doc = {
            "format": "mooncells-document",
            "version": "1",
            "instance_id": instance_id,
            "exported_by": exported_by,
            "data": {
                "agents": agents, "works": works, "worktrees": worktrees,
                "variants": variants, "edges": edges, "findings": findings,
            },
        }
        if work_ids is not None or since:
            doc["scope"] = {k: v for k, v in
                            {"work_ids": work_ids, "since": since}.items()
                            if v is not None}
        return doc

    def import_document(self, doc: dict) -> dict:
        """UUID-Dedupe-Merge: bekannte UUIDs überspringen, neue einfügen.

        Niemals wird ein bestehender Eintrag überschrieben — "first write wins".
        Rückgabe: Report {collection: {"added": n, "skipped": n}}.
        """
        if doc.get("format") != "mooncells-document":
            raise ValueError("Kein Mooncells Document (format != 'mooncells-document')")
        if str(doc.get("version")) != "1":
            raise ValueError(f"Nicht unterstützte Version: {doc.get('version')}")
        data = doc.get("data") or {}
        report: dict[str, dict[str, int]] = {}
        with self._lock:
            # Peers sind instanzlokale Konfiguration — werden niemals
            # exportiert/importiert (Datenschutz + keine UUID-Wanderung).
            for coll in (c for c in COLLECTIONS if c != "peers"):
                added = skipped = updated = 0
                for entity in data.get(coll, []):
                    eid = entity.get("id")
                    if not eid:
                        raise ValueError(f"{coll}: Eintrag ohne id")
                    existing = self._state[coll].get(eid)
                    if existing is None:
                        self._state[coll][eid] = entity
                        added += 1
                    elif coll == "variants" and \
                            existing.get("status", "entwurf") != entity.get("status", "entwurf"):
                        # Einzige sanktionierte Ausnahme von "first write wins":
                        # variant.status (der v2-mutable Feld) darf sich
                        # föderiert verbreiten — alles andere wird nie überschrieben.
                        existing["status"] = entity.get("status", "entwurf")
                        updated += 1
                    else:
                        skipped += 1  # Duplikat → nichts überschreiben
                report[coll] = {"added": added, "skipped": skipped,
                                **({"updated": updated} if updated else {})}
            self._save()
        return report
