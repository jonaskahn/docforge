"""Repository structure: SKILL.md content, budgets, routers, and link integrity.

Coverage grows phase by phase per the context-bounded refactor: budget/router/
link checks are added once SKILL.md and the catalog routers actually exist in
their target shape (see tests/README.md).
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from _support import ROOT


SKILL_ROOT = ROOT / "skills" / "docforge"
SHARED_ROOT = ROOT / "skills" / "docforge" / "_shared"


class SkillContentTests(unittest.TestCase):
    def test_skill_md_routes_to_intake_workflow(self) -> None:
        """SKILL.md stays compact; the intake procedure itself lives in workflows/intake.md."""
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("./_shared/workflows/intake.md", skill)
        self.assertIn("./_shared/rules.md", skill)
        self.assertNotIn("Ask exactly one applicable question at a time", skill)
        self.assertNotIn("[1] Starter", skill)
        self.assertNotIn("Reply with, for example: `2 R`", skill)
        rules = (SHARED_ROOT / "rules.md").read_text(encoding="utf-8")
        self.assertIn("Provider sufficiency rule", rules)
        self.assertIn("missing competing providers are\nnormal", rules)

    def test_intake_workflow_requires_interactive_scope_intake(self) -> None:
        intake = (SHARED_ROOT / "workflows" / "intake.md").read_text(encoding="utf-8")
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
        self.assertIn("that default silently", intake)
        self.assertIn("audience-only follow-up", intake)
        self.assertIn("add more", intake)
        self.assertIn("suitable missing", intake)
        self.assertIn("## Revise selection changes", intake)
        self.assertIn("Do not present a `Keep`\nchoice", intake)
        self.assertIn("`Change to <other tier>`", intake)
        self.assertIn("`Add <value>`", intake)
        self.assertIn("`Remove <value>`", intake)
        self.assertIn("explicit confirmation before reconciling", intake)
        self.assertIn("Business analysts (BA)", intake)
        self.assertIn("Product owners (PO)", intake)
        self.assertIn("Coding agents", intake)
        self.assertIn("all seven", intake)
        self.assertIn("never drop BA/PO/agents", intake)
        self.assertIn("`/docforge-revise flow`", intake)
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
        self.assertIn("/docforge-revise flow", intake)

    def test_revision_workflow_covers_revise_flow(self) -> None:
        revision = (SHARED_ROOT / "workflows" / "revision.md").read_text(encoding="utf-8")
        self.assertIn("`/docforge-revise flow`", revision)
        self.assertIn("Suitable missing audiences", revision)
        self.assertIn("selection.audiences", revision)
        self.assertIn("NOTICE first", revision)
        self.assertIn("communities.md", revision)
        self.assertIn("flow-analysis.json", revision)
        self.assertIn("main-priority", revision)
        self.assertIn("agent/LLM analyzes", revision)
        self.assertIn("offer only `Change to <tier>` alternatives", revision)
        self.assertIn("offer `Add` / `Remove` actions", revision)

    def test_planning_workflow_never_writes_against_stale_tree(self) -> None:
        planning = (SHARED_ROOT / "workflows" / "planning.md").read_text(encoding="utf-8")
        self.assertIn("Never write against an undisplayed manifest\nrevision", planning)

    def test_revision_workflow_enforces_current_template(self) -> None:
        """Revise rewrites documents whose structure/format/content deviates
        from the current template instead of preserving the old structure."""
        revision = (SHARED_ROOT / "workflows" / "revision.md").read_text(encoding="utf-8")
        self.assertIn("Enforce current template conformance", revision)
        self.assertIn("the **newest template is the authority**", revision)
        self.assertIn("is planned `rewrite` to the current\n    template", revision)
        self.assertIn("Never preserve an old\n    structure", revision)
        self.assertIn("even when its source blobs are `FRESH`", revision)
        self.assertIn("### Template rewrite mechanics", revision)
        self.assertIn("Scaffold the **newest** template", revision)
        self.assertIn("`rewrite (template)`", revision)

    def test_source_references_are_human_readable_links(self) -> None:
        """Document bodies mention source files as human-readable links, never
        bare paths or file:line strings."""
        host = (SHARED_ROOT / "references" / "host-neutrality.md").read_text(encoding="utf-8")
        self.assertIn("**Source references.**", host)
        self.assertIn("human-readable label", host)
        self.assertIn("never a bare path or a `path:line` string", host)
        source = (SHARED_ROOT / "references" / "source-analysis.md").read_text(encoding="utf-8")
        self.assertIn("human-readable link", source)
        self.assertIn("host-neutrality.md", source)

    def test_validation_workflow_auto_serves_dashboard_on_completion(self) -> None:
        validation = (SHARED_ROOT / "workflows" / "validation.md").read_text(encoding="utf-8")
        self.assertIn("## 7. Dashboard auto-serve", validation)
        self.assertIn("Never under `--plan-only`", validation)
        self.assertIn("every completed\n`/docforge` (fresh start) and `/docforge-revise` run", validation)
        self.assertIn("Node.js 22+ / npm", validation)

    def test_flow_derivation_reference_covers_dedup(self) -> None:
        derivation = (SHARED_ROOT / "references" / "graph" / "flow-derivation.md").read_text(encoding="utf-8")
        self.assertIn("near-duplicate candidates", derivation)
        self.assertIn("deduplicated label summary", derivation)

    def test_root_readme_describes_bare_invocation(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("/docforge", readme)
        self.assertIn("all applicable unresolved scope questions together", readme)
        self.assertIn("summarizes the complete scope and asks you to", readme)
        self.assertIn("confirm, edit, or cancel", readme)
        self.assertIn("repository evidence", readme)

    def test_claude_plugin_is_whole_repo(self) -> None:
        """Marketplace installs this GitHub repo as the plugin; no mirrored package."""
        marketplace = json.loads(
            (ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
        )
        source = marketplace["plugins"][0]["source"]
        self.assertIsInstance(source, dict)
        self.assertEqual(source.get("source"), "url")
        self.assertEqual(source.get("url"), "https://github.com/jonaskahn/docforge.git")
        self.assertFalse((ROOT / "docforge-plugin").exists())
        plugin_json = ROOT / ".claude-plugin" / "plugin.json"
        self.assertTrue(plugin_json.is_file())
        payload = json.loads(plugin_json.read_text(encoding="utf-8"))
        self.assertEqual(payload["name"], "docforge")
        self.assertEqual(
            marketplace["plugins"][0]["version"],
            payload["version"],
        )
        self.assertTrue((ROOT / "skills" / "docforge" / "SKILL.md").is_file())
        self.assertTrue((ROOT / "skills" / "docforge-revise" / "SKILL.md").is_file())
        self.assertTrue((ROOT / "skills" / "docforge-dashboard" / "SKILL.md").is_file())
        self.assertTrue((ROOT / "agents" / "docforge-audit.md").is_file())
        self.assertTrue((ROOT / "commands" / "docforge.md").is_file())
        self.assertTrue((ROOT / "commands" / "docforge-revise.md").is_file())
        self.assertTrue((ROOT / "commands" / "docforge-dashboard.md").is_file())
        self.assertEqual(
            payload.get("skills"),
            [
                "./skills/docforge",
                "./skills/docforge-revise",
                "./skills/docforge-dashboard",
            ],
        )


    def test_docforge_core_contains_dashboard_capability(self) -> None:
        """The docforge skill is the required bundle: it carries the dashboard
        workflow, runtime, template, and launchers, so installing only
        docforge can still render documentation."""
        core = ROOT / "skills" / "docforge"
        self.assertTrue((core / "_shared" / "workflows" / "dashboard.md").is_file())
        self.assertTrue((core / "_shared" / "runtime" / "dashboard" / "dashboard.py").is_file())
        self.assertTrue((core / "_shared" / "runtime" / "dashboard" / "dashboard.js").is_file())
        self.assertTrue((core / "_shared" / "runtime" / "dashboard" / "template" / "package.json").is_file())
        self.assertTrue((core / "_shared" / "runtime" / "cli" / "python" / "dashboard.py").is_file())
        self.assertTrue((core / "_shared" / "runtime" / "cli" / "js" / "dashboard.js").is_file())

    def test_docforge_core_has_no_sibling_runtime_dependencies(self) -> None:
        """A standalone docforge install must not dereference sibling skill
        directories; docforge-revise and docforge-dashboard are thin
        entrypoints into the core, never the reverse."""
        core = ROOT / "skills" / "docforge"
        needles = (
            "../docforge-revise",
            "../docforge-dashboard",
            "docforge-revise/SKILL.md",
            "docforge-dashboard/SKILL.md",
            "skills/docforge-revise",
            "skills/docforge-dashboard",
        )
        offenders: list[str] = []
        for path in core.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(core).as_posix()
            if path.name == "README.md":
                continue
            if rel.startswith(("_shared/references/", "_shared/content/")):
                continue
            if rel.startswith("_shared/runtime/validation/validate_metadata."):
                continue  # release-time repo check, not a skill runtime path
            if path.suffix not in {".md", ".py", ".js"}:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for needle in needles:
                if needle in text:
                    offenders.append(f"{path.relative_to(ROOT)}: {needle}")
        self.assertEqual(offenders, [])

    def test_entry_skills_declare_core_dependency(self) -> None:
        """revise/dashboard must not pretend to be standalone; they require
        the docforge core skill."""
        revise = (ROOT / "skills" / "docforge-revise" / "SKILL.md").read_text(encoding="utf-8")
        dashboard = (ROOT / "skills" / "docforge-dashboard" / "SKILL.md").read_text(encoding="utf-8")
        for skill in (revise, dashboard):
            self.assertIn("../docforge/_shared", skill)
            self.assertIn("requires the `docforge`", skill)


if __name__ == "__main__":
    unittest.main()
