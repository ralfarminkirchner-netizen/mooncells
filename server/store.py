"""JSON-Datei-Storage mit append-only-Semantik und Konfliktbericht beim Import.

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

import copy
import hashlib
import json
import os
import threading
import uuid
from typing import Any, Optional

COLLECTIONS = ["agents", "works", "worktrees", "variants", "edges", "findings",
               "peers"]


def new_uuid() -> str:
    return str(uuid.uuid4())


def _content_material(entity: dict) -> dict:
    """Kennung ist Identität. Alles andere ist Inhalt."""
    return {key: value for key, value in entity.items() if key != "id"}


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _content_digest(entity: dict) -> str:
    return hashlib.sha256(_canonical(_content_material(entity)).encode("utf-8")).hexdigest()


def _changed_fields(left: dict, right: dict) -> list[str]:
    keys = (set(left) | set(right)) - {"id"}
    return sorted(key for key in keys if _canonical(left.get(key)) != _canonical(right.get(key)))


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
            self._ledger = self._read_ledger(raw.get("importLedger"))
        else:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            self._state = {coll: {} for coll in COLLECTIONS}
            self._ledger = {}
            self._save()

    # ------------------------------------------------------------ I/O

    def _save(self) -> None:
        """Atomar schreiben: erst tmp, dann rename — kein halber Zustand."""
        tmp = self.path + ".tmp"
        payload = {coll: list(self._state[coll].values()) for coll in COLLECTIONS}
        ledger = {}
        for coll in COLLECTIONS:
            rows = self._ledger.get(coll)
            if rows:
                ledger[coll] = {eid: rows[eid] for eid in sorted(rows)}
        if ledger:
            payload["importLedger"] = ledger
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
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
            self._protect_public_entry(coll, entity)
            self._save()
            return entity

    def find_by(self, coll: str, field: str, value: Any) -> list[dict]:
        with self._lock:
            return [e for e in self._state[coll].values() if e.get(field) == value]

    def delete(self, coll: str, entity_id: str) -> bool:
        """Löschen nur für Konfigurations-Collections (z. B. peers) — die
        Kerndaten (agents…findings) bleiben append-only."""
        with self._lock:
            if entity_id not in self._state[coll]:
                return False
            del self._state[coll][entity_id]
            rows = self._ledger.get(coll)
            if rows is not None:
                rows.pop(entity_id, None)
                if not rows:
                    del self._ledger[coll]
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
            self._protect_public_entry(coll, e)
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
        """Gleiche Kennung mit anderem Inhalt ist ein Konflikt.

        Die Reihenfolge wählt keinen Gewinner. Der Bericht nennt den Konflikt
        ausdrücklich. Ein vorhandener öffentlicher Eintrag wird nicht
        überschrieben. Weichen nur nacheinander importierte Inhalte derselben
        Kennung voneinander ab, bleibt keiner davon als öffentlicher Eintrag
        stehen. Gleicher Inhalt wird übersprungen und ändert nichts.
        """
        if doc.get("format") != "mooncells-document":
            raise ValueError("Kein Mooncells Document (format != 'mooncells-document')")
        if str(doc.get("version")) != "1":
            raise ValueError(f"Nicht unterstützte Version: {doc.get('version')}")
        data = doc.get("data") or {}
        report: dict[str, dict] = {}
        with self._lock:
            # Peers sind instanzlokale Konfiguration — werden niemals
            # exportiert/importiert (Datenschutz + keine UUID-Wanderung).
            for coll in (c for c in COLLECTIONS if c != "peers"):
                grouped: dict[str, list[dict]] = {}
                for entity in data.get(coll, []):
                    if not isinstance(entity, dict):
                        raise ValueError(f"{coll}: Eintrag ohne Objekt")
                    eid = entity.get("id")
                    if not isinstance(eid, str) or not eid:
                        raise ValueError(f"{coll}: Eintrag ohne id")
                    grouped.setdefault(eid, []).append(entity)
                added = skipped = 0
                conflicts = []
                for eid, entities in grouped.items():
                    added_n, skipped_n, conflict = self._merge_kennung(coll, eid, entities)
                    added += added_n
                    skipped += skipped_n
                    if conflict is not None:
                        conflicts.append(conflict)
                report[coll] = {"added": added, "skipped": skipped, "conflicts": conflicts}
            self._save()
        return report

    def _merge_kennung(self, coll: str, eid: str, entities: list[dict]) -> tuple[int, int, Optional[dict]]:
        materials = [_content_material(entity) for entity in entities]
        incoming_hashes: list[str] = []
        for entity in entities:
            digest = _content_digest(entity)
            if digest not in incoming_hashes:
                incoming_hashes.append(digest)
        existing = self._state[coll].get(eid)
        existing_digest = _content_digest(existing) if existing is not None else None
        record = self._ledger_get(coll, eid)
        known_hashes = list(record.get("contentHashes", [])) if record else []
        if existing_digest is not None and existing_digest not in known_hashes:
            known_hashes.append(existing_digest)
        combined = list(known_hashes)
        for digest in incoming_hashes:
            if digest not in combined:
                combined.append(digest)
        same_as_public = (existing is not None and len(incoming_hashes) == 1
                          and incoming_hashes[0] == existing_digest)
        if same_as_public:
            return 0, len(entities), None
        conflict = len(combined) > 1
        if not conflict:
            if existing is None:
                self._state[coll][eid] = copy.deepcopy(entities[0])
                self._ledger_put(coll, eid, "import", combined, [])
                return 1, len(entities) - 1, None
            return 0, len(entities), None
        changed = set(record.get("changedFields", [])) if record else set()
        compared = list(materials)
        if existing is not None:
            compared.append(_content_material(existing))
        for index, left in enumerate(compared):
            for right in compared[index + 1:]:
                changed.update(_changed_fields(left, right))
        origin = record.get("origin") if record else ("catalog" if existing is not None else "import")
        if origin != "catalog" and existing is not None:
            # Kein Importinhalt wird nachträglich zum Gewinner einer anderen Zustellung.
            del self._state[coll][eid]
            origin = "import"
        elif origin != "catalog":
            origin = "import"
        stored_hashes = sorted(set(combined))
        stored_changed = sorted(changed)
        self._ledger_put(coll, eid, origin, stored_hashes, stored_changed)
        return 0, 0, {
            "id": eid,
            "kind": "content-conflict",
            "changedFields": stored_changed,
            "contentHashes": stored_hashes,
        }

    def _protect_public_entry(self, coll: str, entity: dict) -> None:
        """Lokaler Bestand bleibt öffentlicher Eintrag und wird vom Import nicht ersetzt."""
        previous = self._ledger_get(coll, entity["id"])
        if previous is None:
            return
        hashes = sorted(set([*previous.get("contentHashes", []), _content_digest(entity)]))
        self._ledger_put(coll, entity["id"], "catalog", hashes, previous.get("changedFields") or [])

    def _ledger_get(self, coll: str, eid: str) -> Optional[dict]:
        return self._ledger.get(coll, {}).get(eid)

    def _ledger_put(self, coll: str, eid: str, origin: str, hashes: list[str], changed: list[str]) -> None:
        entry = {"origin": origin, "contentHashes": sorted(set(hashes))}
        if changed:
            entry["changedFields"] = sorted(set(changed))
        self._ledger.setdefault(coll, {})[eid] = entry

    @staticmethod
    def _read_ledger(raw: Any) -> dict:
        if raw is None:
            return {}
        if not isinstance(raw, dict):
            raise ValueError("importLedger ist kein Objekt")
        for coll, rows in raw.items():
            if coll not in COLLECTIONS or not isinstance(rows, dict):
                raise ValueError("importLedger ist ungültig")
            for record in rows.values():
                if not isinstance(record, dict) or record.get("origin") not in ("catalog", "import"):
                    raise ValueError("importLedger ist ungültig")
                hashes = record.get("contentHashes")
                changed = record.get("changedFields", [])
                if (not isinstance(hashes, list) or not all(isinstance(item, str) for item in hashes)
                        or not isinstance(changed, list) or not all(isinstance(item, str) for item in changed)):
                    raise ValueError("importLedger ist ungültig")
        return raw
