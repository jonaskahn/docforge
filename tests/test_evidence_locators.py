"""Python/Node parity for evidence_locators' dual-hash (whole-file OR
range-scoped) acceptance of inline `path#Lstart-Lend @ <blob>` citations."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from _support import ROOT
from runtime.common.python.evidence_hash import range_blob_hash, raw_blob_hash
from runtime.common.python.evidence_locators import validate_locators

SHARED_ROOT = ROOT / "skills" / "docforge" / "_shared"
JS_MODULE = SHARED_ROOT / "runtime" / "common" / "js" / "evidence_locators.js"


def js_validate_locators(document: Path, text: str) -> list[dict]:
    script = (
        "const m = require(process.argv[1]);"
        "const defects = m.validateLocators(process.argv[2], process.argv[3]);"
        "process.stdout.write(JSON.stringify(defects));"
    )
    result = subprocess.run(
        ["node", "-e", script, str(JS_MODULE), str(document), text],
        text=True, capture_output=True, check=True,
    )
    return json.loads(result.stdout)


def build_fixture(repo: Path, source_content: bytes, citation_blob: str, start: int, end: int) -> tuple[Path, str]:
    (repo / ".git").mkdir()
    source = repo / "src.py"
    source.write_bytes(source_content)
    doc = repo / "doc.md"
    text = (
        "---\n"
        "docforge_provenance:\n"
        '  schema: "2.1"\n'
        '  doc_id: "d"\n'
        '  path: "doc.md"\n'
        '  generated_at: "2026-07-27T09:12:44Z"\n'
        "  generator:\n"
        '    name: "docforge"\n'
        '    version: "2.17.0"\n'
        '  tier: "spine"\n'
        '  target_depth: "orientation"\n'
        "  graph:\n"
        '    provider: "none"\n'
        '    flow: "none"\n'
        "  sections:\n"
        '    - id: "main"\n'
        "      sources:\n"
        '        - path: "src.py"\n'
        f'          git_blob: "{raw_blob_hash(source_content)}"\n'
        '          role: "code"\n'
        "      unresolved: []\n"
        "---\n"
        "# main\n\n"
        f"Citing src.py#L{start}-L{end} @ {citation_blob}\n"
    )
    doc.write_text(text, encoding="utf-8")
    return doc, text


class EvidenceLocatorsDualHashTests(unittest.TestCase):
    def test_whole_file_citation_edited_outside_range_still_validates(self) -> None:
        """Behavior unchanged: an old, whole-file-stamped citation keeps
        validating against edits outside its cited range (it was never
        range-scoped to begin with)."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            content = b"line1\nline2\nline3\nline4\n"
            whole_file_blob = raw_blob_hash(content)
            doc, text = build_fixture(repo, content, whole_file_blob, 2, 2)
            # Edit outside the cited line (line 4); whole-file blob no longer matches.
            (repo / "src.py").write_bytes(b"line1\nline2\nline3\nCHANGED\n")
            py_defects = validate_locators(doc, text)
            js_defects = js_validate_locators(doc, text)
            self.assertEqual(py_defects, js_defects)
            kinds = {d["kind"] for d in py_defects}
            self.assertIn("stale evidence blob", kinds)

    def test_whole_file_citation_edited_inside_range_flags_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            content = b"line1\nline2\nline3\nline4\n"
            whole_file_blob = raw_blob_hash(content)
            doc, text = build_fixture(repo, content, whole_file_blob, 2, 2)
            # Edit inside the cited line (line 2).
            (repo / "src.py").write_bytes(b"line1\nCHANGED\nline3\nline4\n")
            py_defects = validate_locators(doc, text)
            js_defects = js_validate_locators(doc, text)
            self.assertEqual(py_defects, js_defects)
            kinds = {d["kind"] for d in py_defects}
            self.assertIn("stale evidence blob", kinds)

    def test_range_stamped_citation_edited_outside_range_validates_cleanly(self) -> None:
        """The actual fix: a citation stamped against just its cited range
        survives an edit elsewhere in the file, unlike the old whole-file-only
        check."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            content = b"line1\nline2\nline3\nline4\n"
            range_blob = range_blob_hash(content, 2, 2)
            doc, text = build_fixture(repo, content, range_blob, 2, 2)
            # Edit outside the cited line (line 4); range-scoped blob still matches.
            (repo / "src.py").write_bytes(b"line1\nline2\nline3\nCHANGED\n")
            py_defects = validate_locators(doc, text)
            js_defects = js_validate_locators(doc, text)
            self.assertEqual(py_defects, js_defects)
            kinds = {d["kind"] for d in py_defects}
            self.assertNotIn("stale evidence blob", kinds)

    def test_range_stamped_citation_edited_inside_range_flags_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            content = b"line1\nline2\nline3\nline4\n"
            range_blob = range_blob_hash(content, 2, 2)
            doc, text = build_fixture(repo, content, range_blob, 2, 2)
            # Edit inside the cited line (line 2); neither whole-file nor range matches.
            (repo / "src.py").write_bytes(b"line1\nCHANGED\nline3\nline4\n")
            py_defects = validate_locators(doc, text)
            js_defects = js_validate_locators(doc, text)
            self.assertEqual(py_defects, js_defects)
            kinds = {d["kind"] for d in py_defects}
            self.assertIn("stale evidence blob", kinds)


if __name__ == "__main__":
    unittest.main()
