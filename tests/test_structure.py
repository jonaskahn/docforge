"""Repository structure: SKILL.md content, budgets, routers, and link integrity.

Coverage grows phase by phase per the context-bounded refactor: budget/router/
link checks are added once SKILL.md and the catalog routers actually exist in
their target shape (see tests/README.md).
"""

from __future__ import annotations

import unittest
from pathlib import Path

from _support import ROOT


SKILL_ROOT = ROOT / "skills" / "docforge"


class SkillContentTests(unittest.TestCase):
    def test_skill_md_routes_to_intake_workflow(self) -> None:
        """SKILL.md stays compact; the intake procedure itself lives in workflows/intake.md."""
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("workflows/intake.md", skill)
        self.assertIn("Provider sufficiency rule", skill)
        self.assertIn("Missing competing providers are normal", skill)
        self.assertNotIn("Ask exactly one applicable question at a time", skill)
        self.assertNotIn("[1] Starter", skill)
        self.assertNotIn("Reply with, for example: `2 R`", skill)

    def test_intake_workflow_requires_interactive_scope_intake(self) -> None:
        intake = (SKILL_ROOT / "workflows" / "intake.md").read_text(encoding="utf-8")
        self.assertIn("## Bare `/docforge` invocation", intake)
        self.assertIn("interactive intake", intake)
        self.assertIn("## Discovery brief", intake)
        self.assertIn("before**\nasking any scope questions", intake)
        self.assertIn("never present scope questions without this\nbrief", intake)
        self.assertIn("**Recommended** vs **also possible**", intake)
        self.assertIn("Present all applicable unresolved questions together", intake)
        self.assertIn("Collect the applicable answers as one response", intake)
        for question in (
            "Goal or action",
            "Documentation tier",
            "Repository profiles",
            "Output audience",
            "Graph source, only when unresolved",
            "Execution mode",
        ):
            self.assertIn(question, intake)
        self.assertIn("one multi-select per applicable dimension", intake)
        self.assertIn("silent-confirm them on the user's behalf", intake)
        self.assertIn("Never silent-confirm detections or gate judgments", intake)
        self.assertIn("never apply that default silently", intake)
        self.assertIn("audience-only follow-up", intake)
        self.assertIn("Auto-accept (permissionless)", intake)
        self.assertIn("mode-only follow-up", intake)
        self.assertIn("every selected audience", intake)
        self.assertIn("Always wait for explicit confirmation", intake)
        self.assertIn("including when Auto-accept was selected", intake)
        self.assertNotIn("Ask exactly one applicable question at a time", intake)
        self.assertNotIn("[1] Starter", intake)
        self.assertNotIn("Reply with, for example: `2 R`", intake)
        self.assertIn("Do not initialize a\nmanifest", intake)
        self.assertIn("Engineers + beginners", intake)
        self.assertIn("Missing competitors are normal", intake)
        self.assertIn("revising flows", intake)

    def test_revision_workflow_covers_revise_flow(self) -> None:
        revision = (SKILL_ROOT / "workflows" / "revision.md").read_text(encoding="utf-8")
        self.assertIn("`--revise flow`", revision)
        self.assertIn("NOTICE listing", revision)
        self.assertIn("main-priority flows being generated", revision)
        self.assertIn("communities.md", revision)
        self.assertIn("flow-analysis.json", revision)
        self.assertIn("main-priority", revision)
        self.assertIn("agent/LLM analyzes", revision)

    def test_planning_workflow_never_writes_against_stale_tree(self) -> None:
        planning = (SKILL_ROOT / "workflows" / "planning.md").read_text(encoding="utf-8")
        self.assertIn("Never write against an undisplayed manifest\nrevision", planning)

    def test_flow_derivation_reference_covers_dedup(self) -> None:
        derivation = (SKILL_ROOT / "references" / "graph" / "flow-derivation.md").read_text(encoding="utf-8")
        self.assertIn("near-duplicate candidates", derivation)
        self.assertIn("deduplicated label summary", derivation)

    def test_root_readme_describes_bare_invocation(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("/docforge", readme)
        self.assertIn("all applicable unresolved scope questions together", readme)
        self.assertIn("summarizes the complete scope and asks you to", readme)
        self.assertIn("confirm, edit, or cancel", readme)
        self.assertIn("Only one readable provider is required", readme)


if __name__ == "__main__":
    unittest.main()
