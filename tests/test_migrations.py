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

from _support import run

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


if __name__ == "__main__":
    raise SystemExit(unittest.main())
