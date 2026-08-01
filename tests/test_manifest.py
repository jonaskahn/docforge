"""Manifest 3.1: tier/profile selection, status/audit transitions, provenance, migration."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from _support import (
    PORTFOLIO_PATHS,
    ROOT,
    CLI_JS,
    blob_hash,
    initialize,
    load_manifest,
    markdown_with_provenance,
    normalized,
    provenance,
    run,
    write_flow_index,
)
from runtime.common.python.provenance_frontmatter import (
    SCHEMA_VERSION,
    emit_yaml,
    migrate_v1_to_v2,
    parse_frontmatter,
    wrap_document,
)


class ManifestSelectionTests(unittest.TestCase):
    def test_each_tier_profile_selection_has_manifest_indexes(self) -> None:
        profiles = [
            ("shapes", "data-pipeline"),
            ("shapes", "api-service"),
            ("shapes", "web-app"),
            ("shapes", "desktop-app"),
            ("shapes", "library-sdk"),
            ("shapes", "infrastructure-platform"),
            ("audiences", "business-analysts"),
            ("audiences", "product-owners"),
            ("audiences", "coding-agents"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            for tier in ("spine", "diligence", "portfolio"):
                for dimension, profile in profiles:
                    repo = Path(tmp) / f"{tier}-{profile}"
                    repo.mkdir()
                    result = initialize("py", repo, tier, **{dimension: (profile,)})
                    self.assertEqual(result.returncode, 0, result.stderr)
                    paths = {doc["path"] for doc in load_manifest(repo)["documents"]}
                    for selected in paths:
                        if not selected.startswith(("docs/", "docs-portfolio/")):
                            continue
                        parent = str(Path(selected).parent).replace(os.sep, "/")
                        while parent not in ("docs", "docs-portfolio", "."):
                            self.assertIn(f"{parent}/README.md", paths, (tier, profile, selected))
                            parent = str(Path(parent).parent).replace(os.sep, "/")

    def test_every_tier_and_portfolio_layer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            counts = []
            for tier in ("spine", "diligence", "portfolio"):
                repo = Path(tmp) / tier
                repo.mkdir()
                result = initialize("py", repo, tier)
                self.assertEqual(result.returncode, 0, result.stderr)
                manifest = load_manifest(repo)
                self.assertEqual(manifest["version"], "3.1")
                self.assertEqual(manifest["project"]["tier"], tier)
                self.assertEqual(
                    manifest["project"]["profiles"]["audiences"],
                    ["engineers", "beginners"],
                )
                counts.append(len(manifest["documents"]))
                paths = {doc["path"] for doc in manifest["documents"]}
                if tier == "portfolio":
                    self.assertTrue(PORTFOLIO_PATHS <= paths)
            self.assertLess(counts[0], counts[1])
            self.assertLess(counts[1], counts[2])

    def test_overlap_deduplicates_and_retains_origins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            result = initialize(
                "py", repo, "spine",
                shapes=("api-service", "library-sdk"),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            docs = load_manifest(repo)["documents"]
            quickstarts = [doc for doc in docs if doc["path"] == "docs/product/quickstart.md"]
            self.assertEqual(len(quickstarts), 1)
            origins = quickstarts[0]["selection"]["origins"]
            self.assertEqual(origins, [
                {"kind": "shape", "id": "api-service"},
                {"kind": "shape", "id": "library-sdk"},
            ])

    def test_conditional_and_dynamic_documents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            result = initialize(
                "py", repo, "diligence",
                audiences=("product-owners", "coding-agents"),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            paths = {doc["path"] for doc in load_manifest(repo)["documents"]}
            self.assertNotIn("docs/engineering/conventions.md", paths)
            self.assertNotIn("docs/product/product-owner/backlog-traceability.md", paths)
            fake_adr = "0001-record-" + "architecture-decisions.md"
            self.assertFalse(any("example-" in path or path.endswith(fake_adr) for path in paths))
            rejected = run("py", "manage_manifest", "add", "--repo", str(repo),
                           "--type", "backlog-traceability", "--id", "po-backlog",
                           "--path", "docs/product/product-owner/backlog-traceability.md")
            self.assertEqual(rejected.returncode, 2)

            (repo / "CONVENTIONS.md").write_text("# Conventions\n", encoding="utf-8")
            (repo / ".docforge" / "tickets.json").write_text("[]\n", encoding="utf-8")
            result = initialize(
                "py", repo, "diligence",
                audiences=("product-owners", "coding-agents"),
            )
            self.assertNotEqual(result.returncode, 0)
            result = run("py", "manage_manifest", "init", "--repo", str(repo), "--tier", "diligence",
                         "--audience", "product-owners", "--audience", "coding-agents", "--force")
            self.assertEqual(result.returncode, 0, result.stderr)
            paths = {doc["path"] for doc in load_manifest(repo)["documents"]}
            self.assertIn("docs/engineering/conventions.md", paths)
            self.assertNotIn("docs/product/product-owner/backlog-traceability.md", paths)
            added = run("py", "manage_manifest", "add", "--repo", str(repo),
                        "--type", "backlog-traceability", "--id", "po-backlog",
                        "--path", "docs/product/product-owner/backlog-traceability.md")
            self.assertEqual(added.returncode, 0, added.stderr)
            backlog = next(
                doc for doc in load_manifest(repo)["documents"]
                if doc["id"] == "po-backlog"
            )
            self.assertEqual(
                backlog["selection"]["origins"],
                [
                    {"kind": "dynamic", "id": "backlog-traceability"},
                    {"kind": "audience", "id": "product-owners"},
                    {"kind": "condition", "id": "ticket_evidence"},
                ],
            )

            write_flow_index(repo)
            result = run("py", "manage_manifest", "add", "--repo", str(repo), "--type", "flow",
                         "--id", "flow-checkout", "--path", "docs/flows/checkout.md")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("docs/flows/checkout.md", {doc["path"] for doc in load_manifest(repo)["documents"]})

    def test_flow_requirement_is_per_document(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            result = initialize(
                "py", repo, "spine",
                audiences=("business-analysts", "product-owners", "coding-agents"),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            docs = {doc["id"]: doc for doc in load_manifest(repo)["documents"]}
            self.assertNotIn("flow_graph", docs["agents_architecture"]["requires"])
            self.assertNotIn("flow_graph", docs["agents_patterns"]["requires"])
            self.assertNotIn("flow_graph", docs["agents_testing"]["requires"])
            self.assertIn("flow_graph", docs["agents_flow"]["requires"])
            self.assertIn("flow_graph", docs["agents_glossary"]["requires"])
            self.assertIn("flow_graph", docs["ba_process_flows"]["requires"])
            self.assertIn("flow_graph", docs["ba_business_rules"]["requires"])
            self.assertIn("flow_graph", docs["ba_requirements"]["requires"])
            self.assertNotIn("flow_graph", docs["po_features"]["requires"])
            self.assertNotIn("flow_graph", docs["po_metrics"]["requires"])
            self.assertNotIn("flow_graph", docs["po_release_notes"]["requires"])

    def test_audience_profile_paths_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            result = initialize(
                "py", repo, "spine",
                audiences=("business-analysts", "product-owners", "coding-agents"),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            paths = {doc["path"] for doc in load_manifest(repo)["documents"]}
            self.assertTrue({
                "docs/product/business-analyst/README.md",
                "docs/product/business-analyst/process-flows.md",
                "docs/product/business-analyst/business-rules.md",
                "docs/product/business-analyst/requirements-traceability.md",
                "docs/product/product-owner/README.md",
                "docs/product/product-owner/feature-catalog.md",
                "docs/product/product-owner/success-metrics.md",
                "docs/product/product-owner/release-notes.md",
                "AGENTS.md",
                "docs/agents/architecture.md",
                "docs/agents/flow.md",
            } <= paths)
            self.assertNotIn(
                "docs/product/product-owner/backlog-traceability.md", paths,
            )

    def test_completion_requires_independent_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.assertEqual(initialize("py", repo, "spine").returncode, 0)
            for status in ("in_progress", "generated"):
                result = run("py", "manage_manifest", "set", "--repo", str(repo), "--id", "arch_high_level", "--status", status)
                self.assertEqual(result.returncode, 0, result.stderr)
            rejected = run("py", "manage_manifest", "set", "--repo", str(repo), "--id", "arch_high_level", "--status", "complete")
            self.assertEqual(rejected.returncode, 2)
            report = repo / ".docforge" / "audits" / "arch_high_level.md"
            report.parent.mkdir(parents=True, exist_ok=True)
            report.write_text("# Audit\n", encoding="utf-8")
            passed = run("py", "manage_manifest", "audit", "--repo", str(repo), "--id", "arch_high_level",
                         "--mode", "cold-pass", "--verdict", "PASS",
                         "--report", ".docforge/audits/arch_high_level.md")
            self.assertEqual(passed.returncode, 0, passed.stderr)
            complete = run("py", "manage_manifest", "set", "--repo", str(repo), "--id", "arch_high_level", "--status", "complete")
            self.assertEqual(complete.returncode, 0, complete.stderr)
            self.assertEqual(
                run("py", "manage_manifest", "set", "--repo", str(repo), "--id",
                    "arch_high_level", "--status", "in_progress").returncode,
                0,
            )
            self.assertEqual(
                run("py", "manage_manifest", "set", "--repo", str(repo), "--id",
                    "arch_high_level", "--status", "generated").returncode,
                0,
            )
            stale_pass = run("py", "manage_manifest", "set", "--repo", str(repo),
                             "--id", "arch_high_level", "--status", "complete")
            self.assertEqual(stale_pass.returncode, 2)
            repassed = run("py", "manage_manifest", "audit", "--repo", str(repo),
                           "--id", "arch_high_level", "--mode", "subagent",
                           "--verdict", "PASS",
                           "--report", ".docforge/audits/arch_high_level.md")
            self.assertEqual(repassed.returncode, 0, repassed.stderr)
            doc = next(item for item in load_manifest(repo)["documents"] if item["id"] == "arch_high_level")
            self.assertEqual(doc["audit"]["mode"], "subagent")


class ProvenanceAndAuditTests(unittest.TestCase):
    def test_root_sync_preserves_manifest_and_detects_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "source.txt"
            source.write_text("one\n", encoding="utf-8")
            content_hash = blob_hash(source.read_bytes())
            doc = repo / "README.md"
            doc.write_text(
                markdown_with_provenance(
                    provenance(
                        doc_id="root_readme", path="README.md", tier="spine",
                        target_depth="overview", section_id="readme",
                        source_path="source.txt", source_blob=content_hash,
                    ),
                    "# Readme\n",
                ),
                encoding="utf-8",
            )
            manifest = {
                "version": "3.1",
                "project": {"name": "fixture", "root": str(repo), "tier": "spine", "profiles": {
                    "shapes": [], "platforms": [], "frameworks": [],
                    "concerns": [], "audiences": [],
                }},
                "discovery": [],
                "documents": [{
                    "id": "root_readme", "type": "root-readme", "path": "README.md",
                    "status": "complete", "provenance": {
                        **provenance(
                            doc_id="root_readme", path="README.md", tier="spine",
                            target_depth="overview", section_id="readme",
                            source_path="source.txt", source_blob=content_hash,
                        ),
                    },
                    "selection": {"origins": [], "evidence": []}, "audit": {"verdict": "PASS"},
                }],
                "metadata": {},
            }
            manifest_path = repo / ".docforge" / "manifest.json"
            manifest_path.parent.mkdir()
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            for runtime in ("py", "js"):
                result = run(runtime, "check_staleness", "--manifest", str(manifest_path), "--sync-provenance")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("FRESH", result.stdout)
                saved = json.loads(manifest_path.read_text(encoding="utf-8"))
                self.assertEqual(saved["documents"][0]["type"], "root-readme")
                self.assertEqual(saved["documents"][0]["status"], "complete")
                self.assertEqual(saved["documents"][0]["provenance"]["schema"], "2.0")
                self.assertEqual(saved["documents"][0]["provenance"]["doc_id"], "root_readme")
            source.write_text("two\n", encoding="utf-8")
            for runtime in ("py", "js"):
                result = run(runtime, "check_staleness", "--manifest", str(manifest_path), "--section", "readme")
                self.assertEqual(result.returncode, 1)
                self.assertIn("PARTIAL", result.stdout)
            source.unlink()
            for runtime in ("py", "js"):
                result = run(runtime, "check_staleness", "--manifest", str(manifest_path))
                self.assertEqual(result.returncode, 1)
                self.assertIn("MISSING", result.stdout)
            saved = json.loads(manifest_path.read_text(encoding="utf-8"))
            saved["documents"][0]["provenance"]["sections"] = []
            manifest_path.write_text(json.dumps(saved, indent=2) + "\n", encoding="utf-8")
            for runtime in ("py", "js"):
                result = run(runtime, "check_staleness", "--manifest", str(manifest_path))
                self.assertEqual(result.returncode, 1)
                self.assertIn("UNTRACKED", result.stdout)

    def test_document_filter_limits_staleness_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            fresh_source = repo / "fresh.txt"
            stale_source = repo / "stale.txt"
            fresh_source.write_text("fresh\n", encoding="utf-8")
            stale_source.write_text("before\n", encoding="utf-8")
            fresh_blob = blob_hash(fresh_source.read_bytes())
            stale_blob = blob_hash(stale_source.read_bytes())
            fresh_doc = repo / "docs" / "fresh.md"
            stale_doc = repo / "docs" / "stale.md"
            fresh_doc.parent.mkdir()
            fresh_doc.write_text(
                markdown_with_provenance(
                    provenance(
                        doc_id="fresh_doc", path="docs/fresh.md", tier="spine",
                        target_depth="overview", section_id="body",
                        source_path="fresh.txt", source_blob=fresh_blob,
                    ),
                    "# Fresh\n",
                ),
                encoding="utf-8",
            )
            stale_doc.write_text(
                markdown_with_provenance(
                    provenance(
                        doc_id="stale_doc", path="docs/stale.md", tier="spine",
                        target_depth="overview", section_id="body",
                        source_path="stale.txt", source_blob=stale_blob,
                    ),
                    "# Stale\n",
                ),
                encoding="utf-8",
            )
            stale_source.write_text("after\n", encoding="utf-8")
            manifest = {
                "version": "3.1",
                "project": {"name": "fixture", "root": str(repo), "tier": "spine", "profiles": {
                    "shapes": [], "platforms": [], "frameworks": [],
                    "concerns": [], "audiences": [],
                }},
                "discovery": [],
                "documents": [
                    {
                        "id": "fresh_doc", "type": "generic", "path": "docs/fresh.md",
                        "status": "complete",
                        "provenance": provenance(
                            doc_id="fresh_doc", path="docs/fresh.md", tier="spine",
                            target_depth="overview", section_id="body",
                            source_path="fresh.txt", source_blob=fresh_blob,
                        ),
                        "selection": {"origins": [], "evidence": []},
                        "audit": {"verdict": "PASS"},
                    },
                    {
                        "id": "stale_doc", "type": "generic", "path": "docs/stale.md",
                        "status": "complete",
                        "provenance": provenance(
                            doc_id="stale_doc", path="docs/stale.md", tier="spine",
                            target_depth="overview", section_id="body",
                            source_path="stale.txt", source_blob=stale_blob,
                        ),
                        "selection": {"origins": [], "evidence": []},
                        "audit": {"verdict": "PASS"},
                    },
                ],
                "metadata": {},
            }
            manifest_path = repo / ".docforge" / "manifest.json"
            manifest_path.parent.mkdir()
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            for runtime in ("py", "js"):
                by_id = run(
                    runtime, "check_staleness",
                    "--manifest", str(manifest_path), "--document", "fresh_doc",
                )
                self.assertEqual(by_id.returncode, 0, by_id.stderr)
                self.assertIn("FRESH", by_id.stdout)
                self.assertNotIn("docs/stale.md", by_id.stdout)

                by_path = run(
                    runtime, "check_staleness",
                    "--manifest", str(manifest_path), "--document", "docs/stale.md",
                )
                self.assertEqual(by_path.returncode, 1, by_path.stderr)
                self.assertIn("PARTIAL", by_path.stdout)
                self.assertIn("STALE", by_path.stdout)
                self.assertNotIn("docs/fresh.md", by_path.stdout)

                missing = run(
                    runtime, "check_staleness",
                    "--manifest", str(manifest_path), "--document", "missing_doc",
                )
                self.assertEqual(missing.returncode, 0, missing.stderr)
                self.assertIn("no documents matched", missing.stdout)

                untracked = json.loads(manifest_path.read_text(encoding="utf-8"))
                untracked["documents"][0]["provenance"]["sections"] = []
                manifest_path.write_text(json.dumps(untracked, indent=2) + "\n", encoding="utf-8")
                empty = run(
                    runtime, "check_staleness",
                    "--manifest", str(manifest_path), "--document", "fresh_doc",
                )
                self.assertEqual(empty.returncode, 1, empty.stderr)
                self.assertIn("UNTRACKED", empty.stdout)
                # Restore filled provenance for the next runtime.
                untracked["documents"][0]["provenance"] = provenance(
                    doc_id="fresh_doc", path="docs/fresh.md", tier="spine",
                    target_depth="overview", section_id="body",
                    source_path="fresh.txt", source_blob=fresh_blob,
                )
                manifest_path.write_text(json.dumps(untracked, indent=2) + "\n", encoding="utf-8")

    def test_scaffold_audit_exit_codes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            document = {
                "id": "only", "type": "generic", "path": "docs/only.md", "group": "reference",
                "selection": {"origins": [], "evidence": []}, "status": "complete", "requires": [],
                "scaffold_template": "generic.md", "instruction_file": None, "target_depth": "reference",
                "write_order": 1, "provenance_mode": "sections", "audit_profile": "standard",
                "provenance": {"sections": []}, "audit": None,
            }
            manifest = {
                "version": "3.1", "project": {"name": "fixture", "root": str(repo), "tier": "spine", "profiles": {
                    "shapes": [], "platforms": [], "frameworks": [],
                    "concerns": [], "audiences": [],
                }}, "discovery": [],
                "documents": [document], "metadata": {},
            }
            manifest_path = repo / ".docforge" / "manifest.json"
            manifest_path.parent.mkdir()
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            for runtime in ("py", "js"):
                self.assertEqual(run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(manifest_path), "--audit").returncode, 1)
            source = repo / "source.txt"
            source.write_text("evidence\n", encoding="utf-8")
            target = repo / "docs" / "only.md"
            target.parent.mkdir()
            target.write_text(
                markdown_with_provenance(
                    provenance(
                        doc_id="only", path="docs/only.md", tier="spine",
                        target_depth="reference", section_id="only",
                        source_path="source.txt", source_blob=blob_hash(source.read_bytes()),
                    ),
                    "# Only\n\nComplete evidence-backed content.\n",
                ),
                encoding="utf-8",
            )
            for runtime in ("py", "js"):
                result = run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(manifest_path), "--audit")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_provenance_defect_categories_and_runtime_parity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "source.txt"
            source.write_text("evidence\n", encoding="utf-8")
            good = provenance(
                doc_id="only", path="docs/only.md", tier="spine",
                target_depth="reference", section_id="only",
                source_path="source.txt", source_blob=blob_hash(source.read_bytes()),
            )
            document = {
                "id": "only", "type": "generic", "path": "docs/only.md", "group": "reference",
                "selection": {"origins": [], "evidence": []}, "status": "complete", "requires": [],
                "scaffold_template": "generic.md", "instruction_file": None, "target_depth": "reference",
                "write_order": 1, "provenance_mode": "sections", "audit_profile": "standard",
                "provenance": good, "audit": None,
            }
            manifest = {
                "version": "3.1", "project": {
                    "name": "fixture", "root": str(repo), "tier": "spine",
                    "profiles": {"shapes": [], "platforms": [], "frameworks": [], "concerns": [], "audiences": []},
                },
                "discovery": [], "documents": [document], "metadata": {},
            }
            manifest_path = repo / ".docforge" / "manifest.json"
            manifest_path.parent.mkdir()
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            target = repo / "docs" / "only.md"
            target.parent.mkdir()
            cases = {
                "MISSING PROVENANCE": "# Only\n\nBody.\n",
                "UNPARSEABLE PROVENANCE": "---\n{\n---\n# Only\n\nBody.\n",
                "LEGACY PROVENANCE": """---
