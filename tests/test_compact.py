"""Compact layout: the fold mechanism, standard-layout invariance, merged-file
scaffolding, composed contracts, and layout switching — Python/Node parity.

Compact is a second axis orthogonal to tier: every tier keeps its standard
tree byte-identical, and a compact tier covers the same subjects in fewer,
denser files.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _support import initialize, load_manifest, run


def seed_source_files(repo: Path, count: int) -> None:
    src = repo / "src"
    src.mkdir(parents=True, exist_ok=True)
    for index in range(count):
        (src / f"mod_{index}.py").write_text("x = 1\n", encoding="utf-8")


def compact_tree(repo: Path) -> dict[str, str]:
    manifest = load_manifest(repo)
    assert manifest["project"]["scale"]["layout"] == "compact", manifest["project"]["scale"]
    return {doc["id"]: doc["path"] for doc in manifest["documents"]}


class CompactFoldTests(unittest.TestCase):
    def test_small_fixture_detects_compact_and_folds(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    seed_source_files(repo, 7)
                    self.assertEqual(initialize(runtime, repo, "spine", layout=None).returncode, 0)
                    docs = compact_tree(repo)
                    self.assertEqual(
                        sorted(docs.values()),
                        [
                            "CHANGELOG.md", "README.md",
                            "docs/README.md", "docs/architecture.md",
                            "docs/engineering.md", "docs/flows/README.md",
                            "docs/product.md", "docs/reference.md",
                        ],
                    )
                    manifest = load_manifest(repo)
                    members = {
                        doc["id"]: doc.get("compact_members")
                        for doc in manifest["documents"]
                        if doc.get("compact_members")
                    }
                    self.assertEqual(members["product_compact"], ["product_index", "product_overview"])
                    self.assertEqual(members["architecture_compact"], ["architecture_index", "arch_high_level"])
                    self.assertEqual(
                        members["engineering_compact"],
                        ["engineering_index", "setup_guide", "testing_guide"],
                    )
                    self.assertEqual(
                        members["reference_compact"],
                        ["reference_index", "configuration", "limitations", "tech_stack"],
                    )
                    for doc in manifest["documents"]:
                        if doc.get("compact_members"):
                            kinds = {origin["kind"] for origin in doc["selection"]["origins"]}
                            self.assertIn("compact", kinds)
                            self.assertIn("tier", kinds)

    def test_standard_layout_never_folds_any_tier(self) -> None:
        for runtime in ("py", "js"):
            for tier in ("spine", "diligence", "portfolio"):
                with self.subTest(runtime=runtime, tier=tier):
                    with tempfile.TemporaryDirectory() as tmp:
                        repo = Path(tmp)
                        seed_source_files(repo, 7)
                        self.assertEqual(initialize(runtime, repo, tier, layout="standard").returncode, 0)
                        manifest = load_manifest(repo)
                        self.assertTrue(all(not doc.get("compact_members") for doc in manifest["documents"]))
                        self.assertNotIn("product_compact", {doc["id"] for doc in manifest["documents"]})
                        self.assertIn("docs/product/README.md", {doc["path"] for doc in manifest["documents"]})

    def test_compact_covers_same_subjects_as_standard_spine(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            standard_repo = Path(tmp) / "standard"
            compact_repo = Path(tmp) / "compact"
            standard_repo.mkdir()
            compact_repo.mkdir()
            seed_source_files(standard_repo, 7)
            seed_source_files(compact_repo, 7)
            self.assertEqual(initialize("py", standard_repo, "spine", layout="standard").returncode, 0)
            self.assertEqual(initialize("py", compact_repo, "spine", layout=None).returncode, 0)
            standard_ids = {doc["id"] for doc in load_manifest(standard_repo)["documents"]}
            compact = load_manifest(compact_repo)
            unfolded = {
                member
                for doc in compact["documents"]
                for member in (doc.get("compact_members") or [])
            }
            kept = {doc["id"] for doc in compact["documents"] if not doc.get("compact_members")}
            self.assertEqual(unfolded | kept, standard_ids)

    def test_dry_run_tree_shows_merged_entries(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    seed_source_files(repo, 7)
                    self.assertEqual(initialize(runtime, repo, "spine", layout=None).returncode, 0)
                    preview = run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(repo / ".docforge" / "manifest.json"), "--dry-run")
                    self.assertEqual(preview.returncode, 0, preview.stderr)
                    self.assertIn("product_compact", preview.stdout)
                    self.assertIn("docs/product.md", preview.stdout)
                    self.assertNotIn("docs/product/README.md", preview.stdout)

    def test_scaffold_writes_merged_files(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    seed_source_files(repo, 7)
                    self.assertEqual(initialize(runtime, repo, "spine", layout=None).returncode, 0)
                    scaffold = run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(repo / ".docforge" / "manifest.json"), "--document", "product_compact")
                    self.assertEqual(scaffold.returncode, 0, scaffold.stderr)
                    target = repo / "docs" / "product.md"
                    self.assertTrue(target.is_file())
                    text = target.read_text(encoding="utf-8")
                    self.assertTrue(text.startswith("# "))
                    self.assertIn("## At a glance", text)
                    self.assertIn("## Overview", text)

    def test_route_composes_member_contracts(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    result = run(runtime, "query_catalog", "--route", "engineering_compact")
                    self.assertEqual(result.returncode, 0, result.stderr)
                    payload = json.loads(result.stdout)
                    self.assertEqual(payload["id"], "engineering_compact")
                    self.assertIn("## setup_guide", payload["contract"])
                    self.assertIn("## testing_guide", payload["contract"])
                    members = payload["compact"]["members"]
                    self.assertEqual(
                        [member["id"] for member in members],
                        ["engineering_index", "setup_guide", "testing_guide", "conventions", "release_guide"],
                    )
                    self.assertEqual([member["order"] for member in members], [1, 2, 3, 4, 5])

    def test_member_ordering_is_total_when_orders_tie(self) -> None:
        """`compact_order` defaults to 0, so two members can tie. The sort key
        must fall through to the id — comparing the raw `(order, document)`
        pairs would compare two dicts and raise.

        Python-only: `manage_manifest.js` is an execution shim that exits on
        `require`, so its peer helper cannot be imported. The ordering that a
        user can actually reach is covered in both runtimes by
        `test_route_composes_member_contracts`.
        """
        from runtime.manifest.python.manage_manifest import _compact_member_key

        members = [(0, {"id": "zebra"}), (0, {"id": "alpha"}), (1, {"id": "beta"})]
        ordered = [doc["id"] for _order, doc in sorted(members, key=_compact_member_key)]
        self.assertEqual(ordered, ["alpha", "zebra", "beta"])

    def test_reconcile_layout_switch_merges_and_splits(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    seed_source_files(repo, 7)
                    self.assertEqual(initialize(runtime, repo, "spine", layout="standard").returncode, 0)
                    manifest_path = repo / ".docforge" / "manifest.json"
                    for status in ("in_progress", "generated"):
                        result = run(runtime, "manage_manifest", "set", "--repo", str(repo), "--id", "product_overview", "--status", status)
                        self.assertEqual(result.returncode, 0, result.stderr)
                    scaffold = run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(manifest_path), "--document", "product_overview")
                    self.assertEqual(scaffold.returncode, 0, scaffold.stderr)
                    # standard -> compact
                    merge = run(runtime, "manage_manifest", "reconcile", "--repo", str(repo), "--layout", "compact")
                    self.assertEqual(merge.returncode, 0, merge.stderr)
                    self.assertIn("layout: standard -> compact", merge.stdout)
                    manifest = load_manifest(repo)
                    ids = {doc["id"] for doc in manifest["documents"]}
                    self.assertIn("product_compact", ids)
                    self.assertNotIn("product_index", ids)
                    # The written component is preserved as a retire candidate;
                    # reconcile never touches its file.
                    self.assertIn("retire: product_overview", merge.stdout)
                    overview = next(doc for doc in manifest["documents"] if doc["id"] == "product_overview")
                    self.assertEqual(overview["status"], "generated")
                    self.assertEqual(manifest["project"]["scale"]["layout"], "compact")
                    self.assertEqual(manifest["project"]["scale"]["decided_by"], "user")
                    # Approved retirement completes the merge.
                    retired = run(runtime, "manage_manifest", "retire", "--repo", str(repo), "--doc", "product_overview", "--mode", "obsolete")
                    self.assertEqual(retired.returncode, 0, retired.stderr)
                    overview = next(doc for doc in load_manifest(repo)["documents"] if doc["id"] == "product_overview")
                    self.assertEqual(overview["status"], "retired")
                    # compact -> standard
                    split = run(runtime, "manage_manifest", "reconcile", "--repo", str(repo), "--layout", "standard")
                    self.assertEqual(split.returncode, 0, split.stderr)
                    self.assertIn("layout: compact -> standard", split.stdout)
                    ids = {doc["id"] for doc in load_manifest(repo)["documents"]}
                    self.assertNotIn("product_compact", ids)
                    self.assertIn("product_index", ids)
                    self.assertIn("product_overview", ids)
                    overview = next(doc for doc in load_manifest(repo)["documents"] if doc["id"] == "product_overview")
                    self.assertEqual(overview["status"], "planned", "re-selected retired doc is planned for a fresh scaffold")

    def test_gate_runs_on_compact_tree(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    seed_source_files(repo, 7)
                    self.assertEqual(initialize(runtime, repo, "spine", layout=None).returncode, 0)
                    audit = run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(repo / ".docforge" / "manifest.json"), "--audit")
                    self.assertEqual(audit.returncode, 1, audit.stderr)
                    self.assertIn("docs/product.md", audit.stdout)
                    self.assertNotIn("docs/product/README.md", audit.stdout)
                    self.assertIn("8 manifest documents checked", audit.stdout)

    def test_compact_diligence_covers_same_subjects_in_fewer_files_than_standard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            standard_repo = Path(tmp) / "standard"
            compact_repo = Path(tmp) / "compact"
            standard_repo.mkdir()
            compact_repo.mkdir()
            seed_source_files(standard_repo, 7)
            seed_source_files(compact_repo, 7)
            self.assertEqual(initialize("py", standard_repo, "diligence", layout="standard").returncode, 0)
            self.assertEqual(initialize("py", compact_repo, "diligence", layout="compact").returncode, 0)
            standard_docs = load_manifest(standard_repo)["documents"]
            compact_docs = load_manifest(compact_repo)["documents"]
            self.assertLess(len(compact_docs), len(standard_docs))
            standard_ids = {doc["id"] for doc in standard_docs}
            unfolded = {
                member
                for doc in compact_docs
                for member in (doc.get("compact_members") or [])
            }
            kept = {doc["id"] for doc in compact_docs if not doc.get("compact_members")}
            self.assertEqual(unfolded | kept, standard_ids)
            merged_paths = {doc["path"] for doc in compact_docs if doc.get("compact_members")}
            self.assertEqual(
                merged_paths,
                {
                    "docs/architecture.md", "docs/contributing.md", "docs/engineering.md",
                    "docs/operations.md", "docs/product.md", "docs/reference.md", "docs/security.md",
                },
            )
            # Dynamic-child indexes never fold, at any tier.
            standalone_paths = {doc["path"] for doc in compact_docs if not doc.get("compact_members")}
            for dynamic_index in (
                "docs/architecture/concepts/README.md",
                "docs/architecture/decisions/README.md",
                "docs/operations/runbooks/README.md",
            ):
                self.assertIn(dynamic_index, standalone_paths)

    def test_compact_diligence_gate_runs_on_folded_tree(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    seed_source_files(repo, 7)
                    self.assertEqual(initialize(runtime, repo, "diligence", layout="compact").returncode, 0)
                    audit = run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(repo / ".docforge" / "manifest.json"), "--audit")
                    self.assertEqual(audit.returncode, 1, audit.stderr)
                    self.assertIn("docs/security.md", audit.stdout)
                    self.assertIn("16 manifest documents checked", audit.stdout)

    def test_compact_portfolio_covers_same_subjects_in_fewer_files_than_standard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            standard_repo = Path(tmp) / "standard"
            compact_repo = Path(tmp) / "compact"
            standard_repo.mkdir()
            compact_repo.mkdir()
            seed_source_files(standard_repo, 7)
            seed_source_files(compact_repo, 7)
            self.assertEqual(initialize("py", standard_repo, "portfolio", layout="standard").returncode, 0)
            self.assertEqual(initialize("py", compact_repo, "portfolio", layout="compact").returncode, 0)
            standard_docs = load_manifest(standard_repo)["documents"]
            compact_docs = load_manifest(compact_repo)["documents"]
            self.assertLess(len(compact_docs), len(standard_docs))
            portfolio_compact = next(doc for doc in compact_docs if doc["id"] == "portfolio_compact")
            self.assertEqual(portfolio_compact["path"], "docs-portfolio.md")
            self.assertEqual(
                portfolio_compact["compact_members"],
                [
                    "portfolio_readme", "portfolio_repo_inventory", "portfolio_system_context",
                    "portfolio_security", "portfolio_operations", "portfolio_diligence_index",
                    "portfolio_glossary",
                ],
            )
            # Decisions and epics stay standalone dynamic indexes even at Portfolio compact.
            compact_paths = {doc["path"] for doc in compact_docs}
            self.assertIn("docs-portfolio/decisions/README.md", compact_paths)
            self.assertIn("docs-portfolio/epics/README.md", compact_paths)

    def test_compact_portfolio_scaffolds_merged_file_with_all_sections(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    seed_source_files(repo, 7)
                    self.assertEqual(initialize(runtime, repo, "portfolio", layout="compact").returncode, 0)
                    scaffold = run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(repo / ".docforge" / "manifest.json"), "--document", "portfolio_compact")
                    self.assertEqual(scaffold.returncode, 0, scaffold.stderr)
                    target = repo / "docs-portfolio.md"
                    self.assertTrue(target.is_file())
                    text = target.read_text(encoding="utf-8")
                    for heading in (
                        "## At a glance", "## Repository inventory", "## System context",
                        "## Security posture", "## Operations", "## Diligence index", "## Glossary",
                    ):
                        self.assertIn(heading, text)


class LayoutReconcileRecordTests(unittest.TestCase):
    def test_layout_switch_on_a_manifest_without_scale_writes_a_complete_record(self) -> None:
        """`reconcile --layout` used to copy whatever `project.scale` held and
        patch `layout` onto it. On a manifest predating the field that left a
        record with no `class`, which the schema requires."""
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    seed_source_files(repo, 7)
                    self.assertEqual(initialize(runtime, repo, "spine", layout="standard").returncode, 0)
                    manifest_path = repo / ".docforge" / "manifest.json"
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    del manifest["project"]["scale"]
                    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

                    result = run(runtime, "manage_manifest", "reconcile", "--repo", str(repo), "--layout", "compact")
                    self.assertEqual(result.returncode, 0, result.stderr)
                    scale = load_manifest(repo)["project"]["scale"]
                    self.assertEqual(
                        set(scale) >= {"class", "layout", "decided_by", "decided_at", "signals"},
                        True,
                        scale,
                    )
                    self.assertEqual(scale["layout"], "compact")
                    self.assertEqual(scale["decided_by"], "user")
                    self.assertIn(scale["class"], ("small", "medium", "large"))


if __name__ == "__main__":
    unittest.main()
