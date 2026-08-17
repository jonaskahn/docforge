"""Audience presentation, source-citation, and code-fence policy checks."""

from __future__ import annotations

import json
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
HUMAN_TREE_LINKS = (
    "../architecture/", "../engineering/", "../reference/", "../flows/",
    "../product/", "../operations/", "../security/",
)


class StandaloneAgentContentTests(unittest.TestCase):
    """In standalone mode the agent views own their facts, because no
    human-facing document was generated to link. A link into the human tree is
    then both a dead link and a fact with no owner."""

    STANDALONE_TEMPLATES = SHARED / "content" / "agent-context" / "templates" / "standalone"

    def test_standalone_templates_never_link_the_human_tree(self) -> None:
        targets = sorted(self.STANDALONE_TEMPLATES.glob("*.md"))
        self.assertTrue(targets, "standalone templates must exist")
        for target in targets:
            with self.subTest(template=target.name):
                body = target.read_text(encoding="utf-8")
                for prefix in HUMAN_TREE_LINKS:
                    self.assertNotIn(f"]({prefix}", body)

    def test_linked_templates_still_link_their_owners(self) -> None:
        """The linked mode is unchanged; standalone is additive."""
        linked = SHARED / "content" / "agent-context" / "templates"
        architecture = (linked / "agents-architecture.md").read_text(encoding="utf-8")
        self.assertIn("](../architecture/high-level.md)", architecture)
        testing = (linked / "agents-testing.md").read_text(encoding="utf-8")
        self.assertIn("](../engineering/testing.md)", testing)

    def test_standalone_instruction_replaces_the_linking_rule(self) -> None:
        instruction = (
            SHARED / "content" / "agent-context" / "agents-standalone.instruction.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Own the fact, do not route to it", instruction)
        self.assertIn("Agent-sufficient, not a human documentation set", instruction)
        # The depth ceiling is what keeps standalone from becoming a second
        # human documentation set.
        for excluded in ("rationale", "business context", "operational procedure"):
            self.assertIn(excluded, instruction)

    def test_standalone_run_selects_standalone_templates_and_contracts(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                result = initialize(
                    runtime, repo, "spine",
                    audiences=("coding-agents",), layout="standard", groups=("agents",),
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                manifest = load_manifest(repo)
                self.assertEqual(manifest["project"]["agent_context"]["mode"], "standalone")
                by_id = {doc["id"]: doc for doc in manifest["documents"]}
                for doc_id in ("agents_architecture", "agents_testing", "agents_flow"):
                    self.assertIn("/standalone/", by_id[doc_id]["scaffold_template"], doc_id)
                    self.assertEqual(
                        by_id[doc_id]["instruction_file"],
                        "content/agent-context/agents-standalone.instruction.md",
                    )
                # agents_patterns already owns its content in either mode, so it
                # keeps its own template and only swaps contract + instruction.
                self.assertNotIn("/standalone/", by_id["agents_patterns"]["scaffold_template"])

    def test_linked_run_is_untouched_by_the_variant_machinery(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                initialize(runtime, repo, "spine", audiences=("coding-agents",), layout="standard")
                manifest = load_manifest(repo)
                self.assertEqual(manifest["project"]["agent_context"]["mode"], "linked")
                for doc in manifest["documents"]:
                    self.assertNotIn("/standalone/", doc["scaffold_template"], doc["id"])


if __name__ == "__main__":
    unittest.main()
