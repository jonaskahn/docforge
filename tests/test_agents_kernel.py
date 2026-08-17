"""lint_agents_kernel: rubric checks, template guard, Python/Node parity."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _support import initialize, load_manifest, run

GOLDEN = """\
# Demo Repo

A demo service with one framework and one test runner.

<!-- docforge-provenance v2.19.0 | graph abc1234 | 2026-08-01 | regenerate: re-run the coding-agents audience -->

## 1. Commands

**One way to run things. Don't invent alternatives.**

```
npm install
npm run dev
npm test
npm run lint
npm run build
```

The test: a fresh clone runs green after pasting the commands above.

## 2. Boundaries

**Three tiers. No exceptions, no shortcuts.**

Always: run `npm test` before opening a pull request.
Ask first: before deleting a shared branch.
Never: commit secrets, `.env` files, or credentials.
Never: edit or delete applied migrations.
Never: run destructive commands without explicit approval.
Never: push `--force` to `main`.
Never: assume a flaky test is unrelated to your change.

## 3. Module Map

**Layers are disjoint. Don't blur them.**

- api (12) — HTTP surface and request validation
- core (48) — domain logic and services
- store (9) — persistence and migrations

The test: every file under `src/` maps to exactly one layer above.

## 4. Architectural Altitude

**A layer map, not a code tour.**

- To understand a request, start at `src/api/routes.ts`.
- To understand a rule, start at `src/core/services.ts`.

The test: open this file cold, name the top two entry points without scrolling.

## 5. Non-Obvious Conventions

**Match existing shape. Don't normalise the outliers.**

- Never import `src/core/` from `src/api/`; keep the one-way data flow.
- No `asyncio.sleep` in request paths; use the scheduler module.

The test: grep for the convention in two more places before assuming it holds.

## 6. Absolute Rules

**Read and follow. No exceptions, no workarounds.**

### Safety
- MUST NOT commit secrets, `.env` files, or credentials.
- MUST NOT edit migrations after they have been applied.
- MUST NOT disable tests to make them pass.
- MUST NOT run destructive commands without explicit human approval.
- When a hook blocks a command, stop and ask — never work around it.

### While coding
- MUST NOT add abstractions beyond what is planned.
- MUST NOT improve or refactor adjacent unrelated code.
- MUST state assumptions explicitly; if uncertain, ask before proceeding.

## 7. Deeper Context

**This file is the kernel, not the full picture.**

- @docs/agents/architecture.md — stack, quick start, layer map
- @docs/agents/patterns.md — recurring patterns and exemplars
- @docs/agents/testing.md — runner, layout, mock stance
- @docs/agents/tech-debt.md — known gotchas

The test: if the answer is here, don't open `docs/agents/`.

---

