"""Quellenräume: atomare Identität, Herkunft und vorhandene Worktrees."""
import importlib
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient


# Auch das Importieren der App darf keinen Standard-/Produktivbestand erzeugen.
TEMP_ROOT = Path(os.environ.get("MOONCELLS_TEST_TMPDIR",
    "/Volumes/ThunderBolt4_2TB/Development/Tmp" if sys.platform == "darwin" else tempfile.gettempdir()))
if not TEMP_ROOT.is_dir():
    raise RuntimeError("Konfigurierter Prüfbereich fehlt")
IMPORT_DIR = tempfile.TemporaryDirectory(prefix="mooncells-import-test-", dir=TEMP_ROOT)
with patch.dict(os.environ, {"MOONCELLS_DATA": str(Path(IMPORT_DIR.name) / "state.json")}):
    api = importlib.import_module("server.app")
from server.store import JsonStore


def tearDownModule():
    IMPORT_DIR.cleanup()


class SourceSpaceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="mooncells-source-test-", dir=TEMP_ROOT)
        self.store = JsonStore(str(Path(self.directory.name) / "state.json"))
        self.store_patch = patch.object(api, "store", self.store)
        self.sync_patch = patch.object(api, "trigger_autosync", lambda: None)
        self.store_patch.start()
        self.sync_patch.start()
        self.client = TestClient(api.app)
        agent_response = self.client.post("/api/agents", json={"handle": "pruefender-agent", "agent_type": "model"})
        self.assertEqual(agent_response.status_code, 201, agent_response.text)
        self.agent = agent_response.json()

    def tearDown(self):
        self.client.close()
        self.sync_patch.stop()
        self.store_patch.stop()
        self.directory.cleanup()

    def payload(self, source_id="source-a"):
        return {
            "source_ref": {"system": "moonfingers", "kind": "artifact", "source_id": source_id,
                           "title": "Belegte Prüfquelle", "locator": "archive://pruefung/quelle"},
            "title": "Belegte Prüfquelle",
            "content": "Unveränderter Prüftext\nmit Umlauten: äußere Räume.\n",
            "notes": "Technische Prüfdaten; kein Werk von Ralf.",
            "author_id": self.agent["id"],
        }

    def create_space(self, payload=None):
        response = self.client.post("/api/source-spaces", json=payload or self.payload())
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_idempotent_creation_retains_original_content_and_persists(self):
        payload = self.payload()
        first = self.create_space(payload)
        retry = {**payload, "title": "Neuer Anzeigename", "content": "Kein Überschreiben"}
        retry["source_ref"] = {**payload["source_ref"], "title": "Neuer Anzeigename"}
        second = self.create_space(retry)
        self.assertTrue(first["created"])
        self.assertFalse(second["created"])
        for key in ("work", "worktree", "variant"):
            self.assertEqual(first[key], second[key])
            self.assertEqual(len(self.store.list(key + "s")), 1)
        variant = first["variant"]
        self.assertEqual(variant["content"], payload["content"])
        self.assertEqual(variant["status"], "entwurf")
        self.assertIsNone(variant["derived_from"])
        self.assertEqual(variant["label"], "Quellfassung")
        self.assertEqual(variant["source_ref"], first["work"]["source_ref"])
        reopened = JsonStore(self.store.path)
        self.assertEqual(reopened.get("variants", variant["id"]), variant)

    def test_parallel_requests_share_one_atomic_source_space(self):
        with patch.object(self.store, "_save", wraps=self.store._save) as save:
            with ThreadPoolExecutor(max_workers=8) as pool:
                responses = list(pool.map(lambda _: self.create_space(), range(8)))
        self.assertEqual(sum(r["created"] for r in responses), 1)
        self.assertEqual(len({r["work"]["id"] for r in responses}), 1)
        self.assertEqual(save.call_count, 1)
        for collection in ("works", "worktrees", "variants"):
            self.assertEqual(len(self.store.list(collection)), 1)

    def test_save_failure_rolls_back_entire_source_space(self):
        with patch.object(self.store, "_save", side_effect=OSError("Prüf-Schreibfehler")):
            with self.assertRaises(OSError):
                self.client.post("/api/source-spaces", json=self.payload())
        reopened = JsonStore(self.store.path)
        for collection in ("works", "worktrees", "variants"):
            self.assertEqual(self.store.list(collection), [])
            self.assertEqual(reopened.list(collection), [])
        self.assertEqual(len(self.store.list("agents")), 1)

    def test_unknown_agent_and_missing_source_identity_do_not_write(self):
        payload = self.payload()
        payload["author_id"] = "fehlender-agent"
        self.assertEqual(self.client.post("/api/source-spaces", json=payload).status_code, 422)
        payload = self.payload()
        del payload["source_ref"]["source_id"]
        self.assertEqual(self.client.post("/api/source-spaces", json=payload).status_code, 422)
        self.assertEqual(self.store.list("works"), [])

    def test_existing_work_without_source_root_is_explicit_conflict(self):
        payload = self.payload()
        self.client.post("/api/works", json={"work_type": "text", "title": payload["title"],
                                             "source_ref": payload["source_ref"],
                                             "author_id": self.agent["id"]})
        response = self.client.post("/api/source-spaces", json=payload)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(len(self.store.list("works")), 1)
        self.assertEqual(self.store.list("variants"), [])

    def test_worktree_creation_validates_relations_and_work_reads_all_trees(self):
        space = self.create_space()
        work_id = space["work"]["id"]
        for work, author in (("fehlendes-werk", self.agent["id"]), (work_id, "fehlender-agent")):
            response = self.client.post("/api/worktrees", json={"work_id": work, "author_id": author})
            self.assertEqual(response.status_code, 422)
        response = self.client.post("/api/worktrees", json={"work_id": work_id, "author_id": self.agent["id"]})
        self.assertEqual(response.status_code, 201)
        tree = response.json()
        variant_response = self.client.post("/api/variants", json={
            "worktree_id": tree["id"], "label": "Andere Prüf-Ausprägung", "content": "Andere Fassung",
            "author_id": self.agent["id"], "source_ref": self.payload()["source_ref"],
        })
        self.assertEqual(variant_response.status_code, 201)
        result = self.client.get("/api/works/" + work_id).json()
        self.assertEqual(result["worktree"], space["worktree"])
        self.assertEqual({t["id"] for t in result["worktrees"]}, {space["worktree"]["id"], tree["id"]})
        self.assertEqual({v["id"] for v in result["variants"]}, {space["variant"]["id"], variant_response.json()["id"]})

    def test_reference_edges_preserve_source_identity(self):
        origin = self.create_space()
        target = self.create_space(self.payload("source-b"))
        source_ref = {"system": "moonfingers", "kind": "artifact-link", "source_id": "link-a-b",
                      "title": "Belegter Verweis"}
        response = self.client.post("/api/edges", json={
            "edge_type": "verweist-auf", "from_variant_id": origin["variant"]["id"],
            "to_variant_id": target["variant"]["id"], "note": "Belegter Prüf-Verweis",
            "author_id": self.agent["id"], "source_ref": source_ref,
        })
        self.assertEqual(response.status_code, 201)
        edge = response.json()
        self.assertEqual(edge["edge_type"], "verweist-auf")
        self.assertEqual(edge["source_ref"]["source_id"], source_ref["source_id"])
        self.assertEqual(JsonStore(self.store.path).get("edges", edge["id"]), edge)

    def test_health_reports_actual_instance_and_storage(self):
        result = self.client.get("/api/health").json()
        self.assertEqual(result["service"], "mooncells")
        self.assertEqual(result["instance_id"], api.INSTANCE_ID)
        self.assertEqual(result["data_path"], str(Path(self.store.path).resolve()))
        self.assertEqual(result["capabilities"], ["source-spaces", "worktrees", "source-ref"])


if __name__ == "__main__":
    unittest.main()
