"""lint_agents_kernel: rubric checks, template guard, Python/Node parity."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _support import run

GOLDEN = """\
# Demo Repo

A demo service with one framework and one test runner.

<!-- docforge-provenance v2.6.0 | graph abc1234 | 2026-08-01 | regenerate: re-run the coding-agents audience -->

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


if __name__ == "__main__":
    unittest.main()