docforge_provenance:
  doc_id: "x"
  path: "docs/x.md"
  generated_at: "2026-07-27T09:12:44Z"
  generator:
    name: "docforge"
    version: "2.5.0"
  tier: "spine"
  target_depth: "orientation"
  graph:
    provider: "gitnexus"
    flow: "native"
  sections: []
---
# Only

Body.
""",
                "OBSOLETE SCHEMA": "---\n" + json.dumps({
                    "docforge_provenance": {
                        "schema": "1.0",
                        "doc_id": "only",
                        "path": "docs/only.md",
                        "generated_at": "2026-07-27T09:12:44Z",
                        "tool_version": "2.0.0",
                        "tier": "spine",
                        "target_depth": "reference",
                        "graph": {"provider": "gitnexus", "flow": "native"},
                        "sections": good["sections"],
                    },
                }, indent=2) + "\n---\n# Only\n\nBody.\n",
                "EMPTY PROVENANCE": markdown_with_provenance({**good, "sections": []}, "# Only\n\nBody.\n"),
                "INVALID BLOB": markdown_with_provenance({
                    **good,
                    "sections": [{**good["sections"][0], "sources": [{
                        "path": "source.txt", "git_blob": "placeholder", "role": "code",
                    }]}],
                }, "# Only\n\nBody.\n"),
                "UNKNOWN SOURCE": markdown_with_provenance({
                    **good,
                    "sections": [{**good["sections"][0], "sources": [{
                        "path": "missing.txt", "git_blob": "0" * 40, "role": "code",
                    }]}],
                }, "# Only\n\nBody.\n"),
                "UNKNOWN SECTION": markdown_with_provenance({
                    **good,
                    "sections": [{**good["sections"][0], "id": "not-a-heading"}],
                }, "# Only\n\nBody.\n"),
            }
            for category, text in cases.items():
                with self.subTest(category=category):
                    target.write_text(text, encoding="utf-8")
                    outputs = []
                    for runtime in ("py", "js"):
                        result = run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(manifest_path), "--audit")
                        self.assertEqual(result.returncode, 1)
                        self.assertIn(category, result.stdout)
                        outputs.append(normalized(result.stdout, [repo]))
                    self.assertEqual(outputs[0], outputs[1])

    def test_planned_scaffold_tokens_are_not_written_provenance_defects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                self.assertEqual(initialize(runtime, repo, "spine").returncode, 0)
                manifest_path = repo / ".docforge" / "manifest.json"
                created = run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(manifest_path), "--document", "arch_high_level")
                self.assertEqual(created.returncode, 0, created.stderr)
                text = (repo / "docs" / "architecture" / "high-level.md").read_text(encoding="utf-8")
                self.assertTrue(text.startswith("---\nid: "))
                self.assertIn('schema: "2.0"', text)
                result = run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(manifest_path), "--audit")
                for category in (
                    "EMPTY PROVENANCE", "MISSING PROVENANCE", "LEGACY PROVENANCE",
                    "UNPARSEABLE PROVENANCE", "OBSOLETE SCHEMA",
                ):
                    self.assertNotIn(category, result.stdout)

    def test_staleness_reports_no_blob_unparseable_and_legacy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "source.txt"
            source.write_text("evidence\n", encoding="utf-8")
            value = provenance(
                doc_id="only", path="docs/only.md", tier="spine",
                target_depth="reference", section_id="only",
                source_path="source.txt", source_blob="placeholder",
            )
            document = {
                "id": "only", "type": "generic", "path": "docs/only.md",
                "status": "complete", "provenance_mode": "sections", "provenance": value,
            }
            manifest = {
                "version": "3.1", "project": {"root": str(repo)},
                "documents": [document],
            }
            manifest_path = repo / ".docforge" / "manifest.json"
            manifest_path.parent.mkdir()
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            target = repo / "docs" / "only.md"
            target.parent.mkdir()
            target.write_text(markdown_with_provenance(value, "# Only\n"), encoding="utf-8")
            for runtime in ("py", "js"):
                result = run(runtime, "check_staleness", "--manifest", str(manifest_path))
                self.assertEqual(result.returncode, 1)
                self.assertIn("NO_BLOB", result.stdout)
            target.write_text("---\n{\n---\n# Only\n", encoding="utf-8")
            outputs = []
            for runtime in ("py", "js"):
                # Reset broken frontmatter and written status so each runtime
                # exercises failed migration + agent demotion.
                document["status"] = "complete"
                document["provenance"] = value
                document["audit"] = {"mode": "cold-pass", "verdict": "PASS"}
                manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
                target.write_text("---\n{\n---\n# Only\n", encoding="utf-8")
                result = run(runtime, "check_staleness", "--manifest", str(manifest_path), "--sync-provenance")
                self.assertTrue(
                    target.read_text(encoding="utf-8").startswith("---\ndocforge_provenance:\n"),
                    target.read_text(encoding="utf-8")[:80],
                )
                self.assertIn('schema: "2.0"', target.read_text(encoding="utf-8"))
                saved = load_manifest(repo)
                self.assertEqual(saved["documents"][0]["status"], "in_progress")
                self.assertIsNone(saved["documents"][0].get("audit"))
                outputs.append(normalized(result.stdout, [repo]))
            self.assertEqual(outputs[0], outputs[1])
            # Schema-less legacy is reported when not syncing; --sync-provenance
            # converts it to provenance 2.0 and demotes incomplete written docs
            # to in_progress for agent regeneration.
            target.write_text("""---
