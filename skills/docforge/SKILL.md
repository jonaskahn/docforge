---
name: docforge
description: Catalog-driven repository documentation with bounded repository-evidence retrieval, manifest metadata, independent audits, and equivalent Python/Node tools.
---

# Docforge

Slash command: `/docforge`. Fresh-start documentation mode: plan and write new
documentation from repository evidence. Shared cartridge: [`${CLAUDE_SKILL_DIR}/_shared/`](<${CLAUDE_SKILL_DIR}/_shared/README.md>).

Cartridge root: `${CLAUDE_SKILL_DIR}/_shared` (substituted at load — the
absolute directory of this skill, whether installed as a plugin or via Agent
Skills). Resolve every path inside loaded cartridge files against this root,
never the working directory. If you see the literal `${CLAUDE_SKILL_DIR}`
placeholder (older host), ask the user for the absolute cartridge root first.

## Load order

1. [`${CLAUDE_SKILL_DIR}/_shared/rules.md`](<${CLAUDE_SKILL_DIR}/_shared/rules.md>) — safety, graph precondition,
   provider sufficiency, completion.
2. [`${CLAUDE_SKILL_DIR}/_shared/flags.md`](<${CLAUDE_SKILL_DIR}/_shared/flags.md>) — `--plan-only`,
   `--auto-accept`.
3. [`${CLAUDE_SKILL_DIR}/_shared/retrieval.md`](<${CLAUDE_SKILL_DIR}/_shared/retrieval.md>) — catalog retrieval
   protocol.
4. Select a workflow from
   [`${CLAUDE_SKILL_DIR}/_shared/workflows/README.md`](<${CLAUDE_SKILL_DIR}/_shared/workflows/README.md>).
5. Load [`${CLAUDE_SKILL_DIR}/_shared/ownership.md`](<${CLAUDE_SKILL_DIR}/_shared/ownership.md>) when resolving
   which file owns a rule.

Run tools from the cartridge root (`${CLAUDE_SKILL_DIR}/_shared/`). Lock
one session engine first; see
[`${CLAUDE_SKILL_DIR}/_shared/workflows/tools.md`](<${CLAUDE_SKILL_DIR}/_shared/workflows/tools.md>) for execution rules and CLI syntax.

## `/docforge`

| Flag | Effect |
|---|---|
| *(none)* | Interactive intake → [`${CLAUDE_SKILL_DIR}/_shared/workflows/intake.md`](<${CLAUDE_SKILL_DIR}/_shared/workflows/intake.md>) |
| `--plan-only` | See [`${CLAUDE_SKILL_DIR}/_shared/flags.md`](<${CLAUDE_SKILL_DIR}/_shared/flags.md>) |
| `--auto-accept` | See [`${CLAUDE_SKILL_DIR}/_shared/flags.md`](<${CLAUDE_SKILL_DIR}/_shared/flags.md>) |
| `--no-dashboard` | Skip the automatic dashboard build/serve at run completion (see [`${CLAUDE_SKILL_DIR}/_shared/flags.md`](<${CLAUDE_SKILL_DIR}/_shared/flags.md>)) |
| `--help` | Print this command's purpose and full parameter reference — [`${CLAUDE_SKILL_DIR}/_shared/help.md`](<${CLAUDE_SKILL_DIR}/_shared/help.md>) — then stop; run no workflow |

A task with tier/profile already given skips answered intake questions and
goes to [`${CLAUDE_SKILL_DIR}/_shared/workflows/planning.md`](<${CLAUDE_SKILL_DIR}/_shared/workflows/planning.md>),
then writing. Natural-language **update** / **refresh** of a named document →
[`${CLAUDE_SKILL_DIR}/_shared/workflows/revision.md`](<${CLAUDE_SKILL_DIR}/_shared/workflows/revision.md>)
(staleness-first).

## Other routes

- Structural revise (`flow` / `<area>` / `all`) → internal workflow
  [`${CLAUDE_SKILL_DIR}/_shared/workflows/revision.md`](<${CLAUDE_SKILL_DIR}/_shared/workflows/revision.md>)
  (the sibling skill `docforge-revise` is only a thin entrypoint into it).
- Local dashboard (render written docs as a Fumadocs site) → internal
  workflow [`${CLAUDE_SKILL_DIR}/_shared/workflows/dashboard.md`](<${CLAUDE_SKILL_DIR}/_shared/workflows/dashboard.md>)
  (the sibling skill `docforge-dashboard` is only a thin entrypoint into it).
- Staleness, migration, or a whole-tree/cross-document check →
  [`${CLAUDE_SKILL_DIR}/_shared/workflows/validation.md`](<${CLAUDE_SKILL_DIR}/_shared/workflows/validation.md>).
- Read-only progress → plain language or
  `manage_manifest status --repo <repo>` (no `--status` skill flag).
