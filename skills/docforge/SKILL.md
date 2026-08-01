---
name: docforge
description: Catalog-driven repository documentation with bounded repository-evidence retrieval, manifest metadata, independent audits, and equivalent Python/Node tools.
---

# Docforge

Slash command: `/docforge`. Fresh-start documentation mode: plan and write new
documentation from repository evidence. Shared cartridge: [`./_shared/`](./_shared/README.md).

## Load order

1. [`./_shared/rules.md`](./_shared/rules.md) — safety, graph precondition,
   provider sufficiency, completion.
2. [`./_shared/flags.md`](./_shared/flags.md) — `--plan-only`,
   `--auto-accept`.
3. [`./_shared/retrieval.md`](./_shared/retrieval.md) — catalog retrieval
   protocol.
4. Select a workflow from
   [`./_shared/workflows/README.md`](./_shared/workflows/README.md).
5. Load [`./_shared/ownership.md`](./_shared/ownership.md) when resolving
   which file owns a rule.

Run tools from the cartridge root (`./_shared/`). Lock one session engine
first; see [`./_shared/workflows/tools.md`](./_shared/workflows/tools.md) for execution rules and CLI syntax.

## `/docforge`

| Flag | Effect |
|---|---|
| *(none)* | Interactive intake → [`./_shared/workflows/intake.md`](./_shared/workflows/intake.md) |
| `--plan-only` | See [`./_shared/flags.md`](./_shared/flags.md) |
| `--auto-accept` | See [`./_shared/flags.md`](./_shared/flags.md) |

A task with tier/profile already given skips answered intake questions and
goes to [`./_shared/workflows/planning.md`](./_shared/workflows/planning.md),
then writing. Natural-language **update** / **refresh** of a named document →
[`./_shared/workflows/revision.md`](./_shared/workflows/revision.md)
(staleness-first).

## Other routes

- Structural revise (`all` / `<area>` / `flow`) → structural refresh of an
  existing plan/tree in sibling skill
  [`../docforge-revise/SKILL.md`](../docforge-revise/SKILL.md).
- Staleness, migration, or a whole-tree/cross-document check →
  [`./_shared/workflows/validation.md`](./_shared/workflows/validation.md).
- Read-only progress → plain language or
  `manage_manifest status --repo <repo>` (no `--status` skill flag).
