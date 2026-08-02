"""Audience presentation, source-citation, and code-fence policy checks."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _support import blob_hash, initialize, load_manifest, markdown_with_provenance, provenance, run


class PresentationRoutingTests(unittest.TestCase):
    def test_routes_resolve_audience_policy_with_runtime_parity(self) -> None:
        py = run("py", "query_catalog", "--route", "ba_process_flows", "--audience", "engineers", "--audience", "business-analysts")
        js = run("js", "query_catalog", "--route", "ba_process_flows", "--audience", "business-analysts", "--audience", "engineers")
        self.assertEqual(py.returncode, 0, py.stderr)
        self.assertEqual(js.returncode, 0, js.stderr)
        self.assertEqual(py.stdout, js.stdout)
        payload = json.loads(py.stdout)
        self.assertEqual(payload["primary_audience"], "business-analysts")
        self.assertEqual(payload["presentation"]["code"], "contract-only")
        self.assertEqual(payload["presentation"]["repository_paths"], "hidden")
        self.assertEqual(payload["presentation"]["source_evidence"], "provenance-only")

    def test_manifest_snapshot_and_override_invalidate_written_document(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            snapshots = []
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                result = initialize(runtime, repo, "spine")
                self.assertEqual(result.returncode, 0, result.stderr)
                manifest = load_manifest(repo)
                doc = next(item for item in manifest["documents"] if item["id"] == "root_readme")
                self.assertEqual(doc["presentation"]["primary_audience"], "beginners")
                doc["status"] = "complete"
                doc["audit"] = {"mode": "cold-pass", "verdict": "PASS", "timestamp": "x", "report_path": ".docforge/audits/root.md"}
                (repo / ".docforge" / "manifest.json").write_text(json.dumps(manifest) + "\n", encoding="utf-8")
                result = run(runtime, "manage_manifest", "presentation", "--repo", str(repo), "--id", "root_readme", "--related-docs", "none")
                self.assertEqual(result.returncode, 0, result.stderr)
                after = load_manifest(repo)
                doc = next(item for item in after["documents"] if item["id"] == "root_readme")
                self.assertEqual(doc["presentation"]["related_docs"], "none")
                self.assertEqual(doc["presentation_override"], {"related_docs": "none"})
                self.assertEqual(doc["status"], "in_progress")
                self.assertIsNone(doc["audit"])
                snapshots.append(doc["presentation"])
            self.assertEqual(snapshots[0], snapshots[1])


class PresentationLintTests(unittest.TestCase):
    def _document(self, repo: Path, body: str) -> Path:
        (repo / ".docforge").mkdir()
        source = repo / "src" / "worker.py"
        source.parent.mkdir()
        source.write_text("def retry():\n    return True\n", encoding="utf-8")
        doc = repo / "README.md"
        frontmatter = provenance(
            doc_id="root_readme",
            path="README.md",
            tier="spine",
            target_depth="deep-dive",
            section_id="failure-and-recovery",
            source_path="src/worker.py",
            source_blob=blob_hash(source.read_bytes()),
        )
        doc.write_text(markdown_with_provenance(frontmatter, body), encoding="utf-8")
        return doc

    def test_source_links_and_prose_fences_are_rejected_with_parity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            document = self._document(Path(tmp), """# Failure and recovery

[worker source](src/worker.py)

```python
This paragraph explains how retries work in several complete sentences.
It belongs in normal prose because it is not runnable implementation code.
```
""")
            results = [run(runtime, "lint_document", "--file", str(document), "--json") for runtime in ("py", "js")]
            payloads = []
            for result in results:
                self.assertEqual(result.returncode, 1, result.stderr)
                payloads.append(json.loads(result.stdout))
            for payload in payloads:
                kinds = {item["kind"] for item in payload["defects"]}
                self.assertIn("source-code-link", kinds)
                self.assertIn("prose-in-code-fence", kinds)
            self.assertEqual(payloads[0]["defects"], payloads[1]["defects"])

    def test_literal_output_is_not_treated_as_prose(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            document = self._document(Path(tmp), """# Failure and recovery

```text docforge-role=output
Retry attempt 1 failed.
Retry attempt 2 failed.
```
""")
            for runtime in ("py", "js"):
                result = run(runtime, "lint_document", "--file", str(document), "--json")
                payload = json.loads(result.stdout)
                self.assertNotIn("prose-in-code-fence", {item["kind"] for item in payload["defects"]})


if __name__ == "__main__":
    unittest.main()
