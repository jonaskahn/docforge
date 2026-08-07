"""Python/Node parity for the shared evidence_hash helpers: raw/normalized/
range-scoped blob hashing and fresh/cosmetic/stale classification."""

from __future__ import annotations

import json
import subprocess
import unittest

from _support import ROOT

SHARED_ROOT = ROOT / "skills" / "docforge" / "_shared"
JS_MODULE = SHARED_ROOT / "runtime" / "common" / "js" / "evidence_hash.js"

from runtime.common.python.evidence_hash import (
    classify_source,
    line_count,
    normalize_text_bytes,
    normalized_blob_hash,
    range_blob_hash,
    raw_blob_hash,
)


def js_call(function: str, *args: object) -> object:
    """Invoke one exported evidence_hash.js function with JSON-encoded args
    (byte strings passed as latin1-decoded strings, matching a Buffer round
    trip) and return its JSON-decoded result."""
    script = (
        "const m = require(process.argv[1]);"
        "const args = JSON.parse(process.argv[2]).map((a) => "
        "  (a && a.__buffer__) ? Buffer.from(a.data, 'latin1') : a"
        ");"
        f"const result = m.{function}(...args);"
        "process.stdout.write(JSON.stringify("
        "  Buffer.isBuffer(result) ? {__buffer__: true, data: result.toString('latin1')} : result"
        "));"
    )
    encoded_args = [
        {"__buffer__": True, "data": arg.decode("latin1")} if isinstance(arg, bytes) else arg
        for arg in args
    ]
    result = subprocess.run(
        ["node", "-e", script, str(JS_MODULE), json.dumps(encoded_args)],
        text=True, capture_output=True, check=True,
    )
    decoded = json.loads(result.stdout)
    if isinstance(decoded, dict) and decoded.get("__buffer__"):
        return decoded["data"].encode("latin1")
    return decoded


class EvidenceHashParityTests(unittest.TestCase):
    FIXTURES = [
        b"one\ntwo\nthree\n",
        b"one\r\ntwo  \r\nthree\r\n\r\n\r\n",
        b"",
        b"no-trailing-newline",
        b"trailing-blank\n\n\n",
    ]

    def test_raw_blob_hash_matches_across_runtimes(self) -> None:
        for content in self.FIXTURES:
            with self.subTest(content=content):
                self.assertEqual(raw_blob_hash(content), js_call("rawBlobHash", content))

    def test_normalize_text_bytes_matches_across_runtimes(self) -> None:
        for content in self.FIXTURES:
            with self.subTest(content=content):
                self.assertEqual(normalize_text_bytes(content), js_call("normalizeTextBytes", content))

    def test_normalized_blob_hash_matches_across_runtimes(self) -> None:
        for content in self.FIXTURES:
            with self.subTest(content=content):
                self.assertEqual(normalized_blob_hash(content), js_call("normalizedBlobHash", content))

    def test_non_utf8_bytes_return_none_in_both_runtimes(self) -> None:
        binary = bytes([0xFF, 0xFE, 0x00, 0x01, 0x80])
        self.assertIsNone(normalize_text_bytes(binary))
        self.assertIsNone(js_call("normalizeTextBytes", binary))
        self.assertIsNone(normalized_blob_hash(binary))
        self.assertIsNone(js_call("normalizedBlobHash", binary))
        self.assertIsNone(line_count(binary))
        self.assertIsNone(js_call("lineCount", binary))

    def test_range_blob_hash_boundary_cases_match_across_runtimes(self) -> None:
        content = b"l1\nl2\nl3\nl4\nl5\n"
        cases = [(1, 1), (1, 5), (2, 4), (5, 5)]
        for start, end in cases:
            with self.subTest(start=start, end=end):
                self.assertEqual(
                    range_blob_hash(content, start, end),
                    js_call("rangeBlobHash", content, start, end),
                )
        # Out of bounds and invalid orderings both return None in both runtimes.
        for start, end in [(0, 1), (4, 10), (3, 2)]:
            with self.subTest(start=start, end=end, expect_none=True):
                self.assertIsNone(range_blob_hash(content, start, end))
                self.assertIsNone(js_call("rangeBlobHash", content, start, end))

    def test_range_blob_hash_with_and_without_trailing_newline_match(self) -> None:
        for content in (b"a\nb\nc\n", b"a\nb\nc"):
            with self.subTest(content=content):
                self.assertEqual(
                    range_blob_hash(content, 1, 2),
                    js_call("rangeBlobHash", content, 1, 2),
                )

    def test_classify_source_precedence_matches_across_runtimes(self) -> None:
        base = b"l1\nl2\nl3\nl4\nl5\n"
        edited_outside_range = b"l1\nl2\nl3\nl4\nCHANGED\n"
        edited_inside_range = b"l1\nCHANGED\nl3\nl4\nl5\n"

        cases = [
            ("fresh", {"git_blob": raw_blob_hash(base)}, base),
            ("missing", {"git_blob": raw_blob_hash(base)}, None),
            (
                "cosmetic_via_range",
                {
                    "git_blob": raw_blob_hash(base),
                    "evidence_range": {"start": "1", "end": "3"},
                    "range_blob": range_blob_hash(base, 1, 3),
                },
                edited_outside_range,
            ),
            (
                "stale_via_range_edit_inside",
                {
                    "git_blob": raw_blob_hash(base),
                    "evidence_range": {"start": "1", "end": "3"},
                    "range_blob": range_blob_hash(base, 1, 3),
                },
                edited_inside_range,
            ),
            (
                "cosmetic_via_normalized",
                {
                    "git_blob": raw_blob_hash(b"one\ntwo\n"),
                    "git_blob_normalized": normalized_blob_hash(b"one\ntwo\n"),
                },
                b"one\r\ntwo  \r\n",
            ),
            (
                "stale_despite_normalized_present",
                {
                    "git_blob": raw_blob_hash(b"one\ntwo\n"),
                    "git_blob_normalized": normalized_blob_hash(b"one\ntwo\n"),
                },
                b"one\r\nTHREE  \r\n",
            ),
        ]
        for label, source, current in cases:
            with self.subTest(label=label):
                py_result = classify_source(source, current)
                js_result = js_call("classifySource", source, current)
                self.assertEqual(py_result, js_result, f"{label}: py={py_result} js={js_result}")


if __name__ == "__main__":
    unittest.main()
