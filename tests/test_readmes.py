"""Rich section READMEs: scaffold structure, empty states, contract-revision
drift on reconcile, flow-index provenance, and Python/Node parity."""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from _support import (
    ROOT,
    blob_hash,
    initialize,
    load_manifest,
    markdown_with_provenance,
    normalized,
    provenance,
    run,
    write_flow_index,
)


class ReadmeScaffoldTests(unittest.TestCase):
    def _scaffold(self, runtime: str, repo: Path, doc_id: str) -> str:
        result = run(
            runtime, "scaffold_docs",
            "--repo", str(repo),
            "--manifest", str(repo / ".docforge" / "manifest.json"),
            "--document", doc_id,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        doc = next(
            item for item in load_manifest(repo)["documents"] if item["id"] == doc_id
        )
        return (repo / doc["path"]).read_text(encoding="utf-8")

    def test_section_readme_uses_rich_template_with_title_and_managed_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            result = initialize("py", repo, "spine")
            self.assertEqual(result.returncode, 0, result.stderr)
            body = self._scaffold("py", repo, "architecture_index")
            self.assertTrue(body.startswith("---\nid: "), body[:40])
            self.assertIn("docforge_provenance:", body)
            self.assertIn("# Architecture\n", body)
            for heading in ("## At a glance", "## Scope and boundaries", "## Start here", "## Detailed documentation"):
                self.assertIn(heading, body)
            self.assertIn("](high-level.md)", body)
            self.assertIn("docforge-children:start", body)
            self.assertNotIn("{{TITLE}}", body)

    def test_empty_collection_readme_has_honest_empty_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            result = initialize("py", repo, "portfolio")
            self.assertEqual(result.returncode, 0, result.stderr)
            body = self._scaffold("py", repo, "decisions_index")
            self.assertIn("No documents are selected in this section yet", body)
            self.assertNotIn("{{NNNN}}", body)

    def test_docs_index_scaffold_routes_to_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            result = initialize("py", repo, "portfolio")
            self.assertEqual(result.returncode, 0, result.stderr)
            body = self._scaffold("py", repo, "docs_index")
            self.assertIn("# Documentation\n", body)
            self.assertIn("## Start here", body)
            self.assertIn("## Sections", body)
            self.assertIn("](architecture/README.md)", body)
            self.assertIn("](reference/README.md)", body)

    def test_ba_and_po_readmes_scaffold_audience_documents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            result = initialize(
                "py", repo, "diligence",
                audiences=("business-analysts", "product-owners"),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            ba = self._scaffold("py", repo, "ba_index")
            self.assertIn("# Business Analyst documentation\n", ba)
            self.assertIn("](business-rules.md)", ba)
            self.assertIn("](process-flows.md)", ba)
            po = self._scaffold("py", repo, "po_index")
            self.assertIn("# Product Owner documentation\n", po)
            self.assertIn("](feature-catalog.md)", po)

    def test_epics_index_is_selected_at_portfolio_tier(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            result = initialize("py", repo, "portfolio")
            self.assertEqual(result.returncode, 0, result.stderr)
            paths = {doc["path"] for doc in load_manifest(repo)["documents"]}
            self.assertIn("docs-portfolio/epics/README.md", paths)
            body = self._scaffold("py", repo, "epics_index")
            self.assertIn("# Epics\n", body)

    def test_scaffold_readmes_are_byte_equivalent_across_runtimes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            results = {}
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                initialize(
                    runtime, repo, "portfolio",
                    audiences=("business-analysts", "product-owners"),
                )
                bodies = {
                    doc_id: self._scaffold(runtime, repo, doc_id)
                    for doc_id in ("docs_index", "architecture_index", "ba_index", "po_index")
                }
                results[runtime] = {
                    doc_id: normalized(body, [repo])
                    for doc_id, body in bodies.items()
                }
            self.assertEqual(results["py"], results["js"])

    def test_readme_child_coverage_is_an_audit_defect(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "source.txt"
            source.write_text("arch\n", encoding="utf-8")
            readme = repo / "docs" / "architecture" / "README.md"
            readme.parent.mkdir(parents=True)
            readme.write_text(
                markdown_with_provenance(
                    provenance(
                        doc_id="architecture_index", path="docs/architecture/README.md",
                        tier="spine", target_depth="orientation",
                        section_id="architecture", source_path="source.txt",
                        source_blob=blob_hash(source.read_bytes()),
                    ),
                    "# Architecture\n\n## At a glance\n\nOverview without the child link.\n",
                ),
                encoding="utf-8",
            )
            doc = {
                "id": "architecture_index", "type": "folder-index",
                "path": "docs/architecture/README.md", "group": "architecture",
                "selection": {"origins": [], "evidence": []},
                "status": "complete", "requires": [],
                "scaffold_template": "section-readme.template.md",
                "instruction_file": None, "target_depth": "orientation",
                "write_order": 9, "provenance_mode": "sections",
                "audit_profile": "router",
                "provenance": {"sections": []}, "audit": None,
            }
            child = {
                "id": "arch_high_level", "type": "arch-high-level",
                "path": "docs/architecture/high-level.md", "group": "architecture",
                "selection": {"origins": [], "evidence": []},
                "status": "complete", "requires": ["code_graph"],
                "scaffold_template": "architecture-high-level.md",
                "instruction_file": None, "target_depth": "deep-dive",
                "write_order": 10, "provenance_mode": "sections",
                "audit_profile": "architecture",
                "provenance": {"sections": []}, "audit": None,
            }
            (repo / "docs" / "architecture" / "high-level.md").write_text(
                "# Architecture high level\n\nContent.\n", encoding="utf-8",
            )
            manifest = {
                "version": "3.1",
                "generated_at": "2026-08-01T00:00:00+00:00",
                "project": {"name": "fixture", "root": str(repo), "tier": "spine", "profiles": {
                    "shapes": [], "platforms": [], "frameworks": [],
                    "concerns": [], "audiences": [],
                }},
                "discovery": [],
                "documents": [doc, child], "metadata": {},
            }
            manifest_path = repo / ".docforge" / "manifest.json"
            manifest_path.parent.mkdir()
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            for runtime in ("py", "js"):
                result = run(runtime, "scaffold_docs", "--repo", str(repo),
                             "--manifest", str(manifest_path), "--audit")
                self.assertEqual(result.returncode, 1)
                self.assertIn("README CHILD COVERAGE", result.stdout)
                self.assertIn("missing link to docs/architecture/high-level.md", result.stdout)


class ReadmeContractRevisionTests(unittest.TestCase):
    def test_reconcile_demotes_drifted_readme_even_when_fresh(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                result = initialize(runtime, repo, "spine")
                self.assertEqual(result.returncode, 0, result.stderr)
                manifest = load_manifest(repo)
                doc = next(item for item in manifest["documents"] if item["id"] == "docs_index")
                doc["status"] = "complete"
                doc["contract_revision"] = "1.0.0"
                doc["audit"] = {"mode": "cold-pass", "verdict": "PASS", "timestamp": "x", "report_path": ".docforge/audits/docs_index.md"}
                manifest_path = repo / ".docforge" / "manifest.json"
                manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

                result = run(runtime, "manage_manifest", "reconcile", "--repo", str(repo))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("contract-updated: docs_index", result.stdout)
                after = load_manifest(repo)
                doc = next(item for item in after["documents"] if item["id"] == "docs_index")
                self.assertEqual(doc["status"], "in_progress")
                self.assertIsNone(doc["audit"])
                self.assertEqual(doc["contract_revision"], "2.10.0")
                self.assertTrue(doc["scaffold_template"].startswith("content/"))

    def test_reconcile_is_idempotent_once_revision_current(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            initialize("py", repo, "spine")
            for runtime in ("py", "js"):
                result = run(runtime, "manage_manifest", "reconcile", "--repo", str(repo))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("contract-updated", result.stdout)
            manifest = load_manifest(repo)
            doc = next(item for item in manifest["documents"] if item["id"] == "docs_index")
            self.assertEqual(doc["status"], "planned")

    def test_route_exposes_contract_revision_across_runtimes(self) -> None:
        for doc_id in ("docs_index", "flow", "arch_high_level"):
            py_out = run("py", "query_catalog", "--route", doc_id).stdout
            js_out = run("js", "query_catalog", "--route", doc_id).stdout
            self.assertEqual(py_out, js_out, doc_id)
            payload = json.loads(py_out)
            self.assertIn("contract_revision", payload)
            revision = payload["contract_revision"]
            if revision is not None:
                self.assertRegex(revision, r"^\d+\.\d+\.\d+$")
            if doc_id == "docs_index":
                self.assertEqual(revision, "2.10.0")

    def test_legacy_modes_do_not_leak_contract_revision(self) -> None:
        for runtime in ("py", "js"):
            result = run(runtime, "query_catalog", "--id", "docs_index")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("contract_revision", json.loads(result.stdout))


class ReadmeFlowIndexTests(unittest.TestCase):
    def test_flow_index_render_has_rich_intro_and_non_empty_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                write_flow_index(repo)
                result = run(runtime, "flow_index", "render", "--repo", str(repo))
                self.assertEqual(result.returncode, 0, result.stderr)
                matrix = (repo / "docs" / "flows" / "README.md").read_text(encoding="utf-8")
                self.assertIn("## How to read this index", matrix)
                self.assertIn("| Role |", matrix)
                frontmatter = matrix.split("---", 2)[1]
                self.assertIn("sections:", frontmatter)
                self.assertIn(".docforge/flow-index.json", frontmatter)
                self.assertIn("git_blob:", frontmatter)
                payload = json.loads(run(runtime, "query_catalog", "--route", "flows_index").stdout)
                self.assertEqual(payload["contract_revision"], "2.10.0")


if __name__ == "__main__":
    unittest.main()
