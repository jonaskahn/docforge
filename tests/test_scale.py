"""Project-scale classification, `project.scale` recording, and migration
backfill — Python/Node parity throughout.

The classification helper (`compute_scale` / `computeScale`) is a shared
library with three classes keyed on source-file count, a confirmed-profile
nudge at class boundaries, and a layout suggestion that never overrides a
user decision recorded on the manifest.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _support import ROOT, initialize, load_manifest, run

SHARED_ROOT = ROOT / "skills" / "docforge" / "_shared"
sys.path.insert(0, str(SHARED_ROOT))


def compute_scale_py(repo: Path) -> dict:
    from runtime.common.python.scale import compute_scale
    return compute_scale(repo)


def compute_scale_js(repo: Path) -> dict:
    result = subprocess.run(
        [
            "node", "-e",
            "const {computeScale}=require(process.argv[1]);"
            "process.stdout.write(JSON.stringify(computeScale(process.argv[2])));",
            str(SHARED_ROOT / "runtime" / "common" / "js" / "scale.js"),
            str(repo),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def seed_source_files(repo: Path, count: int) -> None:
    src = repo / "src"
    src.mkdir(parents=True, exist_ok=True)
    for index in range(count):
        (src / f"mod_{index}.py").write_text("x = 1\n", encoding="utf-8")


def seed_three_confirmed_profiles(repo: Path) -> None:
    """`express` confirms frameworks/express and shapes/api-service;
    `fastapi` confirms frameworks/fastapi — three strong detections."""
    (repo / "package.json").write_text(
        json.dumps({"dependencies": {"express": "^4.19.0"}}), encoding="utf-8",
    )
    (repo / "pyproject.toml").write_text(
        '[project]\ndependencies = ["fastapi>=0.110"]\n', encoding="utf-8",
    )


class ScaleClassificationTests(unittest.TestCase):
    def test_thresholds_and_layout_suggestion(self) -> None:
        for count, expected, layout in ((7, "small", "compact"), (60, "medium", "standard"), (400, "large", "standard")):
            with self.subTest(count=count):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    seed_source_files(repo, count)
                    py = compute_scale_py(repo)
                    js = compute_scale_js(repo)
                    self.assertEqual(py, js)
                    self.assertEqual(py["class"], expected)
                    self.assertEqual(py["suggested_layout"], layout)
                    self.assertEqual(py["signals"]["tracked_files"], count)
                    self.assertEqual(py["signals"]["source_files"], count)
                    self.assertEqual(py["signals"]["confirmed_profiles"], 0)

    def test_confirmed_profiles_nudge_boundary_up_one_class(self) -> None:
        # 12 source files: below the nudge zone (80% of 16 is 12.8) — stays small.
        with tempfile.TemporaryDirectory() as tmp:
            small_repo = Path(tmp) / "twelve"
            small_repo.mkdir()
            seed_source_files(small_repo, 12)
            seed_three_confirmed_profiles(small_repo)
            py = compute_scale_py(small_repo)
            self.assertEqual(py, compute_scale_js(small_repo))
            self.assertEqual(py["class"], "small")
            self.assertEqual(py["signals"]["confirmed_profiles"], 3)
            self.assertEqual(py["signals"]["tracked_files"], 14)
        # 13 source files: inside the nudge zone — nudged to medium.
        with tempfile.TemporaryDirectory() as tmp:
            nudge_repo = Path(tmp) / "thirteen"
            nudge_repo.mkdir()
            seed_source_files(nudge_repo, 13)
            seed_three_confirmed_profiles(nudge_repo)
            py = compute_scale_py(nudge_repo)
            self.assertEqual(py, compute_scale_js(nudge_repo))
            self.assertEqual(py["class"], "medium")
            self.assertEqual(py["signals"]["confirmed_profiles"], 3)

    def test_ignored_directories_never_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_source_files(repo, 3)
            (repo / "node_modules" / "pkg").mkdir(parents=True)
            (repo / "node_modules" / "pkg" / "index.js").write_text("x\n", encoding="utf-8")
            (repo / ".git").mkdir()
            (repo / ".docforge").mkdir()
            py = compute_scale_py(repo)
            self.assertEqual(py, compute_scale_js(repo))
            self.assertEqual(py["signals"]["tracked_files"], 3)


class ScaleRecordTests(unittest.TestCase):
    def test_init_records_detected_scale(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    seed_source_files(repo, 7)
                    self.assertEqual(initialize(runtime, repo, "spine", layout=None).returncode, 0)
                    scale = load_manifest(repo)["project"]["scale"]
                    self.assertEqual(scale["class"], "small")
                    self.assertEqual(scale["layout"], "compact")
                    self.assertEqual(scale["decided_by"], "detected")
                    self.assertNotIn("detected_class", scale)
                    self.assertEqual(scale["signals"]["source_files"], 7)

    def test_init_explicit_flags_record_user_override(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    seed_source_files(repo, 7)
                    result = run(
                        runtime, "manage_manifest", "init", "--repo", str(repo),
                        "--tier", "spine", "--scale-class", "large",
                        "--layout", "standard",
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    scale = load_manifest(repo)["project"]["scale"]
                    self.assertEqual(scale["class"], "large")
                    self.assertEqual(scale["layout"], "standard")
                    self.assertEqual(scale["decided_by"], "user")
                    self.assertEqual(scale["detected_class"], "small")
                    self.assertEqual(scale["signals"]["source_files"], 7)

    def test_migrate_backfills_missing_scale(self) -> None:
        for from_version in ("3.3", "3.4"):
            for runtime in ("py", "js"):
                with self.subTest(runtime=runtime, from_version=from_version):
                    with tempfile.TemporaryDirectory() as tmp:
                        repo = Path(tmp)
                        seed_source_files(repo, 5)
                        self.assertEqual(initialize(runtime, repo, "spine").returncode, 0)
                        manifest_path = repo / ".docforge" / "manifest.json"
                        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                        manifest["version"] = from_version
                        del manifest["project"]["scale"]
                        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
                        migrated = run(runtime, "migrate_metadata", "--repo", str(repo))
                        self.assertIn(migrated.returncode, (0, 1), migrated.stderr)
                        reloaded = load_manifest(repo)
                        self.assertEqual(reloaded["version"], "3.6")
                        scale = reloaded["project"]["scale"]
                        self.assertEqual(scale["class"], "small")
                        self.assertEqual(scale["layout"], "compact")
                        self.assertEqual(scale["decided_by"], "detected")
                        self.assertEqual(scale["signals"]["source_files"], 5)

    def test_migrate_never_overwrites_existing_scale(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    seed_source_files(repo, 5)
                    self.assertEqual(initialize(runtime, repo, "spine").returncode, 0)
                    manifest_path = repo / ".docforge" / "manifest.json"
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    manifest["version"] = "3.4"
                    manifest["project"]["scale"] = {
                        "class": "large",
                        "layout": "standard",
                        "detected_class": "small",
                        "decided_by": "user",
                        "decided_at": "2026-01-01T00:00:00+00:00",
                        "signals": {"tracked_files": 5, "source_files": 5, "confirmed_profiles": 0},
                    }
                    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
                    migrated = run(runtime, "migrate_metadata", "--repo", str(repo))
                    self.assertIn(migrated.returncode, (0, 1), migrated.stderr)
                    reloaded = load_manifest(repo)
                    self.assertEqual(reloaded["version"], "3.6")
                    scale = reloaded["project"]["scale"]
                    self.assertEqual(scale["class"], "large")
                    self.assertEqual(scale["decided_by"], "user")
                    self.assertEqual(scale["decided_at"], "2026-01-01T00:00:00+00:00")


class ScaleWalkCostTests(unittest.TestCase):
    def test_compute_scale_walks_the_repository_once(self) -> None:
        """`compute_scale` needs both a file inventory and the confirmed-profile
        count, and detection derives the latter from the same inventory. Taking
        both from one walk is the whole point of the helper; it used to call
        `inventory` and then `detect` (which walks again)."""
        from runtime.catalog.python import detect_profiles
        from runtime.common.python import scale as scale_module

        original = detect_profiles.inventory
        walks = []

        def counting(repo: Path):
            walks.append(repo)
            return original(repo)

        detect_profiles.inventory = counting
        try:
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                seed_source_files(repo, 5)
                walks.clear()
                scale_module.compute_scale(repo)
                self.assertEqual(len(walks), 1, f"expected one walk, got {len(walks)}")
        finally:
            detect_profiles.inventory = original

    def test_init_walks_the_repository_once(self) -> None:
        """`init` needs the inventory for discovery and for scale; it must not
        pay for the walk twice (it paid three times)."""
        import contextlib
        import io

        from runtime.catalog.python import detect_profiles
        import runtime.manifest.python.manage_manifest as manage_manifest

        original = detect_profiles.inventory
        walks = []

        def counting(repo: Path):
            walks.append(repo)
            return original(repo)

        detect_profiles.inventory = counting
        manage_manifest.inventory_files = counting
        original_argv = list(sys.argv)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                seed_source_files(repo, 5)
                sys.argv = ["manage_manifest.py", "init", "--repo", str(repo), "--tier", "spine"]
                walks.clear()
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(manage_manifest.main(), 0)
                self.assertEqual(len(walks), 1, f"expected one walk, got {len(walks)}")
        finally:
            detect_profiles.inventory = original
            manage_manifest.inventory_files = original
            sys.argv = original_argv


class ScaleBackfillGuardTests(unittest.TestCase):
    def test_migrate_repairs_a_scale_record_of_the_wrong_type(self) -> None:
        """The backfill guard must test the shape, not truthiness: a truthy
        non-object `scale` is not a usable record, and leaving it in place
        emits a manifest that fails the schema. Python tested the type and
        Node tested truthiness, so the two peers disagreed."""
        for runtime in ("py", "js"):
            for bogus in ("small", 3, ["small"]):
                with self.subTest(runtime=runtime, bogus=bogus):
                    with tempfile.TemporaryDirectory() as tmp:
                        repo = Path(tmp)
                        seed_source_files(repo, 5)
                        self.assertEqual(initialize(runtime, repo, "spine").returncode, 0)
                        manifest_path = repo / ".docforge" / "manifest.json"
                        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                        manifest["version"] = "3.4"
                        manifest["project"]["scale"] = bogus
                        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
                        migrated = run(runtime, "migrate_metadata", "--repo", str(repo))
                        self.assertIn(migrated.returncode, (0, 1), migrated.stderr)
                        scale = load_manifest(repo)["project"]["scale"]
                        self.assertIsInstance(scale, dict)
                        self.assertEqual(
                            set(scale) >= {"class", "layout", "decided_by", "decided_at", "signals"},
                            True,
                            scale,
                        )


class ScaleSchemaTests(unittest.TestCase):
    def test_manifest_schema_requires_scale(self) -> None:
        schema = json.loads(
            (SHARED_ROOT / ".metadata" / "manifest-schema.json").read_text(encoding="utf-8"),
        )
        self.assertIn("scale", schema["properties"]["project"]["required"])
        scale = schema["properties"]["project"]["properties"]["scale"]
        self.assertEqual(
            set(scale["required"]),
            {"class", "layout", "decided_by", "decided_at", "signals"},
        )
        self.assertEqual(scale["properties"]["class"]["enum"], ["small", "medium", "large"])
        self.assertEqual(scale["properties"]["layout"]["enum"], ["compact", "standard"])
        self.assertEqual(scale["properties"]["decided_by"]["enum"], ["detected", "user"])
        self.assertEqual(
            set(scale["properties"]["signals"]["required"]),
            {"tracked_files", "source_files", "confirmed_profiles"},
        )


if __name__ == "__main__":
    unittest.main()
