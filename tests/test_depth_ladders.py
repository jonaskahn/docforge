"""Focused parity tests for the depth-ladder mechanical primitives."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from _support import CLI_JS, ROOT, initialize, load_manifest, run, write_flow_index
from runtime.common.illustration_metrics import illustration_defects
from runtime.common.prov_projection import project_core


class DepthLadderTests(unittest.TestCase):
    def test_prov_core_projection_is_sorted_and_deduplicated(self) -> None:
        provenance = {
            "doc_id": "architecture", "generated_at": "2026-07-31T00:00:00Z",
            "generator": {"name": "docforge", "version": "2.7.0"},
            "sections": [{"sources": [
                {"path": "z.py", "git_blob": "b" * 40, "role": "code"},
                {"path": "a.py", "git_blob": "a" * 40, "role": "config"},
                {"path": "z.py", "git_blob": "b" * 40, "role": "code"},
            ]}],
        }
        projected = project_core(provenance)
        self.assertEqual(len(projected), 7)
        self.assertEqual(projected[3]["object"], f"source:a.py@{'a' * 40}")
        node = subprocess.run(
            ["node", "-e", "const p=require(process.argv[1]); console.log(JSON.stringify(p.projectCore(JSON.parse(process.argv[2]))));", str(CLI_JS.parent.parent / "common" / "prov_projection.js"), json.dumps(provenance)],
            text=True, capture_output=True, check=True,
        )
        self.assertEqual(projected, json.loads(node.stdout))

    def test_illustration_budget_rejects_router_visual(self) -> None:
        document = "```mermaid\nflowchart TD\nA --> B\n```\n"
        self.assertTrue(illustration_defects(document, "router"))

    def test_reconcile_applies_revise_pack_answers_with_runtime_parity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            results = {}
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                self.assertEqual(initialize(runtime, repo, "spine").returncode, 0)
                reconcile = run(runtime, "manage_manifest", "reconcile", "--repo", str(repo),
                                "--tier", "diligence", "--audience", "engineers",
                                "--audience", "security-reviewers")
                self.assertEqual(reconcile.returncode, 0, reconcile.stderr)
                self.assertIn("tier: spine -> diligence", reconcile.stdout)
                self.assertIn("added: arch_low_level", reconcile.stdout)
                self.assertIn("threat_model", reconcile.stdout)
                added = run(runtime, "manage_manifest", "add", "--repo", str(repo),
                            "--type", "adr", "--id", "my-decision",
                            "--path", "docs/architecture/decisions/001-my-decision.md")
                self.assertEqual(added.returncode, 0, added.stderr)
                again = run(runtime, "manage_manifest", "reconcile", "--repo", str(repo),
                            "--tier", "diligence", "--audience", "engineers",
                            "--audience", "security-reviewers")
                self.assertEqual(again.returncode, 0, again.stderr)
                self.assertIn("kept:", again.stdout)
                manifest = load_manifest(repo)
                ids = {doc["id"] for doc in manifest["documents"]}
                self.assertIn("arch_low_level", ids)
                self.assertIn("threat_model", ids)
                self.assertIn("my-decision", ids, "dynamic documents must survive reconcile")
                results[runtime] = (reconcile.stdout, manifest)
            py_stdout, py_manifest = results["py"]
            js_stdout, js_manifest = results["js"]
            py_stdout = py_stdout.replace(str(Path(tmp) / "py"), "<REPO>")
            js_stdout = js_stdout.replace(str(Path(tmp) / "js"), "<REPO>")
            self.assertEqual(py_stdout, js_stdout)
            for manifest in (py_manifest, js_manifest):
                manifest["generated_at"] = "<TIME>"
                manifest["metadata"]["last_updated"] = "<TIME>"
                manifest["project"]["root"] = "<REPO>"
                manifest["project"]["name"] = "<NAME>"
            self.assertEqual(py_manifest, js_manifest)

    def test_plan_tree_annotates_actions_and_flows_with_runtime_parity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.assertEqual(initialize("py", repo, "spine").returncode, 0)
            write_flow_index(repo, status="main", priority="main")
            outputs = {}
            for runtime in ("py", "js"):
                result = run(runtime, "scaffold_docs", "--repo", str(repo),
                             "--manifest", str(repo / ".docforge/manifest.json"),
                             "--dry-run", "--revise")
                self.assertEqual(result.returncode, 0, result.stderr)
                outputs[runtime] = result.stdout
                self.assertIn("action: add — planned; will be scaffolded", result.stdout)
                self.assertIn("Flows:", result.stdout)
                self.assertIn("Checkout (flow-checkout) → docs/flows/checkout.md  [add]", result.stdout)
                self.assertIn("1 main-priority flow documents", result.stdout)
            self.assertEqual(outputs["py"], outputs["js"])


if __name__ == "__main__":
    unittest.main()
