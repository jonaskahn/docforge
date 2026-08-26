"""Agent-context selection gate: the add/update/remove re-ask that fires
whenever agent docs are generated or refreshed.

The gate is a workflow/agent-behavior contract, not a separate runtime
feature — it is assembled from building blocks the runtime already has
(reconcile audience/vendor selection, retire, check_staleness, the plan
tree). These tests pin the contract so the three workflow owners cannot
drift apart: the gate must be documented in planning.md (write-start),
revision.md (revise + named update), and intake.md (target readers +
audience), with consistent semantics across all three.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from _support import ROOT


SHARED_ROOT = ROOT / "skills" / "docforge" / "_shared"
PLANNING = SHARED_ROOT / "workflows" / "planning.md"
REVISION = SHARED_ROOT / "workflows" / "revision.md"
INTAKE = SHARED_ROOT / "workflows" / "intake.md"
GATE_TITLE = "Agent-context selection gate (write-start)"


def compact(text: str) -> str:
    return " ".join(text.split())


class AgentContextGateDocumentationTests(unittest.TestCase):
    def test_gate_is_documented_in_planning_as_write_start(self) -> None:
        planning = PLANNING.read_text(encoding="utf-8")
        self.assertIn(f"## {GATE_TITLE}", planning)
        self.assertIn("after the plan gate is confirmed", planning)
        self.assertIn("before the first agent-context document is materialized", planning)
        prose = compact(planning)
        self.assertIn("never a silent default", prose)
        self.assertIn("`--auto-accept` never waives it", prose)

    def test_gate_rows_cover_the_full_agent_context_set(self) -> None:
        planning = compact(PLANNING.read_text(encoding="utf-8"))
        for token in (
            "AGENTS.md",
            "CLAUDE.md",
            "agents_architecture",
            "agents_patterns",
            "agents_testing",
            "agents_conventions",
            "agents_tech_debt",
            "agents_flow",
            "agents_glossary",
            "vendor shim",
            ".agents/rules/",
            "CLAUDE.local.md",
            ".claude/settings.json",
        ):
            self.assertIn(token, planning)

    def test_tristate_semantics_are_stated(self) -> None:
        for path in (PLANNING, REVISION):
            prose = compact(path.read_text(encoding="utf-8"))
            self.assertIn("**add**", prose)
            self.assertIn("**update**", prose)
            self.assertIn("**remove**", prose)

    def test_remove_routes_through_existing_retirement_everywhere(self) -> None:
        # The retirement-path detail lives in the mechanics owners (planning,
        # revision); intake is the scope-control owner and routes the drop
        # through the gate without restating the path.
        for path in (PLANNING, REVISION):
            prose = compact(path.read_text(encoding="utf-8"))
            self.assertIn("retirement", prose)
            self.assertIn(".docforge/obsolete/", prose)
            self.assertIn("--auto-accept", prose)
        intake = compact(INTAKE.read_text(encoding="utf-8"))
        self.assertIn("retirement", intake)
        self.assertIn("never a silent deletion", intake)

    def test_compact_layout_presents_sections_as_rows(self) -> None:
        planning = compact(PLANNING.read_text(encoding="utf-8"))
        self.assertIn("docs/agents.md", planning)
        self.assertIn("seven merged topic sections as its own row", planning)
        revision = compact(REVISION.read_text(encoding="utf-8"))
        self.assertIn("seven merged", revision)
        self.assertIn("docs/agents.md", revision)

    def test_revise_gate_position_is_after_flow_before_plan_tree(self) -> None:
        revision = REVISION.read_text(encoding="utf-8")
        self.assertIn(
            "after the flow pipeline gate and before the annotated plan tree",
            compact(revision),
        )

    def test_revise_rows_prepopulated_from_staleness_and_catalog(self) -> None:
        revision = compact(REVISION.read_text(encoding="utf-8"))
        self.assertIn("check_staleness", revision)
        self.assertIn("STALE", revision)
        self.assertIn("UNTRACKED", revision)
        self.assertIn("catalog additions", revision)

    def test_intake_defers_per_document_gate_to_write_start(self) -> None:
        intake = compact(INTAKE.read_text(encoding="utf-8"))
        self.assertIn("The agent-context selection gate re-asks per document at write time", intake)
        self.assertIn("the gate is a write-start step, not an intake question", intake)
        self.assertIn(GATE_TITLE, intake)

    def test_intake_audience_drop_is_owned_by_gate(self) -> None:
        intake = compact(INTAKE.read_text(encoding="utf-8"))
        self.assertIn("The write-start agent-context gate owns the per-document drop", intake)
        self.assertIn("`Remove` row", intake)
        self.assertIn("never a silent deletion", intake)

    def test_named_agent_update_also_gates(self) -> None:
        revision = compact(REVISION.read_text(encoding="utf-8"))
        self.assertIn("Agent-context named update", revision)
        self.assertIn("run the agent-context selection gate before writing", revision)
        self.assertIn("check_staleness", revision)


if __name__ == "__main__":
    unittest.main()
