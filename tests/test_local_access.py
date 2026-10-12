"""Direct local API access must retain the Moonfingers browser boundary."""
import importlib
import os
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient


TEMP_ROOT = Path(os.environ.get("MOONCELLS_TEST_TMPDIR",
    "/Volumes/ThunderBolt4_2TB/Development/Tmp" if sys.platform == "darwin" else tempfile.gettempdir()))
if not TEMP_ROOT.is_dir():
    raise RuntimeError("Konfigurierter Prüfbereich fehlt")
IMPORT_DIR = tempfile.TemporaryDirectory(prefix="mooncells-access-import-", dir=TEMP_ROOT)
with patch.dict(os.environ, {"MOONCELLS_DATA": str(Path(IMPORT_DIR.name) / "state.json")}):
    api = importlib.import_module("server.app")
from server.store import JsonStore


def tearDownModule():
    IMPORT_DIR.cleanup()


class LocalAccessTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="mooncells-access-test-", dir=TEMP_ROOT)
        self.store = JsonStore(str(Path(self.directory.name) / "state.json"))
        self.patches = [patch.object(api, "store", self.store),
                        patch.object(api, "INSTANCE_ID", "mooncells-moonfingers"),
                        patch.object(api, "trigger_autosync", lambda: None)]
        for item in self.patches:
            item.start()
        self.client = TestClient(api.app, base_url="http://127.0.0.1:8401")
        self.agent = {"handle": "Zugriffsprüfung", "agent_type": "model"}

    def tearDown(self):
        self.client.close()
        for item in reversed(self.patches):
            item.stop()
        self.directory.cleanup()

    def test_connector_and_same_origin_browser_can_write(self):
        for index, headers in enumerate(({}, {"Origin": "http://localhost:8401", "Sec-Fetch-Site": "same-origin"})):
            response = self.client.post("/api/agents", json={**self.agent, "handle": f"Zugriffsprüfung {index}"}, headers=headers)
            self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_untrusted_host_and_other_listener_cannot_write(self):
        for host in ("example.org:8401", "127.0.0.1:8400", "127.0.0.1:8401@evil.org", ""):
            response = self.client.post("/api/agents", json=self.agent, headers={"Host": host})
            self.assertEqual(response.status_code, 403, response.text)
        self.assertEqual(self.store.list("agents"), [])

    def test_foreign_and_opaque_origins_cannot_write(self):
        for origin in ("https://example.org", "http://127.0.0.1:4322", "null", "https://localhost:8401"):
            response = self.client.post("/api/agents", json=self.agent, headers={"Origin": origin})
            self.assertEqual(response.status_code, 403, response.text)
        self.assertEqual(self.store.list("agents"), [])

    def test_fetch_metadata_blocks_cross_site_reads_and_writes(self):
        headers = {"Sec-Fetch-Site": "cross-site", "Sec-Fetch-Mode": "cors"}
        self.assertEqual(self.client.get("/api/graph", headers=headers).status_code, 403)
        self.assertEqual(self.client.post("/api/peers", json={"url": "https://example.org"},
                                          headers=headers).status_code, 403)
        self.assertEqual(self.store.list("peers"), [])
        headers["Sec-Fetch-Mode"] = "navigate"
        self.assertEqual(self.client.get("/", headers=headers).status_code, 200)
        self.assertEqual(self.client.post("/api/agents", json=self.agent, headers=headers).status_code, 403)

    def test_standalone_8400_and_hosted_instances_keep_existing_access(self):
        with patch.object(api, "INSTANCE_ID", "mooncells-local"):
            with TestClient(api.app, base_url="http://localhost:8400") as client:
                self.assertEqual(client.get("/").status_code, 200)
                self.assertEqual(client.post("/api/agents", json=self.agent,
                                             headers={"Origin": "http://localhost:8400"}).status_code, 201)
        with patch.object(api, "INSTANCE_ID", "mooncells-hosted"):
            with TestClient(api.app, base_url="https://mooncells.example.org") as client:
                self.assertEqual(client.get("/api/health").status_code, 200)


if __name__ == "__main__":
    unittest.main()
