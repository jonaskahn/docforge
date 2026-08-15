---
name: docforge-revise
description: Refreshes documentation Docforge already wrote — the whole tree, one area, or flows; a bare run only syncs manifest metadata.
---

# Docforge Revise

Slash command: `/docforge-revise`. Thin entrypoint into the `docforge`
skill — this skill has no runtime of its own. It requires the `docforge`
skill to be installed and loads its shared cartridge:
[`../docforge/_shared/README.md`](../docforge/_shared/README.md).

Never run any migration or write any file without explicit user confirmation
first.

Cartridge root: `../docforge/_shared` relative to this SKILL.md — the
`docforge` skill's `_shared`, whether installed as a plugin, via Agent Skills,
or in a global skill dir. Locate the copy of this skill that the host loaded —
never resolve against the session working directory. Check, in order:

1. **Repo-local self-host** — if the working repo contains
   `skills/docforge-revise/SKILL.md`, the cartridge is
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

1. [`../docforge/_shared/rules.md`](../docforge/_shared/rules.md) — safety, graph precondition,
   provider sufficiency, completion.
2. [`../docforge/_shared/flags.md`](../docforge/_shared/flags.md) — `--plan-only`,
   `--auto-accept`.
3. [`../docforge/_shared/retrieval.md`](../docforge/_shared/retrieval.md) — catalog retrieval
   protocol.
4. Follow [`../docforge/_shared/workflows/revision.md`](../docforge/_shared/workflows/revision.md)
   for the full revise meaning and procedures.
5. For audience confirm/add-more when rediscovering docs, use the Output
   audience rules in
   [`../docforge/_shared/workflows/intake.md`](../docforge/_shared/workflows/intake.md).

Run tools from the cartridge root (`../docforge/_shared/`). Lock one session engine
first; see [`../docforge/_shared/workflows/tools.md`](../docforge/_shared/workflows/tools.md) for execution rules and CLI syntax.

## Arguments

| Invocation | Behavior |
|---|---|
| `/docforge-revise` | Metadata-only: migrate/upgrade the manifest metadata via `migrate_metadata.{py,js}` (`--dry-run` preview first, apply only when needed). No scope question, no detection, no writing, no dashboard |
| `/docforge-revise flow` | Full flow pipeline |
| `/docforge-revise <area>` | Scoped revise (architecture, flows, operations, …) |
| `/docforge-revise all` | Full-tree revise |

A bare `/docforge-revise` asks nothing and writes nothing — it only brings
the manifest metadata up to date (see
[`../docforge/_shared/workflows/revision.md`](../docforge/_shared/workflows/revision.md),
Bare `/docforge-revise`). Before any migration, detection, or writing, every
scoped revise stops and asks first. The
question pack and stop-and-ask mechanics are owned by
[`../docforge/_shared/workflows/intake.md`](../docforge/_shared/workflows/intake.md)
and
[`../docforge/_shared/workflows/revision.md`](../docforge/_shared/workflows/revision.md):
one confirmation covering Scope, Tier, Profiles, Output audience, and Execution
mode, but scaled to what is actually unresolved or changed — each dimension
shows either its persisted value as an unchanged baseline fact, or, only when
it actually has a delta or a requested change, a `Change to <tier>` /
`Add` / `Remove` control. Never proceed on silent defaults.

When the revise finds foreign docs (`.md` / `.mdx` under `docs/` with no
manifest entry), the same confirmation adds the **unmanaged-document
triage**: per file, Keep self-managed (recommended) or Archive to
`docs/_archive/<year>/` — applied with `manage_manifest.{py,js} unmanaged`
(see [`../docforge/_shared/references/docs-tree.md`](../docforge/_shared/references/docs-tree.md)).

Before writing, revise displays an annotated plan tree (`add` / `update` /
`rewrite` / `unchanged` / `skip`), including the `Flows:` mapping.

## Flags

Same flags as `/docforge` (combinable with a scope argument), including
`--no-dashboard` (skip the automatic dashboard build/serve at completion) and
`--help` (print this command's purpose and full parameter reference from
[`../docforge/_shared/help.md`](../docforge/_shared/help.md) and stop). Detail:
[`../docforge/_shared/flags.md`](../docforge/_shared/flags.md).

Example: `/docforge-revise flow --plan-only`.

## Completion

A revise run is complete only after the whole-tree gate
([`../docforge/_shared/workflows/validation.md`](../docforge/_shared/workflows/validation.md))
passes and — unless the invocation included `--plan-only` or `--no-dashboard`
— the dashboard has been started and its URL reported in the final response
(`validation.md` §7 Dashboard auto-serve). Never finish a run with the docs
revised but the dashboard never started or its URL never shown.

## Not this command

- Fresh-start documentation plan (no revise scope) → `/docforge`
  ([`../docforge/SKILL.md`](../docforge/SKILL.md)).
- Single named-document update/refresh → natural language under `/docforge`,
  staleness-first path in
  [`../docforge/_shared/workflows/revision.md`](../docforge/_shared/workflows/revision.md)
  (not a full revise).
- Read-only progress → plain language or `manage_manifest.{py,js} status`
  (no `--status` skill flag; scripts and README:
  [`../docforge/_shared/runtime/manifest/README.md`](../docforge/_shared/runtime/manifest/README.md)).
