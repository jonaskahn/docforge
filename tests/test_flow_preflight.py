"""Surface-aware preflight ledger parity and safety tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _support import run, write_gitnexus_interchange
from test_flow_analysis import analysis_pack, flow_card


def payload() -> dict:
    def process(identifier: str, entry: str, terminal: str, steps: list[dict]) -> dict:
        return {
            "id": identifier, "entryPointId": entry, "terminalId": terminal,
            "processType": "cross_community", "communities": ["api"], "steps": steps,
        }
    return {
        "routes": [
            {"id": "route-create", "path": "POST /orders", "filePath": "src/http/orders.py", "symbol": "create"},
            {"id": "route-read", "path": "GET /orders", "filePath": "src/http/orders.py", "symbol": "read"},
        ],
        "communities": [{"id": "api", "heuristicLabel": "API"}],
        "processes": [
            process("write-db", "Function:src/http/orders.py:create", "Function:src/db.py:save", [
                {"order": 1, "nodeId": "create", "filePath": "src/http/orders.py", "symbol": "create", "line": 10},
                {"order": 2, "nodeId": "save", "filePath": "src/db.py", "symbol": "save", "line": 20},
            ]),
            process("write-event", "Function:src/http/orders.py:create", "Function:src/queue.py:publish", [
                {"order": 1, "nodeId": "create", "filePath": "src/http/orders.py", "symbol": "create", "line": 10},
                {"order": 2, "nodeId": "publish", "filePath": "src/queue.py", "symbol": "publish", "line": 30},
            ]),
            process("read-db", "Function:src/http/orders.py:read", "Function:src/db.py:find", [
                {"order": 1, "nodeId": "read", "filePath": "src/http/orders.py", "symbol": "read", "line": 40},
                {"order": 2, "nodeId": "find", "filePath": "src/db.py", "symbol": "find", "line": 50},
            ]),
            process("nightly", "Function:src/jobs/nightly.py:cronJob", "Function:src/db.py:archive", [
                {"order": 1, "nodeId": "cron", "filePath": "src/jobs/nightly.py", "symbol": "cronJob", "line": 5},
                {"order": 2, "nodeId": "archive", "filePath": "src/db.py", "symbol": "archive", "line": 70},
            ]),
        ],
    }


class FlowPreflightTests(unittest.TestCase):
    def test_harvest_revise_and_analysis_prepare_refresh_preflight_automatically(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                write_gitnexus_interchange(repo, payload())
                # A normal fresh harvest gets topology evidence without a
                # separate preflight command.
                harvested = run(runtime, "flow_index", "harvest", "--repo", str(repo), "--main-limit", "2")
                self.assertEqual(harvested.returncode, 0, harvested.stderr)
                self.assertIn("refreshed surface-aware flow preflight", harvested.stdout)
                evidence = repo / ".docforge" / "flow-evidence.json"
                self.assertTrue(evidence.is_file())
                revised = run(runtime, "flow_index", "revise", "--repo", str(repo), "--main-limit", "2")
                self.assertEqual(revised.returncode, 0, revised.stderr)
                self.assertIn("refreshed surface-aware flow preflight", revised.stdout)
                # A fresh analysis preparation performs the same refresh and
                # emits topology-backed questions in its companion pack.
                prepared = run(runtime, "flow_analysis", "prepare", "--repo", str(repo), "--json")
                self.assertEqual(prepared.returncode, 0, prepared.stderr)
                pack = json.loads((repo / ".docforge" / "flow-investigation.json").read_text())
                self.assertTrue(pack["entries"])
                self.assertTrue(pack["entries"][0]["topology_variants"])

    def test_native_paths_stay_independent_and_coverage_precedes_score(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                write_gitnexus_interchange(repo, payload())
                prepared = run(runtime, "flow_preflight", "prepare", "--repo", str(repo))
                self.assertEqual(prepared.returncode, 0, prepared.stderr)
                valid = run(runtime, "flow_preflight", "validate", "--repo", str(repo))
                self.assertEqual(valid.returncode, 0, valid.stderr)
                ledger = json.loads((repo / ".docforge" / "flow-evidence.json").read_text())
                create = next(item for item in ledger["entry_points"] if item["locator"]["symbol"] == "create")
                paths = [item for item in ledger["path_variants"] if item["entry_ref"] == create["id"]]
                self.assertEqual({item["process_id"] for item in paths}, {"write-db", "write-event"})
                self.assertEqual(len(paths), 2)
                harvested = run(runtime, "flow_index", "harvest", "--repo", str(repo), "--main-limit", "2")
                self.assertEqual(harvested.returncode, 0, harvested.stderr)
                index = json.loads((repo / ".docforge" / "flow-index.json").read_text())
                main = [item for item in index["flows"] if item["priority"] == "main"]
                self.assertEqual({item["entry_ref"]["kind"] for item in main}, {"http", "schedule"})

    def test_changed_fingerprint_marks_only_affected_entry_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            initial = payload()
            write_gitnexus_interchange(repo, initial)
            self.assertEqual(run("py", "flow_preflight", "prepare", "--repo", str(repo)).returncode, 0)
            ledger_path = repo / ".docforge" / "flow-evidence.json"
            first = json.loads(ledger_path.read_text())
            create = next(item for item in first["entry_points"] if item["locator"]["symbol"] == "create")
            enrichment = repo / "enrichment.json"
            enrichment.write_text(json.dumps({"entries": [{"id": create["id"], "enrichment": {"source": "read"}}]}))
            self.assertEqual(run("py", "flow_preflight", "import", "--repo", str(repo), "--input", str(enrichment)).returncode, 0)
            # The provider artifact changed.  The create entry is therefore
            # stale/not-analyzed, while unrelated records remain available.
            initial["processes"][0]["steps"][1]["symbol"] = "saveChanged"
            write_gitnexus_interchange(repo, initial)
            self.assertEqual(run("py", "flow_preflight", "prepare", "--repo", str(repo)).returncode, 0)
            second = json.loads(ledger_path.read_text())
            refreshed = next(item for item in second["entry_points"] if item["id"] == create["id"])
            self.assertTrue(refreshed["stale"])
            self.assertEqual(refreshed["analysis_state"], "not-analyzed")
            self.assertTrue(all(
                item["id"] == create["id"] or not item["stale"]
                for item in second["entry_points"]
            ))

    def test_python_and_node_normalized_ledger_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            left, right = Path(tmp) / "py", Path(tmp) / "js"
            for repo, runtime in ((left, "py"), (right, "js")):
                write_gitnexus_interchange(repo, payload())
                result = run(runtime, "flow_preflight", "prepare", "--repo", str(repo))
                self.assertEqual(result.returncode, 0, result.stderr)
            py = json.loads((left / ".docforge" / "flow-evidence.json").read_text())
            js = json.loads((right / ".docforge" / "flow-evidence.json").read_text())
            py["generated_at"] = js["generated_at"] = "<TIME>"
            self.assertEqual(py, js)

    def test_incomplete_topology_cannot_pass_flow_analysis_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            broken = payload()
            broken["processes"][0].pop("steps")
            write_gitnexus_interchange(repo, broken)
            self.assertEqual(run("py", "flow_preflight", "prepare", "--repo", str(repo)).returncode, 0)
            ledger = json.loads((repo / ".docforge" / "flow-evidence.json").read_text())
            entry = next(item for item in ledger["entry_points"] if item["locator"]["symbol"] == "create")
            (repo / "src").mkdir()
            (repo / "src" / "flow.py").write_text("def run():\n    return True\n")
            card = flow_card()
            card["evidence_refs"] = entry["evidence_refs"]
            source = repo / "analysis.json"
            source.write_text(json.dumps(analysis_pack([card])))
            imported = run("py", "flow_analysis", "import", "--repo", str(repo), "--analysis", str(source))
            self.assertNotEqual(imported.returncode, 0)
            self.assertIn("not analysis-ready", imported.stderr)


if __name__ == "__main__":
    unittest.main()
