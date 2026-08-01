---
name: docforge-revise
description: Structural refresh of Docforge documentation — revise all, a docs area, or flows. Accepts --plan-only and --auto-accept. Shares the Docforge cartridge.
---

# Docforge Revise

Slash command: `/docforge-revise`. Thin entrypoint into the `docforge`
skill — this skill has no runtime of its own. It requires the `docforge`
skill to be installed and loads its shared cartridge:
[`../docforge/_shared/`](../docforge/_shared/README.md).

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
| `/docforge-revise` | Ask which scope: `all`, `<area>`, or `flow` |
| `/docforge-revise all` | Full-tree revise |
| `/docforge-revise <area>` | Scoped revise (architecture, flows, operations, …) |
| `/docforge-revise flow` | Full flow pipeline |

Before any migration, detection, or writing, revise always stops and asks first,
using the question pack owned by
[`../docforge/_shared/workflows/intake.md`](../docforge/_shared/workflows/intake.md).
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

Same flags as `/docforge` (combinable with a scope argument). Detail:
[`../docforge/_shared/flags.md`](../docforge/_shared/flags.md).

Example: `/docforge-revise flow --plan-only`.

## Not this command

- Fresh-start documentation plan (no revise scope) → `/docforge`
  ([`../docforge/SKILL.md`](../docforge/SKILL.md)).
- Single named-document update/refresh → natural language under `/docforge`,
  staleness-first path in
  [`../docforge/_shared/workflows/revision.md`](../docforge/_shared/workflows/revision.md)
  (not a full revise).
- Read-only progress → plain language or `manage_manifest status` (no
  `--status` skill flag).