docforge_provenance:
  doc_id: "x"
  path: "docs/x.md"
  generated_at: "2026-07-27T09:12:44Z"
  generator:
    name: "docforge"
    version: "2.5.0"
  tier: "spine"
  target_depth: "orientation"
  graph:
    provider: "gitnexus"
    flow: "native"
  sections: []
---
# Only

Body.
""", encoding="utf-8")
            document["status"] = "complete"
            document["provenance"] = {"sections": []}
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            for runtime in ("py", "js"):
                result = run(runtime, "check_staleness", "--manifest", str(manifest_path))
                self.assertEqual(result.returncode, 1)
                self.assertIn("UNTRACKED", result.stdout)
            for runtime in ("py", "js"):
                document["status"] = "complete"
                document["provenance"] = {"sections": []}
                document["audit"] = {"mode": "cold-pass", "verdict": "PASS"}
                manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
                target.write_text("""---
docforge_provenance:
  doc_id: "x"
  path: "docs/x.md"
  generated_at: "2026-07-27T09:12:44Z"
  generator:
    name: "docforge"
    version: "2.5.0"
  tier: "spine"
  target_depth: "orientation"
  graph:
    provider: "gitnexus"
    flow: "native"
  sections: []
---
# Only

Body.
""", encoding="utf-8")
                result = run(runtime, "check_staleness", "--manifest", str(manifest_path), "--sync-provenance")
                self.assertTrue(target.read_text(encoding="utf-8").startswith("---\ndocforge_provenance:\n"))
                self.assertIn('schema: "2.0"', target.read_text(encoding="utf-8"))
                saved = load_manifest(repo)
                self.assertEqual(saved["documents"][0]["status"], "in_progress")
                self.assertIsNone(saved["documents"][0].get("audit"))
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            document["status"] = "complete"
            document["provenance"] = value
            document["audit"] = {"mode": "cold-pass", "verdict": "PASS"}
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            target.write_text(
                "---\n" + json.dumps({
                    "docforge_provenance": {
                        "schema": "1.0",
                        "doc_id": "only",
                        "path": "docs/only.md",
                        "generated_at": "2026-07-27T09:12:44Z",
                        "tool_version": "2.0.0",
                        "tier": "spine",
                        "target_depth": "reference",
                        "graph": {"provider": "gitnexus", "flow": "native"},
                        "sections": value["sections"],
                    },
                }, indent=2) + "\n---\n# Only\n",
                encoding="utf-8",
            )
            for runtime in ("py", "js"):
                result = run(runtime, "check_staleness", "--manifest", str(manifest_path), "--sync-provenance")
                self.assertEqual(result.returncode, 1)
                self.assertIn("Synchronized provenance", result.stdout)
                self.assertIn("NO_BLOB", result.stdout)
                migrated = target.read_text(encoding="utf-8")
                self.assertTrue(migrated.startswith("---\ndocforge_provenance:\n"), migrated[:80])
                self.assertIn('schema: "2.0"', migrated)

    def test_lint_placeholder_token_link_and_forge_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            target = repo / "target.md"
            target.write_text("# Target\n\nBody.\n", encoding="utf-8")
            subject = repo / "subject.md"
            subject.write_text(
                "# Subject\n\n{{unfinished}}\n\n<EXTERNAL_CONTACT>\n\n"
                "[dead](missing.md)\n\nHosted on GitHub.\n",
                encoding="utf-8",
            )
            for runtime in ("py", "js"):
                result = run(runtime, "lint_document", "--file", str(subject), "--json")
                self.assertEqual(result.returncode, 1)
                payload = json.loads(result.stdout)
                kinds = {item["kind"] for item in payload["defects"]}
                self.assertTrue({"scaffold-marker", "dead-link", "forge-leakage"} <= kinds)
                self.assertEqual(payload["tokens"], ["<EXTERNAL_CONTACT>"])

    def test_lint_provenance_gate_has_paired_defects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".docforge").mkdir()
            source = repo / "source.txt"
            source.write_text("evidence\n", encoding="utf-8")
            value = provenance(
                doc_id="subject", path="subject.md", tier="spine",
                target_depth="reference", section_id="frontmatter-only",
                source_path="source.txt", source_blob="placeholder",
            )
            subject = repo / "subject.md"
            subject.write_text(
                markdown_with_provenance(value, "# Subject\n\nBody.\n"),
                encoding="utf-8",
            )
            outputs = []
            for runtime in ("py", "js"):
                result = run(runtime, "lint_document", "--file", str(subject), "--json")
                self.assertEqual(result.returncode, 1)
                payload = json.loads(result.stdout)
                kinds = {item["kind"] for item in payload["defects"]}
                self.assertTrue({"invalid blob", "unknown section"} <= kinds)
                outputs.append(payload["defects"])
            self.assertEqual(outputs[0], outputs[1])

    def test_folder_only_promotion_is_audit_defect(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "source.txt"
            source.write_text("flow\n", encoding="utf-8")
            target = repo / "docs" / "flows" / "checkout" / "README.md"
            target.parent.mkdir(parents=True)
            target.write_text(
                markdown_with_provenance(
                    provenance(
                        doc_id="checkout", path="docs/flows/checkout/README.md",
                        tier="diligence", target_depth="deep-dive",
                        section_id="checkout", source_path="source.txt",
                        source_blob=blob_hash(source.read_bytes()),
                    ),
                    "# Checkout\n\nComplete overview.\n",
                ),
                encoding="utf-8",
            )
            document = {
                "id": "checkout", "type": "flow", "path": "docs/flows/checkout/README.md",
                "group": "flows", "selection": {"origins": [], "evidence": []},
                "status": "complete", "requires": ["flow_graph"], "scaffold_template": "generic.md",
                "instruction_file": "flows.md", "target_depth": "deep-dive", "write_order": 1,
                "provenance_mode": "sections", "audit_profile": "flow",
                "provenance": {"sections": []}, "audit": None,
            }
            manifest = {
                "version": "3.1",
                "project": {"name": "fixture", "root": str(repo), "tier": "diligence", "profiles": {
                    "shapes": [], "platforms": [], "frameworks": [],
                    "concerns": [], "audiences": [],
                }},
                "discovery": [],
                "documents": [document], "metadata": {},
            }
            manifest_path = repo / ".docforge" / "manifest.json"
            manifest_path.parent.mkdir()
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            for runtime in ("py", "js"):
                result = run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(manifest_path), "--audit")
                self.assertEqual(result.returncode, 1)
                self.assertIn("FOLDER-ONLY PROMOTION", result.stdout)


class ProvenanceCodecAndMigrationTests(unittest.TestCase):
    def test_yaml_round_trip_and_runtime_parity(self) -> None:
        value = provenance(
            doc_id="roundtrip", path="docs/roundtrip.md", tier="spine",
            target_depth="reference", section_id="body",
            source_path="source.txt", source_blob="a" * 40,
        )
        text = markdown_with_provenance(value, "# Body\n\nContent.\n")
        state, parsed, _end = parse_frontmatter(text)
        self.assertEqual(state, "ok")
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed["sections"], value["sections"])
        self.assertEqual(parsed["schema"], SCHEMA_VERSION)

        node_script = """
