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
    write_written_doc,
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

    def test_children_block_keeps_its_table_header_at_template_width(self) -> None:
        """The header and separator live inside the managed markers.

        Regenerating the block used to emit data rows only, so every generated
        section README rendered as literal pipe text instead of a table. Each
        template also sets its own width -- the decision log is five columns --
        and a narrower row breaks the table just as badly as a missing header.
        """
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                result = initialize(runtime, repo, "diligence")
                self.assertEqual(result.returncode, 0, result.stderr)

                body = self._scaffold(runtime, repo, "architecture_index")
                block = body.split("docforge-children:start -->")[1].split("<!-- docforge-children:end")[0]
                lines = [line for line in block.splitlines() if line.strip()]
                self.assertEqual(lines[0].strip(), "| Document | Answers |")
                self.assertEqual(lines[1].strip(), "|---|---|")
                self.assertIn("| [Arch High Level](high-level.md) |", block)
                for line in lines:
                    self.assertEqual(line.count("|"), 3, line)

                # The decision log is five columns wide, and it only exists
                # once a record does.
                added = run(
                    runtime, "manage_manifest", "add", "--repo", str(repo),
                    "--type", "adr", "--id", "adr_0001",
                    "--path", "docs/architecture/decisions/0001-use-postgres.md",
                )
                self.assertEqual(added.returncode, 0, added.stderr)
                decisions = self._scaffold(runtime, repo, "decisions_index")
                block = decisions.split("docforge-children:start -->")[1].split("<!-- docforge-children:end")[0]
                lines = [line for line in block.splitlines() if line.strip()]
                self.assertEqual(lines[0].strip(), "| # | Title | Status | Date | Topic |")
                self.assertEqual(lines[1].strip(), "|---|---|---|---|---|")
                for line in lines:
                    self.assertEqual(line.count("|"), 6, line)

    def test_dynamic_only_index_is_absent_until_a_child_is_seeded(self) -> None:
        """A static index over dynamic-only children is not created empty.

        Tier alone used to select it, so every Diligence run materialized
        `decisions/`, `concepts/`, and `runbooks/` folders holding nothing but
        an index explaining its own emptiness -- the child types are gated on
        `discovered_*` conditions no code evaluates. Seeding the first child
        brings the index back as an ancestor.
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            result = initialize("py", repo, "portfolio")
            self.assertEqual(result.returncode, 0, result.stderr)
            paths = {doc["path"] for doc in load_manifest(repo)["documents"]}
            for absent in (
                "docs/architecture/decisions/README.md",
                "docs/architecture/concepts/README.md",
                "docs/operations/runbooks/README.md",
            ):
                self.assertNotIn(absent, paths)

            added = run(
                "py", "manage_manifest", "add", "--repo", str(repo),
                "--type", "adr", "--id", "adr_0001",
                "--path", "docs/architecture/decisions/0001-use-postgres.md",
            )
            self.assertEqual(added.returncode, 0, added.stderr)
            paths = {doc["path"] for doc in load_manifest(repo)["documents"]}
            self.assertIn("docs/architecture/decisions/README.md", paths)

    def test_empty_collection_readme_has_honest_empty_state(self) -> None:
        """An index that legitimately has no child still says so honestly.

        Reached through a manifest that already carries such an index -- the
        state every pre-fix run left behind -- since selection no longer
        creates one.
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            result = initialize("py", repo, "portfolio")
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = load_manifest(repo)
            sibling = next(
                doc for doc in manifest["documents"]
                if doc["id"] == "architecture_index"
            )
            manifest["documents"].append({
                **sibling,
                "id": "decisions_index",
                "type": "decision-index",
                "path": "docs/architecture/decisions/README.md",
                "scaffold_template": "content/records/decision-index.template.md",
            })
            (repo / ".docforge" / "manifest.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
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

    def test_epics_index_appears_at_portfolio_tier_once_an_epic_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            result = initialize("py", repo, "portfolio")
            self.assertEqual(result.returncode, 0, result.stderr)
            paths = {doc["path"] for doc in load_manifest(repo)["documents"]}
            self.assertNotIn("docs-portfolio/epics/README.md", paths)

            added = run(
                "py", "manage_manifest", "add", "--repo", str(repo),
                "--type", "epic", "--id", "epic_checkout",
                "--path", "docs-portfolio/epics/checkout.md",
            )
            self.assertEqual(added.returncode, 0, added.stderr)
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
                self.assertEqual(payload["contract_revision"], "2.23.0")


class AgentContextIsolationTests(unittest.TestCase):
    """Human and agent outputs are isolated: human indexes and documents never
    reference active agent outputs, while agent outputs are self-contained."""

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
        bodies = {}
        for runtime in ("py", "js"):
            for layout in ("standard", "compact"):
                with self.subTest(runtime=runtime, layout=layout), tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    result = initialize(
                        runtime, repo, "spine",
                        audiences=("coding-agents",), layout=layout,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    manifest = load_manifest(repo)
                    paths = {doc["path"] for doc in manifest["documents"]}
                    self.assertIn("AGENTS.md", paths, "fixture must actually select agent docs")
                    body = self._scaffold(runtime, repo, "docs_index")
                    agent_doc_links = {
                        doc["path"].removeprefix("docs/")
                        for doc in manifest["documents"]
                        if doc.get("group") == "agent-context"
                        and doc["path"].startswith("docs/")
                    }
                    for link in agent_doc_links:
                        self.assertNotIn(f"]({link})", body)
                    self.assertNotIn("docs/agents", body)
                    bodies[(runtime, layout)] = normalized(body, [repo])
        for layout in ("standard", "compact"):
            self.assertEqual(bodies[("py", layout)], bodies[("js", layout)], layout)

    def test_agents_index_is_not_selected_or_scaffoldable(self) -> None:
        observed = {}
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                result = initialize(
                    runtime, repo, "spine",
                    audiences=("coding-agents",), layout="standard",
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                manifest = load_manifest(repo)
                ids = {doc["id"] for doc in manifest["documents"]}
                paths = {doc["path"] for doc in manifest["documents"]}
                self.assertNotIn("agents_index", ids)
                self.assertNotIn("docs/agents/README.md", paths)

                topic = run(
                    runtime, "scaffold_docs",
                    "--repo", str(repo),
                    "--manifest", str(repo / ".docforge" / "manifest.json"),
                    "--document", "agents_architecture",
                )
                self.assertEqual(topic.returncode, 0, topic.stderr)
                self.assertFalse((repo / "docs" / "agents" / "README.md").exists())

                missing = run(
                    runtime, "scaffold_docs",
                    "--repo", str(repo),
                    "--manifest", str(repo / ".docforge" / "manifest.json"),
                    "--document", "agents_index",
                )
                combined = missing.stdout + missing.stderr
                self.assertEqual(missing.returncode, 2, combined)
                self.assertIn("document id not found or skipped: agents_index", combined)
                observed[runtime] = {
                    "agent_ids": sorted(
                        doc["id"] for doc in manifest["documents"]
                        if doc.get("group") == "agent-context"
                    ),
                    "returncode": missing.returncode,
                    "not_found": "document id not found or skipped: agents_index" in combined,
                }
        self.assertEqual(observed["py"], observed["js"])

    def _materialize(self, runtime: str, repo: Path) -> None:
        for doc in load_manifest(repo)["documents"]:
            result = run(
                runtime, "scaffold_docs",
                "--repo", str(repo),
                "--manifest", str(repo / ".docforge" / "manifest.json"),
                "--document", doc["id"],
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def _findings(self, runtime: str, repo: Path, label: str) -> list[str]:
        audit = run(
            runtime, "scaffold_docs",
            "--repo", str(repo),
            "--manifest", str(repo / ".docforge" / "manifest.json"),
            "--audit",
        )
        combined = audit.stdout + audit.stderr
        found, collecting = [], False
        heading = label.upper()
        for line in combined.splitlines():
            if line.startswith(f"{heading} ("):
                collecting = True
                continue
            if collecting:
                if not line.startswith("  "):
                    break
                found.append(line.strip())
        return found

    def _leaks(self, runtime: str, repo: Path) -> list[str]:
        return self._findings(runtime, repo, "agent-context leak")

    def _outbound(self, runtime: str, repo: Path) -> list[str]:
        return self._findings(runtime, repo, "agent-context outbound")

    def test_scaffolded_tree_is_free_of_agent_context_boundary_findings(self) -> None:
        observed = {}
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                initialize(runtime, repo, "spine", audiences=("coding-agents",), layout="standard")
                self._materialize(runtime, repo)
                observed[runtime] = {
                    "leaks": self._leaks(runtime, repo),
                    "outbound": self._outbound(runtime, repo),
                }
                self.assertEqual(observed[runtime], {"leaks": [], "outbound": []})
        self.assertEqual(observed["py"], observed["js"])

    def test_human_document_referencing_agent_context_is_a_finding(self) -> None:
        """Links, imports, and bare mentions count even in fences and comments."""
        observed = {}
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                initialize(runtime, repo, "spine", audiences=("coding-agents",), layout="standard")
                self._materialize(runtime, repo)
                index = repo / "docs" / "README.md"
                index.write_text(
                    index.read_text(encoding="utf-8")
                    + "\nSee [architecture](agents/architecture.md), then @AGENTS.md\n"
                    + "\n```sh\ncat AGENTS.md\n```\n"
                    + "<!-- docs/agents/testing.md -->\n",
                    encoding="utf-8",
                )
                leaks = self._leaks(runtime, repo)
                details = {re.sub(r"^[^:]+:\d+ ", "", item) for item in leaks}
                self.assertEqual(
                    details,
                    {
                        "[markdown-link] -> docs/agents/architecture.md",
                        "[at-import] -> AGENTS.md",
                        "[agent-output-path] -> AGENTS.md",
                        "[agent-output-path] -> docs/agents/testing.md",
                    },
                )
                fenced_line = next(
                    number
                    for number, line in enumerate(index.read_text(encoding="utf-8").splitlines(), 1)
                    if line.strip() == "cat AGENTS.md"
                )
                self.assertTrue(
                    any(
                        f":{fenced_line} [agent-output-path] -> AGENTS.md" in item
                        for item in leaks
                    ),
                    leaks,
                )
                observed[runtime] = leaks
        self.assertEqual(observed["py"], observed["js"])

    def test_agent_document_outbound_references_are_findings(self) -> None:
        expected = {
            "[markdown-link] -> ../architecture/high-level.md",
            "[agent-output-path] -> docs/agents/testing.md",
            "[raw-url] -> https://example.com/guide",
            "[at-import] -> docs/product/overview.md",
            "[managed-document-path] -> docs/architecture/high-level.md",
            "[managed-document-path] -> docs/product/overview.md",
        }
        observed = {}
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                initialize(runtime, repo, "spine", audiences=("coding-agents",), layout="standard")
                self._materialize(runtime, repo)
                view = repo / "docs" / "agents" / "architecture.md"
                view.write_text(
                    view.read_text(encoding="utf-8")
                    + "\n[Human architecture](../architecture/high-level.md)\n"
                    + "Peer output: docs/agents/testing.md\n"
                    + "External reference: https://example.com/guide\n"
                    + "@../product/overview.md\n"
                    + "```text\n"
                    + "docs/architecture/high-level.md\n"
                    + "```\n"
                    + "<!-- docs/product/overview.md -->\n",
                    encoding="utf-8",
                )
                outbound = self._outbound(runtime, repo)
                details = {re.sub(r"^[^:]+:\d+ ", "", item) for item in outbound}
                self.assertEqual(details, expected)
                self.assertEqual(len(outbound), len(expected))
                observed[runtime] = outbound
        self.assertEqual(observed["py"], observed["js"])

    def test_agent_source_config_paths_and_commands_are_not_outbound_findings(self) -> None:
        observed = {}
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                initialize(runtime, repo, "spine", audiences=("coding-agents",), layout="standard")
                self._materialize(runtime, repo)
                view = repo / "docs" / "agents" / "architecture.md"
                view.write_text(
                    view.read_text(encoding="utf-8")
                    + "\nSources: src/runtime/parser.py, config/docforge.yaml, pyproject.toml.\n"
                    + "```sh\n"
                    + "python3 -m unittest tests.test_parser\n"
                    + "node scripts/check.js --config config/docforge.json\n"
                    + "```\n"
                    + "<!-- source config: config/strict.yaml -->\n",
                    encoding="utf-8",
                )
                observed[runtime] = self._outbound(runtime, repo)
                self.assertEqual(observed[runtime], [])
        self.assertEqual(observed["py"], observed["js"])

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

    def test_standard_agent_folder_is_routerless_and_readme_reachability_exempt(self) -> None:
        """Standard topic files intentionally have no README router above them,
        so ordinary README child coverage must not report them as unreachable."""
        observed = {}
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                result = initialize(
                    runtime, repo, "spine",
                    audiences=("coding-agents",), layout="standard",
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self._materialize(runtime, repo)
                manifest = load_manifest(repo)
                topic_paths = {
                    doc["path"] for doc in manifest["documents"]
                    if doc.get("group") == "agent-context"
                    and doc["path"].startswith("docs/agents/")
                }
                self.assertTrue(topic_paths)
                self.assertTrue(all((repo / path).is_file() for path in topic_paths))
                self.assertFalse((repo / "docs" / "agents" / "README.md").exists())
                coverage = self._findings(runtime, repo, "readme child coverage")
                agent_findings = [item for item in coverage if "docs/agents" in item]
                self.assertEqual(agent_findings, [], coverage)
                observed[runtime] = agent_findings
        self.assertEqual(observed["py"], observed["js"])


class SectionCohesionTests(unittest.TestCase):
    def _fixture(self, repo: Path, *bodies: str) -> Path:
        """Two written sibling architecture documents with the given bodies
        (prose, no provenance requirements beyond the minimum) and a hand-built
        3.10 manifest."""
        source = repo / "source.txt"
        source.write_text("arch\n", encoding="utf-8")

        def doc(doc_id: str, path: str, order: int) -> dict:
            return {
                "id": doc_id, "type": "arch-high-level", "path": path,
                "group": "architecture",
                "selection": {"origins": [], "evidence": []},
                "status": "complete", "requires": [],
                "scaffold_template": "architecture-high-level.md",
                "instruction_file": None, "target_depth": "deep-dive",
                "write_order": order, "provenance_mode": "sections",
                "audit_profile": "architecture", "dominant_form": None,
                "provenance": provenance(
                    doc_id=doc_id, path=path, tier="spine",
                    target_depth="deep-dive", section_id="coverage",
                    source_path="source.txt",
                    source_blob=blob_hash(source.read_bytes()),
                ),
                "audit": None,
            }

        documents = [
            doc("arch_high_level", "docs/architecture/high-level.md", 10),
            doc("arch_low_level", "docs/architecture/low-level.md", 11),
        ]
        for entry, body in zip(documents, bodies):
            write_written_doc(repo, entry, body)
        manifest = {
            "version": "3.10",
            "generated_at": "2026-08-01T00:00:00+00:00",
            "project": {
                "name": "fixture", "root": str(repo), "tier": "spine",
                "provenance_storage": "json",
                "profiles": {"shapes": [], "platforms": [], "frameworks": [],
                             "concerns": [], "audiences": []},
            },
            "discovery": [], "documents": documents, "metadata": {},
        }
        manifest_path = repo / ".docforge" / "manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        return manifest_path

    def _audit(self, runtime: str, repo: Path, manifest_path: Path):
        return run(runtime, "scaffold_docs", "--repo", str(repo),
                   "--manifest", str(manifest_path), "--audit")

    def test_island_documents_are_an_audit_defect_with_parity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            manifest_path = self._fixture(
                repo,
                "# Coverage\n\nNo links at all.\n",
                "# Coverage\n\nNo links either.\n",
            )
            outputs = [self._audit(runtime, repo, manifest_path) for runtime in ("py", "js")]
            for result in outputs:
                self.assertEqual(result.returncode, 1)
                self.assertIn("SECTION COHESION", result.stdout)
                self.assertIn("docs/architecture/high-level.md is an island", result.stdout)
                self.assertIn("docs/architecture/low-level.md is an island", result.stdout)
            self.assertEqual(outputs[0].stdout, outputs[1].stdout)

    def test_sibling_linked_pair_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            manifest_path = self._fixture(
                repo,
                "# Coverage\n\nSee [low-level](low-level.md) for components.\n",
                "# Coverage\n\nZoom-out is in [high-level](high-level.md).\n",
            )
            for runtime in ("py", "js"):
                result = self._audit(runtime, repo, manifest_path)
                self.assertEqual(result.returncode, 0, result.stdout)

    def test_one_direction_alone_is_enough(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            manifest_path = self._fixture(
                repo,
                "# Coverage\n\nSee [low-level](low-level.md) for components.\n",
                "# Coverage\n\nNo outgoing link, but the sibling links here.\n",
            )
            for runtime in ("py", "js"):
                result = self._audit(runtime, repo, manifest_path)
                self.assertEqual(result.returncode, 0, result.stdout)

    def test_linking_only_the_readme_does_not_satisfy_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            manifest_path = self._fixture(
                repo,
                "# Coverage\n\nSee [the section](README.md).\n",
                "# Coverage\n\nSee [the section](README.md).\n",
            )
            (repo / "docs" / "architecture" / "README.md").write_text("# Architecture\n", encoding="utf-8")
            for runtime in ("py", "js"):
                result = self._audit(runtime, repo, manifest_path)
                self.assertEqual(result.returncode, 1)
                self.assertIn("SECTION COHESION", result.stdout)

    def test_single_non_router_document_is_never_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            manifest_path = self._fixture(
                repo,
                "# Coverage\n\nAlone in the section.\n",
                "# Coverage\n\nAlone in the section.\n",
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["documents"] = manifest["documents"][:1]
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            (repo / "docs" / "architecture" / "low-level.md").unlink()
            for runtime in ("py", "js"):
                result = self._audit(runtime, repo, manifest_path)
                self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == "__main__":
    unittest.main()
