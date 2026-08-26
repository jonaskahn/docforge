"""New agent-context capabilities: 3-tier boundaries, style rubric,
compact cross-topic lint, layer rules, and vendor fan-out."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from _support import ROOT, run

CATALOG_DIR = ROOT / "skills" / "docforge" / "_shared" / ".metadata" / "catalog"
AGENT_CONTEXT = CATALOG_DIR / "documents" / "agent-context"
CONTENT = ROOT / "skills" / "docforge" / "_shared" / "content" / "agent-context"
RUNTIME_PY = ROOT / "skills" / "docforge" / "_shared" / "runtime" / "documents" / "python"
RUNTIME_JS = ROOT / "skills" / "docforge" / "_shared" / "runtime" / "documents" / "js"

FLOW_SNAPSHOT = {
    "contracts/agents-flow.md": "ab62adfa8b2500e44c76cd6850a38b59",
    "templates/agents-flow.md": "24034dc3eaf14b3188748b4bac81b5ed",
}
COMPACT_MEMBERS = [
    "agents_architecture", "agents_patterns", "agents_testing",
    "agents_conventions", "agents_tech_debt", "agents_flow",
    "agents_glossary",
]

SUPPORTED_VENDORS = ["claude", "codex", "cursor", "copilot", "windsurf", "aider", "gemini"]


class FlowIsolationTests(unittest.TestCase):
    def test_flow_content_files_are_byte_identical(self) -> None:
        for rel, expected in FLOW_SNAPSHOT.items():
            with self.subTest(file=rel):
                digest = hashlib.md5((CONTENT / rel).read_bytes()).hexdigest()
                self.assertEqual(digest, expected)

    def test_flow_catalog_record_compact_membership_unchanged(self) -> None:
        record = json.loads((AGENT_CONTEXT / "agents_compact.json").read_text(encoding="utf-8"))
        self.assertEqual(record["compact_members"], COMPACT_MEMBERS)

    def test_flow_record_still_declares_the_same_contract_and_template(self) -> None:
        record = json.loads((AGENT_CONTEXT / "agents_flow.json").read_text(encoding="utf-8"))
        self.assertEqual(record["contract_file"], "content/agent-context/contracts/agents-flow.md")
        self.assertEqual(record["template_file"], "content/agent-context/templates/agents-flow.md")


def _lint_kernel(text):
    results = []
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "AGENTS.md"
        target.write_text(text, encoding="utf-8")
        payloads = []
        for script in (RUNTIME_PY / "lint_agents_kernel.py", RUNTIME_JS / "lint_agents_kernel.js"):
            cmd = ["python3", str(script)] if script.suffix == ".py" else ["node", str(script)]
            result = subprocess.run(cmd + ["--file", str(target), "--json"], capture_output=True, text=True)
            payloads.append(json.loads(result.stdout))
    assert payloads[0] == payloads[1], "py/js parity"
    return payloads[0]["defects"]


class BoundaryGroupingLintTests(unittest.TestCase):
    GOLDEN_BOUNDARIES = (
        "## Boundaries\n\n**Three tiers. No exceptions.**\n\n"
        "Always:\n- Run the focused test for the changed area.\n\n"
        "Ask first:\n- Before deleting a shared branch or applied migration.\n\n"
        "Never:\n- Commit secrets, credentials, or local environment values.\n"
        "- Disable tests, validation, or checks to force success.\n"
        "- Run destructive commands without explicit approval.\n"
    )

    def test_three_tier_boundaries_lint_clean(self) -> None:
        defects = _lint_kernel("# T\n\nIntro.\n\n" + self.GOLDEN_BOUNDARIES)
        grouping = [d for d in defects if d["kind"] == "boundary-grouping"]
        self.assertEqual(grouping, [])

    def test_missing_ask_first_group_is_a_defect(self) -> None:
        dirty = self.GOLDEN_BOUNDARIES.replace(
            "Ask first:\n- Before deleting a shared branch or applied migration.\n\n", ""
        )
        defects = _lint_kernel("# T\n\nIntro.\n\n" + dirty)
        kinds = {d["kind"] for d in defects}
        self.assertIn("boundary-grouping", kinds)

    def test_out_of_order_groups_are_a_defect(self) -> None:
        dirty = self.GOLDEN_BOUNDARIES.replace(
            "Ask first:\n- Before deleting a shared branch or applied migration.\n\nNever:",
            "Never:\n- Commit secrets.\n\nAsk first:\n- Ask before force pushes.\n\nAlways:\n- Placeholder.",
        )
        defects = _lint_kernel("# T\n\nIntro.\n\n" + dirty)
        kinds = {d["kind"] for d in defects}
        self.assertIn("boundary-grouping", kinds)


class KernelStyleRubricTests(unittest.TestCase):
    def test_allcaps_directive_outside_boundaries_is_a_defect(self) -> None:
        text = "# T\n\nIntro.\n\n## Precedence\n\nMUST follow the task requirements first.\n\n## Validation\n\nDone when tests pass.\n"
        defects = _lint_kernel(text)
        allcaps = [d for d in defects if d["kind"] == "kernel-allcaps"]
        self.assertTrue(allcaps, defects)

    def test_tagline_check_flags_plain_prose_after_h2(self) -> None:
        text = "# T\n\nIntro.\n\n## Repository Map\n\nPlain prose without bold.\n"
        defects = _lint_kernel(text)
        taglines = [d for d in defects if d["kind"] == "missing-tagline"]
        self.assertTrue(any(item["detail"].startswith("Repository Map") for item in taglines), defects)


def _run_compact_lint(text):
    outputs = []
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "docs-agents.md"
        target.write_text(text, encoding="utf-8")
        for runtime in ("py", "js"):
            script = RUNTIME_PY / "lint_compact_topics.py" if runtime == "py" else RUNTIME_JS / "lint_compact_topics.js"
            cmd = ["python3", str(script)] if runtime == "py" else ["node", str(script)]
            result = subprocess.run(cmd + ["--file", str(target), "--json"], capture_output=True, text=True)
            outputs.append(json.loads(result.stdout))
    assert outputs[0] == outputs[1], "py/js parity: " + repr(outputs)
    return outputs[0]


class CompactTopicLintTests(unittest.TestCase):
    def test_clean_document_has_no_defects(self) -> None:
        text = "# Compact reference\n\nIntro.\n\n## Architecture\n\nThe api layer calls the core.\n\n## Testing\n\nRun npm test.\n"
        result = _run_compact_lint(text)
        self.assertEqual(result["defects"], [])

    def test_cross_topic_mention_is_a_defect(self) -> None:
        text = "# Compact reference\n\nIntro.\n\n## Architecture\n\nThe api layer calls the core.\n\n## Testing\n\nRun npm test. See Architecture for layer order.\n"
        defects = _run_compact_lint(text)["defects"]
        kinds = {item["kind"] for item in defects}
        self.assertIn("cross-topic-mention", kinds)
        self.assertIn("cross-topic-pointer", kinds)


class CatalogVendorSelectorTests(unittest.TestCase):
    INDEX = json.loads((CATALOG_DIR / "index.json").read_text(encoding="utf-8"))

    def _record(self, name: str) -> dict:
        return json.loads((AGENT_CONTEXT / (name + ".json")).read_text(encoding="utf-8"))

    def test_every_agent_context_record_has_a_vendors_selector(self) -> None:
        # agents_flow is intentionally untouched by this change set; the user
        # scoped it out. All other agent-context records must carry the
        # vendors selector.
        rows = [r for r in self.INDEX["document_types"] if "/agent-context/" in r["record"]]
        self.assertGreater(len(rows), 10)
        for row in rows:
            if row["id"] == "agents_flow":
                continue
            with self.subTest(id=row["id"]):
                record = json.loads((CATALOG_DIR / row["record"]).read_text(encoding="utf-8"))
                selectors = record.get("selection", {}).get("selectors", {})
                self.assertIn("vendors", selectors, row["id"] + " missing vendors selector")
                self.assertIsInstance(selectors["vendors"], list)

    def test_vendor_shim_records_target_exactly_one_vendor_each(self) -> None:
        for name in ("vendor_codex", "vendor_cursor", "vendor_copilot", "vendor_windsurf", "vendor_aider", "vendor_gemini"):
            with self.subTest(id=name):
                record = self._record(name)
                vendors = record["selection"]["selectors"]["vendors"]
                self.assertEqual(len(vendors), 1, vendors)
                self.assertIn(vendors[0], SUPPORTED_VENDORS)

    def test_layer_rule_record_is_conditional_on_layers_available(self) -> None:
        record = self._record("agents_layer_rule")
        self.assertEqual(record["selection"]["condition"], "layers_available")
        self.assertEqual(record["path"], ".agents/rules/<layer-slug>.md")

    def test_kernel_revision_bumped_to_320(self) -> None:
        for name in ("agents_kernel", "claude_shim"):
            with self.subTest(id=name):
                self.assertEqual(self._record(name)["contract_revision"], "3.2.0")

    def test_topic_view_commons_reference_exists_and_is_inherited_by_contracts(self) -> None:
        commons = CONTENT / "references" / "topic-view-commons.md"
        self.assertTrue(commons.is_file())
        for topic in ("architecture", "patterns", "testing", "conventions", "tech-debt", "glossary"):
            with self.subTest(topic=topic):
                contract = (CONTENT / "contracts" / ("agents-" + topic + ".md")).read_text(encoding="utf-8")
                self.assertIn("topic-view-commons.md", contract)


if __name__ == "__main__":
    unittest.main()
