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
            self.assertTrue(body.startswith("# Architecture\n"), body[:40])
            self.assertNotIn("docforge_provenance:", body)
            sidecar = json.loads(
                (repo / ".docforge" / "provenance" / "docs" / "architecture.json").read_text(encoding="utf-8")
            )
            entry = sidecar["files"]["README.md"]
            self.assertEqual(entry["id"], "architecture_index")
            self.assertEqual(entry["title"], "Architecture")
            self.assertEqual(entry["provenance"]["schema"], "2.1")
            self.assertIn("## At a glance", body)
            for heading in ("## Scope and boundaries", "## Start here", "## Detailed documentation"):
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
                "version": "3.2",
                "generated_at": "2026-08-01T00:00:00+00:00",
                "project": {"name": "fixture", "root": str(repo), "tier": "spine", "provenance_storage": "markdown", "profiles": {
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


CATALOG_DOCUMENTS = ROOT / "skills" / "docforge" / "_shared" / ".metadata" / "catalog" / "documents"


def catalog_contract_revision(doc_id: str, group: str = "") -> str:
    """The catalog's own value, so a contract bump never breaks these tests.

    `contract_revision` moves independently of the catalog version -- only its
    MAJOR.MINOR.PATCH shape is validated (query_catalog `--validate`)."""
    record = CATALOG_DOCUMENTS / group / f"{doc_id}.json" if group else CATALOG_DOCUMENTS / f"{doc_id}.json"
    return json.loads(record.read_text(encoding="utf-8"))["contract_revision"]


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
                self.assertEqual(doc["contract_revision"], catalog_contract_revision("docs_index"))
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
                self.assertEqual(revision, catalog_contract_revision("docs_index"))

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
                self.assertFalse(matrix.startswith("---"), "rendered matrix must stay frontmatter-free")
                sidecar = json.loads((repo / ".docforge" / "provenance" / "docs" / "flows.json").read_text(encoding="utf-8"))
                entry_provenance = sidecar["files"]["README.md"]["provenance"]
                self.assertTrue(entry_provenance["sections"])
                sources = entry_provenance["sections"][0]["sources"]
                self.assertIn(".docforge/flow-index.json", [source["path"] for source in sources])
                self.assertTrue(sources[0]["git_blob"])
                payload = json.loads(run(runtime, "query_catalog", "--route", "flows_index").stdout)
                self.assertEqual(payload["contract_revision"], "2.19.0")


class AgentContextRoutingTests(unittest.TestCase):
    """The reference boundary is one-way: agent-context documents may link
    human-facing documents, and no human-facing index enumerates an
    agent-context child. See references/document-composition.md."""

    def _scaffold(self, runtime: str, repo: Path, doc_id: str) -> str:
        result = run(
            runtime, "scaffold_docs",
            "--repo", str(repo),
            "--manifest", str(repo / ".docforge" / "manifest.json"),
            "--document", doc_id,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        doc = next(item for item in load_manifest(repo)["documents"] if item["id"] == doc_id)
        return (repo / doc["path"]).read_text(encoding="utf-8")

    def test_docs_index_never_enumerates_agent_children_in_either_layout(self) -> None:
        for runtime in ("py", "js"):
            for layout, forbidden in (("standard", "agents/README.md"), ("compact", "agents.md")):
                with self.subTest(runtime=runtime, layout=layout), tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    result = initialize(
                        runtime, repo, "spine",
                        audiences=("coding-agents",), layout=layout,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    paths = {doc["path"] for doc in load_manifest(repo)["documents"]}
                    self.assertIn("AGENTS.md", paths, "fixture must actually select agent docs")
                    body = self._scaffold(runtime, repo, "docs_index")
                    self.assertNotIn(forbidden, body)
                    self.assertNotIn("docs/agents", body)

    def test_agent_index_still_enumerates_its_own_children(self) -> None:
        """The filter is relative to the referencing document, not global --
        docs/agents/README.md must keep routing the views beneath it."""
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                result = initialize(
                    runtime, repo, "spine",
                    audiences=("coding-agents",), layout="standard",
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                body = self._scaffold(runtime, repo, "agents_index")
                self.assertIn("](architecture.md)", body)
                self.assertIn("](patterns.md)", body)

    def _materialize(self, runtime: str, repo: Path) -> None:
        for doc in load_manifest(repo)["documents"]:
            run(
                runtime, "scaffold_docs",
                "--repo", str(repo),
                "--manifest", str(repo / ".docforge" / "manifest.json"),
                "--document", doc["id"],
            )

    def _leaks(self, runtime: str, repo: Path) -> list[str]:
        audit = run(
            runtime, "scaffold_docs",
            "--repo", str(repo),
            "--manifest", str(repo / ".docforge" / "manifest.json"),
            "--audit",
        )
        combined = audit.stdout + audit.stderr
        found, collecting = [], False
        for line in combined.splitlines():
            if line.startswith("AGENT-CONTEXT LEAK"):
                collecting = True
                continue
            if collecting:
                if not line.startswith("  "):
                    break
                found.append(line.strip())
        return found

    def test_scaffolded_tree_is_free_of_agent_context_leaks(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                initialize(runtime, repo, "spine", audiences=("coding-agents",), layout="standard")
                self._materialize(runtime, repo)
                self.assertEqual(self._leaks(runtime, repo), [])

    def test_human_document_referencing_agent_context_is_a_finding(self) -> None:
        """Links, `@`-refs, and bare mentions all count; the same strings inside
        a fence do not, because a quoted filename is not a reference."""
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                initialize(runtime, repo, "spine", audiences=("coding-agents",), layout="standard")
                self._materialize(runtime, repo)
                index = repo / "docs" / "README.md"
                index.write_text(
                    index.read_text(encoding="utf-8")
                    + "\nSee [views](agents/README.md), then @AGENTS.md.\n"
                    + "\n```sh\ncat AGENTS.md\n```\n",
                    encoding="utf-8",
                )
                leaks = self._leaks(runtime, repo)
                self.assertTrue(any("AGENTS.md" in item for item in leaks), leaks)
                self.assertTrue(any("docs/agents/README.md" in item for item in leaks), leaks)
                # The fenced `cat AGENTS.md` sits on its own line; every finding
                # must point at the prose line instead.
                fenced_line = next(
                    number
                    for number, line in enumerate(index.read_text(encoding="utf-8").splitlines(), 1)
                    if line.strip() == "cat AGENTS.md"
                )
                self.assertFalse([item for item in leaks if f":{fenced_line} " in item], leaks)

    def test_agent_documents_may_reference_human_documents_freely(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                initialize(runtime, repo, "spine", audiences=("coding-agents",), layout="standard")
                self._materialize(runtime, repo)
                view = repo / "docs" / "agents" / "architecture.md"
                view.write_text(
                    view.read_text(encoding="utf-8")
                    + "\nSee [high level](../architecture/high-level.md) and @AGENTS.md.\n",
                    encoding="utf-8",
                )
                self.assertEqual(self._leaks(runtime, repo), [])

    def test_repository_without_the_agent_audience_can_never_leak(self) -> None:
        """Targets come from the manifest, so a repo that owns `agents/` or
        `.claude/settings.json` itself is untouchable by this rule."""
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                initialize(runtime, repo, "spine", layout="standard")
                self._materialize(runtime, repo)
                index = repo / "docs" / "README.md"
                index.write_text(
                    index.read_text(encoding="utf-8")
                    + "\nOur `src/agents/` package and `.claude/settings.json` are hand-written.\n",
                    encoding="utf-8",
                )
                self.assertEqual(self._leaks(runtime, repo), [])

    def test_whole_tree_gate_never_demands_an_agent_row_in_a_human_index(self) -> None:
        """readme_child_coverage and child_rows read the same filtered list, so
        the auto-generated table can never disagree with the audit that checks
        it."""
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                result = initialize(
                    runtime, repo, "spine",
                    audiences=("coding-agents",), layout="standard",
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                run(
                    runtime, "scaffold_docs",
                    "--repo", str(repo),
                    "--manifest", str(repo / ".docforge" / "manifest.json"),
                )
                audit = run(
                    runtime, "scaffold_docs",
                    "--repo", str(repo),
                    "--manifest", str(repo / ".docforge" / "manifest.json"),
                    "--audit",
                )
                combined = audit.stdout + audit.stderr
                for line in combined.splitlines():
                    if "readme child coverage" in line or "docs/README.md" in line:
                        self.assertNotIn("agents", line, combined)


if __name__ == "__main__":
    unittest.main()
