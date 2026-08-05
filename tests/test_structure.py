"""Repository structure: SKILL.md content, budgets, routers, and link integrity.

Coverage grows phase by phase per the context-bounded refactor: budget/router/
link checks are added once SKILL.md and the catalog routers actually exist in
their target shape (see tests/README.md).
"""

from __future__ import annotations

import json
import re
import subprocess
import unittest
from pathlib import Path

from _support import ROOT, run


SKILL_ROOT = ROOT / "skills" / "docforge"
SHARED_ROOT = ROOT / "skills" / "docforge" / "_shared"

AGENT_PLACEHOLDER = re.compile(r"\$\{CLAUDE_(?:PLUGIN_ROOT|SKILL_DIR)\}")
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


class CatalogFormAllowlistTests(unittest.TestCase):
    def test_dominant_form_allowlist_matches_across_schema_python_js(self) -> None:
        """The dominant_form allowlist is intentionally duplicated in three
        places (JSON Schema enum, Python set, JS set) for validation speed at
        each call site; this test is the guard against them drifting apart."""
        schema = json.loads((SHARED_ROOT / ".metadata" / "catalog-schema.json").read_text(encoding="utf-8"))
        schema_forms = set(schema["definitions"]["document"]["properties"]["dominant_form"]["enum"])

        from runtime.catalog.python.query_catalog import ALLOWED_DOMINANT_FORMS as py_forms

        node = subprocess.run(
            [
                "node", "-e",
                "const m=require(process.argv[1]); console.log(JSON.stringify([...m.ALLOWED_DOMINANT_FORMS]));",
                str(SHARED_ROOT / "runtime" / "catalog" / "js" / "query_catalog.js"),
            ],
            text=True, capture_output=True, check=True,
        )
        js_forms = set(json.loads(node.stdout))

        self.assertEqual(schema_forms, py_forms)
        self.assertEqual(py_forms, js_forms)


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

    def test_revision_questions_are_delta_aware_not_a_reflexive_full_ask(self) -> None:
        """Revise scales its question pack to what actually changed instead
        of always re-asking Tier/Profiles/Output audience on every run."""
        revision = (SHARED_ROOT / "workflows" / "revision.md").read_text(encoding="utf-8")
        self.assertIn("**delta-aware**", revision)
        self.assertIn("asked only when the invocation requests a tier change", revision)
        self.assertIn("asked only for\n   dimensions with an actual delta", revision)
        self.assertIn("skips their controls entirely", revision)
        self.assertNotIn("exactly like a fresh start", revision)
        intake = (SHARED_ROOT / "workflows" / "intake.md").read_text(encoding="utf-8")
        self.assertIn("never a reflexive full re-ask of every dimension on every run", intake)
        self.assertIn(
            "`/docforge-revise flow`, `/docforge-revise <area>`, `/docforge-revise all`",
            intake,
        )
        self.assertNotIn("exactly like a fresh start", intake)

    def test_planning_workflow_never_writes_against_stale_tree(self) -> None:
        planning = (SHARED_ROOT / "workflows" / "planning.md").read_text(encoding="utf-8")
        self.assertIn("Never write against an undisplayed manifest\nrevision", planning)

    def test_planning_workflow_locks_graph_provider_via_init(self) -> None:
        planning = (SHARED_ROOT / "workflows" / "planning.md").read_text(encoding="utf-8")
        init_pos = planning.index("manage_manifest.py init")
        lock_pos = planning.index("`init` locks the graph provider into the manifest")
        self.assertLess(init_pos, lock_pos, "graph-provider note must follow the init command block")
        self.assertIn("--graph-provider", planning)

    def test_writing_workflow_links_graph_retrieval_policy(self) -> None:
        writing = (SHARED_ROOT / "workflows" / "writing.md").read_text(encoding="utf-8")
        self.assertIn(
            "[`../references/graph/graph-sources.md`](../references/graph/graph-sources.md)",
            writing,
        )
        self.assertIn(
            "[`../references/source-analysis.md`](../references/source-analysis.md)",
            writing,
        )
        self.assertIn("native tool first, whole-file read last", writing)
        self.assertIn("Never re-detect and never re-ask", writing)

    def test_writing_workflow_parallel_workers_never_select_provider(self) -> None:
        writing = (SHARED_ROOT / "workflows" / "writing.md").read_text(encoding="utf-8")
        self.assertIn(
            "never calls `precheck_graph` or `set-graph` itself and never selects or\n  relocks a provider",
            writing,
        )
        self.assertIn("locked graph provider/flow (`manifest[\"graph\"]`, read-only)", writing)

    def test_parallel_execution_denies_worker_provider_selection(self) -> None:
        parallel = (SHARED_ROOT / "references" / "parallel-execution.md").read_text(encoding="utf-8")
        self.assertIn(
            "a worker never calls `precheck_graph` or `set-graph` and never",
            parallel,
        )

    def test_rules_documents_graph_provider_persistence(self) -> None:
        rules = (SHARED_ROOT / "rules.md").read_text(encoding="utf-8")
        self.assertIn("## Graph provider persistence", rules)
        self.assertIn("not re-selected mid-session without\n`set-graph --force`", rules)

    def test_graph_sources_documents_automatic_locking(self) -> None:
        graph_sources = (SHARED_ROOT / "references" / "graph" / "graph-sources.md").read_text(encoding="utf-8")
        self.assertIn("## Session persistence", graph_sources)
        self.assertIn(
            "locks the selected provider into the manifest\nautomatically",
            graph_sources,
        )
        self.assertIn("registry-priority pick", graph_sources)

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

    def test_source_evidence_stays_in_provenance(self) -> None:
        """Reader-facing source citations are replaced by provenance and docs links."""
        host = (SHARED_ROOT / "references" / "host-neutrality.md").read_text(encoding="utf-8")
        self.assertIn("Source grounding stays in provenance", host)
        evidence = (SHARED_ROOT / "references" / "evidence-presentation.md").read_text(encoding="utf-8")
        self.assertIn("Never show source paths, line ranges, blob hashes", evidence)
        code = (SHARED_ROOT / "references" / "code-presentation.md").read_text(encoding="utf-8")
        self.assertIn("Never paste repository implementation", code)

    def test_validation_workflow_auto_serves_dashboard_on_completion(self) -> None:
        validation = (SHARED_ROOT / "workflows" / "validation.md").read_text(encoding="utf-8")
        self.assertIn("## 7. Dashboard auto-serve", validation)
        self.assertIn("Never under `--plan-only`", validation)
        self.assertIn("`--no-dashboard`", validation)
        self.assertIn("every completed\n`/docforge` (fresh start) and `/docforge-revise` run", validation)
        self.assertIn("Node.js 22+ / npm", validation)

    def test_completion_requires_dashboard_start_and_reported_url(self) -> None:
        """A run is complete only when the dashboard was started and its URL
        reported; both entrypoints carry the completion contract, not just
        the validation workflow."""
        rules = (SHARED_ROOT / "rules.md").read_text(encoding="utf-8")
        self.assertIn("the dashboard has been started\nand its URL reported", rules)
        self.assertIn("`--plan-only` or `--no-dashboard`", rules)
        revision = (SHARED_ROOT / "workflows" / "revision.md").read_text(encoding="utf-8")
        self.assertIn("## Completion", revision)
        self.assertIn("dashboard: <url>", revision)
        for skill in (
            ROOT / "skills" / "docforge" / "SKILL.md",
            ROOT / "skills" / "docforge-revise" / "SKILL.md",
        ):
            text = skill.read_text(encoding="utf-8")
            self.assertIn("## Completion", text)
            self.assertIn("dashboard has been started", text)
            self.assertIn("URL reported in the final response", text)
            self.assertIn("Never finish a run with the docs", text)

    def test_dashboard_failure_requests_revision_before_open(self) -> None:
        """A failed dashboard build is never opened; the user is asked to
        revise the documentation first."""
        workflow = (SHARED_ROOT / "workflows" / "dashboard.md").read_text(encoding="utf-8")
        self.assertIn("## When the build fails: revise before the dashboard", workflow)
        self.assertIn("Never open the dashboard and never present the previous build", workflow)
        self.assertIn("`/docforge-revise`", workflow)
        self.assertIn("passes the whole-tree gate", workflow)
        self.assertIn("`--auto-accept` does not waive this", workflow)
        thin = (ROOT / "skills" / "docforge-dashboard" / "SKILL.md").read_text(encoding="utf-8")
        # Thin entrypoint delegates the full procedure to workflows/dashboard.md
        # and carries only a pointer-level summary of the build-failure gate.
        self.assertIn("## Preflight gates", thin)
        self.assertIn("**not** opened", thin)
        self.assertIn("`/docforge-revise`", thin)
        self.assertIn("`--auto-accept` bypasses", thin)

    def test_dashboard_scan_suggests_revision_before_open(self) -> None:
        """The dashboard scans for missing metadata, broken links, stale
        sources, and untracked docs; findings trigger a "you should revise
        again" recommendation before the dashboard is trusted."""
        workflow = (SHARED_ROOT / "workflows" / "dashboard.md").read_text(encoding="utf-8")
        self.assertIn("## Scan: you should revise again", workflow)
        self.assertIn("**you should revise again**", workflow)
        self.assertIn("**metadata**", workflow)
        self.assertIn("**broken_link**", workflow)
        self.assertIn("`scan` exits `1`", workflow)
        self.assertIn("never a summary that\n   hides a finding", workflow)
        thin = (ROOT / "skills" / "docforge-dashboard" / "SKILL.md").read_text(encoding="utf-8")
        # Thin entrypoint summarizes the scan gate and points at the workflow owner.
        self.assertIn("## Preflight gates", thin)
        self.assertIn("**Scan**", thin)
        self.assertIn("`/docforge-revise`", thin)
        self.assertIn("clean scan means ready", thin)
        help_text = (SHARED_ROOT / "help.md").read_text(encoding="utf-8")
        self.assertIn("`scan` (read-only diagnostics", help_text)

    def test_dashboard_legacy_manifest_gate(self) -> None:
        """A legacy manifest (any pre-3.0 version) stops the dashboard with a
        three-option gate: revise all, update metadata only
        (migrate_metadata), or stop."""
        workflow = (SHARED_ROOT / "workflows" / "dashboard.md").read_text(encoding="utf-8")
        self.assertIn("## Legacy manifest gate", workflow)
        self.assertIn("**Revise all (recommended)**", workflow)
        self.assertIn("**Update metadata only**", workflow)
        self.assertIn("**Stop**", workflow)
        self.assertIn("`--auto-accept` never bypasses this gate", workflow)
        self.assertIn("`migrate_metadata.{py,js} --dry-run`", workflow)
        self.assertIn("for **any** legacy version", workflow)
        self.assertNotIn("Legacy manifest gate (v1.1)", workflow)
        thin = (ROOT / "skills" / "docforge-dashboard" / "SKILL.md").read_text(encoding="utf-8")
        # Thin entrypoint summarizes the three-option legacy gate; the full
        # option text lives in workflows/dashboard.md (asserted above).
        self.assertIn("## Preflight gates", thin)
        self.assertIn("**Legacy manifest**", thin)
        self.assertIn("three-option gate", thin)
        self.assertIn("revise all", thin)
        self.assertIn("update metadata", thin)
        self.assertIn("any** legacy version", thin)
        self.assertNotIn("Legacy manifest gate (v1.1)", thin)

    def test_help_supported_by_all_entrypoints(self) -> None:
        """--help is accepted by all three entrypoints and routes to the
        canonical per-entrypoint reference in _shared/help.md."""
        help_text = (SHARED_ROOT / "help.md").read_text(encoding="utf-8")
        for section in ("## `/docforge`", "## `/docforge-revise`", "## `/docforge-dashboard`"):
            self.assertIn(section, help_text)
        for flag in ("--plan-only", "--auto-accept", "--no-dashboard", "--force"):
            self.assertIn(flag, help_text)
        flags = (SHARED_ROOT / "flags.md").read_text(encoding="utf-8")
        self.assertIn("--no-dashboard", flags)
        self.assertIn("| `--help` |", flags)
        for path in sorted((ROOT / "commands").glob("*.md")):
            text = path.read_text(encoding="utf-8")
            self.assertIn("--help", text)
            self.assertIn("_shared/help.md", text)
        for skill_dir in (
            SKILL_ROOT,
            ROOT / "skills" / "docforge-revise",
            ROOT / "skills" / "docforge-dashboard",
        ):
            self.assertIn("--help", (skill_dir / "SKILL.md").read_text(encoding="utf-8"))

    def test_revision_scope_order_is_flow_area_all(self) -> None:
        """The revise scope question presents flow, then <area>, then all;
        a bare /docforge-revise is metadata-only migration, not a scope ask."""
        revision = (SHARED_ROOT / "workflows" / "revision.md").read_text(encoding="utf-8")
        scope_line = next(
            line for line in revision.splitlines() if line.strip().startswith("1. **Scope**")
        )
        self.assertLess(scope_line.index("flow"), scope_line.index("<area>"))
        self.assertLess(scope_line.index("<area>"), scope_line.index("all"))
        self.assertIn("never for a bare", revision)
        revise = (ROOT / "skills" / "docforge-revise" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Metadata-only: migrate/upgrade the manifest metadata", revise)
        self.assertIn("`migrate_metadata.{py,js}`", revise)
        self.assertNotIn("Ask which scope", revise)
        bare = (SHARED_ROOT / "workflows" / "revision.md").read_text(encoding="utf-8")
        self.assertIn("## Commands", bare)
        self.assertIn("### Bare `/docforge-revise` — metadata-only migration", bare)
        intake = (SHARED_ROOT / "workflows" / "intake.md").read_text(encoding="utf-8")
        self.assertIn("`/docforge-revise flow`, `/docforge-revise <area>`, `/docforge-revise all`", intake)

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
        self.assertFalse((ROOT / "agents").exists())
        self.assertFalse((ROOT / "skills" / "docforge" / "agents").exists())
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
        self.assertTrue((core / "_shared" / "runtime" / "dashboard" / "python" / "dashboard.py").is_file())
        self.assertTrue((core / "_shared" / "runtime" / "dashboard" / "js" / "dashboard.js").is_file())
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
            if rel in {
                "_shared/runtime/validation/python/validate_metadata.py",
                "_shared/runtime/validation/js/validate_metadata.js",
            }:
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

    def test_skill_md_links_resolve_relative_to_skill_dir(self) -> None:
        """Every cartridge link in the shipped SKILL.md files is relative to
        the SKILL.md's own directory (`./` or `../`), never CWD-relative or
        agent-placeholder-relative; the lookup order and the ask-the-user
        fallback are present."""
        for skill_dir in sorted((ROOT / "skills").glob("*")):
            skill = skill_dir / "SKILL.md"
            if not skill.is_file():
                continue
            text = skill.read_text(encoding="utf-8")
            self.assertNotRegex(text, AGENT_PLACEHOLDER)
            self.assertIn("ask the user for the absolute", text)
            self.assertIn("Repo-local self-host", text)
            self.assertIn("Global skill dirs", text)
            for link in LINK.findall(text):
                self.assertTrue(
                    link.startswith(("./", "../")),
                    f"{skill_dir.name}: CWD-relative or non-relative link {link!r}",
                )
                target = (skill_dir / link).resolve()
                self.assertTrue(target.is_file(), f"{skill_dir.name}: unresolved link {link}")

    def test_skills_tree_has_no_agent_placeholders(self) -> None:
        """No `${CLAUDE_SKILL_DIR}` / `${CLAUDE_PLUGIN_ROOT}` survives anywhere
        under skills/ — the cartridge is host-neutral. `commands/` is the only
        Claude-Code-only surface and keeps its plugin-root placeholders."""
        offenders: list[str] = []
        for path in (ROOT / "skills").rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in {".md", ".py", ".js"}:
                continue
            if AGENT_PLACEHOLDER.search(path.read_text(encoding="utf-8", errors="replace")):
                offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual(offenders, [])

    def test_commands_resolve_via_plugin_root(self) -> None:
        """Slash commands reference skills and cartridge through
        ${CLAUDE_PLUGIN_ROOT}, and every referenced path exists."""
        for path in sorted((ROOT / "commands").glob("*.md")):
            text = path.read_text(encoding="utf-8")
            self.assertIn("${CLAUDE_PLUGIN_ROOT}", text)
            for match in re.finditer(
                r"\$\{CLAUDE_PLUGIN_ROOT\}(/[a-zA-Z0-9_./-]+)", text
            ):
                target = (ROOT / match.group(1).lstrip("/")).resolve()
                self.assertTrue(
                    target.exists(), f"{path.name}: unresolved reference {match.group(0)}"
                )


class RuntimeReadmeTests(unittest.TestCase):
    """Every runtime subsystem documents its scripts so agents can pick the
    right tool without reading sources. Runtime READMEs are agent/operator
    documentation and are exempt from the obsolete-nested-README rule."""

    SUBSYSTEMS = [
        "catalog", "cli", "common", "dashboard", "documents", "flows",
        "graph", "manifest", "migrations", "portfolio", "validation",
    ]

    def test_every_subsystem_has_readme_linked_from_runtime_root(self) -> None:
        root_readme = (SHARED_ROOT / "runtime" / "README.md").read_text(encoding="utf-8")
        for name in self.SUBSYSTEMS:
            readme = SHARED_ROOT / "runtime" / name / "README.md"
            self.assertTrue(readme.is_file(), f"missing runtime/{name}/README.md")
            self.assertIn(f"{name}/README.md", root_readme, name)

    def test_subsystem_readmes_name_every_script(self) -> None:
        for name in self.SUBSYSTEMS:
            readme_path = SHARED_ROOT / "runtime" / name / "README.md"
            readme = readme_path.read_text(encoding="utf-8")
            for lang in ("js", "python"):
                scripts_dir = readme_path.parent / lang
                if not scripts_dir.is_dir():
                    continue
                for script in sorted(scripts_dir.glob(f"*.{lang}")):
                    stem = script.stem
                    if stem == "__init__":
                        continue
                    self.assertIn(
                        stem, readme,
                        f"{name}/README.md does not document {lang}/{stem}",
                    )

    def test_runtime_readmes_are_exempt_from_obsolete_readme_rule(self) -> None:
        runtime_readmes = {
            f"skills/docforge/_shared/runtime/{name}/README.md"
            for name in self.SUBSYSTEMS
        }
        for runtime in ("py", "js"):
            result = run(runtime, "validate_metadata")
            for rel in sorted(runtime_readmes):
                self.assertNotIn(rel, result.stdout, runtime)


if __name__ == "__main__":
    unittest.main()
