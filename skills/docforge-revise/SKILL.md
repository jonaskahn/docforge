---
name: docforge-revise
description: Structural refresh of Docforge documentation — revise all, a docs area, or flows. Accepts --plan-only and --auto-accept. Shares the Docforge cartridge.
---

# Docforge Revise

Slash command: `/docforge-revise`. Thin entrypoint into the `docforge`
skill — this skill has no runtime of its own. It requires the `docforge`
skill to be installed and loads its shared cartridge:
[`${CLAUDE_SKILL_DIR}/../docforge/_shared/`](<${CLAUDE_SKILL_DIR}/../docforge/_shared/README.md>).

Cartridge root: `${CLAUDE_SKILL_DIR}/../docforge/_shared` (substituted at
load — resolves to the docforge skill's `_shared`, whether installed as a
plugin or via Agent Skills). Resolve every path inside loaded cartridge files
against this root, never the working directory. If you see the literal
`${CLAUDE_SKILL_DIR}` placeholder (older host), ask the user for the absolute
cartridge root first.

## Load order

1. [`${CLAUDE_SKILL_DIR}/../docforge/_shared/rules.md`](<${CLAUDE_SKILL_DIR}/../docforge/_shared/rules.md>) — safety, graph precondition,
   provider sufficiency, completion.
2. [`${CLAUDE_SKILL_DIR}/../docforge/_shared/flags.md`](<${CLAUDE_SKILL_DIR}/../docforge/_shared/flags.md>) — `--plan-only`,
   `--auto-accept`.
3. [`${CLAUDE_SKILL_DIR}/../docforge/_shared/retrieval.md`](<${CLAUDE_SKILL_DIR}/../docforge/_shared/retrieval.md>) — catalog retrieval
   protocol.
4. Follow [`${CLAUDE_SKILL_DIR}/../docforge/_shared/workflows/revision.md`](<${CLAUDE_SKILL_DIR}/../docforge/_shared/workflows/revision.md>)
   for the full revise meaning and procedures.
5. For audience confirm/add-more when rediscovering docs, use the Output
   audience rules in
   [`${CLAUDE_SKILL_DIR}/../docforge/_shared/workflows/intake.md`](<${CLAUDE_SKILL_DIR}/../docforge/_shared/workflows/intake.md>).

Run tools from the cartridge root (`${CLAUDE_SKILL_DIR}/../docforge/_shared/`). Lock one session engine
first; see [`${CLAUDE_SKILL_DIR}/../docforge/_shared/workflows/tools.md`](<${CLAUDE_SKILL_DIR}/../docforge/_shared/workflows/tools.md>) for execution rules and CLI syntax.

## Arguments

| Invocation | Behavior |
|---|---|
| `/docforge-revise` | Ask which scope: `flow`, `<area>`, or `all` |
| `/docforge-revise flow` | Full flow pipeline |
| `/docforge-revise <area>` | Scoped revise (architecture, flows, operations, …) |
| `/docforge-revise all` | Full-tree revise |

Before any migration, detection, or writing, revise always stops and asks first,
using the question pack owned by
[`${CLAUDE_SKILL_DIR}/../docforge/_shared/workflows/intake.md`](<${CLAUDE_SKILL_DIR}/../docforge/_shared/workflows/intake.md>).
Present the discovery brief and question set in one response: Scope, Tier,
Profiles (shape / platform / framework / concern), Output audience, and
Execution mode. For every persisted manifest choice, display the current value
or values as the baseline. Offer `Change to <tier>` alternatives for tier, and
only `Add <value>` / `Remove <value>` actions for profiles and audiences; never
offer a `Keep` option or require re-selecting current values. Fresh detection
is a recommended `Add` action. Show the confirmation summary and wait for
explicit confirmation before continuing; never proceed on silent defaults.

Before writing, revise displays an annotated plan tree (`add` / `update` /
`rewrite` / `unchanged` / `skip`), including the `Flows:` mapping.

## Flags

Same flags as `/docforge` (combinable with a scope argument), including
`--no-dashboard` (skip the automatic dashboard build/serve at completion) and
`--help` (print this command's purpose and full parameter reference from
[`${CLAUDE_SKILL_DIR}/../docforge/_shared/help.md`](<${CLAUDE_SKILL_DIR}/../docforge/_shared/help.md>) and stop). Detail:
[`${CLAUDE_SKILL_DIR}/../docforge/_shared/flags.md`](<${CLAUDE_SKILL_DIR}/../docforge/_shared/flags.md>).

Example: `/docforge-revise flow --plan-only`.

## Completion

A revise run is complete only after the whole-tree gate
([`${CLAUDE_SKILL_DIR}/../docforge/_shared/workflows/validation.md`](<${CLAUDE_SKILL_DIR}/../docforge/_shared/workflows/validation.md>))
passes and — unless the invocation included `--plan-only` or `--no-dashboard`
— the dashboard has been started and its URL reported in the final response
(`validation.md` §7 Dashboard auto-serve). Never finish a run with the docs
revised but the dashboard never started or its URL never shown.

## Not this command

- Fresh-start documentation plan (no revise scope) → `/docforge`
  ([`${CLAUDE_SKILL_DIR}/../docforge/SKILL.md`](<${CLAUDE_SKILL_DIR}/../docforge/SKILL.md>)).
- Single named-document update/refresh → natural language under `/docforge`,
  staleness-first path in
  [`${CLAUDE_SKILL_DIR}/../docforge/_shared/workflows/revision.md`](<${CLAUDE_SKILL_DIR}/../docforge/_shared/workflows/revision.md>)
  (not a full revise).
- Read-only progress → plain language or `manage_manifest status` (no
  `--status` skill flag).
