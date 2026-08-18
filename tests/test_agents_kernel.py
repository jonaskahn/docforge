"""lint_agents_kernel: canonical contract, defects, and runtime parity."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _support import ROOT, initialize, load_manifest, run


GOLDEN = """\
# Demo Repo

A TypeScript service with an HTTP API, domain layer, and PostgreSQL store.

<!-- docforge-provenance v2.23.0 | graph abc1234 | 2026-08-01 | regenerate: re-run the coding-agents audience -->

## Commands

```sh
npm ci
npm run dev
npm test -- --runInBand
npm run lint
npm run build
```

## Repository Map

- `src/api`: HTTP routes and request validation.
- `src/core`: Domain rules and application services.
- `src/store`: Persistence adapters and migrations.
- Requests enter through `src/api/routes.ts` and hand off to `src/core/services.ts`.

Dependency direction: `src/api` may depend on `src/core`; `src/core` must not depend on `src/api`.

## Precedence

1. Preserve safety constraints and explicit approval requirements.
2. Follow the user's task requirements.
3. Follow the repository rules stated here.
4. If instructions conflict or evidence is missing, stop and ask.

## Boundaries

- Always run the focused test for the changed area.
- Ask first before deleting a shared branch or applied migration.
- Never commit secrets, credentials, or local environment values.
- Never disable tests, validation, or checks to force success.
- Never run destructive commands without explicit approval.

## Conventions

- Keep request parsing in `src/api` and domain decisions in `src/core`.
- Use the existing store adapter boundary for persistence changes.

## Validation

- Minimum for a focused change: `npm test -- --runInBand`
- Required before completion: `npm run lint && npm test && npm run build`
- Success means every command exits zero without skipped checks.

