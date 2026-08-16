"""Catalog record integrity: every id resolves its record, contract, template,
and optional instruction, with a summary under the 160-character budget."""

from __future__ import annotations

import json
import unittest

from _support import ROOT, run

SKILL_ROOT = ROOT / "skills" / "docforge" / "_shared"
CATALOG_DIR = SKILL_ROOT / ".metadata" / "catalog"


class CatalogRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = json.loads((CATALOG_DIR / "index.json").read_text(encoding="utf-8"))
        cls.tiers = set(cls.index["tiers"])
        cls.groups = set(cls.index["groups"])

    def test_catalog_version_is_current(self) -> None:
        self.assertEqual(self.index["version"], "2.19.0")

    def test_document_type_count_and_unique_ids(self) -> None:
        document_types = self.index["document_types"]
        # 137, +5 for the compact groups that make the compact tree bounded:
        # flows_compact, decisions_compact, concepts_compact, ba_compact,
        # po_compact.
        self.assertEqual(len(document_types), 142)
        ids = [entry["id"] for entry in document_types]
        self.assertEqual(len(ids), len(set(ids)), "duplicate document ids in index.json")

    def test_every_readme_record_has_title_summary_and_contract_revision(self) -> None:
        readme_paths = {
            "README.md",
            "docs/README.md",
            "docs/architecture/README.md",
            "docs/architecture/concepts/README.md",
            "docs/architecture/contracts/README.md",
            "docs/architecture/decisions/README.md",
            "docs/product/README.md",
            "docs/product/migrations/README.md",
            "docs/product/business-analyst/README.md",
            "docs/product/product-owner/README.md",
            "docs/flows/README.md",
            "docs/engineering/README.md",
            "docs/operations/README.md",
            "docs/operations/runbooks/README.md",
            "docs/reference/README.md",
            "docs/security/README.md",
            "docs/contributing/README.md",
            "docs/agents/README.md",
            "docs-portfolio/README.md",
            "docs-portfolio/decisions/README.md",
            "docs-portfolio/epics/README.md",
        }
        matched = {
            entry["path"] for entry in self.index["document_types"] if entry["path"] in readme_paths
        }
        self.assertEqual(matched, readme_paths, "declared README paths must all be cataloged")
        for entry in self.index["document_types"]:
            if entry["path"] not in readme_paths:
                continue
            with self.subTest(path=entry["path"]):
                detail = json.loads((CATALOG_DIR / entry["record"]).read_text(encoding="utf-8"))
                self.assertTrue(detail.get("title"), f"{entry['id']}: title must be non-empty")
                self.assertLessEqual(len(detail["title"]), 80)
                self.assertTrue(
                    detail.get("contract_revision"),
                    f"{entry['id']}: contract_revision must be set",
                )
                self.assertTrue(
                    detail["template_file"].startswith("content/"),
                    f"{entry['id']}: template must live in content/",
                )

    def test_profiles_path_map_resolves(self) -> None:
        for dimension, rel in self.index["profiles"].items():
            with self.subTest(dimension=dimension):
                self.assertTrue((CATALOG_DIR / rel).is_file(), rel)

    def test_every_record_path_resolves(self) -> None:
        for entry in self.index["document_types"]:
            with self.subTest(id=entry["id"]):
                self.assertIn(entry["tier"], self.tiers)
                self.assertTrue(entry["path"], "path must be non-empty")
                self.assertIn("record", entry)
                record_path = CATALOG_DIR / entry["record"]
                self.assertTrue(record_path.is_file(), f"missing record for {entry['id']}")
                detail = json.loads(record_path.read_text(encoding="utf-8"))
                self.assertEqual(detail["id"], entry["id"])
                self.assertIn(detail["group"], self.groups, entry["id"])

    def test_every_summary_contract_and_template_resolve(self) -> None:
        for entry in self.index["document_types"]:
            detail = json.loads((CATALOG_DIR / entry["record"]).read_text(encoding="utf-8"))
            with self.subTest(id=entry["id"]):
                summary = detail.get("summary")
                self.assertTrue(summary, f"{entry['id']}: summary must be non-empty")
                self.assertLessEqual(len(summary), 160, f"{entry['id']}: summary exceeds 160 chars")

                contract = detail.get("contract_file")
                self.assertTrue(contract, f"{entry['id']}: contract_file is mandatory")
                self.assertTrue((SKILL_ROOT / contract).is_file(), f"{entry['id']}: missing {contract}")

                template = detail.get("template_file")
                self.assertTrue(template, f"{entry['id']}: template_file is mandatory")
                self.assertTrue((SKILL_ROOT / template).is_file(), f"{entry['id']}: missing {template}")

                instruction = detail.get("instruction_file")
                if instruction is not None:
                    self.assertTrue(
                        (SKILL_ROOT / instruction).is_file(),
                        f"{entry['id']}: missing instruction {instruction}",
                    )

                # scaffold_template was renamed to template_file; the old key
                # must not linger in a migrated record.
                self.assertNotIn("scaffold_template", detail, entry["id"])

    def test_portfolio_documents_never_require_a_code_graph(self) -> None:
        """references/portfolio.md: 'Docforge never builds or requires a
        graph spanning repositories.' Every docs-portfolio/* record's craft
        resolves cross-repo evidence from member manifests/flow-index files,
        never a code_graph capability."""
        for entry in self.index["document_types"]:
            if entry["path"].split("/")[0] != "docs-portfolio":
                continue
            detail = json.loads((CATALOG_DIR / entry["record"]).read_text(encoding="utf-8"))
            with self.subTest(id=entry["id"]):
                self.assertNotIn("code_graph", detail.get("requires", []))

    def test_five_corrected_portfolio_records_keep_only_evidenced_capabilities(self) -> None:
        expected = {
            "portfolio_system_context": ["manifests"],
            "portfolio_glossary": ["manifests"],
            "portfolio_security": ["manifests"],
            "portfolio_operations": ["manifests"],
            "portfolio_readme": ["git_history"],
        }
        by_id = {entry["id"]: entry for entry in self.index["document_types"]}
        for doc_id, requires in expected.items():
            detail = json.loads((CATALOG_DIR / by_id[doc_id]["record"]).read_text(encoding="utf-8"))
            with self.subTest(id=doc_id):
                self.assertEqual(detail["requires"], requires)

    def test_query_catalog_validate_passes_on_both_runtimes(self) -> None:
        for runtime in ("py", "js"):
            result = run(runtime, "query_catalog", "--validate")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_query_catalog_validate_enforces_compact_core_cap(self) -> None:
        """The core cap counts only tier-driven members — no selector, no
        condition — because those are the ones the catalog can see. Profile-
        driven members depend on a project's confirmed profiles, so they are
        bounded at plan time by COMPACT_SECTION_CAP instead."""
        record_path = CATALOG_DIR / "documents" / "architecture" / "architecture_compact.json"
        original = record_path.read_text(encoding="utf-8")
        try:
            record = json.loads(original)
            # Real ungated records, so they count as core members.
            record["compact_members"] = record["compact_members"] + [
                "root_readme", "changelog", "docs_index",
            ]
            record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
            for runtime in ("py", "js"):
                with self.subTest(runtime=runtime):
                    result = run(runtime, "query_catalog", "--validate")
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("depth brake", result.stdout + result.stderr)
        finally:
            record_path.write_text(original, encoding="utf-8")

    def test_profile_driven_members_do_not_count_against_the_core_cap(self) -> None:
        """`architecture_compact` declares far more than eight members today —
        21 of them profile-driven. The catalog must still validate, or the
        bounded compact tree could not exist."""
        record = json.loads(
            (CATALOG_DIR / "documents" / "architecture" / "architecture_compact.json")
            .read_text(encoding="utf-8")
        )
        self.assertGreater(len(record["compact_members"]), 8)
        core = []
        for member_id in record["compact_members"]:
            row = next(r for r in self.index["document_types"] if r["id"] == member_id)
            member = json.loads((CATALOG_DIR / row["record"]).read_text(encoding="utf-8"))
            rule = member["selection"]
            if not any((rule.get("selectors") or {}).values()) and not rule.get("condition"):
                core.append(member_id)
        self.assertLessEqual(len(core), 8, core)
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                self.assertEqual(run(runtime, "query_catalog", "--validate").returncode, 0)

    def test_every_foldable_record_declares_a_compact_group(self) -> None:
        """The bounded-tree invariant, enforced at the catalog level: anything
        that is neither a fixed tooling path nor portfolio-tier must fold, or a
        confirmed profile would add a file to a compact tree."""
        fixed = {
            "root_readme", "changelog", "docs_index", "contributing_root",
            "security_root", "agents_kernel", "claude_shim", "claude_local",
            "claude_settings",
        }
        missing = []
        for row in self.index["document_types"]:
            record = json.loads((CATALOG_DIR / row["record"]).read_text(encoding="utf-8"))
            if record["group"] == "portfolio" or record["selection"]["mode"] == "compact":
                continue
            if record["id"] in fixed or record.get("compact_group"):
                continue
            missing.append(record["id"])
        self.assertEqual(missing, [], "records that would stay standalone in a compact tree")

    def test_agents_compact_registered_and_within_member_cap(self) -> None:
        row = next(r for r in self.index["document_types"] if r["id"] == "agents_compact")
        self.assertEqual(row["path"], "docs/agents.md")
        record = json.loads((CATALOG_DIR / row["record"]).read_text(encoding="utf-8"))
        self.assertEqual(record["type"], "compact-doc")
        self.assertEqual(record["compact_target"], "docs/agents.md")
        self.assertLessEqual(len(record["compact_members"]), 8)
        members = set(record["compact_members"])
        for expected in (
            "agents_index", "agents_architecture", "agents_patterns", "agents_testing",
            "agents_conventions", "agents_tech_debt", "agents_flow", "agents_glossary",
        ):
            self.assertIn(expected, members)
        # Fixed host-contract files are never part of the fold.
        for excluded in ("agents_kernel", "claude_shim", "claude_local", "claude_settings"):
            self.assertNotIn(excluded, members)
        for member_id in members:
            member_row = next(r for r in self.index["document_types"] if r["id"] == member_id)
            member = json.loads((CATALOG_DIR / member_row["record"]).read_text(encoding="utf-8"))
            self.assertEqual(member.get("compact_group"), "agents_compact")

    def test_portfolio_is_standard_only_no_compact_group_remains(self) -> None:
        """Portfolio's value is per-member separation; folding the collection
        layer into one file would erase it. `portfolio_compact` was removed
        and none of its former members carry a `compact_group` any more."""
        self.assertFalse(
            any(r["id"] == "portfolio_compact" for r in self.index["document_types"])
        )
        for member_id in (
            "portfolio_readme", "portfolio_repo_inventory", "portfolio_system_context",
            "portfolio_security", "portfolio_operations", "portfolio_diligence_index",
            "portfolio_glossary",
        ):
            row = next(r for r in self.index["document_types"] if r["id"] == member_id)
            record = json.loads((CATALOG_DIR / row["record"]).read_text(encoding="utf-8"))
            self.assertNotIn("compact_group", record)
            self.assertNotIn("compact_order", record)
        for path in (
            "compact/contracts/portfolio.md", "compact/instructions/portfolio.md",
            "compact/templates/portfolio.template.md",
        ):
            self.assertFalse((SKILL_ROOT / "content" / path).exists())


if __name__ == "__main__":
    unittest.main()
