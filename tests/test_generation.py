"""generate_indexes: determinism, --check drift detection, --write idempotency.

Runs against the real skill catalog rather than a temp fixture, since the
generator reads the live .metadata/catalog/index.json; every test restores
whatever it mutates so the tracked repository is left unchanged.
"""

from __future__ import annotations

import unittest

from _support import ROOT, run

SKILL_ROOT = ROOT / "skills" / "docforge" / "_shared"
GENERATED_README = SKILL_ROOT / ".metadata" / "catalog" / "documents" / "INDEX.md"


class GenerationTests(unittest.TestCase):
    def test_check_passes_on_current_output(self) -> None:
        for runtime in ("py", "js"):
            result = run(runtime, "generate_indexes", "--check")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_repeated_write_produces_identical_bytes(self) -> None:
        before = GENERATED_README.read_text(encoding="utf-8")
        for runtime in ("py", "js"):
            result = run(runtime, "generate_indexes", "--write")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("no changes", result.stdout)
        after = GENERATED_README.read_text(encoding="utf-8")
        self.assertEqual(before, after)

    def test_cross_runtime_write_is_byte_identical(self) -> None:
        py_result = run("py", "generate_indexes", "--write")
        py_snapshot = GENERATED_README.read_text(encoding="utf-8")
        js_result = run("js", "generate_indexes", "--write")
        js_snapshot = GENERATED_README.read_text(encoding="utf-8")
        self.assertEqual(py_result.returncode, 0)
        self.assertEqual(js_result.returncode, 0)
        self.assertEqual(py_snapshot, js_snapshot)

    def test_check_detects_manual_drift_without_writing(self) -> None:
        original = GENERATED_README.read_text(encoding="utf-8")
        try:
            GENERATED_README.write_text(original + "MUTATED\n", encoding="utf-8")
            for runtime in ("py", "js"):
                result = run(runtime, "generate_indexes", "--check")
                self.assertEqual(result.returncode, 1)
                self.assertIn("documents/INDEX.md", result.stdout)
                # --check must never write.
                self.assertEqual(GENERATED_README.read_text(encoding="utf-8"), original + "MUTATED\n")
        finally:
            GENERATED_README.write_text(original, encoding="utf-8")
        for runtime in ("py", "js"):
            result = run(runtime, "generate_indexes", "--check")
            self.assertEqual(result.returncode, 0, result.stdout)

    def test_no_timestamp_in_generated_output(self) -> None:
        text = GENERATED_README.read_text(encoding="utf-8")
        self.assertNotRegex(text, r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d")

    def test_unknown_flags_and_missing_mode_exit_two(self) -> None:
        for runtime in ("py", "js"):
            result = run(runtime, "generate_indexes", "--bogus")
            self.assertEqual(result.returncode, 2)
            result = run(runtime, "generate_indexes")
            self.assertEqual(result.returncode, 2)
            result = run(runtime, "generate_indexes", "--write", "--check")
            self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