Working if: commands are reproducible, boundaries hold, and validation passes.
"""


class AgentsKernelLintTests(unittest.TestCase):
    def _lint(self, repo: Path, text: str) -> list[tuple[int, str]]:
        target = repo / "AGENTS.md"
        target.write_text(text, encoding="utf-8")
        results = []
        for runtime in ("py", "js"):
            result = run(
                runtime,
                "lint_agents_kernel",
                "--file",
                str(target),
                "--repo",
                str(repo),
                "--json",
            )
            results.append((result.returncode, result.stdout))
        return results

    def _payload(self, repo: Path, text: str) -> tuple[int, dict]:
        results = self._lint(repo, text)
        self.assertEqual(results[0], results[1], "Python and Node lint results differ")
        return results[0][0], json.loads(results[0][1])

    def test_golden_canonical_kernel_lints_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            returncode, payload = self._payload(Path(tmp), GOLDEN)
        self.assertEqual(returncode, 0, payload)
        self.assertEqual(payload["defects"], [])
        self.assertEqual(payload["warnings"], [])

    def test_required_headings_and_order_are_enforced(self) -> None:
        cases = {
            "missing": (
                GOLDEN.replace("## Repository Map", "## Modules"),
                "missing-section",
            ),
            "out-of-order": (
                GOLDEN.replace(
                    "## Repository Map\n",
                    "## Precedence\n\nRepository rules follow the safety hierarchy.\n\n## Repository Map\n",
                ).replace(
                    "## Precedence\n\n1. Preserve safety constraints and explicit approval requirements.\n"
                    "2. Follow the user's task requirements.\n"
                    "3. Follow the repository rules stated here.\n"
                    "4. If instructions conflict or evidence is missing, stop and ask.\n\n",
                    "",
                ),
                "section-order",
            ),
        }
        for name, (dirty, expected_kind) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                returncode, payload = self._payload(Path(tmp), dirty)
                self.assertEqual(returncode, 1, payload)
                self.assertIn(expected_kind, {item["kind"] for item in payload["defects"]})

    def test_commands_and_safety_boundaries_are_enforced(self) -> None:
        command_block = """```sh
npm ci
npm run dev
npm test -- --runInBand
npm run lint
npm run build
```"""
        cases = {
            "commands": (
                GOLDEN.replace(command_block, "Run the verified project commands."),
                {"missing-command-block"},
            ),
            "safety": (
                GOLDEN.replace(
                    "- Never commit secrets, credentials, or local environment values.\n"
                    "- Never disable tests, validation, or checks to force success.\n"
                    "- Never run destructive commands without explicit approval.",
                    "- Keep changes focused.\n"
                    "- Preserve existing behavior.\n"
                    "- Report unexpected failures.",
                ),
                {"missing-safety-rule"},
            ),
        }
        for name, (dirty, expected_kinds) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                returncode, payload = self._payload(Path(tmp), dirty)
                self.assertEqual(returncode, 1, payload)
                kinds = {item["kind"] for item in payload["defects"]}
                self.assertTrue(expected_kinds.issubset(kinds), payload)
                if name == "safety":
                    details = {item["detail"] for item in payload["defects"]}
                    self.assertTrue(any("secrets" in detail for detail in details))
                    self.assertTrue(any("validation" in detail for detail in details))
                    self.assertTrue(any("destructive commands" in detail for detail in details))

    def test_forbidden_references_are_detected_in_prose_fences_and_comments(self) -> None:
        provenance = "<!-- docforge-provenance v2.23.0 | graph abc1234 | 2026-08-01 | regenerate: re-run the coding-agents audience -->"
        cases = {
            "markdown-link": (
                GOLDEN.replace(
                    "Working if:",
                    "[Policy](POLICY.md)\n\nWorking if:",
                ),
                "doc-reference",
                "markdown-link: POLICY.md",
            ),
            "raw-url-in-comment": (
                GOLDEN.replace(
                    provenance,
                    provenance + "\n<!-- https://example.com/project-policy -->",
                ),
                "bare-url",
                "https://example.com/project-policy",
            ),
            "at-import-in-fence": (
                GOLDEN.replace("npm ci\n", "npm ci\n@docs/agents/testing.md\n"),
                "doc-reference",
                "at-import: @docs/agents/testing.md",
            ),
            "bare-markdown-path-in-comment": (
                GOLDEN.replace(
                    provenance,
                    provenance + "\n<!-- Consult POLICY.md before release. -->",
                ),
                "doc-reference",
                "bare-path: POLICY.md",
            ),
            "bare-docs-path-in-fence": (
                GOLDEN.replace("npm ci\n", "npm ci\ndocs/agents/\n"),
                "doc-reference",
                "bare-path: docs/agents/",
            ),
        }
        for name, (dirty, expected_kind, expected_detail) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                returncode, payload = self._payload(Path(tmp), dirty)
                self.assertEqual(returncode, 1, payload)
                matches = [
                    item
                    for item in payload["defects"]
                    if item["kind"] == expected_kind and expected_detail in item["detail"]
                ]
                self.assertTrue(matches, payload)

    def test_nonblank_line_budget_is_enforced(self) -> None:
        nonblank = sum(bool(line.strip()) for line in GOLDEN.splitlines())
        padding = "\n".join(
            f"Additional evidenced rule {number}."
            for number in range(1, 82 - nonblank)
        )
        dirty = GOLDEN.rstrip() + "\n" + padding + "\n"
        self.assertEqual(sum(bool(line.strip()) for line in dirty.splitlines()), 81)

        with tempfile.TemporaryDirectory() as tmp:
            returncode, payload = self._payload(Path(tmp), dirty)
        self.assertEqual(returncode, 1, payload)
        line_cap = [item for item in payload["defects"] if item["kind"] == "line-cap"]
        self.assertEqual(len(line_cap), 1, payload)
        self.assertIn("81 nonblank lines, cap is 80", line_cap[0]["detail"])


class AgentsKernelCanonicalTemplateTests(unittest.TestCase):
    TEMPLATES = (
        ROOT / "skills" / "docforge" / "_shared" / "content" / "agent-context" / "templates"
    )
    CATALOG = (
        ROOT
        / "skills"
        / "docforge"
        / "_shared"
        / ".metadata"
        / "catalog"
        / "documents"
        / "agent-context"
    )
    KERNEL_TEMPLATE = "content/agent-context/templates/agents-kernel.md"

    def _record(self, name: str) -> dict:
        return json.loads((self.CATALOG / f"{name}.json").read_text(encoding="utf-8"))

    def test_canonical_template_has_contract_headings_and_budget(self) -> None:
        template = (self.TEMPLATES / "agents-kernel.md").read_text(encoding="utf-8")
        headings = [line.removeprefix("## ") for line in template.splitlines() if line.startswith("## ")]
        self.assertEqual(
            headings,
            ["Commands", "Repository Map", "Precedence", "Boundaries", "Conventions", "Validation"],
        )
        self.assertLessEqual(sum(bool(line.strip()) for line in template.splitlines()), 80)

    def test_only_one_kernel_template_exists_and_catalog_has_no_variants(self) -> None:
        templates = sorted(path.name for path in self.TEMPLATES.glob("agents-kernel*.md"))
        self.assertEqual(templates, ["agents-kernel.md"])
        self.assertFalse((self.TEMPLATES / "agents-kernel.compact.md").exists())
        for record_name in ("agents_kernel", "claude_shim"):
            record = self._record(record_name)
            self.assertFalse(
                [key for key in record if "variant" in key],
                f"{record_name} still declares template variants",
            )

    def test_claude_record_is_the_same_full_kernel_profile(self) -> None:
        agents = self._record("agents_kernel")
        claude = self._record("claude_shim")
        self.assertEqual(agents["path"], "AGENTS.md")
        self.assertEqual(claude["path"], "CLAUDE.md")
        for field in (
            "type",
            "summary",
            "contract_file",
            "instruction_file",
            "requires",
            "target_depth",
            "provenance_mode",
            "audit_profile",
            "presentation",
            "template_file",
        ):
            with self.subTest(field=field):
                self.assertEqual(claude[field], agents[field])

    def test_standard_and_compact_manifests_choose_the_same_kernel_template(self) -> None:
        for runtime in ("py", "js"):
            selected = []
            for layout in ("standard", "compact"):
                with self.subTest(runtime=runtime, layout=layout), tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    result = initialize(
                        runtime,
                        repo,
                        "spine",
                        audiences=("coding-agents",),
                        layout=layout,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    by_id = {doc["id"]: doc for doc in load_manifest(repo)["documents"]}
                    pointers = []
                    for doc_id in ("agents_kernel", "claude_shim"):
                        doc = by_id[doc_id]
                        self.assertEqual(doc["scaffold_template"], self.KERNEL_TEMPLATE)
                        self.assertFalse([key for key in doc if "variant" in key], doc)
                        pointers.append(doc["scaffold_template"])
                    selected.append(tuple(pointers))
            self.assertEqual(selected[0], selected[1])


if __name__ == "__main__":
    unittest.main()
