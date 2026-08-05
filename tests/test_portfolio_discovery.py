"""discover_child_repos: per-member tier reporting and cross-repo flow-edge
resolution (mapping / heuristic / omit), with Python/JS parity."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _support import ROOT, initialize, run


def make_repo(parent: Path, name: str) -> Path:
    repo = parent / name
    repo.mkdir()
    (repo / ".git").mkdir()
    return repo


def write_flow_index_raw(repo: Path, flows: list[dict]) -> None:
    target = repo / ".docforge" / "flow-index.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({
        "version": "1.1",
        "generated_at": "2026-07-29T00:00:00+00:00",
        "project": repo.name,
        "sources": ["fixture"],
        "providers": ["gitnexus"],
        "summary": {"total": len(flows), "main": len(flows), "deferred": 0, "confirmed": 0},
        "flows": flows,
    }, indent=2) + "\n", encoding="utf-8")


def write_repo_identity(root: Path, flows: list[dict]) -> None:
    target = root / ".metadata" / "portfolio" / "repo-identity.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({"version": "1.1", "packages": [], "flows": flows}, indent=2), encoding="utf-8")


class TierFieldTests(unittest.TestCase):
    def test_collection_reports_each_members_own_tier(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            diligent = make_repo(root, "svc-diligent")
            spine_only = make_repo(root, "svc-spine")
            self.assertEqual(initialize("py", diligent, "diligence").returncode, 0)
            self.assertEqual(initialize("py", spine_only, "spine").returncode, 0)

            for runtime in ("py", "js"):
                result = run(runtime, "discover_child_repos", "--root", str(root), "--json")
                self.assertEqual(result.returncode, 0, result.stderr)
                data = json.loads(result.stdout)
                by_path = {c["path"]: c for c in data["collection"]}
                self.assertEqual(by_path[str(diligent)]["tier"], "diligence")
                self.assertEqual(by_path[str(spine_only)]["tier"], "spine")
                self.assertIn("tier: diligence", by_path[str(diligent)]["status"])

    def test_ungenerated_member_reports_null_tier(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_repo(root, "svc-empty")
            for runtime in ("py", "js"):
                result = run(runtime, "discover_child_repos", "--root", str(root), "--json")
                data = json.loads(result.stdout)
                (entry,) = [c for c in data["collection"] if c["membership"].startswith("detected")]
                self.assertIsNone(entry["tier"])
                self.assertTrue(entry["status"].startswith("none"))


class FlowEdgeResolutionTests(unittest.TestCase):
    def test_heuristic_match_against_owners_own_signature(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            caller = make_repo(root, "svc-caller")
            owner = make_repo(root, "svc-owner")
            write_flow_index_raw(owner, [{
                "entry_ref": {"kind": "http", "signature": "POST /orders"},
                "evidence": [],
            }])
            write_flow_index_raw(caller, [{
                "entry_ref": {"kind": "cli", "signature": "checkout"},
                "evidence": [{"note": "calls POST /orders on svc-owner"}],
            }])

            for runtime in ("py", "js"):
                result = run(runtime, "discover_child_repos", "--root", str(root), "--json")
                self.assertEqual(result.returncode, 0, result.stderr)
                edges = json.loads(result.stdout)["flow_edges"]
                self.assertEqual(edges, [{
                    "repo": "svc-caller",
                    "counterpart": "svc-owner",
                    "channel_kind": "http",
                    "signature": "POST /orders",
                    "resolution": "heuristic",
                }])

    def test_mapping_row_wins_and_dedupes_against_heuristic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            caller = make_repo(root, "svc-caller")
            owner = make_repo(root, "svc-owner")
            write_flow_index_raw(owner, [{
                "entry_ref": {"kind": "http", "signature": "POST /orders"},
                "evidence": [],
            }])
            write_flow_index_raw(caller, [{
                "entry_ref": {"kind": "cli", "signature": "checkout"},
                "evidence": [{"note": "calls POST /orders on svc-owner"}],
            }])
            write_repo_identity(root, [{
                "repo_id": "svc-caller",
                "role": "producer",
                "channel": {"kind": "http", "signature": "POST /orders"},
                "counterpart_repo_id": "svc-owner",
            }])

            for runtime in ("py", "js"):
                result = run(runtime, "discover_child_repos", "--root", str(root), "--json")
                edges = json.loads(result.stdout)["flow_edges"]
                self.assertEqual(len(edges), 1, edges)
                self.assertEqual(edges[0]["resolution"], "mapping")

    def test_consumer_role_row_is_normalized_to_caller_to_callee(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_repo(root, "svc-caller")
            make_repo(root, "svc-owner")
            write_repo_identity(root, [{
                "repo_id": "svc-owner",
                "role": "consumer",
                "channel": {"kind": "queue", "signature": "orders.created"},
                "counterpart_repo_id": "svc-caller",
            }])

            for runtime in ("py", "js"):
                result = run(runtime, "discover_child_repos", "--root", str(root), "--json")
                edges = json.loads(result.stdout)["flow_edges"]
                self.assertEqual(edges, [{
                    "repo": "svc-caller",
                    "counterpart": "svc-owner",
                    "channel_kind": "queue",
                    "signature": "orders.created",
                    "resolution": "mapping",
                }])

    def test_no_signal_omits_the_edge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_repo(root, "svc-a")
            owner = make_repo(root, "svc-b")
            write_flow_index_raw(owner, [{
                "entry_ref": {"kind": "http", "signature": "POST /orders"},
                "evidence": [],
            }])
            for runtime in ("py", "js"):
                result = run(runtime, "discover_child_repos", "--root", str(root), "--json")
                self.assertEqual(json.loads(result.stdout)["flow_edges"], [])

    def test_parent_excluded_from_flow_edges(self) -> None:
        """The parent is excluded from flow-edge extraction, same as dependency edges."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_flow_index_raw(root, [{
                "entry_ref": {"kind": "http", "signature": "GET /health"},
                "evidence": [],
            }])
            caller = make_repo(root, "svc-caller")
            write_flow_index_raw(caller, [{
                "entry_ref": {"kind": "cli", "signature": "ping"},
                "evidence": [{"note": "calls GET /health on the parent"}],
            }])
            for runtime in ("py", "js"):
                result = run(runtime, "discover_child_repos", "--root", str(root), "--json")
                self.assertEqual(json.loads(result.stdout)["flow_edges"], [])


class PortfolioDiscoveryParityTests(unittest.TestCase):
    def test_py_and_js_outputs_are_structurally_identical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            diligent = make_repo(root, "svc-diligent")
            spine_only = make_repo(root, "svc-spine")
            self.assertEqual(initialize("py", diligent, "diligence").returncode, 0)
            self.assertEqual(initialize("py", spine_only, "spine").returncode, 0)
            write_flow_index_raw(diligent, [{
                "entry_ref": {"kind": "http", "signature": "POST /orders"},
                "evidence": [],
            }])
            write_flow_index_raw(spine_only, [{
                "entry_ref": {"kind": "cli", "signature": "checkout"},
                "evidence": [{"note": "calls POST /orders on svc-diligent"}],
            }])

            py_result = run("py", "discover_child_repos", "--root", str(root), "--json")
            js_result = run("js", "discover_child_repos", "--root", str(root), "--json")
            self.assertEqual(py_result.returncode, 0, py_result.stderr)
            self.assertEqual(js_result.returncode, 0, js_result.stderr)
            self.assertEqual(json.loads(py_result.stdout), json.loads(js_result.stdout))


if __name__ == "__main__":
    unittest.main()
