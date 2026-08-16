"""Manifest 3.2: tier/profile selection, status/audit transitions, provenance, migration."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
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
    normalized_blob_hash,
    provenance,
    range_blob_hash,
    remove_sidecar_entry,
    run,
    write_flow_index,
    write_written_doc,
)
from test_dashboard import fake_npm_env, run_dashboard, stop_dashboard
from runtime.common.python.provenance_frontmatter import (
    SCHEMA_VERSION,
    emit_yaml,
    migrate_v1_to_v2,
    parse_frontmatter,
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
                self.assertEqual(manifest["version"], "3.7")
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
            # This test is about conditional/dynamic selection, not layout —
            # force standard so a small fixture's auto-detected scale doesn't
            # fold `conventions` into the compact `docs/engineering.md`.
            result = run("py", "manage_manifest", "init", "--repo", str(repo), "--tier", "diligence",
                         "--audience", "product-owners", "--audience", "coding-agents",
                         "--layout", "standard", "--force")
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
                            "--id", "arch_high_level", "--mode", "cold-pass",
                           "--verdict", "PASS",
                           "--report", ".docforge/audits/arch_high_level.md")
            self.assertEqual(repassed.returncode, 0, repassed.stderr)
            doc = next(item for item in load_manifest(repo)["documents"] if item["id"] == "arch_high_level")
            self.assertEqual(doc["audit"]["mode"], "cold-pass")


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
                "project": {"name": "fixture", "root": str(repo), "tier": "spine", "provenance_storage": "markdown", "profiles": {
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

    def test_whitespace_and_eol_only_change_reports_cosmetic_not_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "source.txt"
            source.write_text("one\ntwo\n", encoding="utf-8")
            raw_blob = blob_hash(source.read_bytes())
            norm_blob = normalized_blob_hash(source.read_bytes())
            doc = repo / "README.md"
            value = provenance(
                doc_id="root_readme", path="README.md", tier="spine",
                target_depth="overview", section_id="readme",
                source_path="source.txt", source_blob=raw_blob,
                normalized_blob=norm_blob,
            )
            doc.write_text(markdown_with_provenance(value, "# Readme\n"), encoding="utf-8")
            manifest = {
                "version": "3.1", "project": {"root": str(repo), "provenance_storage": "markdown"},
                "documents": [{
                    "id": "root_readme", "type": "root-readme", "path": "README.md",
                    "status": "complete", "provenance_mode": "sections", "provenance": value,
                }],
            }
            manifest_path = repo / ".docforge" / "manifest.json"
            manifest_path.parent.mkdir()
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            # Whitespace/EOL-only edit: same semantic lines, CRLF + trailing spaces.
            source.write_text("one\r\ntwo  \r\n", encoding="utf-8")
            for runtime in ("py", "js"):
                result = run(runtime, "check_staleness", "--manifest", str(manifest_path))
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("COSMETIC", result.stdout)
                self.assertNotIn("STALE", result.stdout)

    def test_semantic_change_with_incidental_whitespace_still_reports_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "source.txt"
            source.write_text("one\ntwo\n", encoding="utf-8")
            raw_blob = blob_hash(source.read_bytes())
            norm_blob = normalized_blob_hash(source.read_bytes())
            doc = repo / "README.md"
            value = provenance(
                doc_id="root_readme", path="README.md", tier="spine",
                target_depth="overview", section_id="readme",
                source_path="source.txt", source_blob=raw_blob,
                normalized_blob=norm_blob,
            )
            doc.write_text(markdown_with_provenance(value, "# Readme\n"), encoding="utf-8")
            manifest = {
                "version": "3.1", "project": {"root": str(repo), "provenance_storage": "markdown"},
                "documents": [{
                    "id": "root_readme", "type": "root-readme", "path": "README.md",
                    "status": "complete", "provenance_mode": "sections", "provenance": value,
                }],
            }
            manifest_path = repo / ".docforge" / "manifest.json"
            manifest_path.parent.mkdir()
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            # Real content change on line 2, plus incidental CRLF/trailing-space noise.
            source.write_text("one\r\nTHREE  \r\n", encoding="utf-8")
            for runtime in ("py", "js"):
                result = run(runtime, "check_staleness", "--manifest", str(manifest_path))
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("STALE", result.stdout)
                self.assertNotIn("COSMETIC", result.stdout)

    def test_range_scoped_source_outside_edit_reports_cosmetic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "source.txt"
            source.write_text("l1\nl2\nl3\nl4\nl5\n", encoding="utf-8")
            raw_blob = blob_hash(source.read_bytes())
            scoped_blob = range_blob_hash(source.read_bytes(), 2, 3)
            doc = repo / "README.md"
            value = provenance(
                doc_id="root_readme", path="README.md", tier="spine",
                target_depth="overview", section_id="readme",
                source_path="source.txt", source_blob=raw_blob,
                evidence_range=(2, 3), range_blob=scoped_blob,
            )
            doc.write_text(markdown_with_provenance(value, "# Readme\n"), encoding="utf-8")
            manifest = {
                "version": "3.1", "project": {"root": str(repo), "provenance_storage": "markdown"},
                "documents": [{
                    "id": "root_readme", "type": "root-readme", "path": "README.md",
                    "status": "complete", "provenance_mode": "sections", "provenance": value,
                }],
            }
            manifest_path = repo / ".docforge" / "manifest.json"
            manifest_path.parent.mkdir()
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            # Edit line 5, outside the recorded range 2-3.
            source.write_text("l1\nl2\nl3\nl4\nCHANGED\n", encoding="utf-8")
            for runtime in ("py", "js"):
                result = run(runtime, "check_staleness", "--manifest", str(manifest_path))
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("COSMETIC", result.stdout)
                self.assertNotIn("STALE", result.stdout)

    def test_range_scoped_source_inside_edit_reports_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "source.txt"
            source.write_text("l1\nl2\nl3\nl4\nl5\n", encoding="utf-8")
            raw_blob = blob_hash(source.read_bytes())
            scoped_blob = range_blob_hash(source.read_bytes(), 2, 3)
            doc = repo / "README.md"
            value = provenance(
                doc_id="root_readme", path="README.md", tier="spine",
                target_depth="overview", section_id="readme",
                source_path="source.txt", source_blob=raw_blob,
                evidence_range=(2, 3), range_blob=scoped_blob,
            )
            doc.write_text(markdown_with_provenance(value, "# Readme\n"), encoding="utf-8")
            manifest = {
                "version": "3.1", "project": {"root": str(repo), "provenance_storage": "markdown"},
                "documents": [{
                    "id": "root_readme", "type": "root-readme", "path": "README.md",
                    "status": "complete", "provenance_mode": "sections", "provenance": value,
                }],
            }
            manifest_path = repo / ".docforge" / "manifest.json"
            manifest_path.parent.mkdir()
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            # Edit line 2, inside the recorded range 2-3.
            source.write_text("l1\nCHANGED\nl3\nl4\nl5\n", encoding="utf-8")
            for runtime in ("py", "js"):
                result = run(runtime, "check_staleness", "--manifest", str(manifest_path))
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("STALE", result.stdout)
                self.assertNotIn("COSMETIC", result.stdout)

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
                "project": {"name": "fixture", "root": str(repo), "tier": "spine", "provenance_storage": "markdown", "profiles": {
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
                "version": "3.1", "project": {"name": "fixture", "root": str(repo), "tier": "spine", "provenance_storage": "markdown", "profiles": {
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
            good_provenance = provenance(
                doc_id="only", path="docs/only.md", tier="spine",
                target_depth="reference", section_id="only",
                source_path="source.txt", source_blob=blob_hash(source.read_bytes()),
            )
            write_written_doc(
                repo, {**document, "provenance": good_provenance},
                "# Only\n\nComplete evidence-backed content.\n",
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
                    "provenance_storage": "markdown",
                    "profiles": {"shapes": [], "platforms": [], "frameworks": [], "concerns": [], "audiences": []},
                },
                "discovery": [], "documents": [document], "metadata": {},
            }
            manifest_path = repo / ".docforge" / "manifest.json"
            manifest_path.parent.mkdir()
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            target = repo / "docs" / "only.md"
            target.parent.mkdir()
            body = "# Only\n\nBody.\n"
            # States a document reaches before it has ever been migrated: no
            # sidecar entry exists yet, so these stay pure inline fixtures.
            inline_cases = {
                "MISSING PROVENANCE": "# Only\n\nBody.\n",
                "UNPARSEABLE PROVENANCE": "---\n{\n---\n# Only\n\nBody.\n",
                "LEGACY PROVENANCE": """---
