"""Focused parity tests for the depth-ladder mechanical primitives."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from _support import CLI_JS, ROOT, initialize, run, write_flow_index
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
