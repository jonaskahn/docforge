"""Declared illustration coverage: the `missing-illustration` mechanical
defect in `scaffold_docs --audit`, with Python/Node parity."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _support import blob_hash, load_manifest, provenance, run, write_written_doc


def _repo_manifest(repo: Path) -> tuple[dict, dict]:
    """A hand-built manifest with two planned architecture documents and one
    agent-context document, sidecar-ready provenance, and no scaffolding.

    Returns `(manifest, source)` where `source` is a real file the stamped
    provenance cites."""
    source = repo / "source.txt"
    source.write_text("arch\n", encoding="utf-8")

    def doc(doc_id: str, path: str, group: str, depth: str, order: int, dominant_form: str | None) -> dict:
        return {
            "id": doc_id,
            "type": "arch-high-level",
            "path": path,
            "group": group,
            "selection": {"origins": [], "evidence": []},
            "status": "complete",
            "requires": [],
            "scaffold_template": "architecture-high-level.md",
            "instruction_file": None,
            "target_depth": depth,
            "write_order": order,
            "provenance_mode": "sections",
            "audit_profile": "architecture",
            "dominant_form": dominant_form,
            "provenance": provenance(
                doc_id=doc_id,
                path=path,
                tier="spine",
                target_depth=depth,
                section_id="coverage",
                source_path="source.txt",
                source_blob=blob_hash(source.read_bytes()),
            ),
            "audit": None,
        }

    documents = [
        doc("arch_high_level", "docs/architecture/high-level.md", "architecture", "deep-dive", 10, "flowchart"),
        doc("agents_test", "docs/agents/test.md", "agent-context", "deep-dive", 40, "flowchart"),
    ]
    manifest = {
        "version": "3.10",
        "generated_at": "2026-08-01T00:00:00+00:00",
        "project": {
            "name": "fixture",
            "root": str(repo),
            "tier": "spine",
            "provenance_storage": "json",
            "profiles": {"shapes": [], "platforms": [], "frameworks": [], "concerns": [], "audiences": []},
        },
        "discovery": [],
        "documents": documents,
        "metadata": {},
    }
    manifest_path = repo / ".docforge" / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    for entry in documents:
        write_written_doc(repo, entry, "# Coverage\n\nGrounded body text.\n")
    return manifest, source


class MissingIllustrationTests(unittest.TestCase):
    def test_diagram_form_without_fence_is_a_defect_with_parity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _manifest, _source = _repo_manifest(repo)
            outputs = [
                run(runtime, "scaffold_docs", "--repo", str(repo),
                    "--manifest", str(repo / ".docforge" / "manifest.json"), "--audit")
                for runtime in ("py", "js")
            ]
            for result in outputs:
                self.assertEqual(result.returncode, 1)
                self.assertIn("MISSING ILLUSTRATION", result.stdout)
                self.assertIn("docs/architecture/high-level.md: declared dominant_form flowchart", result.stdout)
                self.assertNotIn("docs/agents/test.md", result.stdout)
            self.assertEqual(outputs[0].stdout, outputs[1].stdout)

    def test_diagram_form_with_mermaid_fence_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            manifest, _source = _repo_manifest(repo)
            doc = next(item for item in manifest["documents"] if item["id"] == "arch_high_level")
            write_written_doc(repo, doc, "# Coverage\n\nGrounded body text.\n\n```mermaid\nflowchart LR\n  A --> B\n```\n")
            for runtime in ("py", "js"):
                result = run(runtime, "scaffold_docs", "--repo", str(repo),
                              "--manifest", str(repo / ".docforge" / "manifest.json"), "--audit")
                self.assertEqual(result.returncode, 0, result.stdout)

    def test_diagram_form_with_structural_text_fence_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            manifest, _source = _repo_manifest(repo)
            doc = next(item for item in manifest["documents"] if item["id"] == "arch_high_level")
            write_written_doc(repo, doc, "# Coverage\n\nGrounded body text.\n\n```text\nrepo/\n├── src/      implementation\n└── tests/    suites\n```\n")
            for runtime in ("py", "js"):
                result = run(runtime, "scaffold_docs", "--repo", str(repo),
                              "--manifest", str(repo / ".docforge" / "manifest.json"), "--audit")
                self.assertEqual(result.returncode, 0, result.stdout)

    def test_table_form_and_null_form_never_require_a_fence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            manifest, _source = _repo_manifest(repo)
            doc = next(item for item in manifest["documents"] if item["id"] == "arch_high_level")
            for form in ("table", None):
                doc["dominant_form"] = form
                manifest_path = repo / ".docforge" / "manifest.json"
                manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
                for runtime in ("py", "js"):
                    result = run(runtime, "scaffold_docs", "--repo", str(repo),
                                  "--manifest", str(manifest_path), "--audit")
                    self.assertEqual(result.returncode, 0, result.stdout)

    def test_planned_document_without_fence_is_not_a_defect(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            manifest, _source = _repo_manifest(repo)
            doc = next(item for item in manifest["documents"] if item["id"] == "arch_high_level")
            doc["status"] = "planned"
            (repo / ".docforge" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            for runtime in ("py", "js"):
                result = run(runtime, "scaffold_docs", "--repo", str(repo),
                              "--manifest", str(repo / ".docforge" / "manifest.json"), "--audit")
                self.assertEqual(result.returncode, 0, result.stdout)


class DominantFormSeedingTests(unittest.TestCase):
    def test_manifest_documents_carry_declared_form_and_routes_expose_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            result = run("py", "manage_manifest", "init", "--repo", str(repo), "--tier", "spine", "--layout", "standard")
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = load_manifest(repo)
            self.assertIn("dominant_form", manifest["documents"][0])
            by_id = {doc["id"]: doc for doc in manifest["documents"]}
            self.assertEqual(by_id["arch_high_level"]["dominant_form"], "flowchart")
            self.assertEqual(by_id["root_readme"]["dominant_form"], None)
            route = run("py", "query_catalog", "--route", "arch_high_level")
            self.assertEqual(route.returncode, 0, route.stderr)
            self.assertEqual(json.loads(route.stdout)["dominant_form"], "flowchart")
            route_js = run("js", "query_catalog", "--route", "arch_high_level")
            self.assertEqual(json.loads(route_js.stdout)["dominant_form"], "flowchart")

    def test_reconcile_keeps_declared_form_synced_and_demotes_on_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            result = run("py", "manage_manifest", "init", "--repo", str(repo), "--tier", "spine", "--layout", "standard")
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest_path = repo / ".docforge" / "manifest.json"
            manifest = load_manifest(repo)
            doc = next(item for item in manifest["documents"] if item["id"] == "arch_high_level")
            doc["dominant_form"] = "table"
            doc["status"] = "complete"
            doc["audit"] = {"mode": "cold-pass", "verdict": "PASS", "timestamp": "x", "report_path": ".docforge/audits/arch.md"}
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            result = run("py", "manage_manifest", "reconcile", "--repo", str(repo), "--tier", "spine")
            self.assertEqual(result.returncode, 0, result.stderr)
            after = load_manifest(repo)
            doc = next(item for item in after["documents"] if item["id"] == "arch_high_level")
            self.assertEqual(doc["dominant_form"], "flowchart")
            self.assertEqual(doc["status"], "in_progress")
            self.assertIsNone(doc["audit"])


if __name__ == "__main__":
    unittest.main()
