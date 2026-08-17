"""Audience presentation, source-citation, and code-fence policy checks."""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from _support import ROOT, blob_hash, initialize, load_manifest, markdown_with_provenance, provenance, run


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


SHARED = ROOT / "skills" / "docforge" / "_shared"
AGENT_CONTENT = SHARED / "content" / "agent-context"
AGENT_TEMPLATES = AGENT_CONTENT / "templates"
AGENT_CATALOG = SHARED / ".metadata" / "catalog" / "documents" / "agent-context"
FORBIDDEN_TEMPLATE_REFERENCES = (
    ("Markdown link", re.compile(r"!?\[[^\]\n]*\]\([^)\n]*\)")),
    ("raw URL", re.compile(r"\bhttps?://")),
    (
        "@ import",
        re.compile(
            r"(?<![\w@])@((?:(?:\.{1,2}/|/)?[\w.~+-]+)(?:/[\w.~+-]+)*/?"
            r"(?:#[\w.~:-]+)?)"
        ),
    ),
    (
        "document path",
        re.compile(
            r"(?<![\w@])(?:(?:\.{1,2}/|/)?(?:[\w.~+-]+/)*[\w.~+-]+\."
            r"(?:md|mdx|markdown|rst|adoc|asciidoc)(?:#[\w.~:-]+)?|"
            r"docs/[\w.~+/-]*)",
            re.IGNORECASE,
        ),
    ),
)


class PermanentAgentIsolationTests(unittest.TestCase):
    def _records(self) -> list[dict]:
        index = json.loads((AGENT_CATALOG / "index.json").read_text(encoding="utf-8"))
        return [
            json.loads((AGENT_CATALOG / item["path"]).read_text(encoding="utf-8"))
            for item in index["records"]
        ]

    def _agent_documents(self, manifest: dict) -> dict[str, dict]:
        return {
            doc["id"]: doc
            for doc in manifest["documents"]
            if doc["group"] == "agent-context"
        }

    def test_every_generated_agent_template_is_reference_free(self) -> None:
        records = self._records()
        template_files = {record["template_file"] for record in records}

        self.assertIn("content/agent-context/templates/agents-kernel.md", template_files)
        self.assertIn("content/compact/templates/agents.template.md", template_files)
        self.assertIn("content/agent-context/templates/claude-local-md.md", template_files)
        self.assertIn("content/agent-context/templates/claude-settings.json", template_files)
        self.assertTrue(
            any(path.endswith("agents-architecture.md") for path in template_files),
            "topic templates were not included",
        )
        self.assertNotIn("README.md", {Path(path).name for path in template_files})

        for relative in sorted(template_files):
            target = SHARED / relative
            with self.subTest(template=relative):
                self.assertTrue(target.is_file(), f"missing generated-output template: {relative}")
                body = target.read_text(encoding="utf-8")
                for kind, pattern in FORBIDDEN_TEMPLATE_REFERENCES:
                    self.assertIsNone(pattern.search(body), f"{relative} contains a forbidden {kind}")

    def test_catalog_records_are_permanently_isolated(self) -> None:
        for record in self._records():
            with self.subTest(document=record["id"]):
                self.assertEqual(record["presentation"]["related_docs"], "none")
                self.assertNotEqual(record["selection"]["mode"], "standalone")
                self.assertFalse([key for key in record if "variant" in key], record)
                self.assertNotIn("/standalone/", record["template_file"])
                self.assertNotIn("standalone", record["instruction_file"])
                self.assertTrue((SHARED / record["template_file"]).is_file())
                self.assertTrue((SHARED / record["instruction_file"]).is_file())

        standalone = AGENT_TEMPLATES / "standalone"
        standalone_outputs = (
            [
                path
                for path in standalone.rglob("*")
                if path.is_file() and path.name.casefold() != "readme.md"
            ]
            if standalone.exists()
            else []
        )
        self.assertEqual(standalone_outputs, [], "standalone generated templates still exist")
        self.assertFalse((AGENT_CONTENT / "agents-standalone.instruction.md").exists())

    def test_agent_only_and_mixed_runs_share_canonical_agent_inputs(self) -> None:
        catalog = {record["id"]: record for record in self._records()}
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                agent_only_repo = root / "agent-only"
                mixed_repo = root / "mixed"
                agent_only_repo.mkdir()
                mixed_repo.mkdir()

                agent_only_result = initialize(
                    runtime,
                    agent_only_repo,
                    "spine",
                    audiences=("coding-agents",),
                    layout="standard",
                    groups=("agents",),
                )
                mixed_result = initialize(
                    runtime,
                    mixed_repo,
                    "spine",
                    audiences=("coding-agents",),
                    layout="standard",
                )
                self.assertEqual(agent_only_result.returncode, 0, agent_only_result.stderr)
                self.assertEqual(mixed_result.returncode, 0, mixed_result.stderr)

                agent_only = load_manifest(agent_only_repo)
                mixed = load_manifest(mixed_repo)
                self.assertNotIn("agent_context", agent_only["project"])
                self.assertNotIn("agent_context", mixed["project"])

                agent_only_docs = self._agent_documents(agent_only)
                mixed_docs = self._agent_documents(mixed)
                self.assertTrue(agent_only_docs)
                self.assertEqual(agent_only_docs.keys(), mixed_docs.keys())
                self.assertFalse(
                    [doc for doc in agent_only["documents"] if doc["group"] != "agent-context"],
                    "agent-only fixture unexpectedly contains human documentation",
                )
                self.assertTrue(
                    [doc for doc in mixed["documents"] if doc["group"] != "agent-context"],
                    "mixed fixture must contain human documentation",
                )

                for doc_id, agent_only_doc in agent_only_docs.items():
                    with self.subTest(runtime=runtime, document=doc_id):
                        mixed_doc = mixed_docs[doc_id]
                        expected = catalog[doc_id]
                        agent_only_pointer = (
                            agent_only_doc["scaffold_template"],
                            agent_only_doc["instruction_file"],
                        )
                        mixed_pointer = (
                            mixed_doc["scaffold_template"],
                            mixed_doc["instruction_file"],
                        )
                        self.assertEqual(agent_only_pointer, mixed_pointer)
                        self.assertEqual(
                            agent_only_pointer,
                            (expected["template_file"], expected["instruction_file"]),
                        )
                        self.assertEqual(agent_only_doc["presentation"]["related_docs"], "none")
                        self.assertEqual(mixed_doc["presentation"]["related_docs"], "none")
                        self.assertNotIn("standalone", " ".join(agent_only_pointer))


if __name__ == "__main__":
    unittest.main()
