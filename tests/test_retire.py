"""Retirement: reconcile retire reporting, the `retire` command (obsolete move
/ delete / dry-run), entry preservation, re-selection, and gate exclusion —
Python/Node parity throughout.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from _support import initialize, load_manifest, run


def make_written_diligence_doc(runtime: str, repo: Path, doc_id: str = "arch_low_level") -> None:
    assert initialize(runtime, repo, "diligence").returncode == 0
    manifest_path = repo / ".docforge" / "manifest.json"
    for status in ("in_progress", "generated"):
        result = run(runtime, "manage_manifest", "set", "--repo", str(repo), "--id", doc_id, "--status", status)
        assert result.returncode == 0, result.stderr
    scaffold = run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(manifest_path), "--document", doc_id)
    assert scaffold.returncode == 0, scaffold.stderr


class ReconcileRetireReportingTests(unittest.TestCase):
    def test_downgrade_reports_written_docs_as_retire_candidates(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    make_written_diligence_doc(runtime, repo)
                    reconcile = run(runtime, "manage_manifest", "reconcile", "--repo", str(repo), "--tier", "spine")
                    self.assertEqual(reconcile.returncode, 0, reconcile.stderr)
                    self.assertIn("tier: diligence -> spine", reconcile.stdout)
                    self.assertIn("1 retire", reconcile.stdout)
                    self.assertIn("retire: arch_low_level", reconcile.stdout)
                    manifest = load_manifest(repo)
                    doc = next(d for d in manifest["documents"] if d["id"] == "arch_low_level")
                    self.assertEqual(doc["status"], "generated", "entry preserved until retire runs")
                    self.assertTrue((repo / doc["path"]).is_file(), "reconcile never moves files")


class RetireCommandTests(unittest.TestCase):
    def test_obsolete_mode_moves_file_and_preserves_entry(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    make_written_diligence_doc(runtime, repo)
                    run(runtime, "manage_manifest", "reconcile", "--repo", str(repo), "--tier", "spine")
                    result = run(runtime, "manage_manifest", "retire", "--repo", str(repo), "--doc", "arch_low_level", "--mode", "obsolete")
                    self.assertEqual(result.returncode, 0, result.stderr)
                    year = str(datetime.now(timezone.utc).year)
                    moved = repo / ".docforge" / "obsolete" / year / "docs" / "architecture" / "low-level.md"
                    self.assertTrue(moved.is_file(), f"{runtime}: file moved to {moved}")
                    manifest = load_manifest(repo)
                    doc = next(d for d in manifest["documents"] if d["id"] == "arch_low_level")
                    self.assertEqual(doc["status"], "retired")
                    self.assertIn("retired_at", doc)
                    self.assertEqual(
                        doc["retired_destination"],
                        f".docforge/obsolete/{year}/docs/architecture/low-level.md",
                    )
                    gitignore = (repo / ".docforge" / ".gitignore").read_text(encoding="utf-8")
                    self.assertIn("obsolete/", gitignore)
                    self.assertTrue((repo / ".docforge" / "obsolete" / year / ".gitignore").is_file())

    def test_delete_mode_removes_file_and_preserves_entry(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    make_written_diligence_doc(runtime, repo)
                    run(runtime, "manage_manifest", "reconcile", "--repo", str(repo), "--tier", "spine")
                    result = run(runtime, "manage_manifest", "retire", "--repo", str(repo), "--doc", "arch_low_level", "--mode", "delete")
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertFalse((repo / "docs/architecture/low-level.md").exists())
                    manifest = load_manifest(repo)
                    doc = next(d for d in manifest["documents"] if d["id"] == "arch_low_level")
                    self.assertEqual(doc["status"], "retired")
                    self.assertIn("retired_at", doc)
                    self.assertNotIn("retired_destination", doc)

    def test_dry_run_moves_nothing(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    make_written_diligence_doc(runtime, repo)
                    run(runtime, "manage_manifest", "reconcile", "--repo", str(repo), "--tier", "spine")
                    result = run(runtime, "manage_manifest", "retire", "--repo", str(repo), "--doc", "arch_low_level", "--mode", "obsolete", "--dry-run")
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn("DRY RUN", result.stdout)
                    self.assertTrue((repo / "docs/architecture/low-level.md").is_file())
                    manifest = load_manifest(repo)
                    doc = next(d for d in manifest["documents"] if d["id"] == "arch_low_level")
                    self.assertEqual(doc["status"], "generated")

    def test_rejects_non_written_documents(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    self.assertEqual(initialize(runtime, repo, "spine").returncode, 0)
                    result = run(runtime, "manage_manifest", "retire", "--repo", str(repo), "--doc", "arch_high_level", "--mode", "delete")
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("only written documents can be retired", result.stderr)

    def test_retire_is_idempotent(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    make_written_diligence_doc(runtime, repo)
                    run(runtime, "manage_manifest", "reconcile", "--repo", str(repo), "--tier", "spine")
                    first = run(runtime, "manage_manifest", "retire", "--repo", str(repo), "--doc", "arch_low_level", "--mode", "obsolete")
                    self.assertEqual(first.returncode, 0, first.stderr)
                    second = run(runtime, "manage_manifest", "retire", "--repo", str(repo), "--doc", "arch_low_level", "--mode", "obsolete")
                    self.assertEqual(second.returncode, 0, second.stderr)
                    self.assertIn("already retired", second.stdout)
                    manifest = load_manifest(repo)
                    doc = next(d for d in manifest["documents"] if d["id"] == "arch_low_level")
                    self.assertEqual(doc["status"], "retired")


class RetiredLifecycleTests(unittest.TestCase):
    def test_reselection_returns_retired_doc_to_planned(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    make_written_diligence_doc(runtime, repo)
                    run(runtime, "manage_manifest", "reconcile", "--repo", str(repo), "--tier", "spine")
                    run(runtime, "manage_manifest", "retire", "--repo", str(repo), "--doc", "arch_low_level", "--mode", "obsolete")
                    reconcile = run(runtime, "manage_manifest", "reconcile", "--repo", str(repo), "--tier", "diligence")
                    self.assertEqual(reconcile.returncode, 0, reconcile.stderr)
                    manifest = load_manifest(repo)
                    doc = next(d for d in manifest["documents"] if d["id"] == "arch_low_level")
                    self.assertEqual(doc["status"], "planned")
                    self.assertNotIn("retired_at", doc)
                    self.assertNotIn("retired_destination", doc)

    def test_gate_excludes_retired_documents(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    make_written_diligence_doc(runtime, repo)
                    run(runtime, "manage_manifest", "reconcile", "--repo", str(repo), "--tier", "spine")
                    run(runtime, "manage_manifest", "retire", "--repo", str(repo), "--doc", "arch_low_level", "--mode", "obsolete")
                    audit = run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(repo / ".docforge" / "manifest.json"), "--audit")
                    # Bare repo: other planned spine docs are missing -> exit 1,
                    # but the retired doc must not be among the missing files.
                    self.assertEqual(audit.returncode, 1, audit.stderr)
                    self.assertNotIn("  docs/architecture/low-level.md", audit.stdout)

    def test_plan_tree_annotates_retired_action(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    make_written_diligence_doc(runtime, repo)
                    run(runtime, "manage_manifest", "reconcile", "--repo", str(repo), "--tier", "spine")
                    run(runtime, "manage_manifest", "retire", "--repo", str(repo), "--doc", "arch_low_level", "--mode", "delete")
                    preview = run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(repo / ".docforge" / "manifest.json"), "--dry-run")
                    self.assertEqual(preview.returncode, 0, preview.stderr)
                    self.assertNotIn("arch_low_level", preview.stdout)


class RetiredStatusHandlingTests(unittest.TestCase):
    """`retired` is a status like any other: every code path that branches on
    status must handle it. These cover the paths that did not."""

    def test_set_on_a_retired_document_returns_it_to_planned(self) -> None:
        """`TRANSITIONS` had no `retired` key, so `set` raised an uncaught
        KeyError in Python and a TypeError in Node — two different crashes for
        the same input, on a status the tool itself assigns."""
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    make_written_diligence_doc(runtime, repo)
                    run(runtime, "manage_manifest", "retire", "--repo", str(repo), "--doc", "arch_low_level", "--mode", "delete")
                    result = run(runtime, "manage_manifest", "set", "--repo", str(repo), "--id", "arch_low_level", "--status", "planned")
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertNotIn("Traceback", result.stderr)
                    entry = next(d for d in load_manifest(repo)["documents"] if d["id"] == "arch_low_level")
                    self.assertEqual(entry["status"], "planned")

    def test_set_rejects_an_unreachable_transition_cleanly(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    make_written_diligence_doc(runtime, repo)
                    run(runtime, "manage_manifest", "retire", "--repo", str(repo), "--doc", "arch_low_level", "--mode", "delete")
                    result = run(runtime, "manage_manifest", "set", "--repo", str(repo), "--id", "arch_low_level", "--status", "complete")
                    self.assertEqual(result.returncode, 2, result.stdout)
                    self.assertIn("invalid status transition", result.stdout + result.stderr)

    def test_status_buckets_account_for_retired_documents(self) -> None:
        """`total_documents` counts retired docs, so without a `retired`
        bucket the metadata block silently stopped summing to the total."""
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    make_written_diligence_doc(runtime, repo)
                    retire = run(runtime, "manage_manifest", "retire", "--repo", str(repo), "--doc", "arch_low_level", "--mode", "delete")
                    self.assertEqual(retire.returncode, 0, retire.stderr)
                    metadata = load_manifest(repo)["metadata"]
                    self.assertEqual(metadata["retired"], 1)
                    buckets = sum(
                        value for key, value in metadata.items()
                        if key not in {"total_documents", "last_updated"}
                    )
                    self.assertEqual(buckets, metadata["total_documents"])
                    status = run(runtime, "manage_manifest", "status", "--repo", str(repo))
                    self.assertIn("retired=1", status.stdout)


class RetireSchemaTests(unittest.TestCase):
    def test_schema_allows_retired_status_and_stamps(self) -> None:
        schema = json.loads(
            (Path(__file__).resolve().parents[1] / "skills" / "docforge" / "_shared" / ".metadata" / "manifest-schema.json").read_text(encoding="utf-8"),
        )
        document = schema["definitions"]["document"]["properties"]
        self.assertIn("retired", document["status"]["enum"])
        self.assertIn("retired_at", document)
        self.assertIn("retired_destination", document)


if __name__ == "__main__":
    unittest.main()