docforge_provenance:
  doc_id: "x"
  path: "docs/x.md"
  generated_at: "2026-07-27T09:12:44Z"
  generator:
    name: "docforge"
    version: "2.19.0"
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
                        "tool_version": "2.19.0",
                        "tier": "spine",
                        "target_depth": "reference",
                        "graph": {"provider": "gitnexus", "flow": "native"},
                        "sections": good["sections"],
                    },
                }, indent=2) + "\n---\n# Only\n\nBody.\n",
            }
            # Structurally current provenance with a deliberate content defect
            # — the sidecar is what makes lint treat it as "ok" and validate
            # the section/source shape below the top-level state check.
            sidecar_cases = {
                "EMPTY PROVENANCE": {**good, "sections": []},
                "INVALID BLOB": {
                    **good,
                    "sections": [{**good["sections"][0], "sources": [{
                        "path": "source.txt", "git_blob": "placeholder", "role": "code",
                    }]}],
                },
                "UNKNOWN SOURCE": {
                    **good,
                    "sections": [{**good["sections"][0], "sources": [{
                        "path": "missing.txt", "git_blob": "0" * 40, "role": "code",
                    }]}],
                },
                "UNKNOWN SECTION": {
                    **good,
                    "sections": [{**good["sections"][0], "id": "not-a-heading"}],
                },
            }
            for category, text in inline_cases.items():
                with self.subTest(category=category):
                    remove_sidecar_entry(repo, "docs/only.md")
                    target.write_text(text, encoding="utf-8")
                    outputs = []
                    for runtime in ("py", "js"):
                        result = run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(manifest_path), "--audit")
                        self.assertEqual(result.returncode, 1)
                        self.assertIn(category, result.stdout)
                        outputs.append(normalized(result.stdout, [repo]))
                    self.assertEqual(outputs[0], outputs[1])
            for category, case_provenance in sidecar_cases.items():
                with self.subTest(category=category):
                    remove_sidecar_entry(repo, "docs/only.md")
                    write_written_doc(repo, {**document, "provenance": case_provenance}, body)
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
                self.assertFalse(text.startswith("---"))
                sidecar = json.loads((repo / ".docforge/provenance/docs/architecture.json").read_text(encoding="utf-8"))
                self.assertEqual(sidecar["files"]["high-level.md"]["provenance"]["schema"], SCHEMA_VERSION)
                result = run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(manifest_path), "--audit")
                for category in (
                    "EMPTY PROVENANCE", "MISSING PROVENANCE", "LEGACY PROVENANCE",
                    "UNPARSEABLE PROVENANCE", "OBSOLETE SCHEMA",
                ):
                    self.assertNotIn(category, result.stdout)

    def test_staleness_reports_no_blob_unparseable_and_legacy(self) -> None:
        """A pre-sidecar document keeps its frontmatter until something moves
        it. `--sync-provenance` is that something: on every path (garbage
        frontmatter, schema-less legacy, obsolete schema 1.0) the target ends
        up frontmatter-free and the provenance lands in the folder sidecar —
        there is no other destination now that `markdown` storage is gone."""

        def sidecar_provenance(repo: Path) -> dict:
            path = repo / ".docforge" / "provenance" / "docs.json"
            return json.loads(path.read_text(encoding="utf-8"))["files"]["only.md"]["provenance"]

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
                "version": "3.1", "project": {"root": str(repo), "provenance_storage": "json"},
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
                # Reset broken frontmatter, written status, and any sidecar
                # entry the previous runtime's iteration stamped — the sidecar
                # wins over the file, so a stale entry would hide the garbage
                # frontmatter this iteration means to exercise.
                remove_sidecar_entry(repo, "docs/only.md")
                document["status"] = "complete"
                document["provenance"] = value
                document["audit"] = {"mode": "cold-pass", "verdict": "PASS"}
                manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
                target.write_text("---\n{\n---\n# Only\n", encoding="utf-8")
                result = run(runtime, "check_staleness", "--manifest", str(manifest_path), "--sync-provenance")
                self.assertEqual(target.read_text(encoding="utf-8"), "# Only\n")
                self.assertEqual(sidecar_provenance(repo)["schema"], "2.0")
                saved = load_manifest(repo)
                self.assertEqual(saved["documents"][0]["status"], "in_progress")
                self.assertIsNone(saved["documents"][0].get("audit"))
                outputs.append(normalized(result.stdout, [repo]))
            self.assertEqual(outputs[0], outputs[1])
            # Schema-less legacy is reported when not syncing; --sync-provenance
            # converts it to current provenance and demotes incomplete written
            # docs to in_progress for agent regeneration.
            target.write_text("""---
docforge_provenance:
  doc_id: "x"
  path: "docs/x.md"
  generated_at: "2026-07-27T09:12:44Z"
  generator:
    name: "docforge"
    version: "2.19.0"
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
                remove_sidecar_entry(repo, "docs/only.md")
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
    version: "2.19.0"
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
                self.assertEqual(target.read_text(encoding="utf-8"), "# Only\n\nBody.\n")
                self.assertEqual(sidecar_provenance(repo)["schema"], SCHEMA_VERSION)
                saved = load_manifest(repo)
                self.assertEqual(saved["documents"][0]["status"], "in_progress")
                self.assertIsNone(saved["documents"][0].get("audit"))
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            obsolete_frontmatter = (
                "---\n" + json.dumps({
                    "docforge_provenance": {
                        "schema": "1.0",
                        "doc_id": "only",
                        "path": "docs/only.md",
                        "generated_at": "2026-07-27T09:12:44Z",
                        "tool_version": "2.19.0",
                        "tier": "spine",
                        "target_depth": "reference",
                        "graph": {"provider": "gitnexus", "flow": "native"},
                        "sections": value["sections"],
                    },
                }, indent=2) + "\n---\n# Only\n"
            )
            for runtime in ("py", "js"):
                remove_sidecar_entry(repo, "docs/only.md")
                document["status"] = "complete"
                document["provenance"] = value
                document["audit"] = {"mode": "cold-pass", "verdict": "PASS"}
                manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
                target.write_text(obsolete_frontmatter, encoding="utf-8")
                result = run(runtime, "check_staleness", "--manifest", str(manifest_path), "--sync-provenance")
                self.assertEqual(result.returncode, 1)
                self.assertIn("Synchronized provenance", result.stdout)
                self.assertIn("NO_BLOB", result.stdout)
                self.assertEqual(target.read_text(encoding="utf-8"), "# Only\n")
                self.assertEqual(sidecar_provenance(repo)["schema"], SCHEMA_VERSION)

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
            write_written_doc(repo, {"id": "subject", "path": "subject.md", "provenance": value}, "# Subject\n\nBody.\n")
            outputs = []
            for runtime in ("py", "js"):
                result = run(runtime, "lint_document", "--file", str(subject), "--json")
                self.assertEqual(result.returncode, 1)
                payload = json.loads(result.stdout)
                kinds = {item["kind"] for item in payload["defects"]}
                self.assertTrue({"invalid blob", "unknown section"} <= kinds)
                outputs.append(payload["defects"])
            self.assertEqual(outputs[0], outputs[1])

    def test_lint_requires_public_description(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "source.txt"
            source.write_text("evidence\n", encoding="utf-8")
            value = provenance(
                doc_id="subject", path="subject.md", tier="spine",
                target_depth="reference", section_id="body",
                source_path="source.txt", source_blob=blob_hash(source.read_bytes()),
            )
            missing = repo / "missing.md"
            missing.write_text(markdown_with_provenance(value, "# Missing\n\nBody.\n"), encoding="utf-8")
            long_doc = repo / "long.md"
            long_text = markdown_with_provenance(value, "# Long\n\nBody.\n").replace(
                "---\n",
                f'---\ndescription: "{"x" * 200}"\n',
                1,
            )
            long_doc.write_text(long_text, encoding="utf-8")
            for runtime in ("py", "js"):
                result = run(runtime, "lint_document", "--file", str(missing), "--json")
                self.assertEqual(result.returncode, 1)
                kinds = {item["kind"] for item in json.loads(result.stdout)["defects"]}
                self.assertIn("missing description", kinds)

                result = run(runtime, "lint_document", "--file", str(long_doc), "--json")
                self.assertEqual(result.returncode, 1)
                kinds = {item["kind"] for item in json.loads(result.stdout)["defects"]}
                self.assertIn("long description", kinds)

    def test_lint_accepts_described_document(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "source.txt"
            source.write_text("evidence\n", encoding="utf-8")
            value = provenance(
                doc_id="subject", path="subject.md", tier="spine",
                target_depth="reference", section_id="body",
                source_path="source.txt", source_blob=blob_hash(source.read_bytes()),
            )
            subject = repo / "subject.md"
            text = markdown_with_provenance(value, "# Subject\n\nBody.\n")
            text = text.replace("---\n", '---\ndescription: "A valid description."\n', 1)
            subject.write_text(text, encoding="utf-8")
            for runtime in ("py", "js"):
                result = run(runtime, "lint_document", "--file", str(subject), "--json")
                payload = json.loads(result.stdout)
                kinds = {item["kind"] for item in payload["defects"]}
                self.assertNotIn("missing description", kinds)
                self.assertNotIn("long description", kinds)

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
                "project": {"name": "fixture", "root": str(repo), "tier": "diligence", "provenance_storage": "markdown", "profiles": {
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
        self.assertEqual(parsed["schema"], value["schema"])

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
            "tool_version": "2.19.0",
            "tier": "spine",
            "target_depth": "reference",
            "graph": {"provider": "gitnexus", "flow": "native"},
            "sections": [{"id": "body", "sources": [], "unresolved": []}],
        }
        migrated = migrate_v1_to_v2(legacy, "# Body\n")
        self.assertEqual(migrated["schema"], SCHEMA_VERSION)
        self.assertEqual(migrated["generator"], {"name": "docforge", "version": "2.19.0"})
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
                sidecar_dir = repo / ".docforge" / "provenance"
                if sidecar_dir.exists():
                    import shutil
                    shutil.rmtree(sidecar_dir)
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
                self.assertTrue(text.startswith("# Concepts"), text[:40])
                sidecar = json.loads((repo / ".docforge/provenance/docs/architecture/concepts.json").read_text(encoding="utf-8"))
                migrated = sidecar["files"]["README.md"]["provenance"]
                self.assertEqual(migrated["schema"], SCHEMA_VERSION)
                self.assertEqual(migrated["doc_id"], "concepts_index")
                self.assertEqual(migrated["generated_at"], "2026-07-27T00:00:00Z")
                self.assertEqual(migrated["tier"], "diligence")
                self.assertEqual(migrated["graph"]["provider"], "understand-anything")
                self.assertEqual(migrated["graph"]["flow"], "native")
                source = migrated["sections"][0]["sources"][0]
                self.assertEqual(source["path"], "docs/architecture/concepts/auth-rbac.md")
                self.assertEqual(source["git_blob"], blob)
                self.assertEqual(source["role"], "doc")
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
                "tool_version": "2.19.0",
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
                "project": {"name": "fixture", "root": str(repo), "tier": "spine", "provenance_storage": "markdown", "profiles": {
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
                # Reset fixtures between runtimes so each starts from JSON 1.0 /
                # broken — including the sidecar, which wins over a stale file
                # and would otherwise carry the previous runtime's migration
                # forward instead of exercising a fresh one.
                remove_sidecar_entry(repo, "README.md")
                remove_sidecar_entry(repo, "docs/broken.md")
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

                self.assertEqual(readme.read_text(encoding="utf-8"), "# Readme\n")
                readme_provenance = json.loads(
                    (repo / ".docforge" / "provenance" / "root.json").read_text(encoding="utf-8"),
                )["files"]["README.md"]["provenance"]
                self.assertEqual(readme_provenance["schema"], SCHEMA_VERSION)
                self.assertIn("generator", readme_provenance)

                self.assertEqual(unparseable.read_text(encoding="utf-8"), "# Broken\n")
                broken_provenance = json.loads(
                    (repo / ".docforge" / "provenance" / "docs.json").read_text(encoding="utf-8"),
                )["files"]["broken.md"]["provenance"]
                self.assertEqual(broken_provenance["schema"], SCHEMA_VERSION)
                self.assertEqual(broken_provenance["doc_id"], "broken")

                saved = load_manifest(repo)
                self.assertEqual(saved["version"], "3.7")
                self.assertEqual(saved["documents"][0]["provenance"]["schema"], SCHEMA_VERSION)
                self.assertIn("generator", saved["documents"][0]["provenance"])
                self.assertEqual(saved["documents"][1]["provenance"]["schema"], SCHEMA_VERSION)
                self.assertEqual(saved["documents"][1]["provenance"]["doc_id"], "broken")
                self.assertEqual(saved["documents"][1]["status"], "in_progress")
                self.assertIsNone(saved["documents"][1].get("audit"))

                again = run(runtime, "migrate_metadata", "--repo", str(repo), "--manifest", str(manifest_path))
                self.assertEqual(again.returncode, 0, again.stderr + again.stdout)
                self.assertNotIn("FAILED  docs/broken.md", again.stdout)
                self.assertNotIn("REGENERATED  docs/broken.md", again.stdout)
                self.assertEqual(load_manifest(repo)["documents"][1]["status"], "in_progress")

    def test_migrate_31_to_32_seeds_catalog_descriptions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            index = repo / "docs" / "README.md"
            index.parent.mkdir(parents=True)
            index.write_text(
                "---\n" + json.dumps({"docforge_provenance": {
                    "schema": "2.0", "doc_id": "docs_index", "path": "docs/README.md",
                    "generated_at": "2026-08-01T00:00:00Z",
                    "generator": {"name": "docforge", "version": "2.19.0"},
                    "tier": "spine", "target_depth": "orientation",
                    "graph": {"provider": "gitnexus", "flow": "native"},
                    "sections": [{
                        "id": "main",
                        "sources": [{"path": "src/main.ts", "git_blob": blob_hash(b"evidence"), "role": "code"}],
                        "unresolved": [],
                    }],
                }}, indent=2) + "\n---\n# Documentation\n\nBody.\n",
                encoding="utf-8",
            )
            manifest = {
                "version": "3.1",
                "project": {"name": "fixture", "root": str(repo), "tier": "spine", "provenance_storage": "markdown", "profiles": {
                    "shapes": [], "platforms": [], "frameworks": [],
                    "concerns": [], "audiences": [],
                }},
                "discovery": [],
                "documents": [{
                    "id": "docs_index", "type": "docs-index", "path": "docs/README.md",
                    "title": "Documentation", "status": "complete", "requires": [],
                    "scaffold_template": "docs-index.template.md", "target_depth": "orientation",
                    "write_order": 30, "provenance_mode": "sections", "audit_profile": "router",
                    "provenance": {"sections": []}, "audit": None,
                }],
                "metadata": {},
            }
            manifest_path = repo / ".docforge" / "manifest.json"
            manifest_path.parent.mkdir()
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

            for runtime in ("py", "js"):
                manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
                result = run(runtime, "migrate_metadata", "--repo", str(repo), "--manifest", str(manifest_path))
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                migrated = load_manifest(repo)
                self.assertEqual(migrated["version"], "3.7")
                self.assertIn("description", migrated["documents"][0])
                self.assertEqual(migrated["documents"][0]["description"], "Self-introduction to the documentation: what the repo is, who it serves, and the reader question each selected section answers")
                self.assertEqual(migrated["documents"][0]["provenance"]["schema"], "2.0")

                # Idempotent: a second run keeps the seeded description.
                again = run(runtime, "migrate_metadata", "--repo", str(repo), "--manifest", str(manifest_path))
                self.assertEqual(again.returncode, 0, again.stderr + again.stdout)
                self.assertEqual(load_manifest(repo)["documents"][0]["description"], migrated["documents"][0]["description"])

    def test_migrate_31_keeps_existing_description(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            readme = repo / "docs" / "README.md"
            readme.parent.mkdir(parents=True)
            readme.write_text(
                markdown_with_provenance(
                    provenance(
                        doc_id="docs_index", path="docs/README.md", tier="spine",
                        target_depth="orientation", section_id="main",
                        source_path="src/main.ts", source_blob=blob_hash(b"evidence"),
                    ),
                    "# Documentation\n\nBody.\n",
                ),
                encoding="utf-8",
            )
            manifest = {
                "version": "3.1",
                "project": {"name": "fixture", "root": str(repo), "tier": "spine", "provenance_storage": "markdown", "profiles": {
                    "shapes": [], "platforms": [], "frameworks": [],
                    "concerns": [], "audiences": [],
                }},
                "discovery": [],
                "documents": [{
                    "id": "docs_index", "type": "docs-index", "path": "docs/README.md",
                    "title": "Documentation", "description": "Writer-refined one-liner.",
                    "status": "generated", "requires": [],
                    "scaffold_template": "docs-index.template.md", "target_depth": "orientation",
                    "write_order": 30, "provenance_mode": "sections", "audit_profile": "router",
                    "provenance": {"sections": []}, "audit": None,
                }],
                "metadata": {},
            }
            manifest_path = repo / ".docforge" / "manifest.json"
            manifest_path.parent.mkdir()
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            for runtime in ("py", "js"):
                manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
                result = run(runtime, "migrate_metadata", "--repo", str(repo), "--manifest", str(manifest_path))
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                migrated = load_manifest(repo)
                self.assertEqual(migrated["version"], "3.7")
                self.assertEqual(migrated["documents"][0]["description"], "Writer-refined one-liner.")

    def test_obsolete_schema_defect_names_migrate_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            value = {
                "schema": "1.0",
                "doc_id": "subject",
                "path": "subject.md",
                "generated_at": "2026-07-27T09:12:44Z",
                "tool_version": "2.19.0",
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


def seed_v1_1_repo(repo: Path) -> None:
    """A legacy 1.1 repository: `project_context` / `document_groups`, no
    per-document provenance, schema-less or absent frontmatter."""
    blob = "8eb720c92a52ffc34673bc0e83b6b4d5ea714ee9"
    for rel in ("docs/architecture", "docs/product", "docs/flows", ".docforge"):
        (repo / rel).mkdir(parents=True, exist_ok=True)
    (repo / "docs/architecture/high-level.md").write_text(
        "---\n"
        "docforge_provenance:\n"
        "  doc: docs/architecture/high-level.md\n"
        "  generated_at: 2026-07-28T00:00:00Z\n"
        "  graph_snapshot: .ua/knowledge-graph.json\n"
        "  sections:\n"
        "    - id: system-in-context\n"
        "      sources:\n"
        "        - path: src/main.ts\n"
        f"          git_blob: {blob}\n"
        "---\n"
        "# High-level\n\nContent.\n",
        encoding="utf-8",
    )
    (repo / "docs/product/overview.md").write_text("# Overview\n\nBody.\n", encoding="utf-8")
    (repo / "docs/README.md").write_text("# Documentation\n", encoding="utf-8")
    (repo / "docs/flows/checkout.md").write_text("# Checkout\n\nSteps.\n", encoding="utf-8")
    (repo / "AGENTS.md").write_text("# Legacy Repo\n\nKernel.\n", encoding="utf-8")
    manifest = {
        "version": "1.1",
        "generated_at": "2026-07-28T00:00:00Z",
        "project_context": {
            "repo_name": "legacy",
            "repo_path": str(repo),
            "tier": "core",
            "overlays": ["agent-context"],
        },
        "document_groups": [
            {"group": "architecture", "documents": [
                {
                    "id": "arch_high_level", "type": "architecture-high-level",
                    "path": "docs/architecture/high-level.md", "status": "complete",
                    "template": "architecture-high-level.md",
                    "requires_domain_graph": False, "requires_knowledge_graph": True,
                    "sections": [],
                },
                {
                    "id": "arch_low_level", "type": "architecture-low-level",
                    "path": "docs/architecture/low-level.md", "status": "planned",
                    "template": "architecture-low-level.md",
                    "requires_domain_graph": False, "requires_knowledge_graph": True,
                    "sections": [],
                },
            ]},
            {"group": "product", "documents": [
                {
                    "id": "docs_index", "type": "docs-index",
                    "path": "docs/README.md", "status": "complete",
                    "sections": [{"id": "introduction", "sources": [
                        {"path": "README.md", "git_blob": blob},
                    ]}],
                },
                {
                    "id": "product_overview", "type": "product-overview",
                    "path": "docs/product/overview.md", "status": "generated",
                    "sections": [{"id": "overview", "sources": [
                        {"path": "package.json", "git_blob": blob},
                    ]}],
                },
            ]},
            {"group": "reference", "documents": [
                {
                    "id": "legacy_skip", "type": "limitations-register",
                    "path": "docs/reference/limitations.md", "status": "skipped",
                    "sections": [],
                },
            ]},
            {"group": "flows", "documents": [
                {
                    "id": "flow_checkout", "type": "flows",
                    "path": "docs/flows/checkout.md", "status": "complete",
                    "sections": [{"id": "checkout", "sources": [
                        {"path": "src/checkout.py", "git_blob": blob},
                    ]}],
                },
            ]},
            {"group": "agent-context", "documents": [
                {
                    "id": "agents_kernel", "type": "agents-kernel",
                    "path": "AGENTS.md", "status": "complete",
                    "sections": [{"id": "kernel", "sources": [
                        {"path": "AGENTS.md", "git_blob": blob},
                    ]}],
                },
            ]},
        ],
        "metadata": {},
    }
    (repo / ".docforge" / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


class ManifestV11MigrationTests(unittest.TestCase):
    def test_v1_1_re_registers_manifest_and_adopts_written_docs(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp) / runtime
                    repo.mkdir()
                    seed_v1_1_repo(repo)
                    result = run(runtime, "migrate_metadata", "--repo", str(repo))
                    self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                    manifest = load_manifest(repo)
                    self.assertEqual(manifest["version"], "3.7")
                    self.assertEqual(manifest["project"]["tier"], "spine")
                    self.assertEqual(manifest["project"]["profiles"]["audiences"], ["coding-agents"])
                    docs = {doc["id"]: doc for doc in manifest["documents"]}

                    high = docs["arch_high_level"]
                    self.assertEqual(high["status"], "generated")
                    self.assertEqual(high["type"], "architecture-high-level")
                    self.assertEqual(high["provenance"]["schema"], SCHEMA_VERSION)
                    self.assertEqual(high["provenance"]["doc_id"], "arch_high_level")
                    self.assertEqual(high["provenance"]["graph"], {"provider": "understand-anything", "flow": "native"})
                    source = high["provenance"]["sections"][0]["sources"][0]
                    self.assertEqual(source["path"], "src/main.ts")
                    self.assertEqual(source["role"], "code")
                    high_text = (repo / "docs/architecture/high-level.md").read_text(encoding="utf-8")
                    self.assertIn("# High-level\n\nContent.\n", high_text)
                    arch_sidecar = json.loads((repo / ".docforge/provenance/docs/architecture.json").read_text(encoding="utf-8"))
                    self.assertEqual(arch_sidecar["files"]["high-level.md"]["provenance"]["schema"], SCHEMA_VERSION)
                    self.assertEqual(arch_sidecar["files"]["high-level.md"]["provenance"]["doc_id"], "arch_high_level")

                    overview = docs["product_overview"]
                    self.assertEqual(overview["status"], "generated")
                    self.assertEqual(overview["provenance"]["schema"], SCHEMA_VERSION)
                    self.assertEqual(overview["provenance"]["sections"][0]["sources"][0]["path"], "package.json")
                    self.assertEqual(overview["provenance"]["sections"][0]["sources"][0]["role"], "manifest")
                    overview_text = (repo / "docs/product/overview.md").read_text(encoding="utf-8")
                    self.assertIn("# Overview\n\nBody.\n", overview_text)
                    product_sidecar = json.loads((repo / ".docforge/provenance/docs/product.json").read_text(encoding="utf-8"))
                    self.assertEqual(product_sidecar["files"]["overview.md"]["provenance"]["schema"], SCHEMA_VERSION)

                    self.assertEqual(docs["arch_low_level"]["status"], "planned")
                    self.assertEqual(docs["legacy_skip"]["status"], "skipped")

                    flow = docs["flow_checkout"]
                    self.assertEqual(flow["status"], "generated")
                    self.assertEqual(flow["type"], "flows")
                    self.assertEqual(flow["provenance"]["sections"][0]["sources"][0]["path"], "src/checkout.py")

                    agents = docs["agents_kernel"]
                    self.assertEqual(agents["status"], "generated")
                    self.assertEqual(agents["provenance_mode"], "manifest")
                    self.assertEqual(agents["provenance"]["doc_id"], "agents_kernel")
                    agents_text = (repo / "AGENTS.md").read_text(encoding="utf-8")
                    self.assertTrue(agents_text.startswith("# Legacy Repo"))
                    self.assertNotIn("docforge_provenance", agents_text)

                    self.assertFalse(any(doc["status"] == "complete" for doc in manifest["documents"]))

                    # Rerun is idempotent for written documents. The standard
                    # 3.x pass reports planned/skipped entries without files
                    # as MISSING (pre-existing behavior), so the exit code is
                    # 1 while the migrated state stays put.
                    again = run(runtime, "migrate_metadata", "--repo", str(repo))
                    self.assertEqual(again.returncode, 1)
                    self.assertIn("MISSING  docs/architecture/low-level.md", again.stdout)
                    self.assertEqual(
                        {doc["id"]: doc["status"] for doc in load_manifest(repo)["documents"]},
                        {doc["id"]: doc["status"] for doc in manifest["documents"]},
                    )
                    self.assertEqual(
                        (repo / "docs/architecture/high-level.md").read_text(encoding="utf-8"),
                        high_text,
                    )

    def test_v1_1_migration_dry_run_writes_nothing(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp) / runtime
                    repo.mkdir()
                    seed_v1_1_repo(repo)
                    manifest_path = repo / ".docforge" / "manifest.json"
                    before_manifest = manifest_path.read_text(encoding="utf-8")
                    before_file = (repo / "docs/architecture/high-level.md").read_text(encoding="utf-8")
                    result = run(runtime, "migrate_metadata", "--repo", str(repo), "--dry-run")
                    self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                    self.assertEqual(manifest_path.read_text(encoding="utf-8"), before_manifest)
                    self.assertEqual(
                        (repo / "docs/architecture/high-level.md").read_text(encoding="utf-8"),
                        before_file,
                    )

    def test_v1_1_missing_written_file_is_failed_and_planned(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp) / runtime
                    repo.mkdir()
                    seed_v1_1_repo(repo)
                    (repo / "docs/product/overview.md").unlink()
                    result = run(runtime, "migrate_metadata", "--repo", str(repo), "--report")
                    self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
                    report = json.loads(result.stdout)
                    failed = [item for item in report["results"] if item["action"] == "failed"]
                    self.assertEqual(
                        [item["doc"] for item in failed],
                        ["docs/product/overview.md"],
                    )
                    self.assertIn("file absent", failed[0]["detail"])
                    docs = {doc["id"]: doc for doc in load_manifest(repo)["documents"]}
                    self.assertEqual(docs["product_overview"]["status"], "planned")

    def test_v1_1_migration_parity_and_dashboard_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repos = {}
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                seed_v1_1_repo(repo)
                result = run(runtime, "migrate_metadata", "--repo", str(repo))
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                repos[runtime] = repo
            py_manifest = load_manifest(repos["py"])
            js_manifest = load_manifest(repos["js"])
            py_manifest["project"]["root"] = js_manifest["project"]["root"]
            for manifest in (py_manifest, js_manifest):
                manifest["project"]["scale"]["decided_at"] = "<TIME>"
            self.assertEqual(py_manifest, js_manifest)
            self.assertEqual(
                (repos["py"] / "docs/architecture/high-level.md").read_text(encoding="utf-8"),
                (repos["js"] / "docs/architecture/high-level.md").read_text(encoding="utf-8"),
            )
            plan = run("py", "dashboard", "start", "--repo", str(repos["py"]), "--plan-only")
            self.assertEqual(plan.returncode, 0, plan.stderr + plan.stdout)
            self.assertIn("0 problems", plan.stdout)
            self.assertIn("-> /docs", plan.stdout)
            self.assertIn("-> /docs/architecture/high-level", plan.stdout)
            self.assertIn("-> /docs/flows/checkout", plan.stdout)

    def test_v1_1_dashboard_scan_and_status_stay_read_only_on_legacy_manifest(self) -> None:
        # `scan`/`status` never auto-migrate (strictly read-only); they keep
        # failing with the same clear version-mismatch error as before.
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp) / runtime
                    repo.mkdir()
                    seed_v1_1_repo(repo)
                    manifest_path = repo / ".docforge" / "manifest.json"
                    before_manifest = manifest_path.read_text(encoding="utf-8")
                    for command in ("scan", "status"):
                        result = run_dashboard(runtime, command, "--repo", str(repo))
                        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
                        self.assertIn("manifest must use version", result.stderr)
                        self.assertEqual(manifest_path.read_text(encoding="utf-8"), before_manifest)

    def test_v1_1_dashboard_plan_only_previews_migration_without_writing(self) -> None:
        # `dashboard start --plan-only` against an UNMIGRATED legacy manifest
        # must preview the migration (no separate `migrate_metadata` call
        # needed first) and write nothing.
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp) / runtime
                    repo.mkdir()
                    seed_v1_1_repo(repo)
                    manifest_path = repo / ".docforge" / "manifest.json"
                    before_manifest = manifest_path.read_text(encoding="utf-8")
                    before_file = (repo / "docs/architecture/high-level.md").read_text(encoding="utf-8")
                    result = run_dashboard(runtime, "start", "--repo", str(repo), "--plan-only")
                    self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
                    self.assertIn("manifest is legacy", result.stdout)
                    self.assertIn("--plan-only preview (no writes)", result.stdout)
                    self.assertEqual(manifest_path.read_text(encoding="utf-8"), before_manifest)
                    self.assertEqual(
                        (repo / "docs/architecture/high-level.md").read_text(encoding="utf-8"),
                        before_file,
                    )

    def test_v1_1_dashboard_start_auto_migrates_without_prompt(self) -> None:
        # A real (non-plan-only) `dashboard start` against an unmigrated
        # legacy manifest must auto-migrate it (no stop-and-ask gate),
        # print what changed, and then proceed to build/serve normally.
        env, _bin = fake_npm_env()
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp) / runtime
                    repo.mkdir()
                    seed_v1_1_repo(repo)
                    try:
                        result = run_dashboard(runtime, "start", "--repo", str(repo), "--no-open", env=env)
                        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                        self.assertIn("manifest: legacy manifest auto-migrated to 3.7", result.stdout)
                        manifest = load_manifest(repo)
                        self.assertEqual(manifest["version"], "3.7")
                        # scan/status must not perform the same auto-migration
                        # on a manifest that's already migrated -- this just
                        # confirms the migrated manifest is now readable by
                        # the strictly read-only commands too.
                        status = run_dashboard(runtime, "status", "--repo", str(repo))
                        self.assertEqual(status.returncode, 0, status.stderr + status.stdout)
                    finally:
                        stop_dashboard(runtime, repo)


def seed_v2_0_repo(repo: Path) -> None:
    """A 2.0-era repository: flat `documents`, `project.overlays`, no
    per-document frontmatter, manifest-only section provenance."""
    blob = "8eb720c92a52ffc34673bc0e83b6b4d5ea714ee9"
    for rel in ("docs/architecture", "docs/product/product-owner", "docs/engineering", ".docforge"):
        (repo / rel).mkdir(parents=True, exist_ok=True)
    (repo / "docs/architecture/high-level.md").write_text("# High-level\n\nContent.\n", encoding="utf-8")
    (repo / "docs/product/overview.md").write_text("# Overview\n\nBody.\n", encoding="utf-8")
    (repo / "docs/product/product-owner/release-notes.md").write_text("# Release Notes\n\nBody.\n", encoding="utf-8")
    manifest = {
        "version": "2.0",
        "generated_at": "2026-07-28T00:00:00Z",
        "project": {
            "name": "legacy2",
            "root": str(repo),
            "tier": "diligence",
            "overlays": ["api", "business-analyst"],
        },
        "documents": [
            {
                "id": "arch_high_level", "type": "architecture-high-level",
                "path": "docs/architecture/high-level.md", "group": "architecture",
                "selection": {"origins": [{"kind": "tier", "id": "spine"}], "evidence": []},
                "status": "complete", "requires": ["code_graph"],
                "scaffold_template": "architecture-high-level.md", "instruction_file": None,
                "target_depth": "orientation", "write_order": 10,
                "provenance_mode": "sections", "audit_profile": "architecture",
                "provenance": {"sections": [{"id": "system-in-context", "sources": [
                    {"path": "src/main.ts", "git_blob": blob},
                ]}]},
                "audit": {"mode": "cold-pass", "verdict": "PASS",
                          "timestamp": "2026-07-28T00:00:00Z", "report_path": ".docforge/audits/arch.md"},
            },
            {
                "id": "product_overview", "type": "product-overview",
                "path": "docs/product/overview.md", "group": "product",
                "selection": {"origins": [{"kind": "tier", "id": "spine"}], "evidence": []},
                "status": "generated", "requires": ["code_graph"],
                "scaffold_template": "product-overview.md", "instruction_file": None,
                "target_depth": "orientation", "write_order": 20,
                "provenance_mode": "sections", "audit_profile": "standard",
                "provenance": {"sections": [{"id": "overview", "sources": [
                    {"path": "package.json", "git_blob": blob},
                ]}]},
                "audit": None,
            },
            {
                "id": "po_release_notes", "type": "release-notes",
                "path": "docs/product/product-owner/release-notes.md", "group": "product",
                "selection": {"origins": [{"kind": "overlay", "id": "product-owner"}], "evidence": []},
                "status": "complete", "requires": [],
                "scaffold_template": "release-notes.md", "instruction_file": None,
                "target_depth": "orientation", "write_order": 30,
                "provenance_mode": "sections", "audit_profile": "standard",
                "provenance": {"sections": [{"id": "release", "sources": [
                    {"path": "CHANGELOG.md", "git_blob": blob},
                ]}]},
                "audit": None,
            },
            {
                "id": "setup_guide", "type": "setup-guide",
                "path": "docs/engineering/setup.md", "group": "engineering",
                "selection": {"origins": [{"kind": "tier", "id": "spine"}], "evidence": []},
                "status": "planned", "requires": ["manifests"],
                "scaffold_template": "setup.md", "instruction_file": None,
                "target_depth": "orientation", "write_order": 40,
                "provenance_mode": "sections", "audit_profile": "standard",
                "provenance": {"sections": []},
                "audit": None,
            },
        ],
        "metadata": {},
    }
    (repo / ".docforge" / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


class ManifestV20MigrationTests(unittest.TestCase):
    def test_v2_0_re_registers_overlays_and_preserves_metadata(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp) / runtime
                    repo.mkdir()
                    seed_v2_0_repo(repo)
                    result = run(runtime, "migrate_metadata", "--repo", str(repo))
                    self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                    manifest = load_manifest(repo)
                    self.assertEqual(manifest["version"], "3.7")
                    self.assertEqual(manifest["project"]["tier"], "diligence")
                    self.assertEqual(manifest["project"]["name"], "legacy2")
                    self.assertEqual(manifest["project"]["profiles"]["shapes"], ["api-service"])
                    self.assertEqual(manifest["project"]["profiles"]["audiences"], ["business-analysts"])
                    docs = {doc["id"]: doc for doc in manifest["documents"]}

                    high = docs["arch_high_level"]
                    self.assertEqual(high["status"], "generated")
                    self.assertEqual(high["target_depth"], "orientation")
                    self.assertEqual(high["write_order"], 10)
                    self.assertEqual(high["requires"], ["code_graph"])
                    self.assertEqual(high["selection"]["origins"], [{"kind": "tier", "id": "spine"}])
                    self.assertIsNone(high["audit"])
                    self.assertEqual(high["provenance"]["schema"], SCHEMA_VERSION)
                    self.assertEqual(high["provenance"]["generator"]["version"], "2.0")
                    self.assertEqual(high["provenance"]["sections"][0]["sources"][0]["role"], "code")
                    high_text = (repo / "docs/architecture/high-level.md").read_text(encoding="utf-8")
                    self.assertIn("# High-level\n\nContent.\n", high_text)
                    arch_sidecar = json.loads((repo / ".docforge/provenance/docs/architecture.json").read_text(encoding="utf-8"))
                    self.assertEqual(arch_sidecar["files"]["high-level.md"]["provenance"]["schema"], SCHEMA_VERSION)
                    self.assertEqual(arch_sidecar["files"]["high-level.md"]["provenance"]["generator"]["version"], "2.0")

                    notes = docs["po_release_notes"]
                    self.assertEqual(notes["type"], "release-notes")
                    self.assertEqual(notes["status"], "generated")
                    self.assertEqual(
                        notes["selection"]["origins"],
                        [{"kind": "audience", "id": "product-owners"}],
                    )
                    self.assertEqual(notes["provenance"]["generator"]["version"], "2.0")

                    self.assertEqual(docs["setup_guide"]["status"], "planned")
                    self.assertEqual(docs["setup_guide"]["requires"], ["manifests"])

    def test_unknown_legacy_version_is_re_registered_not_hard_coded(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp) / runtime
                    repo.mkdir()
                    seed_v1_1_repo(repo)
                    manifest_path = repo / ".docforge" / "manifest.json"
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    manifest["version"] = "0.9"
                    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
                    result = run(runtime, "migrate_metadata", "--repo", str(repo), "--report")
                    self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                    report = json.loads(result.stdout)
                    self.assertIn("re-registered from 0.9", report["results"][0]["detail"])
                    out = load_manifest(repo)
                    self.assertEqual(out["version"], "3.7")
                    overview = next(doc for doc in out["documents"] if doc["id"] == "product_overview")
                    self.assertEqual(
                        overview["selection"]["origins"],
                        [{"kind": "dynamic", "id": "legacy-v0.9"}],
                    )
                    self.assertEqual(overview["provenance"]["generator"]["version"], "0.9")

    def test_v2_0_migration_parity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repos = {}
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                seed_v2_0_repo(repo)
                result = run(runtime, "migrate_metadata", "--repo", str(repo))
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                repos[runtime] = repo
            py_manifest = load_manifest(repos["py"])
            js_manifest = load_manifest(repos["js"])
            py_manifest["project"]["root"] = js_manifest["project"]["root"]
            for manifest in (py_manifest, js_manifest):
                manifest["project"]["scale"]["decided_at"] = "<TIME>"
            self.assertEqual(py_manifest, js_manifest)


class GraphProviderLockTests(unittest.TestCase):
    def test_init_leaves_graph_absent_when_nothing_ready(self) -> None:
        for runtime in ("py", "js"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                result = initialize(runtime, repo, "spine")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("No graph provider ready yet", result.stdout)
                self.assertNotIn("graph", load_manifest(repo))

    def test_init_auto_locks_the_one_ready_provider(self) -> None:
        for runtime in ("py", "js"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                (repo / ".gitnexus").mkdir()
                (repo / ".gitnexus" / "lbug").write_bytes(b"fixture")
                result = initialize(runtime, repo, "spine")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("Locked graph provider: gitnexus", result.stdout)
                graph = load_manifest(repo)["graph"]
                self.assertEqual(graph["provider"], "gitnexus")
                self.assertEqual(graph["flow"], "native")
                self.assertTrue(graph["locked_at"])

    def test_init_graph_provider_flag_overrides_registry_priority(self) -> None:
        for runtime in ("py", "js"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                (repo / ".gitnexus").mkdir()
                (repo / ".gitnexus" / "lbug").write_bytes(b"fixture")
                (repo / ".codegraph").mkdir()
                (repo / ".codegraph" / "codegraph.db").write_bytes(b"fixture")
                result = run(
                    runtime, "manage_manifest", "init", "--repo", str(repo), "--tier", "spine",
                    "--graph-provider", "codegraph",
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(load_manifest(repo)["graph"]["provider"], "codegraph")

    def test_set_graph_persists_across_status_mutation(self) -> None:
        """Regression: save_manifest() wholesale-rewrites `metadata` on every
        save; `graph` is a sibling top-level key and must survive untouched."""
        for runtime in ("py", "js"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                (repo / ".gitnexus").mkdir()
                (repo / ".gitnexus" / "lbug").write_bytes(b"fixture")
                self.assertEqual(initialize(runtime, repo, "spine").returncode, 0)
                graph_before = load_manifest(repo)["graph"]
                doc_id = load_manifest(repo)["documents"][0]["id"]
                result = run(
                    runtime, "manage_manifest", "set", "--repo", str(repo),
                    "--id", doc_id, "--status", "in_progress",
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(load_manifest(repo)["graph"], graph_before)

    def test_set_graph_self_heals_missing_graph(self) -> None:
        for runtime in ("py", "js"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                self.assertEqual(initialize(runtime, repo, "spine").returncode, 0)
                self.assertNotIn("graph", load_manifest(repo))
                (repo / ".gitnexus").mkdir()
                (repo / ".gitnexus" / "lbug").write_bytes(b"fixture")
                result = run(runtime, "manage_manifest", "set-graph", "--repo", str(repo))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(load_manifest(repo)["graph"]["provider"], "gitnexus")

    def test_set_graph_rejects_unknown_provider(self) -> None:
        for runtime in ("py", "js"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                self.assertEqual(initialize(runtime, repo, "spine").returncode, 0)
                result = run(
                    runtime, "manage_manifest", "set-graph", "--repo", str(repo),
                    "--provider", "bogus",
                )
                self.assertEqual(result.returncode, 2)
                self.assertIn("unknown graph provider", result.stderr)

    def test_set_graph_same_provider_updates_flow_keeps_locked_at(self) -> None:
        for runtime in ("py", "js"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                (repo / ".gitnexus").mkdir()
                (repo / ".gitnexus" / "lbug").write_bytes(b"fixture")
                self.assertEqual(initialize(runtime, repo, "spine").returncode, 0)
                locked_at = load_manifest(repo)["graph"]["locked_at"]
                result = run(
                    runtime, "manage_manifest", "set-graph", "--repo", str(repo),
                    "--provider", "gitnexus",
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                graph = load_manifest(repo)["graph"]
                self.assertEqual(graph["locked_at"], locked_at)
                self.assertEqual(graph["flow"], "native")

    def test_set_graph_rejects_provider_switch_without_force(self) -> None:
        for runtime in ("py", "js"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                (repo / ".gitnexus").mkdir()
                (repo / ".gitnexus" / "lbug").write_bytes(b"fixture")
                (repo / ".codegraph").mkdir()
                (repo / ".codegraph" / "codegraph.db").write_bytes(b"fixture")
                self.assertEqual(initialize(runtime, repo, "spine").returncode, 0)
                self.assertEqual(load_manifest(repo)["graph"]["provider"], "gitnexus")
                blocked = run(
                    runtime, "manage_manifest", "set-graph", "--repo", str(repo),
                    "--provider", "codegraph",
                )
                self.assertEqual(blocked.returncode, 2)
                self.assertIn("--force", blocked.stderr)
                self.assertEqual(load_manifest(repo)["graph"]["provider"], "gitnexus")
                forced = run(
                    runtime, "manage_manifest", "set-graph", "--repo", str(repo),
                    "--provider", "codegraph", "--force",
                )
                self.assertEqual(forced.returncode, 0, forced.stderr)
                self.assertEqual(load_manifest(repo)["graph"]["provider"], "codegraph")

    def test_set_graph_before_init_fails(self) -> None:
        for runtime in ("py", "js"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                result = run(runtime, "manage_manifest", "set-graph", "--repo", str(repo))
                self.assertEqual(result.returncode, 2)


class UnmanagedDocsTests(unittest.TestCase):
    """Unmanaged docs: foreign `.md` files under the docs tree that the user
    decided to keep self-managed — never tracked, never re-asked, updatable
    in place without ownership. Both runtimes share the same behavior."""

    def seed(self, repo: Path) -> None:
        (repo / "docs").mkdir()
        (repo / "docs" / "notes.md").write_text("# Notes\n", encoding="utf-8")
        (repo / "docs" / "guides").mkdir()
        (repo / "docs" / "guides" / "extra.md").write_text("# Extra\n", encoding="utf-8")
        (repo / "docs-portfolio").mkdir()
        (repo / "docs-portfolio" / "investors.md").write_text("# Investors\n", encoding="utf-8")
        (repo / "docs" / "readme.txt").write_text("not markdown", encoding="utf-8")

    def test_add_list_remove_parity_and_guards(self) -> None:
        for runtime in ("py", "js"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                self.assertEqual(initialize(runtime, repo, "spine").returncode, 0)
                self.seed(repo)
                listed = run(runtime, "manage_manifest", "unmanaged", "--repo", str(repo), "--action", "list")
                self.assertEqual(listed.returncode, 0, listed.stderr)
                self.assertIn("unmanaged  none", listed.stdout)
                outside = run(runtime, "manage_manifest", "unmanaged", "--repo", str(repo), "--action", "add", "--path", "docs/readme.txt")
                self.assertEqual(outside.returncode, 2)
                missing = run(runtime, "manage_manifest", "unmanaged", "--repo", str(repo), "--action", "add", "--path", "docs/nope.md")
                self.assertEqual(missing.returncode, 2)
                added = run(runtime, "manage_manifest", "unmanaged", "--repo", str(repo), "--action", "add", "--path", "docs/notes.md")
                self.assertEqual(added.returncode, 0, added.stderr)
                self.assertIn("self-managed", added.stdout)
                manifest = load_manifest(repo)
                entries = manifest["project"]["unmanaged_docs"]
                self.assertEqual([entry["path"] for entry in entries], ["docs/notes.md"])
                self.assertEqual(len(entries[0]["decided_at"]), 25)
                dup = run(runtime, "manage_manifest", "unmanaged", "--repo", str(repo), "--action", "add", "--path", "docs/notes.md")
                self.assertEqual(dup.returncode, 0, dup.stderr)
                self.assertIn("already self-managed", dup.stdout)
                self.assertEqual(len(load_manifest(repo)["project"]["unmanaged_docs"]), 1)
                listed = run(runtime, "manage_manifest", "unmanaged", "--repo", str(repo), "--action", "list")
                self.assertIn("docs/notes.md", listed.stdout)
                removed = run(runtime, "manage_manifest", "unmanaged", "--repo", str(repo), "--action", "remove", "--path", "docs/notes.md")
                self.assertEqual(removed.returncode, 0, removed.stderr)
                self.assertEqual(load_manifest(repo)["project"]["unmanaged_docs"], [])
                self.assertTrue((repo / "docs" / "notes.md").is_file())

    def test_unmanaged_rejects_tracked_document(self) -> None:
        for runtime in ("py", "js"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                self.assertEqual(initialize(runtime, repo, "spine").returncode, 0)
                (repo / "docs").mkdir()
                (repo / "docs" / "README.md").write_text("# R\n", encoding="utf-8")
                result = run(runtime, "manage_manifest", "unmanaged", "--repo", str(repo), "--action", "add", "--path", "docs/README.md")
                self.assertEqual(result.returncode, 2)
                self.assertIn("tracked manifest document", result.stderr)

    def test_archive_moves_file_and_records_target(self) -> None:
        for runtime in ("py", "js"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                self.assertEqual(initialize(runtime, repo, "spine").returncode, 0)
                self.seed(repo)
                preview = run(runtime, "manage_manifest", "unmanaged", "--repo", str(repo), "--action", "archive", "--path", "docs/notes.md", "--dry-run")
                self.assertEqual(preview.returncode, 0, preview.stderr)
                self.assertIn("DRY RUN", preview.stdout)
                self.assertTrue((repo / "docs" / "notes.md").is_file())
                archived = run(runtime, "manage_manifest", "unmanaged", "--repo", str(repo), "--action", "archive", "--path", "docs/notes.md")
                self.assertEqual(archived.returncode, 0, archived.stderr)
                year = str(datetime.now(timezone.utc).year)
                self.assertFalse((repo / "docs" / "notes.md").exists())
                self.assertTrue((repo / "docs" / "_archive" / year / "notes.md").is_file())
                self.assertIn(f"docs/_archive/{year}/notes.md", archived.stdout)
                entries = load_manifest(repo)["project"]["unmanaged_docs"]
                self.assertEqual([entry["path"] for entry in entries], [f"docs/_archive/{year}/notes.md"])
                portfolio = run(runtime, "manage_manifest", "unmanaged", "--repo", str(repo), "--action", "archive", "--path", "docs-portfolio/investors.md")
                self.assertEqual(portfolio.returncode, 0, portfolio.stderr)
                self.assertTrue((repo / "docs-portfolio" / "_archive" / year / "investors.md").is_file())

    def test_unmanaged_never_flag_untracked_in_scan_or_audit(self) -> None:
        for runtime in ("py", "js"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                self.assertEqual(initialize(runtime, repo, "spine").returncode, 0)
                self.seed(repo)
                (repo / "docs" / "_archive").mkdir()
                (repo / "docs" / "_archive" / "old.md").write_text("# Old\n", encoding="utf-8")
                added = run(runtime, "manage_manifest", "unmanaged", "--repo", str(repo), "--action", "add", "--path", "docs/notes.md")
                self.assertEqual(added.returncode, 0, added.stderr)
                scan = run(runtime, "dashboard", "scan", "--repo", str(repo), "--json")
                self.assertEqual(scan.returncode, 1, scan.stderr)
                scan_result = json.loads(scan.stdout)
                untracked = [p["detail"] for p in scan_result["problems"] if p["kind"] == "untracked"]
                self.assertNotIn("docs/notes.md", untracked)
                self.assertNotIn("docs/_archive/old.md", untracked)
                self.assertNotIn("docs/guides/extra.md", scan_result["unmanaged"])
                self.assertIn("docs/notes.md", scan_result["unmanaged"])
                audit = run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(repo / ".docforge" / "manifest.json"), "--audit")
                self.assertEqual(audit.returncode, 1, audit.stderr)
                self.assertNotIn("docs/notes.md", audit.stdout)
                self.assertIn("docs/guides/extra.md", audit.stdout)

    def test_migrate_3_3_seeds_unmanaged_docs(self) -> None:
        for runtime in ("py", "js"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                self.assertEqual(initialize(runtime, repo, "spine").returncode, 0)
                manifest_path = repo / ".docforge" / "manifest.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["version"] = "3.3"
                del manifest["project"]["unmanaged_docs"]
                manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
                migrated = run(runtime, "migrate_metadata", "--repo", str(repo))
                # Exit 1 comes from MISSING planned-doc files in a bare repo;
                # the migration itself must not fail.
                self.assertIn(migrated.returncode, (0, 1), migrated.stderr)
                self.assertNotIn("FAILED", migrated.stdout)
                reloaded = load_manifest(repo)
                self.assertEqual(reloaded["version"], "3.7")
                self.assertEqual(reloaded["project"]["unmanaged_docs"], [])
                # Second run is a clean no-op apart from the same MISSING files.
                again = run(runtime, "migrate_metadata", "--repo", str(repo))
                self.assertNotIn("FAILED", again.stdout)

    def test_unmanaged_update_keeps_file_untracked(self) -> None:
        """Updating an unmanaged doc in place never adds a manifest entry and
        never stamps provenance — the file stays self-managed."""
        for runtime in ("py", "js"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                self.assertEqual(initialize(runtime, repo, "spine").returncode, 0)
                self.seed(repo)
                added = run(runtime, "manage_manifest", "unmanaged", "--repo", str(repo), "--action", "add", "--path", "docs/notes.md")
                self.assertEqual(added.returncode, 0, added.stderr)
                (repo / "docs" / "notes.md").write_text("# Notes updated\n", encoding="utf-8")
                manifest = load_manifest(repo)
                self.assertNotIn("docs/notes.md", {doc["path"] for doc in manifest["documents"]})
                scan = run(runtime, "dashboard", "scan", "--repo", str(repo), "--json")
                self.assertEqual(scan.returncode, 1, scan.stderr)
                result = json.loads(scan.stdout)
                self.assertIn("docs/notes.md", result["unmanaged"])
                self.assertNotIn("docs/notes.md", [p["detail"] for p in result["problems"] if p["kind"] == "untracked"])


class PreviewTests(unittest.TestCase):
    """`preview` sizes a scope for intake's confirmation summary. It runs
    inside intake's no-side-effect boundary, so writing anything at all is a
    defect, not just writing a manifest."""

    SCOPE = [
        "--shape", "library-sdk", "--platform", "container", "--framework", "kafka",
        "--concern", "observability", "--concern", "authentication",
        "--concern", "background-processing",
        "--audience", "engineers", "--audience", "beginners", "--audience", "coding-agents",
    ]

    def test_preview_writes_nothing(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    (repo / "src").mkdir()
                    (repo / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
                    before = sorted(p.relative_to(repo).as_posix() for p in repo.rglob("*"))
                    result = run(runtime, "manage_manifest", "preview", "--repo", str(repo),
                                 "--tier", "diligence", *self.SCOPE)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    after = sorted(p.relative_to(repo).as_posix() for p in repo.rglob("*"))
                    self.assertEqual(before, after)
                    self.assertFalse((repo / ".docforge").exists())

    def test_preview_reports_both_layouts_and_attributes_the_count(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    (repo / "src").mkdir()
                    (repo / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
                    result = run(runtime, "manage_manifest", "preview", "--repo", str(repo),
                                 "--tier", "diligence", "--layout", "compact", "--json", *self.SCOPE)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    report = json.loads(result.stdout)
                    self.assertLess(report["compact_count"], report["standard_count"])
                    self.assertEqual(report["count"], report["compact_count"])
                    cost = {(item["dimension"], item["value"]): item["documents"]
                            for item in report["attribution"]}
                    # These shift narrative emphasis only; they select no documents.
                    for free in (("platforms", "container"), ("frameworks", "kafka"),
                                 ("concerns", "authentication"), ("concerns", "background-processing"),
                                 ("concerns", "observability")):
                        self.assertEqual(cost[free], 0, free)
                    # The audience is the expensive pick, and the whole point of
                    # showing this before the user confirms.
                    self.assertGreater(cost[("audiences", "coding-agents")], 0)

    def test_preview_reports_the_constraint_instead_of_a_compact_count_at_portfolio(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    (repo / "src").mkdir()
                    (repo / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
                    result = run(runtime, "manage_manifest", "preview", "--repo", str(repo),
                                 "--tier", "portfolio", "--json")
                    self.assertEqual(result.returncode, 0, result.stderr)
                    report = json.loads(result.stdout)
                    self.assertIsNone(report["compact_count"])
                    self.assertIn("portfolio tier requires standard layout",
                                  report["compact_unavailable"])
                    self.assertEqual(report["layout"], "standard")


class PortfolioLayoutMigrationTests(unittest.TestCase):
    def test_migrate_forces_a_portfolio_manifest_off_compact(self) -> None:
        """A manifest written before compact was restricted (or hand-edited)
        would otherwise keep generating a folded portfolio layer."""
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    (repo / "src").mkdir()
                    (repo / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
                    self.assertEqual(
                        run(runtime, "manage_manifest", "init", "--repo", str(repo),
                            "--tier", "portfolio").returncode, 0)
                    manifest_path = repo / ".docforge" / "manifest.json"
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    manifest["project"]["scale"]["layout"] = "compact"
                    manifest["project"]["scale"]["decided_by"] = "user"
                    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
                    # migrate exits 1 on the unmaterialized plan; the manifest
                    # upgrade itself still lands, which is what is under test.
                    run(runtime, "migrate_metadata", "--repo", str(repo),
                        "--manifest", str(manifest_path))
                    scale = json.loads(manifest_path.read_text(encoding="utf-8"))["project"]["scale"]
                    self.assertEqual(scale["layout"], "standard")
                    self.assertEqual(scale["decided_by"], "tier-constraint")

    def test_migrate_leaves_a_diligence_compact_manifest_alone(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    (repo / "src").mkdir()
                    (repo / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
                    self.assertEqual(
                        run(runtime, "manage_manifest", "init", "--repo", str(repo),
                            "--tier", "diligence", "--layout", "compact").returncode, 0)
                    manifest_path = repo / ".docforge" / "manifest.json"
                    run(runtime, "migrate_metadata", "--repo", str(repo),
                        "--manifest", str(manifest_path))
                    scale = json.loads(manifest_path.read_text(encoding="utf-8"))["project"]["scale"]
                    self.assertEqual(scale["layout"], "compact")
                    self.assertEqual(scale["decided_by"], "user")


if __name__ == "__main__":
    unittest.main()
