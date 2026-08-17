"""Historical one-shot migrations: Python/Node parity.

`split_catalog` and `split_document_catalog` are the only historical tools
that were Python-only; both now ship Node peers and are exercised on both
runtimes against a synthetic skill root (`--root`) so the real metadata tree
is never touched.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _support import (
    blob_hash,
    initialize,
    load_manifest,
    normalized,
    provenance,
    run,
    write_written_doc,
)

DOC_CATALOG_SOURCE = """# Document catalog

| Type | Must present | Keep out | Primary mode | Depth |
|---|---|---|---|---|
| docs-index / folder-index | What the area owns, start-here paths | Child facts, invented lore | Explanation | orientation |
| architecture-high-level | System overview, boundaries | Implementation details | Explanation | deep-dive |
| runbook | Steps in order, rollback | Rationale, prose | Procedure | reference |
| release-notes | What changed per release, impact | Speculation, internal chatter | Reference | overview |

## Risk-register routing

Tail risk documentation routes to the risk register.
"""


def seed_skill_root(root: Path) -> None:
    metadata = root / ".metadata"
    metadata.mkdir(parents=True)
    shapes = [
        {"id": "infrastructure-platform", "order": 10, "signals": [], "aliases": ["infra"]},
        {"id": "api-service", "order": 20, "signals": [], "aliases": []},
    ]
    catalog = {
        "$schema": "catalog-schema.json",
        "version": "2.19.0",
        "tiers": [{"id": "spine", "order": 10}, {"id": "diligence", "order": 20}],
        "profiles": {
            "shapes": shapes,
            "platforms": [{"id": "browser", "order": 1, "signals": [], "aliases": []}],
            "frameworks": [{"id": "react", "order": 1, "signals": [], "aliases": []}],
            "concerns": [{"id": "privacy", "order": 1, "signals": [], "aliases": []}],
            "audiences": [{"id": "engineers", "order": 1, "signals": [], "aliases": []}],
        },
        "groups": ["root", "architecture"],
        "capabilities": ["code_graph"],
        "cue_hints": [],
        "documents": [
            {
                "id": "arch_high_level",
                "type": "architecture-high-level",
                "path": "docs/architecture/high-level.md",
                "selection": {"min_tier": "spine", "origins": [], "evidence": []},
            },
            {
                "id": "runbook_deploy",
                "type": "runbook",
                "path": "docs/operations/runbooks/deploy.md",
                "selection": {"min_tier": "diligence", "origins": [], "evidence": []},
            },
        ],
    }
    (metadata / "catalog.json").write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    references = root / "references"
    references.mkdir(parents=True)
    (references / "document-catalog.md").write_text(DOC_CATALOG_SOURCE, encoding="utf-8")


class SplitCatalogParityTests(unittest.TestCase):
    def _run(self, runtime: str, root: Path, *args: str):
        return run(runtime, "split_catalog", "--root", str(root), *args)

    def test_dry_run_parity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            py_root, js_root = Path(tmp) / "py", Path(tmp) / "js"
            for root in (py_root, js_root):
                root.mkdir()
                seed_skill_root(root)
            py_result = self._run("py", py_root, "--dry-run")
            js_result = self._run("js", js_root, "--dry-run")
            self.assertEqual(py_result.returncode, 0, py_result.stderr)
            self.assertEqual(js_result.returncode, 0, js_result.stderr)
            self.assertEqual(py_result.stdout, js_result.stdout)
            summary = json.loads(py_result.stdout)
            self.assertEqual(summary["version"], "2.19.0")
            self.assertEqual(summary["document_types"], 2)
            self.assertEqual(summary["infra_signals"], 9)
            self.assertEqual(summary["infra_aliases"], ["infra", "deployment-config", "iac"])
            # Dry run writes nothing.
            self.assertFalse((py_root / ".metadata" / "catalog" / "index.json").exists())

    def test_split_trees_are_byte_identical_and_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            py_root, js_root = Path(tmp) / "py", Path(tmp) / "js"
            for root in (py_root, js_root):
                root.mkdir()
                seed_skill_root(root)
            for runtime, root in (("py", py_root), ("js", js_root)):
                result = self._run(runtime, root)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"Wrote .metadata/catalog/index.json + 2 types + 5 profile files (version 2.19.0).", result.stdout)
            for runtime, root in (("py", py_root), ("js", js_root)):
                index = json.loads((root / ".metadata" / "catalog" / "index.json").read_text(encoding="utf-8"))
                self.assertEqual(index["version"], "2.19.0")
                self.assertEqual(index["tiers"], {"spine": {"order": 10}, "diligence": {"order": 20}})
                self.assertEqual(
                    [row["id"] for row in index["document_types"]],
                    ["arch_high_level", "runbook_deploy"],
                )
                infra = json.loads((root / ".metadata" / "catalog" / "profiles" / "shapes.json").read_text(encoding="utf-8"))
                infra_profile = next(item for item in infra if item["id"] == "infrastructure-platform")
                self.assertEqual(infra_profile["aliases"], ["infra", "deployment-config", "iac"])
                self.assertEqual(len(infra_profile["signals"]), 9)
            # Byte-identical split trees across runtimes.
            rel_files = [
                ".metadata/catalog/index.json",
                ".metadata/catalog/types/arch_high_level.json",
                ".metadata/catalog/types/runbook_deploy.json",
                *[f".metadata/catalog/profiles/{d}.json" for d in ("shapes", "platforms", "frameworks", "concerns", "audiences")],
            ]
            for rel in rel_files:
                self.assertEqual(
                    (py_root / rel).read_text(encoding="utf-8"),
                    (js_root / rel).read_text(encoding="utf-8"),
                    rel,
                )
            # Round-trip: drop the monolith and re-run; the split tree is the source.
            for runtime, root in (("py", py_root), ("js", js_root)):
                (root / ".metadata" / "catalog.json").unlink()
                again = self._run(runtime, root)
                self.assertEqual(again.returncode, 0, again.stderr)
                self.assertIn("Wrote .metadata/catalog/index.json + 2 types + 5 profile files (version 2.19.0).", again.stdout)
            for rel in rel_files:
                self.assertEqual(
                    (py_root / rel).read_text(encoding="utf-8"),
                    (js_root / rel).read_text(encoding="utf-8"),
                    f"round-trip {rel}",
                )

    def test_missing_catalog_errors_on_both_runtimes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                root = Path(tmp) / runtime
                root.mkdir()
                result = self._run(runtime, root)
                self.assertEqual(result.returncode, 1)
                self.assertIn("neither", result.stderr)


class SplitDocumentCatalogParityTests(unittest.TestCase):
    def _run(self, runtime: str, root: Path, *args: str):
        return run(runtime, "split_document_catalog", "--root", str(root), *args)

    def test_dry_run_and_write_parity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            py_root, js_root = Path(tmp) / "py", Path(tmp) / "js"
            for root in (py_root, js_root):
                root.mkdir()
                seed_skill_root(root)
            for runtime, root in (("py", py_root), ("js", js_root)):
                dry = self._run(runtime, root, "--dry-run")
                self.assertEqual(dry.returncode, 0, dry.stderr)
                self.assertIn("would write 5 contract files + README.md", dry.stdout)
                for name in ("architecture-high-level", "docs-index", "folder-index", "release-notes", "runbook"):
                    self.assertIn(f"  {name}.md", dry.stdout)
                self.assertFalse((root / "references" / "catalog-contracts").exists())
            for runtime, root in (("py", py_root), ("js", js_root)):
                result = self._run(runtime, root)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("Wrote 5 contracts under references/catalog-contracts/", result.stdout)
            rel_files = [
                "references/catalog-contracts/README.md",
                "references/document-catalog.md",
                *[f"references/catalog-contracts/{name}.md" for name in
                  ("architecture-high-level", "docs-index", "folder-index", "release-notes", "runbook")],
            ]
            for rel in rel_files:
                self.assertEqual(
                    (py_root / rel).read_text(encoding="utf-8"),
                    (js_root / rel).read_text(encoding="utf-8"),
                    rel,
                )
            readme = (py_root / "references/catalog-contracts/README.md").read_text(encoding="utf-8")
            self.assertIn("## Risk-register routing", readme)
            aliased = (py_root / "references/catalog-contracts/docs-index.md").read_text(encoding="utf-8")
            self.assertIn("Aliased with: `folder-index`", aliased)
            stub = (py_root / "references/document-catalog.md").read_text(encoding="utf-8")
            self.assertIn("has been split for context efficiency", stub)

    def test_missing_source_errors_on_both_runtimes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                root = Path(tmp) / runtime
                root.mkdir()
                result = self._run(runtime, root)
                self.assertEqual(result.returncode, 1)
                self.assertIn("missing", result.stderr)


class Manifest39MigrationParityTests(unittest.TestCase):
    CANONICAL_PRESENTATION = {
        "primary_audience": "coding-agents",
        "code": "task-focused",
        "related_docs": "none",
        "repository_paths": "actionable-only",
        "source_evidence": "provenance-only",
    }
    OLD_PRESENTATION = {
        **CANONICAL_PRESENTATION,
        "related_docs": "traceability",
    }
    AGENT_AUDIT = {
        "mode": "cold-pass",
        "verdict": "PASS",
        "timestamp": "2026-08-01T00:00:00+00:00",
        "report_path": ".docforge/audits/agents_compact.md",
    }
    INDEX_AUDIT = {
        "mode": "cold-pass",
        "verdict": "PASS",
        "timestamp": "2026-08-02T00:00:00+00:00",
        "report_path": ".docforge/audits/agents_index.md",
    }

    def _semantic_report(self, report: dict, repo: Path) -> dict:
        """Normalize only the repo prefix so payload semantics can be compared.

        The raw manifest label is asserted separately: both runtimes should
        expose the same repository-relative path to callers.
        """
        copied = json.loads(json.dumps(report))
        prefix = f"{repo}/"
        for item in copied["results"]:
            if item["doc"].startswith(prefix):
                item["doc"] = item["doc"][len(prefix):]
        return copied

    def _seed_38_fixture(self, runtime: str, repo: Path) -> tuple[str, str]:
        result = initialize(
            runtime, repo, "spine",
            audiences=("coding-agents",), groups=("agents",), layout="compact",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest_path = repo / ".docforge" / "manifest.json"
        manifest = load_manifest(repo)
        compact = next(
            doc for doc in manifest["documents"] if doc["id"] == "agents_compact"
        )
        manifest["version"] = "3.8"
        manifest["project"]["agent_context"] = {
            "mode": "linked",
            "decided_by": "derived",
            "decided_at": "2026-08-01T00:00:00+00:00",
        }
        self.assertEqual(manifest["project"]["groups"], ["agent-context"])

        source = repo / "source.txt"
        source.write_text("migration evidence\n", encoding="utf-8")
        source_hash = blob_hash(source.read_bytes())
        compact.update({
            "status": "complete",
            "audit": dict(self.AGENT_AUDIT),
            # These are the historical linked-mode pointers. The files keep
            # their names in 3.9, but their contract is now permanently
            # self-contained, so every written agent document is re-grounded.
            "scaffold_template": "content/compact/templates/agents.template.md",
            "instruction_file": "content/compact/instructions/agents.md",
            "requires": ["code_graph", "flow_graph"],
            "target_depth": "orientation",
            "contract_revision": "2.19.0",
            "presentation": dict(self.OLD_PRESENTATION),
            "presentation_override": {"related_docs": "traceability"},
            "compact_members": ["agents_index", *compact["compact_members"]],
            "provenance": provenance(
                doc_id="agents_compact",
                path="docs/agents.md",
                tier="spine",
                target_depth="orientation",
                section_id="coding-agent-views",
                source_path="source.txt",
                source_blob=source_hash,
            ),
        })
        agents_index = {
            "id": "agents_index",
            "title": "Coding-agent views",
            "description": "Historical coding-agent views index.",
            "type": "folder-index",
            "path": "docs/agents/README.md",
            "group": "agent-context",
            "selection": {
                "origins": [{"kind": "audience", "id": "coding-agents"}],
                "evidence": [],
            },
            "status": "complete",
            "requires": [],
            "scaffold_template": "content/shared/section-readme.template.md",
            "instruction_file": "content/shared/folder-index.instruction.md",
            "target_depth": "orientation",
            "write_order": 204,
            "nav_order": 80,
            "provenance_mode": "sections",
            "audit_profile": "router",
            "contract_revision": "2.19.0",
            "presentation": dict(self.OLD_PRESENTATION),
            "provenance": provenance(
                doc_id="agents_index",
                path="docs/agents/README.md",
                tier="spine",
                target_depth="orientation",
                section_id="coding-agent-views",
                source_path="source.txt",
                source_blob=source_hash,
            ),
            "audit": dict(self.INDEX_AUDIT),
        }
        manifest["documents"] = [compact, agents_index]
        manifest["metadata"] = {
            "total_documents": 2,
            "planned": 0,
            "in_progress": 0,
            "generated": 0,
            "needs_review": 0,
            "complete": 2,
            "skipped": 0,
            "retired": 0,
            "last_updated": "2026-08-02T00:00:00+00:00",
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        compact_body = "# Coding-agent views\n\nHistorical compact body.\n"
        index_body = "# Coding-agent views\n\nHistorical index body.\n"
        write_written_doc(repo, compact, compact_body)
        write_written_doc(repo, agents_index, index_body)
        return compact_body, index_body

    def test_3_8_to_3_9_retires_modes_and_preserves_index_for_reconcile(self) -> None:
        reports = []
        manifest_labels = []
        snapshots = []
        reconcile_outputs = []
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                with self.subTest(runtime=runtime):
                    repo = Path(tmp) / runtime
                    repo.mkdir()
                    compact_body, index_body = self._seed_38_fixture(runtime, repo)
                    result = run(
                        runtime, "migrate_metadata", "--repo", str(repo), "--report",
                    )
                    self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                    report = json.loads(result.stdout)
                    reports.append(self._semantic_report(report, repo))
                    manifest_report = report["results"][0]
                    manifest_labels.append(manifest_report["doc"])
                    self.assertTrue(
                        manifest_report["doc"].endswith(".docforge/manifest.json"),
                        manifest_report,
                    )
                    self.assertIn(
                        "retained as retirement candidate without touching its body: agents_index",
                        manifest_report["detail"],
                    )

                    manifest = load_manifest(repo)
                    self.assertEqual(manifest["version"], "3.9")
                    self.assertNotIn("agent_context", manifest["project"])
                    self.assertEqual(manifest["project"]["groups"], ["agent-context"])
                    by_id = {doc["id"]: doc for doc in manifest["documents"]}
                    retained = by_id["agents_compact"]
                    self.assertEqual(retained["status"], "in_progress")
                    self.assertIsNone(retained["audit"])
                    self.assertEqual(
                        retained["scaffold_template"],
                        "content/compact/templates/agents.template.md",
                    )
                    self.assertEqual(
                        retained["instruction_file"],
                        "content/compact/instructions/agents.md",
                    )
                    self.assertEqual(retained["requires"], [])
                    self.assertEqual(retained["presentation"], self.CANONICAL_PRESENTATION)
                    self.assertNotIn("presentation_override", retained)
                    self.assertNotIn("agents_index", retained["compact_members"])
                    self.assertEqual(
                        (repo / "docs" / "agents.md").read_text(encoding="utf-8"),
                        compact_body,
                    )

                    retired_candidate = by_id["agents_index"]
                    self.assertEqual(retired_candidate["status"], "complete")
                    self.assertEqual(retired_candidate["audit"], self.INDEX_AUDIT)
                    index_path = repo / "docs" / "agents" / "README.md"
                    self.assertTrue(index_path.is_file())
                    self.assertEqual(index_path.read_text(encoding="utf-8"), index_body)
                    snapshots.append({
                        "version": manifest["version"],
                        "groups": manifest["project"]["groups"],
                        "retained": {
                            field: retained.get(field)
                            for field in (
                                "status", "audit", "scaffold_template",
                                "instruction_file", "requires", "presentation",
                                "compact_members",
                            )
                        },
                        "index": {
                            field: retired_candidate.get(field)
                            for field in ("status", "audit", "path")
                        },
                    })

                    reconcile = run(
                        runtime, "manage_manifest", "reconcile", "--repo", str(repo),
                    )
                    self.assertEqual(
                        reconcile.returncode, 0, reconcile.stderr + reconcile.stdout,
                    )
                    self.assertIn("retire: agents_index", reconcile.stdout)
                    self.assertNotIn("agent-mode", reconcile.stdout + reconcile.stderr)
                    reconciled = load_manifest(repo)
                    self.assertNotIn("agent_context", reconciled["project"])
                    self.assertEqual(reconciled["project"]["groups"], ["agent-context"])
                    reconciled_index = next(
                        doc for doc in reconciled["documents"]
                        if doc["id"] == "agents_index"
                    )
                    self.assertEqual(reconciled_index["status"], "complete")
                    self.assertEqual(reconciled_index["audit"], self.INDEX_AUDIT)
                    self.assertEqual(index_path.read_text(encoding="utf-8"), index_body)
                    reconcile_outputs.append(normalized(reconcile.stdout, [repo]))

        self.assertEqual(reports[0], reports[1])
        self.assertEqual(snapshots[0], snapshots[1])
        self.assertEqual(reconcile_outputs[0], reconcile_outputs[1])
        self.assertEqual(
            manifest_labels,
            [".docforge/manifest.json", ".docforge/manifest.json"],
            "migration reports must use the same repository-relative manifest label",
        )

    def test_3_7_upgrades_directly_to_3_9_with_runtime_parity(self) -> None:
        reports = []
        snapshots = []
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                with self.subTest(runtime=runtime):
                    repo = Path(tmp) / runtime
                    repo.mkdir()
                    result = initialize(
                        runtime, repo, "spine",
                        audiences=("coding-agents",), groups=("agents",),
                        layout="standard",
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    manifest_path = repo / ".docforge" / "manifest.json"
                    manifest = load_manifest(repo)
                    manifest["version"] = "3.7"
                    manifest["documents"] = [
                        next(
                            doc for doc in manifest["documents"]
                            if doc["id"] == "agents_kernel"
                        )
                    ]
                    manifest["project"].pop("agent_context", None)
                    scale_before = {
                        field: manifest["project"]["scale"][field]
                        for field in ("class", "layout", "decided_by")
                    }
                    manifest["project"]["scale"]["signals"] = {
                        "tracked_files": 1,
                        "source_files": 1,
                        "confirmed_profiles": 1,
                    }
                    profiles_before = manifest["project"]["profiles"]
                    groups_before = manifest["project"]["groups"]
                    manifest_path.write_text(
                        json.dumps(manifest, indent=2) + "\n", encoding="utf-8",
                    )

                    migrated = run(
                        runtime, "migrate_metadata", "--repo", str(repo), "--report",
                    )
                    self.assertEqual(
                        migrated.returncode, 0, migrated.stderr + migrated.stdout,
                    )
                    reports.append(self._semantic_report(json.loads(migrated.stdout), repo))
                    current = load_manifest(repo)
                    self.assertEqual(current["version"], "3.9")
                    self.assertNotIn("agent_context", current["project"])
                    self.assertEqual(current["project"]["profiles"], profiles_before)
                    self.assertEqual(current["project"]["groups"], groups_before)
                    self.assertEqual(
                        {
                            field: current["project"]["scale"][field]
                            for field in ("class", "layout", "decided_by")
                        },
                        scale_before,
                    )
                    self.assertTrue({"declared_dependencies", "flow_candidates"} <= set(
                        current["project"]["scale"]["signals"]
                    ))
                    snapshots.append({
                        "version": current["version"],
                        "profiles": current["project"]["profiles"],
                        "groups": current["project"]["groups"],
                        "scale": {
                            field: current["project"]["scale"][field]
                            for field in ("class", "layout", "decided_by", "signals")
                        },
                    })

        self.assertEqual(reports[0], reports[1])
        self.assertEqual(snapshots[0], snapshots[1])


if __name__ == "__main__":
    raise SystemExit(unittest.main())
