"""Profile detection, alias normalization, and discovery-gate behavior."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _support import ROOT, initialize, load_manifest, normalized, run


class ProfileSelectionTests(unittest.TestCase):
    def test_all_canonical_profiles_are_accepted_and_frameworks_add_no_tree(self) -> None:
        index = json.loads(
            (ROOT / "skills" / "docforge" / "_shared" / ".metadata" / "catalog" / "index.json")
            .read_text(encoding="utf-8")
        )
        profiles_dir = ROOT / "skills" / "docforge" / "_shared" / ".metadata" / "catalog" / "profiles"
        catalog_profiles = {
            dimension: json.loads((profiles_dir / f"{dimension}.json").read_text(encoding="utf-8"))
            for dimension in ("shapes", "platforms", "frameworks", "concerns", "audiences")
        }
        with tempfile.TemporaryDirectory() as tmp:
            base_repo = Path(tmp) / "base"
            profile_repo = Path(tmp) / "profiles"
            base_repo.mkdir()
            profile_repo.mkdir()
            self.assertEqual(initialize("py", base_repo, "spine").returncode, 0)
            args = ["init", "--repo", str(profile_repo), "--tier", "spine"]
            flag_for = {
                "shapes": "--shape",
                "platforms": "--platform",
                "frameworks": "--framework",
                "concerns": "--concern",
                "audiences": "--audience",
            }
            for dimension, definitions in catalog_profiles.items():
                for definition in definitions:
                    args += [flag_for[dimension], definition["id"]]
            result = run("py", "manage_manifest", *args)
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = load_manifest(profile_repo)
            for dimension, definitions in catalog_profiles.items():
                self.assertEqual(
                    manifest["project"]["profiles"][dimension],
                    [item["id"] for item in definitions],
                )

            framework_repo = Path(tmp) / "frameworks"
            framework_repo.mkdir()
            framework_args = [
                item
                for definition in catalog_profiles["frameworks"]
                for item in ("--framework", definition["id"])
            ]
            framework_result = run(
                "py", "manage_manifest", "init",
                "--repo", str(framework_repo), "--tier", "spine",
                *framework_args,
            )
            self.assertEqual(framework_result.returncode, 0, framework_result.stderr)
            base_paths = {doc["path"] for doc in load_manifest(base_repo)["documents"]}
            framework_paths = {
                doc["path"] for doc in load_manifest(framework_repo)["documents"]
            }
            self.assertEqual(framework_paths, base_paths)
        self.assertGreater(len(index["document_types"]), 0)

    def test_aliases_normalize_and_obsolete_overlay_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                result = run(
                    runtime, "manage_manifest", "init",
                    "--repo", str(repo), "--tier", "diligence",
                    "--shape", "desktop", "--shape", "desktop-app",
                    "--platform", "mac", "--audience", "agent",
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                profiles = load_manifest(repo)["project"]["profiles"]
                self.assertEqual(profiles["shapes"], ["desktop-app"])
                self.assertEqual(profiles["platforms"], ["macos"])
                self.assertEqual(profiles["audiences"], ["coding-agents"])
                obsolete = run(
                    runtime, "manage_manifest", "init",
                    "--repo", str(repo), "--tier", "spine",
                    "--overlay", "agent", "--force",
                )
                self.assertEqual(obsolete.returncode, 2)
                self.assertIn("--overlay is unsupported in Docforge 2.0", obsolete.stderr)

    def test_desktop_mobile_and_specialized_shape_packs(self) -> None:
        expected = {
            "desktop-app": {
                "docs/architecture/application-lifecycle.md",
                "docs/architecture/ui-and-state.md",
                "docs/architecture/platform-integration.md",
                "docs/security/permissions.md",
                "docs/reference/platform-compatibility.md",
                "docs/operations/distribution.md",
            },
            "cli-tui": {
                "docs/reference/commands.md",
                "docs/reference/output-and-exit-codes.md",
                "docs/operations/distribution.md",
            },
            "embedded-iot": {
                "docs/architecture/hardware-map.md",
                "docs/architecture/firmware-lifecycle.md",
                "docs/operations/flashing-and-recovery.md",
            },
            "smart-contract": {
                "docs/architecture/contract-system.md",
                "docs/security/economic-invariants.md",
                "docs/operations/network-deployment.md",
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            for shape, required in expected.items():
                repo = Path(tmp) / shape
                repo.mkdir()
                result = initialize("py", repo, "spine", shapes=(shape,))
                self.assertEqual(result.returncode, 0, result.stderr)
                paths = {doc["path"] for doc in load_manifest(repo)["documents"]}
                self.assertTrue(required <= paths, (shape, required - paths))

    def test_profile_detection_for_native_macos_mixed_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            project = repo / "EasyKey.xcodeproj"
            project.mkdir()
            (project / "project.pbxproj").write_text(
                "SDKROOT = macosx; com.apple.product-type.framework;\n",
                encoding="utf-8",
            )
            source = repo / "App.swift"
            source.write_text(
                "import SwiftUI\nimport AppKit\n// accessibility Keychain SMAppService\n",
                encoding="utf-8",
            )
            (repo / "Localizable.xcstrings").write_text("{}\n", encoding="utf-8")
            outputs = []
            detected_payloads = []
            for runtime in ("py", "js"):
                result = run(runtime, "detect_profiles", "--repo", str(repo), "--json")
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                detected = {
                    (item["dimension"], item["id"]): item["confidence"]
                    for item in payload["detections"]
                }
                for item in (
                    ("shapes", "desktop-app"),
                    ("shapes", "library-sdk"),
                    ("platforms", "macos"),
                    ("frameworks", "swiftui"),
                    ("frameworks", "appkit"),
                    ("concerns", "localization"),
                    ("concerns", "secure-storage"),
                    ("concerns", "login-helper"),
                ):
                    self.assertIn(item, detected)
                outputs.append(normalized(result.stdout, [repo]))
                if runtime == "py":
                    init_result = initialize(
                        runtime, repo, "spine",
                        shapes=("desktop-app", "library-sdk"),
                        platforms=("macos",),
                        frameworks=("swiftui", "appkit"),
                        concerns=("localization", "secure-storage", "login-helper"),
                    )
                else:
                    init_result = run(
                        runtime, "manage_manifest", "init",
                        "--repo", str(repo), "--tier", "spine",
                        "--shape", "desktop-app", "--shape", "library-sdk",
                        "--platform", "macos",
                        "--framework", "swiftui", "--framework", "appkit",
                        "--concern", "localization",
                        "--concern", "secure-storage",
                        "--concern", "login-helper",
                        "--force",
                    )
                self.assertEqual(init_result.returncode, 0, init_result.stderr)
                saved = load_manifest(repo)
                self.assertNotIn(
                    "accessibility", saved["project"]["profiles"]["concerns"],
                )
                detected_payloads.append(saved["discovery"])
            self.assertEqual(outputs[0], outputs[1])
            self.assertEqual(detected_payloads[0], detected_payloads[1])
            self.assertTrue(detected_payloads[0])

    def test_structured_dependency_detection(self) -> None:
        cases = {
            # React app: react + express detected from declared npm dependencies.
            "react-app": (
                {"package.json": '{"dependencies":{"react":"^18","react-dom":"^18","express":"^4"}}'},
                {("frameworks", "react"), ("frameworks", "express"), ("shapes", "api-service")},
                set(),
            ),
            # Substring bleed: react-dom/preact alone must NOT match react.
            "no-react": (
                {"package.json": '{"dependencies":{"react-dom":"^18","preact":"^10"}}'},
                set(),
                {("frameworks", "react")},
            ),
            # Case insensitivity: lowercase django in requirements.txt still matches.
            "django-lower": (
                {"requirements.txt": "django==5.0\ngunicorn\n"},
                {("frameworks", "django")},
                set(),
            ),
            # Bleed fix: torchvision without torch must not detect pytorch/ml-system.
            "torchvision-only": (
                {"pyproject.toml": '[project]\nname = "x"\ndependencies = ["torchvision>=0.1"]\n'},
                set(),
                {("frameworks", "pytorch"), ("shapes", "ml-system")},
            ),
            # torch present detects both.
            "torch": (
                {"pyproject.toml": '[project]\nname = "x"\ndependencies = ["torch>=2.0"]\n'},
                {("frameworks", "pytorch"), ("shapes", "ml-system")},
                set(),
            ),
            # Maven groupId identifies spring-boot.
            "spring": (
                {"pom.xml": "<project><dependencies><dependency>"
                 "<groupId>org.springframework.boot</groupId>"
                 "<artifactId>spring-boot-starter-web</artifactId>"
                 "</dependency></dependencies></project>"},
                {("frameworks", "spring-boot")},
                set(),
            ),
            # Malformed manifests must not crash and must detect nothing spurious.
            "malformed": (
                {"package.json": '{"dependencies": {bad', "pyproject.toml": "[project\nbroken"},
                set(),
                {("frameworks", "react"), ("frameworks", "pytorch")},
            ),
        }
        for label, (files, expected, forbidden) in cases.items():
            with self.subTest(case=label):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    for name, content in files.items():
                        (repo / name).write_text(content, encoding="utf-8")
                    outputs = []
                    for runtime in ("py", "js"):
                        result = run(runtime, "detect_profiles", "--repo", str(repo), "--json")
                        self.assertEqual(result.returncode, 0, result.stderr)
                        payload = json.loads(result.stdout)
                        detected = {(item["dimension"], item["id"]) for item in payload["detections"]}
                        self.assertTrue(expected <= detected, f"{label}/{runtime}: missing {expected - detected}")
                        self.assertFalse(forbidden & detected, f"{label}/{runtime}: unexpected {forbidden & detected}")
                        outputs.append(normalized(result.stdout, [repo]))
                    self.assertEqual(outputs[0], outputs[1])

    def test_weak_vs_strong_signal_confidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src" / "models").mkdir(parents=True)
            (repo / "src" / "models" / "user.py").write_text("class User: pass\n", encoding="utf-8")
            outputs = []
            for runtime in ("py", "js"):
                result = run(runtime, "detect_profiles", "--repo", str(repo), "--json")
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                by_id = {
                    (item["dimension"], item["id"]): item
                    for item in payload["detections"]
                }
                ml = by_id.get(("shapes", "ml-system"))
                self.assertIsNotNone(ml)
                self.assertEqual(ml["confidence"], "candidate")
                self.assertEqual(ml["match_strength"], "weak")
                self.assertTrue(any(cue.startswith("path:") for cue in ml["cues"]))
                outputs.append(normalized(result.stdout, [repo]))
            self.assertEqual(outputs[0], outputs[1])

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "requirements.txt").write_text("django==5.0\n", encoding="utf-8")
            (repo / "app" / "models").mkdir(parents=True)
            (repo / "app" / "models" / "user.py").write_text("from django.db import models\n", encoding="utf-8")
            for runtime in ("py", "js"):
                result = run(runtime, "detect_profiles", "--repo", str(repo), "--json")
                self.assertEqual(result.returncode, 0, result.stderr)
                by_id = {
                    (item["dimension"], item["id"]): item
                    for item in json.loads(result.stdout)["detections"]
                }
                self.assertEqual(by_id[("concerns", "persistence")]["confidence"], "confirmed")
                self.assertEqual(by_id[("frameworks", "django")]["confidence"], "confirmed")
                if ("shapes", "ml-system") in by_id:
                    self.assertEqual(by_id[("shapes", "ml-system")]["confidence"], "candidate")

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "package.json").write_text(
                '{"dependencies":{"openai":"^4.0.0"}}',
                encoding="utf-8",
            )
            for runtime in ("py", "js"):
                result = run(runtime, "detect_profiles", "--repo", str(repo), "--json")
                self.assertEqual(result.returncode, 0, result.stderr)
                by_id = {
                    (item["dimension"], item["id"]): item
                    for item in json.loads(result.stdout)["detections"]
                }
                self.assertEqual(by_id[("concerns", "ai-ml")]["confidence"], "confirmed")
                self.assertEqual(by_id[("concerns", "ai-ml")]["match_strength"], "strong")

    def test_discovery_gate_pack_and_judgment(self) -> None:
        from discovery_gate import apply_judgment, validate_judgment

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "requirements.txt").write_text("django==5.0\n", encoding="utf-8")
            (repo / "app" / "models").mkdir(parents=True)
            (repo / "app" / "models" / "user.py").write_text("class User: pass\n", encoding="utf-8")
            packs = []
            for runtime in ("py", "js"):
                result = run(runtime, "detect_profiles", "--repo", str(repo), "--emit-gate-pack")
                self.assertEqual(result.returncode, 0, result.stderr)
                pack = json.loads(result.stdout)
                self.assertTrue(pack["needs_gate"])
                self.assertIn("cues", pack)
                self.assertIn("catalog_ids", pack)
                packs.append(normalized(result.stdout, [repo]))
            self.assertEqual(packs[0], packs[1])
            pack = json.loads(run("py", "detect_profiles", "--repo", str(repo), "--emit-gate-pack").stdout)
            good = {
                "version": 1,
                "decisions": [
                    {
                        "dimension": "concerns",
                        "id": "persistence",
                        "action": "promote",
                        "confidence": "confirmed",
                        "reason": "Django ORM entities under app/models/.",
                        "grounded_cues": ["path:models", "dep:pip:django"],
                    },
                    {
                        "dimension": "shapes",
                        "id": "ml-system",
                        "action": "drop",
                        "confidence": "suppressed",
                        "reason": "models/ is ORM; no training stack.",
                        "grounded_cues": ["path:models"],
                    },
                ],
                "notes_for_user": "Treating models/ as persistence.",
            }
            self.assertEqual(validate_judgment(good, pack), [])
            applied = apply_judgment(pack["detections"], good, pack)
            self.assertTrue(applied["ok"])
            recommended_ids = {(row["dimension"], row["id"]) for row in applied["recommended"]}
            dismissed_ids = {(row["dimension"], row["id"]) for row in applied["dismissed"]}
            self.assertIn(("concerns", "persistence"), recommended_ids)
            self.assertIn(("shapes", "ml-system"), dismissed_ids)
            bad = {
                "version": 1,
                "decisions": [{
                    "dimension": "concerns",
                    "id": "not-a-real-concern",
                    "action": "propose",
                    "confidence": "candidate",
                    "reason": "invented",
                }],
                "notes_for_user": "bad",
            }
            self.assertTrue(validate_judgment(bad, pack))
            failed = apply_judgment(pack["detections"], bad, pack)
            self.assertFalse(failed["ok"])

    def test_glob_matcher_single_star_does_not_cross_slash(self) -> None:
        from runtime.catalog.python.detect_profiles import matches_path

        self.assertTrue(matches_path("src/app.py", "src/*.py"))
        self.assertFalse(matches_path("src/nested/app.py", "src/*.py"))
        self.assertTrue(matches_path("src/nested/app.py", "src/**/*.py"))


if __name__ == "__main__":
    unittest.main()
