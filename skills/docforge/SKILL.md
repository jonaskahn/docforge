---
name: docforge
description: Catalog-driven repository documentation with bounded repository-evidence retrieval, manifest metadata, independent audits, and equivalent Python/Node tools.
---

# Docforge

Slash command: `/docforge`. Fresh-start documentation mode: plan and write new
documentation from repository evidence. Shared cartridge:
[`./_shared/README.md`](./_shared/README.md).

Cartridge root: the `_shared/` directory that ships next to this SKILL.md.
Locate the copy of this skill that the host loaded — never resolve against the
session working directory. Check, in order:

1. **Repo-local self-host** — if the working repo contains
   `skills/docforge/SKILL.md`, the cartridge is
   `<repo>/skills/docforge/_shared`.
2. **Plugin root** — a plugin install keeps the same layout:
   `<plugin-root>/skills/docforge/_shared`.
3. **Global skill dirs** — the running agent's own dir first, then the shared
   standard set: `~/.agents/skills/docforge/_shared`,
   `~/.claude/skills/docforge/_shared`,
   `~/.config/opencode/skills/docforge/_shared`, plus any other skill dir the
   running agent documents.

Use the repo-local copy when the working repo self-hosts it; otherwise the
global one. Resolve every path inside loaded cartridge files against this
root, never the working directory. If no copy can be located,
ask the user for the absolute cartridge root first.

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

Run tools from the cartridge root (`./_shared/`). Lock
one session engine first; see
[`./_shared/workflows/tools.md`](./_shared/workflows/tools.md) for execution rules and CLI syntax.

## `/docforge`

| Flag | Effect |
|---|---|
| *(none)* | Interactive intake → [`./_shared/workflows/intake.md`](./_shared/workflows/intake.md) |
| `--plan-only` | See [`./_shared/flags.md`](./_shared/flags.md) |
| `--auto-accept` | See [`./_shared/flags.md`](./_shared/flags.md) |
| `--no-dashboard` | Skip the automatic dashboard build/serve at run completion (see [`./_shared/flags.md`](./_shared/flags.md)) |
| `--help` | Print this command's purpose and full parameter reference — [`./_shared/help.md`](./_shared/help.md) — then stop; run no workflow |

A task with tier/profile already given skips answered intake questions and
goes to [`./_shared/workflows/planning.md`](./_shared/workflows/planning.md),
then writing. Natural-language **update** / **refresh** of a named document →
[`./_shared/workflows/revision.md`](./_shared/workflows/revision.md)
(staleness-first).

## Completion

A run is complete only after the whole-tree gate
([`./_shared/workflows/validation.md`](./_shared/workflows/validation.md))
passes and — unless the invocation included `--plan-only` or `--no-dashboard`
— the dashboard has been started and its URL reported in the final response
(`validation.md` §7 Dashboard auto-serve). Never finish a run with the docs
written but the dashboard never started or its URL never shown.

## Other routes

- Structural revise (`flow` / `<area>` / `all`) → internal workflow
  [`./_shared/workflows/revision.md`](./_shared/workflows/revision.md)
  (the sibling skill `docforge-revise` is only a thin entrypoint into it).
- Local dashboard (render written docs as a Fumadocs site) → internal
  workflow [`./_shared/workflows/dashboard.md`](./_shared/workflows/dashboard.md)
  (the sibling skill `docforge-dashboard` is only a thin entrypoint into it).
- Staleness, migration, or a whole-tree/cross-document check →
  [`./_shared/workflows/validation.md`](./_shared/workflows/validation.md).
- Read-only progress → plain language or
  `manage_manifest.{py,js} status --repo <repo>` (no `--status` skill flag;
  scripts and README:
  [`./_shared/runtime/manifest/README.md`](./_shared/runtime/manifest/README.md)).
