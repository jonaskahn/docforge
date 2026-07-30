---
name: docforge-revise
description: Structural refresh of Docforge documentation — revise all, a docs area, or flows. Accepts --plan-only and --auto-accept. Shares the Docforge cartridge.
---

# Docforge Revise

Slash command: `/docforge-revise`. Companion to `/docforge`. Shared cartridge:
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
first (see [`../docforge/_shared/rules.md`](../docforge/_shared/rules.md)); always put
subcommands before flags:

```sh
# Example after locking python3 for this session:
python3 runtime/cli/python/query_catalog.py --route <document-id>

# Example after locking node instead:
node runtime/cli/js/query_catalog.js --route <document-id>
```

## Arguments

| Invocation | Behavior |
|---|---|
| `/docforge-revise` | Ask which scope: `all`, `<area>`, or `flow` |
| `/docforge-revise all` | Full-tree revise |
| `/docforge-revise <area>` | Scoped revise (architecture, flows, operations, …) |
| `/docforge-revise flow` | Full flow pipeline |

## Flags

Same flags as `/docforge` (combinable with a scope argument). Detail:
[`../docforge/_shared/flags.md`](../docforge/_shared/flags.md).

Example: `/docforge-revise flow --plan-only`.

## Not this command

- Brand-new documentation plan (no revise scope) → `/docforge`
  ([`../docforge/SKILL.md`](../docforge/SKILL.md)).
- Single named-document update/refresh → natural language under `/docforge`,
  staleness-first path in
  [`../docforge/_shared/workflows/revision.md`](../docforge/_shared/workflows/revision.md)
  (not a full revise).
- Read-only progress → plain language or `manage_manifest status` (no
  `--status` skill flag).