const pf = require(process.argv[1]);
const value = JSON.parse(process.argv[2]);
process.stdout.write(pf.emitYaml(value));
"""
        py_out = emit_yaml(value)
        result = subprocess.run(
            ["node", "-e", node_script, str(CLI_JS / "provenance_frontmatter.js"), json.dumps(value)],
            cwd=ROOT, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, py_out)

        wrapped = wrap_document(value, "# Wrapped\n")
        self.assertTrue(wrapped.startswith("---\ndocforge_provenance:\n"))
        self.assertIn("# Wrapped\n", wrapped)

    def test_rejected_yaml_constructs(self) -> None:
        from runtime.common.python.provenance_frontmatter import YamlCodecError, parse_yaml_mapping

        for raw in ['a: &id 1\n', 'a: *id\n', 'a: |\n  x\n', 'a: [1, 2]\n']:
            with self.assertRaises(YamlCodecError):
                parse_yaml_mapping(raw)

    def test_migrate_v1_to_v2_preserves_sections(self) -> None:
        legacy = {
            "schema": "1.0",
            "doc_id": "legacy",
            "path": "legacy.md",
            "generated_at": "2026-07-27T09:12:44Z",
            "tool_version": "2.0.0",
            "tier": "spine",
            "target_depth": "reference",
            "graph": {"provider": "gitnexus", "flow": "native"},
            "sections": [{"id": "body", "sources": [], "unresolved": []}],
        }
        migrated = migrate_v1_to_v2(legacy, "# Body\n")
        self.assertEqual(migrated["schema"], SCHEMA_VERSION)
        self.assertEqual(migrated["generator"], {"name": "docforge", "version": "2.0.0"})
        self.assertEqual(migrated["sections"], legacy["sections"])
        self.assertTrue(migrated["content_hash"].startswith("sha256:"))

    def test_migrate_schema_less_doc_graph_snapshot_preserves_sections(self) -> None:
        blob = "8eb720c92a52ffc34673bc0e83b6b4d5ea714ee9"
        schema_less = {
            "doc": "docs/architecture/concepts/README.md",
            "generated_at": "2026-07-27T00:00:00Z",
            "graph_snapshot": ".ua/knowledge-graph.json",
            "sections": [{
                "id": "main",
                "sources": [
                    {"path": "docs/architecture/concepts/auth-rbac.md", "git_blob": blob},
                    {"path": "docs/architecture/concepts/queue-system.md", "git_blob": blob},
                ],
            }],
        }
        migrated = migrate_v1_to_v2(
            schema_less,
            "# Concepts\n",
            defaults={
                "doc_id": "concepts_index",
                "path": "docs/architecture/concepts/README.md",
                "tier": "diligence",
                "target_depth": "orientation",
            },
        )
        self.assertEqual(migrated["schema"], SCHEMA_VERSION)
        self.assertEqual(migrated["doc_id"], "concepts_index")
        self.assertEqual(migrated["path"], "docs/architecture/concepts/README.md")
        self.assertEqual(migrated["generated_at"], "2026-07-27T00:00:00Z")
        self.assertEqual(migrated["tier"], "diligence")
        self.assertEqual(migrated["target_depth"], "orientation")
        self.assertEqual(
            migrated["graph"],
            {"provider": "understand-anything", "flow": "native"},
        )
        self.assertEqual(len(migrated["sections"]), 1)
        self.assertEqual(migrated["sections"][0]["id"], "main")
        self.assertEqual(migrated["sections"][0]["unresolved"], [])
        self.assertEqual(
            migrated["sections"][0]["sources"],
            [
                {
                    "path": "docs/architecture/concepts/auth-rbac.md",
                    "git_blob": blob,
                    "role": "doc",
                },
                {
                    "path": "docs/architecture/concepts/queue-system.md",
                    "git_blob": blob,
                    "role": "doc",
                },
            ],
        )

    def test_migrate_metadata_preserves_schema_less_file_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            blob = "8eb720c92a52ffc34673bc0e83b6b4d5ea714ee9"
            concepts = repo / "docs" / "architecture" / "concepts"
            concepts.mkdir(parents=True)
            for name in ("auth-rbac.md", "queue-system.md", "search-index.md", "kafka-integration.md"):
                (concepts / name).write_text(f"# {name}\n", encoding="utf-8")
            readme = concepts / "README.md"
            readme.write_text(
                "---\n"
                "docforge_provenance:\n"
                "  doc: docs/architecture/concepts/README.md\n"
                "  generated_at: 2026-07-27T00:00:00Z\n"
                "  graph_snapshot: .ua/knowledge-graph.json\n"
                "  sections:\n"
                "    - id: main\n"
                "      sources:\n"
                "        - path: docs/architecture/concepts/auth-rbac.md\n"
                f"          git_blob: {blob}\n"
                "        - path: docs/architecture/concepts/queue-system.md\n"
                f"          git_blob: {blob}\n"
                "        - path: docs/architecture/concepts/search-index.md\n"
                f"          git_blob: {blob}\n"
                "        - path: docs/architecture/concepts/kafka-integration.md\n"
                f"          git_blob: {blob}\n"
                "---\n"
                "# Concepts\n",
                encoding="utf-8",
            )
            manifest = {
                "version": "3.0",
                "project": {
                    "name": "fixture",
                    "root": str(repo),
                    "tier": "diligence",
                    "profiles": {
                        "shapes": [], "platforms": [], "frameworks": [],
                        "concerns": [], "audiences": [],
                    },
                },
                "discovery": [],
                "documents": [{
                    "id": "concepts_index",
                    "type": "folder-index",
                    "path": "docs/architecture/concepts/README.md",
                    "status": "complete",
                    "provenance": {},
                    "provenance_mode": "sections",
                    "target_depth": "orientation",
                }],
                "metadata": {},
            }
            manifest_path = repo / ".docforge" / "manifest.json"
            manifest_path.parent.mkdir()
            for runtime in ("py", "js"):
                readme.write_text(
                    "---\n"
                    "docforge_provenance:\n"
                    "  doc: docs/architecture/concepts/README.md\n"
                    "  generated_at: 2026-07-27T00:00:00Z\n"
                    "  graph_snapshot: .ua/knowledge-graph.json\n"
                    "  sections:\n"
                    "    - id: main\n"
                    "      sources:\n"
                    "        - path: docs/architecture/concepts/auth-rbac.md\n"
                    f"          git_blob: {blob}\n"
                    "        - path: docs/architecture/concepts/queue-system.md\n"
                    f"          git_blob: {blob}\n"
                    "        - path: docs/architecture/concepts/search-index.md\n"
                    f"          git_blob: {blob}\n"
                    "        - path: docs/architecture/concepts/kafka-integration.md\n"
                    f"          git_blob: {blob}\n"
                    "---\n"
                    "# Concepts\n",
                    encoding="utf-8",
                )
                manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
                result = run(runtime, "migrate_metadata", "--repo", str(repo), "--manifest", str(manifest_path))
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                self.assertNotIn("REGENERATED", result.stdout)
                text = readme.read_text(encoding="utf-8")
                self.assertTrue(text.startswith("---\ndocforge_provenance:\n"), text[:80])
                self.assertIn('schema: "2.0"', text)
                self.assertIn('doc_id: "concepts_index"', text)
                self.assertIn('generated_at: "2026-07-27T00:00:00Z"', text)
                self.assertIn('tier: "diligence"', text)
                self.assertIn('provider: "understand-anything"', text)
                self.assertIn('flow: "native"', text)
                self.assertIn('path: "docs/architecture/concepts/auth-rbac.md"', text)
                self.assertIn(f'git_blob: "{blob}"', text)
                self.assertIn('role: "doc"', text)
                self.assertNotIn("graph_snapshot", text)
                self.assertNotIn("<GENERATED_AT>", text)
                self.assertNotIn("<TIER>", text)
                self.assertNotIn("sections: []", text)
                saved = load_manifest(repo)
                sections = saved["documents"][0]["provenance"]["sections"]
                self.assertEqual(len(sections), 1)
                self.assertEqual(len(sections[0]["sources"]), 4)

    def test_migrate_metadata_idempotent_and_regenerates_unparseable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "source.txt"
            source.write_text("evidence\n", encoding="utf-8")
            blob = blob_hash(source.read_bytes())
            legacy_provenance = {
                "schema": "1.0",
                "doc_id": "readme",
                "path": "README.md",
                "generated_at": "2026-07-27T09:12:44Z",
                "tool_version": "2.0.0",
                "tier": "spine",
                "target_depth": "overview",
                "graph": {"provider": "gitnexus", "flow": "native"},
                "sections": [{
                    "id": "readme",
                    "sources": [{"path": "source.txt", "git_blob": blob, "role": "code"}],
                    "unresolved": [],
                }],
            }
            readme = repo / "README.md"
            readme.write_text(
                "---\n" + json.dumps({"docforge_provenance": legacy_provenance}, indent=2) + "\n---\n# Readme\n",
                encoding="utf-8",
            )
            unparseable = repo / "docs" / "broken.md"
            unparseable.parent.mkdir(parents=True)
            unparseable.write_text("---\n{\n---\n# Broken\n", encoding="utf-8")
            manifest = {
                "version": "3.0",
                "project": {"name": "fixture", "root": str(repo), "tier": "spine", "profiles": {
                    "shapes": [], "platforms": [], "frameworks": [],
                    "concerns": [], "audiences": [],
                }},
                "discovery": [],
                "documents": [
                    {
                        "id": "readme", "type": "root-readme", "path": "README.md",
                        "status": "complete", "provenance": legacy_provenance,
                        "provenance_mode": "sections", "target_depth": "overview",
                    },
                    {
                        "id": "broken", "type": "generic", "path": "docs/broken.md",
                        "status": "complete", "provenance": {"sections": []},
                        "provenance_mode": "sections", "target_depth": "orientation",
                    },
                ],
                "metadata": {},
            }
            manifest_path = repo / ".docforge" / "manifest.json"
            manifest_path.parent.mkdir()
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

            for runtime in ("py", "js"):
                # Reset fixtures between runtimes so each starts from JSON 1.0 / broken.
                readme.write_text(
                    "---\n" + json.dumps({"docforge_provenance": legacy_provenance}, indent=2) + "\n---\n# Readme\n",
                    encoding="utf-8",
                )
                unparseable.write_text("---\n{\n---\n# Broken\n", encoding="utf-8")
                manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

                result = run(runtime, "migrate_metadata", "--repo", str(repo), "--manifest", str(manifest_path))
                self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
                self.assertIn("FAILED", result.stdout)
                self.assertIn("docs/broken.md", result.stdout)
                self.assertIn("agent must regenerate provenance", result.stdout)

                readme_text = readme.read_text(encoding="utf-8")
                self.assertTrue(readme_text.startswith("---\ndocforge_provenance:\n"), readme_text[:80])
                self.assertIn('schema: "2.0"', readme_text)
                self.assertIn("generator:", readme_text)
                self.assertIn("# Readme", readme_text)

                broken_text = unparseable.read_text(encoding="utf-8")
                self.assertTrue(broken_text.startswith("---\ndocforge_provenance:\n"), broken_text[:80])
                self.assertIn('schema: "2.0"', broken_text)
                self.assertIn('doc_id: "broken"', broken_text)
                self.assertIn("# Broken", broken_text)

                saved = load_manifest(repo)
                self.assertEqual(saved["version"], "3.1")
                self.assertEqual(saved["documents"][0]["provenance"]["schema"], "2.0")
                self.assertIn("generator", saved["documents"][0]["provenance"])
                self.assertEqual(saved["documents"][1]["provenance"]["schema"], "2.0")
                self.assertEqual(saved["documents"][1]["provenance"]["doc_id"], "broken")
                self.assertEqual(saved["documents"][1]["status"], "in_progress")
                self.assertIsNone(saved["documents"][1].get("audit"))

                again = run(runtime, "migrate_metadata", "--repo", str(repo), "--manifest", str(manifest_path))
                self.assertEqual(again.returncode, 0, again.stderr + again.stdout)
                self.assertNotIn("FAILED  docs/broken.md", again.stdout)
                self.assertNotIn("REGENERATED  docs/broken.md", again.stdout)
                self.assertEqual(load_manifest(repo)["documents"][1]["status"], "in_progress")

    def test_obsolete_schema_defect_names_migrate_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            value = {
                "schema": "1.0",
                "doc_id": "subject",
                "path": "subject.md",
                "generated_at": "2026-07-27T09:12:44Z",
                "tool_version": "2.0.0",
                "tier": "spine",
                "target_depth": "reference",
                "graph": {"provider": "gitnexus", "flow": "native"},
                "sections": [],
            }
            subject = repo / "subject.md"
            subject.write_text(
                "---\n" + json.dumps({"docforge_provenance": value}, indent=2) + "\n---\n# Subject\n\nBody.\n",
                encoding="utf-8",
            )
            for runtime in ("py", "js"):
                result = run(runtime, "lint_document", "--file", str(subject), "--json")
                self.assertEqual(result.returncode, 1)
                payload = json.loads(result.stdout)
                kinds = {item["kind"] for item in payload["defects"]}
                self.assertIn("obsolete schema", kinds)
                details = {item["detail"] for item in payload["defects"] if item["kind"] == "obsolete schema"}
                self.assertTrue(any("migrate_metadata" in detail for detail in details))

    def test_docforge_gitignore_and_finish_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            docforge_dir = repo / ".docforge"

            result = run("py", "manage_manifest", "init", "--repo", str(repo), "--tier", "spine")
            self.assertEqual(result.returncode, 0, result.stderr)
            gitignore = docforge_dir / ".gitignore"
            self.assertTrue(gitignore.is_file())
            content = gitignore.read_text(encoding="utf-8")
            self.assertIn("tmp/", content)
            self.assertIn("audits/", content)
            self.assertIn("scratch/", content)
            self.assertIn("backups/", content)
            self.assertIn("cache/", content)

            tmp_file = docforge_dir / "tmp" / "provisional.json"
            scratch_file = docforge_dir / "scratch" / "profiles.json"
            tmp_file.parent.mkdir(parents=True, exist_ok=True)
            scratch_file.parent.mkdir(parents=True, exist_ok=True)
            tmp_file.write_text("{}\n", encoding="utf-8")
            scratch_file.write_text("{}\n", encoding="utf-8")
            self.assertTrue(tmp_file.exists())
            self.assertTrue(scratch_file.exists())

            finish_res = run("py", "manage_manifest", "finish", "--repo", str(repo))
            self.assertEqual(finish_res.returncode, 0, finish_res.stderr)
            self.assertFalse(tmp_file.exists())
            self.assertFalse(scratch_file.exists())
            self.assertTrue((docforge_dir / "manifest.json").is_file())
            self.assertTrue(gitignore.is_file())


if __name__ == "__main__":
    unittest.main()
