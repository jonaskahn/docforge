"""Provenance storage: folder sidecar store, mode flip, and json-mode
behavior parity across the Python and Node runtimes.

The default `json` storage keeps public identity (id/title/description) and
`docforge_provenance` in one git-tracked JSON per docs folder under
`.docforge/provenance/`; markdown files stay frontmatter-free. The legacy
`markdown` storage keeps inline frontmatter. Both modes must survive the
full write/revise pipeline on both runtimes.
"""

from __future__ import annotations

import json
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
)

SCHEMA_VERSION = "2.1"
SIDECAR_ROOT = ".docforge/provenance"


class StoreParityTests(unittest.TestCase):
    def test_sidecar_path_mapping_and_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for runtime in ("py", "js"):
                script = (
                    "common/python/provenance_store" if runtime == "py"
                    else "common/js/provenance_store.js"
                )
                probe = [
                    "python3", "-c",
                    "import sys; sys.path.insert(0, 'skills/docforge/_shared'); "
                    "from runtime.common.python import provenance_store as s; "
                    "import pathlib; r = pathlib.Path(sys.argv[1]); "
                    "print(s.sidecar_path(r, 'docs/architecture').relative_to(r)); "
                    "print(s.sidecar_path(r, '').relative_to(r)); "
                    "print(s.folder_of('docs/architecture/concepts/README.md')); "
                    "import json as _json; print(_json.dumps(s.folder_of('README.md')))",
                    str(repo),
                ] if runtime == "py" else [
                    "node", "-e",
                    "const s = require(process.argv[1]); const r = process.argv[2]; "
                    "console.log(s.sidecarPath(r, 'docs/architecture').replace(r + '/', '')); "
                    "console.log(s.sidecarPath(r, '').replace(r + '/', '')); "
                    "console.log(s.folderOf('docs/architecture/concepts/README.md')); "
                    "console.log(JSON.stringify(s.folderOf('README.md')))",
                    str(ROOT / "skills/docforge/_shared/runtime/common/js/provenance_store.js"),
                    str(repo),
                ]
                import subprocess
                result = subprocess.run(probe, cwd=ROOT, text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                lines = result.stdout.strip().splitlines()
                self.assertEqual(lines, [
                    ".docforge/provenance/docs/architecture.json",
                    ".docforge/provenance/root.json",
                    "docs/architecture/concepts",
                    '""',
                ])

    def test_entry_write_remove_and_empty_cleanup(self) -> None:
        from runtime.common.python import provenance_store as store

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            entry = {
                "id": "architecture_index",
                "title": "Architecture",
                "description": "One-liner.",
                "provenance": {"schema": SCHEMA_VERSION, "doc_id": "architecture_index"},
            }
            store.write_entry(repo, "docs/architecture/README.md", entry)
            sidecar = repo / SIDECAR_ROOT / "docs" / "architecture.json"
            self.assertTrue(sidecar.is_file())
            self.assertEqual(store.entry_for(repo, "docs/architecture/README.md")["title"], "Architecture")
            store.write_entry(repo, "docs/architecture/high-level.md", entry)
            store.remove_entry(repo, "docs/architecture/README.md")
            self.assertTrue(sidecar.is_file())
            store.remove_entry(repo, "docs/architecture/high-level.md")
            self.assertFalse(sidecar.exists())

    def test_read_doc_metadata_states(self) -> None:
        from runtime.common.python import provenance_store as store

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            target = repo / "docs" / "only.md"
            target.parent.mkdir(parents=True)
            target.write_text(
                markdown_with_provenance(
                    provenance(doc_id="only", path="docs/only.md", tier="spine",
                               target_depth="orientation", section_id="only",
                               source_path="src.py", source_blob="a" * 40),
                    "# Only\n\nBody.\n",
                ),
                encoding="utf-8",
            )
            doc = {"path": "docs/only.md", "id": "only"}
            meta = store.read_doc_metadata(repo, doc, store.STORAGE_JSON)
            self.assertEqual(meta["state"], "inline")
            self.assertEqual(meta["source"], "markdown")
            self.assertEqual(meta["provenance"]["doc_id"], "only")
            action = store.move_inline_to_sidecar(repo, doc, store.STORAGE_JSON)
            self.assertEqual(action, "moved")
            self.assertTrue((repo / SIDECAR_ROOT / "docs.json").is_file())
            self.assertFalse(target.read_text(encoding="utf-8").startswith("---"))
            meta = store.read_doc_metadata(repo, doc, store.STORAGE_JSON)
            self.assertEqual(meta["state"], "ok")
            self.assertEqual(meta["source"], "sidecar")
            self.assertEqual(meta["public"]["id"], "only")
            action = store.move_sidecar_to_inline(repo, doc)
            self.assertEqual(action, "moved")
            self.assertTrue(target.read_text(encoding="utf-8").startswith("---\nid: "))
            self.assertFalse((repo / SIDECAR_ROOT / "docs.json").exists())
            self.assertEqual(store.read_doc_metadata(repo, doc, store.STORAGE_JSON)["state"], "inline")

    def test_storage_for_defaults_to_json(self) -> None:
        from runtime.common.python import provenance_store as store

        self.assertEqual(store.storage_for({}), store.STORAGE_JSON)
        self.assertEqual(store.storage_for({"project": {}}), store.STORAGE_JSON)
        self.assertEqual(
            store.storage_for({"project": {"provenance_storage": "markdown"}}),
            store.STORAGE_MARKDOWN,
        )


class JsonModePipelineTests(unittest.TestCase):
    def _seed_inline_repo(self, repo: Path, runtime: str) -> None:
        source = repo / "source.txt"
        source.write_text("evidence\n", encoding="utf-8")
        value = provenance(
            doc_id="only", path="docs/only.md", tier="spine",
            target_depth="reference", section_id="only",
            source_path="source.txt", source_blob=blob_hash(source.read_bytes()),
        )
        manifest = {
            "version": "3.2",
            "project": {"name": "fixture", "root": str(repo), "tier": "spine",
                        "profiles": {"shapes": [], "platforms": [], "frameworks": [], "concerns": [], "audiences": []}},
            "discovery": [],
            "documents": [{
                "id": "only", "type": "generic", "path": "docs/only.md",
                "title": "Only", "description": "One-liner.", "status": "complete", "requires": [],
                "group": "reference",
                "scaffold_template": "generic.md", "instruction_file": None,
                "target_depth": "reference", "write_order": 1,
                "provenance_mode": "sections", "audit_profile": "standard",
                "provenance": value, "audit": None,
            }],
            "metadata": {},
        }
        manifest_path = repo / ".docforge" / "manifest.json"
        manifest_path.parent.mkdir()
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        target = repo / "docs" / "only.md"
        target.parent.mkdir()
        target.write_text(markdown_with_provenance(value, "# Only\n\nBody.\n"), encoding="utf-8")

    def test_migrate_32_to_33_moves_inline_into_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                self._seed_inline_repo(repo, runtime)
                manifest_path = repo / ".docforge" / "manifest.json"
                preview = run(runtime, "migrate_metadata", "--repo", str(repo), "--manifest", str(manifest_path), "--dry-run")
                self.assertEqual(preview.returncode, 0, preview.stderr)
                self.assertIn("inline -> sidecar", preview.stdout)
                self.assertFalse((repo / SIDECAR_ROOT).exists())
                result = run(runtime, "migrate_metadata", "--repo", str(repo), "--manifest", str(manifest_path))
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                saved = load_manifest(repo)
                self.assertEqual(saved["version"], "3.3")
                self.assertEqual(saved["project"]["provenance_storage"], "json")
                self.assertEqual(saved["documents"][0]["provenance"]["schema"], "2.0")
                target = repo / "docs" / "only.md"
                self.assertTrue(target.read_text(encoding="utf-8").startswith("# Only\n"))
                sidecar = json.loads((repo / SIDECAR_ROOT / "docs.json").read_text(encoding="utf-8"))
                entry = sidecar["files"]["only.md"]
                self.assertEqual(entry["id"], "only")
                self.assertEqual(entry["title"], "Only")
                self.assertEqual(entry["provenance"]["doc_id"], "only")
                again = run(runtime, "migrate_metadata", "--repo", str(repo), "--manifest", str(manifest_path))
                self.assertEqual(again.returncode, 0, again.stderr + again.stdout)
                self.assertTrue(target.read_text(encoding="utf-8").startswith("# Only\n"))

    def test_init_seeds_json_and_scaffold_writes_sidecar_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                self.assertEqual(initialize(runtime, repo, "spine").returncode, 0)
                manifest = load_manifest(repo)
                self.assertEqual(manifest["version"], "3.3")
                self.assertEqual(manifest["project"]["provenance_storage"], "json")
                manifest_path = repo / ".docforge" / "manifest.json"
                result = run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(manifest_path), "--document", "arch_high_level")
                self.assertEqual(result.returncode, 0, result.stderr)
                target = repo / "docs" / "architecture" / "high-level.md"
                body = target.read_text(encoding="utf-8")
                self.assertFalse(body.startswith("---"))
                sidecar = json.loads((repo / SIDECAR_ROOT / "docs" / "architecture.json").read_text(encoding="utf-8"))
                entry = sidecar["files"]["high-level.md"]
                self.assertEqual(entry["id"], "arch_high_level")
                self.assertEqual(entry["provenance"]["schema"], SCHEMA_VERSION)

    def test_set_storage_flips_both_directions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                self._seed_inline_repo(repo, runtime)
                manifest_path = repo / ".docforge" / "manifest.json"
                run(runtime, "migrate_metadata", "--repo", str(repo), "--manifest", str(manifest_path))
                target = repo / "docs" / "only.md"
                self.assertTrue(target.read_text(encoding="utf-8").startswith("# Only\n"))
                to_markdown = run(runtime, "manage_manifest", "set-storage", "--repo", str(repo), "--storage", "markdown")
                self.assertEqual(to_markdown.returncode, 0, to_markdown.stderr)
                self.assertIn("sidecar -> inline", to_markdown.stdout)
                self.assertTrue(target.read_text(encoding="utf-8").startswith("---\nid: "))
                self.assertFalse((repo / SIDECAR_ROOT / "docs.json").exists())
                self.assertEqual(load_manifest(repo)["project"]["provenance_storage"], "markdown")
                back = run(runtime, "manage_manifest", "set-storage", "--repo", str(repo), "--storage", "json", "--dry-run")
                self.assertEqual(back.returncode, 0, back.stderr)
                self.assertIn("inline -> sidecar", back.stdout)
                self.assertTrue(target.read_text(encoding="utf-8").startswith("---\nid: "))
                back = run(runtime, "manage_manifest", "set-storage", "--repo", str(repo), "--storage", "json")
                self.assertEqual(back.returncode, 0, back.stderr)
                self.assertTrue(target.read_text(encoding="utf-8").startswith("# Only\n"))
                self.assertEqual(load_manifest(repo)["project"]["provenance_storage"], "json")

    def test_check_staleness_sync_auto_moves_inline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                self._seed_inline_repo(repo, runtime)
                manifest_path = repo / ".docforge" / "manifest.json"
                run(runtime, "migrate_metadata", "--repo", str(repo), "--manifest", str(manifest_path))
                target = repo / "docs" / "only.md"
                self.assertTrue(target.read_text(encoding="utf-8").startswith("# Only\n"))
                # An inline-frontmatter copy reappears (e.g. restored from an
                # older branch) while the sidecar entry is gone: sync moves it.
                value = provenance(
                    doc_id="only", path="docs/only.md", tier="spine",
                    target_depth="reference", section_id="only",
                    source_path="source.txt",
                    source_blob=blob_hash((repo / "source.txt").read_bytes()),
                )
                target.write_text(markdown_with_provenance(value, "# Only\n\nBody.\n"), encoding="utf-8")
                (repo / SIDECAR_ROOT / "docs.json").unlink()
                sync = run(runtime, "check_staleness", "--manifest", str(manifest_path), "--sync-provenance")
                self.assertEqual(sync.returncode, 0, sync.stderr + sync.stdout)
                self.assertIn("FRESH", sync.stdout)
                self.assertTrue(target.read_text(encoding="utf-8").startswith("# Only\n"))
                saved = load_manifest(repo)
                self.assertEqual(saved["documents"][0]["provenance"]["schema"], "2.0")

    def test_lint_and_audit_read_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                self._seed_inline_repo(repo, runtime)
                manifest_path = repo / ".docforge" / "manifest.json"
                run(runtime, "migrate_metadata", "--repo", str(repo), "--manifest", str(manifest_path))
                lint = run(runtime, "lint_document", "--file", str(repo / "docs" / "only.md"))
                self.assertEqual(lint.returncode, 0, lint.stderr + lint.stdout)
                audit = run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(manifest_path), "--audit")
                self.assertEqual(audit.returncode, 0, audit.stderr + audit.stdout)

    def test_plan_flags_inline_pending_migration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._seed_inline_repo(repo, "py")
            manifest_path = repo / ".docforge" / "manifest.json"
            preview = run("py", "scaffold_docs", "--repo", str(repo), "--manifest", str(manifest_path), "--dry-run")
            self.assertEqual(preview.returncode, 0, preview.stderr)
            self.assertIn("inline provenance pending sidecar migration", preview.stdout)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
