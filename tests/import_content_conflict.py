"""Importreihenfolge darf den öffentlichen Eintrag nicht entscheiden.

Gleicher Kennung und abweichender Inhalt ergeben in beiden Reihenfolgen
denselben Konfliktbericht und denselben öffentlichen Zustand.
"""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from server.store import JsonStore

NOW = "2026-10-27T00:00:00+00:00"
NOTES = "kennung-notiz"
STATUS = "kennung-status"
SHARED = "kennung-gemeinsam"
ACTOR = "kennung-akteur"
ONE = "Inhalt eins"
OTHER = "Inhalt zwei"


def document(variants, agents=None):
    return {
        "format": "mooncells-document",
        "version": "1",
        "instance_id": "isolierte-probe",
        "exported_by": ACTOR,
        "exported_at": NOW,
        "data": {
            "agents": agents if agents is not None else [agent("Akteur")],
            "variants": variants,
        },
    }


def agent(handle):
    return {"id": ACTOR, "handle": handle, "agent_type": "human", "created_at": NOW}


def variant(kenn, label, notes, status="entwurf"):
    return {
        "id": kenn, "worktree_id": "kennung-werkbaum", "derived_from": None,
        "label": label, "notes": notes, "status": status, "author_id": ACTOR,
        "created_at": NOW,
    }


def shared_variant():
    return variant(SHARED, "Gemeinsames Label", "Gleicher Inhalt")


class ImportContentConflictTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="import-conflict-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def store(self, name):
        return JsonStore(str(self.root / name / "state.json"))

    def test_import_order_does_not_decide_public_state(self):
        packets = {
            "A": document(
                [variant(NOTES, "Label eins", ONE), shared_variant()],
                [agent("Akteur eins")],
            ),
            "B": document(
                [variant(NOTES, "Label zwei", OTHER), shared_variant()],
                [agent("Akteur zwei")],
            ),
        }
        status_packets = {
            "draft": document([variant(STATUS, "Festes Label", "Feste Notiz", "entwurf")]),
            "reviewed": document([variant(STATUS, "Festes Label", "Feste Notiz", "geprüft")]),
        }
        fresh = [self._run(packets, ["A", "B"]), self._run(packets, ["B", "A"])]
        self._assert_same_public_outcome(fresh, NOTES, {ONE, OTHER}, ["label", "notes"])
        self.assertEqual(
            [item["label"] for item in fresh[0]["public"]["variants"]],
            ["Gemeinsames Label"],
        )
        reloaded = JsonStore(fresh[0]["path"])
        again = reloaded.import_document(copy.deepcopy(packets["A"]))
        self.assertEqual(reloaded.list("variants"), fresh[0]["public"]["variants"])
        self.assertEqual(again["variants"]["conflicts"][0]["kind"], "content-conflict")
        self.assertNotIn(ONE, json.dumps(again["variants"]["conflicts"]))

        status = [
            self._run(status_packets, ["draft", "reviewed"]),
            self._run(status_packets, ["reviewed", "draft"]),
        ]
        self._assert_same_public_outcome(status, STATUS, {"entwurf", "geprüft"}, ["status"])
        self.assertNotIn("updated", json.dumps(status[0]["reports"]))

        within = []
        for order in (["A", "B"], ["B", "A"]):
            combined = document(
                [variant(NOTES, "Label eins" if key == "A" else "Label zwei",
                         ONE if key == "A" else OTHER) for key in order],
                [agent("Akteur eins"), agent("Akteur zwei")],
            )
            store = self.store("batch-" + "-".join(order))
            report = store.import_document(combined)
            within.append({"public": self._public(store), "report": report, "path": store.path})
        self.assertEqual(within[0]["public"], within[1]["public"])
        self.assertEqual(within[0]["public"]["variants"], [])
        self.assertEqual(
            within[0]["report"]["variants"]["conflicts"][0]["changedFields"],
            within[1]["report"]["variants"]["conflicts"][0]["changedFields"],
        )
        self.assertEqual(within[0]["report"]["agents"]["conflicts"][0]["kind"], "content-conflict")

        catalog = []
        original = variant(NOTES, "Bestand", "Öffentlicher Eintrag")
        for order in (["A", "B"], ["B", "A"]):
            store = self.store("catalog-" + "-".join(order))
            store.add("variants", copy.deepcopy(original))
            before = copy.deepcopy(store.get("variants", NOTES))
            reports = [store.import_document(copy.deepcopy(packets[key])) for key in order]
            catalog.append({
                "entry": copy.deepcopy(store.get("variants", NOTES)),
                "before": before,
                "reports": reports,
                "public": self._public(store),
            })
        self.assertEqual(catalog[0]["entry"], catalog[0]["before"])
        self.assertEqual(catalog[0]["entry"], catalog[1]["entry"])
        self.assertEqual(catalog[0]["public"]["variants"], catalog[1]["public"]["variants"])
        for item in catalog:
            self.assertTrue(all(report["variants"]["conflicts"] for report in item["reports"]))
            self.assertNotIn(ONE, json.dumps(item["entry"]))
            self.assertNotIn(OTHER, json.dumps(item["entry"]))

        stale = self.store("stale-status")
        stale.import_document(copy.deepcopy(status_packets["draft"]))
        stale.update_fields("variants", STATUS, {"status": "geprüft"})
        protected = copy.deepcopy(stale.get("variants", STATUS))
        stale_report = stale.import_document(copy.deepcopy(status_packets["draft"]))
        self.assertEqual(stale.get("variants", STATUS), protected)
        self.assertEqual(stale_report["variants"]["conflicts"][0]["changedFields"], ["status"])
        self.assertEqual(protected["status"], "geprüft")

        repeated = self.store("repeat")
        first = repeated.import_document(copy.deepcopy(packets["A"]))
        before = Path(repeated.path).read_bytes()
        second = repeated.import_document(copy.deepcopy(packets["A"]))
        self.assertEqual(first["variants"]["conflicts"], [])
        self.assertEqual(second["variants"], {"added": 0, "skipped": 2, "conflicts": []})
        self.assertEqual(second["agents"], {"added": 0, "skipped": 1, "conflicts": []})
        self.assertEqual(Path(repeated.path).read_bytes(), before)

    def _run(self, packets, order):
        store = self.store("order-" + "-".join(order) + "-" + next(iter(packets)))
        reports = [store.import_document(copy.deepcopy(packets[key])) for key in order]
        return {
            "public": self._public(store),
            "reports": reports,
            "bytes": Path(store.path).read_bytes(),
            "path": store.path,
        }

    def _public(self, store):
        return {coll: copy.deepcopy(store.list(coll)) for coll in
                ("agents", "works", "worktrees", "variants", "edges", "findings")}

    def _assert_same_public_outcome(self, outcomes, kenn, raw_values, fields):
        self.assertEqual(outcomes[0]["public"], outcomes[1]["public"])
        self.assertEqual(outcomes[0]["bytes"], outcomes[1]["bytes"])
        stored = json.dumps(outcomes[0]["public"])
        self.assertNotIn(kenn, stored)
        for value in raw_values:
            self.assertNotIn(value, stored)
        conflicts = []
        for outcome in outcomes:
            found = [conflict for report in outcome["reports"]
                     for coll in report.values() for conflict in coll["conflicts"]]
            self.assertTrue(found)
            conflicts.append(found)
            for conflict in found:
                self.assertEqual(conflict["kind"], "content-conflict")
                self.assertNotIn("updated", conflict)
                for value in raw_values:
                    self.assertNotIn(value, json.dumps(conflict))
        self.assertEqual(conflicts[0], conflicts[1])
        matched = [item for item in conflicts[0] if item["id"] == kenn]
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0]["changedFields"], fields)


if __name__ == "__main__":
    unittest.main()
