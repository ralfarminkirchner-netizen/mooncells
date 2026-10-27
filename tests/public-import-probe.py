#!/usr/bin/env python3
"""Bounded, local proof of the public Mooncells import at a fixed revision.

Run from any directory (Python with existing Pydantic 2 required):
  python3 tests/public-import-probe.py --temp-root /existing/absolute/temp-dir \
      --output /existing/absolute/result.json
The temporary directory and output parent must exist; output is a JSON file.
Only the two pinned public Git blobs are loaded. Fake state is temporary and
deleted. No HTTP, service, canonical state, installation, or Git mutation.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

REVISION = "95f7923eb58b6a1ed540c2daa86c255998e39c0d"
PUBLIC_REMOTE = "https://github.com/ralfarminkirchner-netizen/mooncells.git"
EXPECTED_SOURCES = {
    "server/store.py": {"gitBlob": "848b1bba833a4315d648397c91b50a1ce8fbabdb",
                        "sha256": "7dd77f82b901afa088b5f7a7ddbb86f3c2c23f0486358151c57586a04f743e4a"},
    "server/models.py": {"gitBlob": "bcc350d8672b9a14b03fe47fe7419ed5527820a9",
                         "sha256": "f611b2ef761119db2eedd3c2ca90a6a897bc598619eb2859d56d8df60a8204b9"},
}
NOW = "2026-10-27T00:00:00+00:00"
IDS = {name: f"00000000-0000-4000-8000-{index:012d}" for index, name in
       enumerate(("agent", "work", "worktree", "notes", "label", "status"), 1)}
sys.dont_write_bytecode = True


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def fake_document(models, changes):
    variants = []
    for key, label, notes, status in changes:
        variants.append(models.Variant(
            id=IDS[key], worktree_id=IDS["worktree"], label=label, notes=notes,
            status=status, author_id=IDS["agent"], created_at=NOW))
    return models.MooncellsDocument(
        instance_id="isolated-fake-instance", exported_by=IDS["agent"],
        exported_at=NOW, data=models.DocumentData(
            agents=[models.Agent(id=IDS["agent"], handle="Local fake actor",
                                 agent_type="human", created_at=NOW)],
            works=[models.Work(id=IDS["work"], work_type="fake-test",
                               title="Local fake work", author_id=IDS["agent"],
                               created_at=NOW)],
            worktrees=[models.Worktree(id=IDS["worktree"], work_id=IDS["work"],
                                      author_id=IDS["agent"], created_at=NOW)],
            variants=variants)).model_dump(mode="json")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parent.parent,
                        help="Git checkout containing the pinned public commit; defaults to this repository")
    parser.add_argument("--temp-root", required=True, type=Path,
                        help="Existing absolute directory for disposable fake state")
    parser.add_argument("--output", required=True, type=Path,
                        help="Absolute JSON result file in an existing directory")
    args = parser.parse_args()
    if not args.temp_root.is_absolute() or not args.temp_root.is_dir():
        parser.error("--temp-root must be an existing absolute directory")
    if (not args.output.is_absolute() or not args.output.parent.is_dir()
            or args.output.is_symlink()
            or (args.output.exists() and not args.output.is_file())):
        parser.error("--output must be an absolute regular file in an existing directory, not a symlink")
    temp_root = args.temp_root.resolve()
    output = args.output.resolve()
    if git(args.repo, "rev-parse", REVISION).decode().strip() != REVISION:
        raise RuntimeError("Pinned public commit missing")
    source_bindings = {}
    checks = []

    def check(name, condition):
        checks.append({"check": name, "passed": bool(condition)})
        assert condition, name

    with tempfile.TemporaryDirectory(prefix="public-mooncells-import-", dir=temp_root) as temp:
        temp = Path(temp)
        for module_name in ("store", "models"):
            source_path = f"server/{module_name}.py"
            content = git(args.repo, "show", f"{REVISION}:{source_path}")
            source_bindings[source_path] = {
                "gitBlob": git(args.repo, "rev-parse", f"{REVISION}:{source_path}").decode().strip(),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
            if source_bindings[source_path] != EXPECTED_SOURCES[source_path]:
                raise RuntimeError(f"Pinned public source binding mismatch: {source_path}")
            (temp / f"{module_name}.py").write_bytes(content)
        store_module = load_module("isolated_public_mooncells_store", temp / "store.py")
        models = load_module("isolated_public_mooncells_models", temp / "models.py")
        packets = {
            "A": fake_document(models, [("notes", "Fixed fake label", "Fake notes A", "entwurf"),
                                         ("label", "Fake label A", "Fixed fake notes", "entwurf")]),
            "B": fake_document(models, [("notes", "Fixed fake label", "Fake notes B", "entwurf"),
                                         ("label", "Fake label B", "Fixed fake notes", "entwurf")]),
            "draft": fake_document(models, [("status", "Fixed fake label", "Fixed fake notes", "entwurf")]),
            "reviewed": fake_document(models, [("status", "Fixed fake label", "Fixed fake notes", "geprüft")]),
        }

        def run_case(name, order):
            path = temp / name / "state.json"
            store = store_module.JsonStore(str(path))
            steps = []
            for key in order:
                # Copy because the public store retains entity dictionaries.
                report = store.import_document(copy.deepcopy(packets[key]))
                steps.append({"packet": key, "variants": report["variants"]})
                check(f"{name}/{key}: no conflict-report field",
                      set(report).issubset(set(store_module.COLLECTIONS)))
            before = path.read_bytes()
            last_packet = order[-1]
            repeat = store.import_document(copy.deepcopy(packets[last_packet]))
            after = path.read_bytes()
            expected = len(packets[last_packet]["data"]["variants"])
            check(f"{name}: immediate repeat skips identical variants",
                  repeat["variants"] == {"added": 0, "skipped": expected})
            check(f"{name}: immediate repeat keeps byte-identical stored state", before == after)
            check(f"{name}: all repeated entities skipped",
                  all(item["added"] == 0 and "updated" not in item for item in repeat.values()))
            restarted = store_module.JsonStore(str(path))
            check(f"{name}: reloaded state equals stored state",
                  restarted.list("variants") == store.list("variants"))
            return {"order": order, "steps": steps,
                    "finalVariants": [{k: v[k] for k in ("id", "label", "notes", "status")}
                                      for v in store.list("variants")],
                    "repeatReport": repeat,
                    "stateSha256": hashlib.sha256(after).hexdigest()}, store

        ab, _ = run_case("notes-labels-A-B", ["A", "B"])
        ba, _ = run_case("notes-labels-B-A", ["B", "A"])
        check("different notes and labels: A then B keeps A",
              ab["finalVariants"][0]["notes"] == "Fake notes A"
              and ab["finalVariants"][1]["label"] == "Fake label A")
        check("different notes and labels: B then A keeps B",
              ba["finalVariants"][0]["notes"] == "Fake notes B"
              and ba["finalVariants"][1]["label"] == "Fake label B")
        check("same-ID unequal content: opposite import orders do not converge",
              ab["finalVariants"] != ba["finalVariants"])
        dr, status_store = run_case("status-draft-reviewed", ["draft", "reviewed"])
        rd, _ = run_case("status-reviewed-draft", ["reviewed", "draft"])
        check("status: last imported value wins in both orders",
              dr["finalVariants"][0]["status"] == "geprüft"
              and rd["finalVariants"][0]["status"] == "entwurf"
              and dr["steps"][-1]["variants"] == {"added": 0, "skipped": 0, "updated": 1}
              and rd["steps"][-1]["variants"] == {"added": 0, "skipped": 0, "updated": 1})
        stale_report = status_store.import_document(copy.deepcopy(packets["draft"]))
        check("a previously seen stale status packet overwrites a newer local value",
              status_store.get("variants", IDS["status"])["status"] == "entwurf"
              and stale_report["variants"] == {"added": 0, "skipped": 0, "updated": 1})
        result = {
            "revision": REVISION, "publicRemote": PUBLIC_REMOTE,
            "sources": source_bindings,
            "runtime": {"python": sys.version.split()[0], "pydantic": __import__("pydantic").__version__},
            "scope": "Actual public models and JsonStore.import_document; fake local records; no HTTP/API/sync/service test",
            "cases": [ab, ba, dr, rd],
            "staleStatusReplay": {"variants": stale_report["variants"],
                                  "finalStatus": status_store.get("variants", IDS["status"])["status"]},
            "checks": checks, "passed": all(item["passed"] for item in checks),
            "temporaryStateRemovedOnExit": True,
        }
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Revision: {REVISION}")
    print(f"PASS {len(checks)} bounded assertions; public models + public store; no HTTP or services")
    print("Notes/labels: A→B retains A; B→A retains B; known IDs skipped without content conflict report.")
    print("Status: draft→reviewed ends reviewed; reviewed→draft ends draft; status updates reported updated=1.")
    print("Immediate identical repeat: every case all skipped and persisted state byte-identical.")
    print("Replay of previously seen draft after reviewed: updated=1, final draft (no freshness guard).")
    print(f"Evidence: {output}")
    print("Temporary public sources and fake state removed.")


if __name__ == "__main__":
    main()