Working if: agents stop asking "where does X live?", hook denials are respected, and PRs match the conventions above without being told.
"""


class AgentsKernelLintTests(unittest.TestCase):
    def _repo(self, tmp: str) -> Path:
        repo = Path(tmp)
        for name in ("architecture", "patterns", "testing", "tech-debt"):
            target = repo / "docs" / "agents" / f"{name}.md"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f"# {name}\n", encoding="utf-8")
        return repo

    def _lint(self, repo: Path, text: str):
        target = repo / "AGENTS.md"
        target.write_text(text, encoding="utf-8")
        results = []
        for runtime in ("py", "js"):
            result = run(
                runtime, "lint_agents_kernel",
                "--file", str(target), "--repo", str(repo), "--json",
            )
            results.append((result.returncode, result.stdout))
        return results

    def test_golden_realized_kernel_lints_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            results = self._lint(repo, GOLDEN)
            for returncode, stdout in results:
                self.assertEqual(returncode, 0, stdout)
                self.assertEqual(json.loads(stdout)["defects"], [])
            self.assertEqual(results[0], results[1])

    def test_title_shape_defects(self) -> None:
        dirty = GOLDEN.replace("## 1. Commands", "## 1. Commands?").replace(
            "## 2. Boundaries", "## 2. Deep dive",
        )
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            results = self._lint(repo, dirty)
            kinds = {
                item["kind"]
                for _returncode, stdout in results
                for item in json.loads(stdout)["defects"]
            }
            self.assertIn("title-shape", kinds)
            self.assertEqual(results[0][0], results[1][0])
            self.assertEqual(results[0][1], results[1][1])

    def test_tagline_length_defect(self) -> None:
        dirty = GOLDEN.replace(
            "**One way to run things. Don't invent alternatives.**",
            "**One and only one canonical way to run things, and never any invented alternative.**",
        )
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            results = self._lint(repo, dirty)
            for returncode, stdout in results:
                self.assertEqual(returncode, 1, stdout)
                kinds = {item["kind"] for item in json.loads(stdout)["defects"]}
                self.assertIn("tagline-length", kinds)
            self.assertEqual(results[0], results[1])

    def test_weak_tagline_warning(self) -> None:
        dirty = GOLDEN.replace("**A layer map, not a code tour.**", "**A layer map for a new reader.**")
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            results = self._lint(repo, dirty)
            for returncode, stdout in results:
                self.assertEqual(returncode, 0, stdout)
                kinds = {item["kind"] for item in json.loads(stdout)["warnings"]}
                self.assertIn("weak-tagline", kinds)
            self.assertEqual(results[0], results[1])

    def test_low_negation_ratio_warning(self) -> None:
        dirty = GOLDEN.replace(
            "- Never import `src/core/` from `src/api/`; keep the one-way data flow.\n",
            "- Imports always flow in one direction.\n",
        ).replace(
            "- No `asyncio.sleep` in request paths; use the scheduler module.",
            "- Scheduling always uses the scheduler module.",
        )
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            results = self._lint(repo, dirty)
            for returncode, stdout in results:
                self.assertEqual(returncode, 0, stdout)
                kinds = {item["kind"] for item in json.loads(stdout)["warnings"]}
                self.assertIn("low-negation-ratio", kinds)
            self.assertEqual(results[0], results[1])

    def test_bullet_length_warning(self) -> None:
        dirty = GOLDEN.replace(
            "- MUST NOT commit secrets, `.env` files, or credentials.",
            "- MUST NOT commit secrets.",
        )
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            results = self._lint(repo, dirty)
            for returncode, stdout in results:
                self.assertEqual(returncode, 0, stdout)
                kinds = {item["kind"] for item in json.loads(stdout)["warnings"]}
                self.assertIn("bullet-length", kinds)
            self.assertEqual(results[0], results[1])


class AgentsKernelCompactVariantTests(unittest.TestCase):
    """`agents_kernel` declares no `compact_group`, so `AGENTS.md` is written in
    every layout — but compact materializes only `docs/agents.md`. The standard
    template's `@docs/agents/*.md` fan-out therefore produced `dangling-at-ref`
    defects on a kernel written faithfully from its own template. The fix is a
    layout variant, not a linter exception: the disk check is correct."""

    TEMPLATES = (
        Path(__file__).resolve().parents[1]
        / "skills" / "docforge" / "_shared" / "content" / "agent-context" / "templates"
    )

    def _section_seven(self, text: str) -> str:
        start = text.index("## 7. Deeper Context")
        return text[start:text.index("---", start)]

    def test_compact_kernel_references_only_the_merged_file(self) -> None:
        compact = (self.TEMPLATES / "agents-kernel.compact.md").read_text(encoding="utf-8")
        section = self._section_seven(compact)
        self.assertIn("@docs/agents.md", section)
        self.assertNotIn("@docs/agents/", section)
        # `@` imports resolve a path; an anchored path is not a file, so the
        # compact-anchor rule that applies to indexes cannot apply here.
        self.assertNotIn("@docs/agents.md#", section)

    def test_kernel_templates_differ_only_in_section_seven(self) -> None:
        """The variant duplicates a ~90-line template for one section. This is
        the guard that keeps the other 80 lines from drifting apart."""
        standard = (self.TEMPLATES / "agents-kernel.md").read_text(encoding="utf-8")
        compact = (self.TEMPLATES / "agents-kernel.compact.md").read_text(encoding="utf-8")
        self.assertNotEqual(self._section_seven(standard), self._section_seven(compact))
        self.assertEqual(
            standard.replace(self._section_seven(standard), ""),
            compact.replace(self._section_seven(compact), ""),
        )

    def test_compact_layout_selects_the_variant_template(self) -> None:
        for runtime in ("py", "js"):
            for layout, expected in (
                ("standard", "content/agent-context/templates/agents-kernel.md"),
                ("compact", "content/agent-context/templates/agents-kernel.compact.md"),
            ):
                with self.subTest(runtime=runtime, layout=layout), tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    result = initialize(
                        runtime, repo, "spine", audiences=("coding-agents",), layout=layout,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    kernel = next(
                        doc for doc in load_manifest(repo)["documents"]
                        if doc["id"] == "agents_kernel"
                    )
                    self.assertEqual(kernel["scaffold_template"], expected)

    def test_compact_kernel_scaffold_lints_without_dangling_refs(self) -> None:
        """The regression proof: the standard template fails this."""
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                initialize(runtime, repo, "spine", audiences=("coding-agents",), layout="compact")
                for doc_id in ("agents_kernel", "agents_compact"):
                    run(
                        runtime, "scaffold_docs",
                        "--repo", str(repo),
                        "--manifest", str(repo / ".docforge" / "manifest.json"),
                        "--document", doc_id,
                    )
                lint = run(
                    runtime, "lint_agents_kernel",
                    "--file", str(repo / "AGENTS.md"), "--repo", str(repo),
                )
                self.assertNotIn("dangling-at-ref", lint.stdout + lint.stderr)


if __name__ == "__main__":
    unittest.main()
