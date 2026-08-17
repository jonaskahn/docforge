"""Provenance storage: the folder sidecar store and its behavior parity
across the Python and Node runtimes.

Public identity (id/title/description) and `docforge_provenance` live in one
git-tracked JSON per docs folder under `.docforge/provenance/`; generated
markdown stays frontmatter-free. Documents predating the store still carry
inline frontmatter — the store reads that layout so migration can move it,
and reports it as `inline` so nothing treats it as current.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _support import (
    MANIFEST_VERSION,
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
            meta = store.read_doc_metadata(repo, doc)
            self.assertEqual(meta["state"], "inline")
            self.assertEqual(meta["source"], "markdown")
            self.assertEqual(meta["provenance"]["doc_id"], "only")
            action = store.move_inline_to_sidecar(repo, doc)
            self.assertEqual(action, "moved")
            self.assertTrue((repo / SIDECAR_ROOT / "docs.json").is_file())
            self.assertFalse(target.read_text(encoding="utf-8").startswith("---"))
            meta = store.read_doc_metadata(repo, doc)
            self.assertEqual(meta["state"], "ok")
            self.assertEqual(meta["source"], "sidecar")
            self.assertEqual(meta["public"]["id"], "only")
            store.remove_entry(repo, "docs/only.md")
            self.assertFalse((repo / SIDECAR_ROOT / "docs.json").exists())
            self.assertEqual(store.read_doc_metadata(repo, doc)["state"], "missing")

    def test_old_schema_detection_is_explicit(self) -> None:
        """Legacy/obsolete metadata is never folded into ok/inline and is
        never silently moved — the store reports it explicitly, always on,
        with no opt-in/opt-out."""
        from runtime.common.python import provenance_store as store

        legacy_text = (
            "---\n"
            "docforge_provenance:\n"
            '  doc_id: "only"\n'
            '  path: "docs/only.md"\n'
            '  generated_at: "2026-07-27T09:12:44Z"\n'
            "  sections:\n"
            '    - id: "only"\n'
            "      sources: []\n"
            "      unresolved: []\n"
            "---\n"
            "# Only\n\nBody.\n"
        )
        obsolete_text = (
            "---\n"
            "docforge_provenance:\n"
            '  schema: "1.0"\n'
            '  tool_version: "2.19.0"\n'
            '  doc_id: "only"\n'
            '  path: "docs/only.md"\n'
            '  generated_at: "2026-07-27T09:12:44Z"\n'
            "  sections: []\n"
            "---\n"
            "# Only\n\nBody.\n"
        )
        if True:
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                target = repo / "docs" / "only.md"
                target.parent.mkdir(parents=True)
                doc = {"path": "docs/only.md", "id": "only", "title": "Only"}

                target.write_text(legacy_text, encoding="utf-8")
                meta = store.read_doc_metadata(repo, doc)
                self.assertEqual(meta["state"], "legacy")
                if True:
                    action = store.move_inline_to_sidecar(repo, doc)
                    self.assertEqual(action, "legacy-schema")
                    self.assertEqual(target.read_text(encoding="utf-8"), legacy_text)
                    self.assertFalse((repo / SIDECAR_ROOT / "docs.json").exists())

                target.write_text(obsolete_text, encoding="utf-8")
                meta = store.read_doc_metadata(repo, doc)
                self.assertEqual(meta["state"], "obsolete")
                if True:
                    action = store.move_inline_to_sidecar(repo, doc)
                    self.assertEqual(action, "obsolete-schema")
                    self.assertEqual(target.read_text(encoding="utf-8"), obsolete_text)
                    self.assertFalse((repo / SIDECAR_ROOT / "docs.json").exists())

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            doc = {"path": "docs/only.md", "id": "only", "title": "Only"}
            legacy_provenance = {"doc_id": "only", "path": "docs/only.md", "sections": []}
            store.write_entry(repo, "docs/only.md", {"id": "only", "title": "Only", "provenance": legacy_provenance})
            meta = store.read_doc_metadata(repo, doc)
            self.assertEqual(meta["state"], "legacy")
            self.assertEqual(meta["source"], "sidecar")
            store.write_entry(repo, "docs/only.md", {"id": "only", "title": "Only", "provenance": {"schema": "1.0", "tool_version": "2.19.0"}})
            meta = store.read_doc_metadata(repo, doc)
            self.assertEqual(meta["state"], "obsolete")
            self.assertEqual(meta["source"], "sidecar")

class JsonModePipelineTests(unittest.TestCase):

    def test_sync_never_silently_moves_old_schema_inline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                self._seed_inline_repo(repo, runtime)
                manifest_path = repo / ".docforge" / "manifest.json"
                run(runtime, "migrate_metadata", "--repo", str(repo), "--manifest", str(manifest_path))
                target = repo / "docs" / "only.md"
                # Replace the migrated sidecar entry with a schema-less legacy
                # provenance and drop the clean markdown back to inline-free
                # content: sync must report it explicitly, never move it.
                legacy_sidecar = {
                    "schema": "1.0",
                    "folder": "docs",
                    "files": {
                        "only.md": {
                            "id": "only",
                            "title": "Only",
                            "provenance": {
                                "doc_id": "only",
                                "path": "docs/only.md",
                                "generated_at": "2026-07-27T09:12:44Z",
                                "sections": [],
                            },
                        }
                    },
                }
                (repo / SIDECAR_ROOT / "docs.json").write_text(json.dumps(legacy_sidecar, indent=2) + "\n", encoding="utf-8")
                target.write_text("# Only\n\nBody.\n", encoding="utf-8")
                sync = run(runtime, "check_staleness", "--manifest", str(manifest_path), "--sync-provenance")
                self.assertEqual(sync.returncode, 1)
                self.assertIn("UNTRACKED", sync.stdout)
                self.assertIn("legacy provenance", sync.stdout)
                self.assertEqual(target.read_text(encoding="utf-8"), "# Only\n\nBody.\n")
                saved_sidecar = json.loads((repo / SIDECAR_ROOT / "docs.json").read_text(encoding="utf-8"))
                self.assertEqual(
                    saved_sidecar["files"]["only.md"]["provenance"],
                    legacy_sidecar["files"]["only.md"]["provenance"],
                )

    def _seed_inline_repo(self, repo: Path, runtime: str) -> None:
        source = repo / "source.txt"
        source.write_text("evidence\n", encoding="utf-8")
        source_blob = blob_hash(source.read_bytes())
        value = provenance(
            doc_id="only", path="docs/only.md", tier="spine",
            target_depth="reference", section_id="only",
            source_path="source.txt", source_blob=source_blob,
        )
        index_value = provenance(
            doc_id="docs_index", path="docs/README.md", tier="spine",
            target_depth="orientation", section_id="documentation",
            source_path="source.txt", source_blob=source_blob,
        )
        manifest = {
            "version": "3.2",
            "project": {"name": "fixture", "root": str(repo), "tier": "spine",
                        "profiles": {"shapes": [], "platforms": [], "frameworks": [], "concerns": [], "audiences": []}},
            "discovery": [],
            "documents": [{
                "id": "docs_index", "type": "docs-index", "path": "docs/README.md",
                "title": "Documentation", "description": "One-liner.", "status": "complete",
                "requires": [], "group": "root",
                "scaffold_template": "docs-index.template.md", "instruction_file": None,
                "target_depth": "orientation", "write_order": 30,
                "provenance_mode": "sections", "audit_profile": "router",
                "provenance": index_value, "audit": None,
            }, {
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
        index = repo / "docs" / "README.md"
        index.write_text(
            markdown_with_provenance(index_value, "# Documentation\n\nSee [Only](only.md).\n\nBody.\n"),
            encoding="utf-8",
        )

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
                self.assertEqual(saved["version"], MANIFEST_VERSION)
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
                self.assertEqual(manifest["version"], MANIFEST_VERSION)
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

    def test_markdown_storage_is_normalized_away_by_migration(self) -> None:
        """`markdown` storage no longer exists. A manifest still declaring it
        is normalized to `json` and its documents lose their frontmatter in
        the same migrate run — there is no flip back."""
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                self._seed_inline_repo(repo, runtime)
                manifest_path = repo / ".docforge" / "manifest.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["project"]["provenance_storage"] = "markdown"
                manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

                migrated = run(runtime, "migrate_metadata", "--repo", str(repo), "--manifest", str(manifest_path))
                self.assertIn(migrated.returncode, (0, 1), migrated.stderr)
                self.assertEqual(load_manifest(repo)["project"]["provenance_storage"], "json")
                target = repo / "docs" / "only.md"
                self.assertTrue(target.read_text(encoding="utf-8").startswith("# Only\n"))
                self.assertTrue((repo / SIDECAR_ROOT / "docs.json").is_file())

                flip = run(runtime, "manage_manifest", "set-storage", "--repo", str(repo), "--storage", "markdown")
                self.assertEqual(flip.returncode, 2, "set-storage must no longer exist")

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
                # older branch) while its sidecar entry is gone: sync moves it.
                value = provenance(
                    doc_id="only", path="docs/only.md", tier="spine",
                    target_depth="reference", section_id="only",
                    source_path="source.txt",
                    source_blob=blob_hash((repo / "source.txt").read_bytes()),
                )
                target.write_text(markdown_with_provenance(value, "# Only\n\nBody.\n"), encoding="utf-8")
                sidecar_path = repo / SIDECAR_ROOT / "docs.json"
                sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
                del sidecar["files"]["only.md"]
                sidecar_path.write_text(json.dumps(sidecar, indent=2) + "\n", encoding="utf-8")
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

    def test_dashboard_converts_sidecar_docs_to_id_title_only(self) -> None:
        from test_dashboard import fake_npm_env, run_dashboard, stop_dashboard

        env, _bin = fake_npm_env()
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                self._seed_inline_repo(repo, runtime)
                manifest_path = repo / ".docforge" / "manifest.json"
                run(runtime, "migrate_metadata", "--repo", str(repo), "--manifest", str(manifest_path))
                try:
                    result = run_dashboard(runtime, "start", "--repo", str(repo), "--no-open", env=env)
                    self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                    page = repo / ".docforge" / "dashboard" / "content" / "docs" / "only.mdx"
                    text = page.read_text(encoding="utf-8")
                    self.assertTrue(text.startswith('---\nid: "only"\n'))
                    self.assertIn('title: "Only"', text)
                    head = text.split("\n---\n", 1)[0]
                    self.assertIn('description: "One-liner."', head)
                    self.assertNotIn("docforge_provenance:", head)
                    self.assertIn("# Only\n\nBody.", text)
                finally:
                    stop_dashboard(runtime, repo)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
