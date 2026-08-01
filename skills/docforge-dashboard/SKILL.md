---
name: docforge-dashboard
description: Local Fumadocs dashboard for Docforge documentation — start, stop, or check the generated site at /docs. Thin entrypoint into the Docforge cartridge.
---

# Docforge Dashboard

Slash command: `/docforge-dashboard`. Thin entrypoint into the `docforge`
skill — this skill has no runtime of its own. It requires the `docforge`
skill to be installed and loads its shared cartridge:
[`../docforge/_shared/README.md`](../docforge/_shared/README.md).

## Load order

1. [`../docforge/_shared/rules.md`](../docforge/_shared/rules.md) — safety, graph precondition,
   provider sufficiency, completion.
2. [`../docforge/_shared/flags.md`](../docforge/_shared/flags.md) — `--plan-only`,
   `--auto-accept`.
3. [`../docforge/_shared/retrieval.md`](../docforge/_shared/retrieval.md) — catalog retrieval
   protocol.
4. Follow [`../docforge/_shared/workflows/dashboard.md`](../docforge/_shared/workflows/dashboard.md)
   for the full dashboard lifecycle.
5. For execution rules and CLI syntax, use
   [`../docforge/_shared/workflows/tools.md`](../docforge/_shared/workflows/tools.md).

Run tools from the cartridge root (`../docforge/_shared/`). Lock one session
engine first; see
[`../docforge/_shared/workflows/tools.md`](../docforge/_shared/workflows/tools.md).

```sh
# After locking python3 for this session:
python3 runtime/cli/python/dashboard.py start --repo <repo> [--force] [--plan-only] [--no-open]

# After locking node instead:
node runtime/cli/js/dashboard.js start --repo <repo> [--force] [--plan-only] [--no-open]
```

## `/docforge-dashboard`

| Flag | Effect |
|---|---|
| *(none)* | `dashboard start`: reconcile metadata → rebuild generated output when the working-tree signature changed → serve → open |
| `--force` | Ignore signatures: always regenerate generated output (`content/docs`, assets, navigation, app shell), keeping `node_modules` |
| `--plan-only` | Preflight, metadata dry-run, signatures, and route plan; no conversion, no writes, no server |
| `--auto-accept` | Skip the revise-vs-render prompt and routine pauses; never authorizes npm install of new packages without its own confirmation gate (see [`../docforge/_shared/flags.md`](../docforge/_shared/flags.md)) |

Subcommands: `start` (build-if-changed → serve → open), `status` (read-only
state), `stop` (shut down the background dev server). See
[`../docforge/_shared/workflows/dashboard.md`](../docforge/_shared/workflows/dashboard.md)
for the full lifecycle and isolation rules.

## Not this command

- Fresh-start documentation plan → `/docforge`
  ([`../docforge/SKILL.md`](../docforge/SKILL.md)).
- Structural revise of the documentation itself → `/docforge-revise`
  ([`../docforge-revise/SKILL.md`](../docforge-revise/SKILL.md)).
- Read-only progress → plain language or `manage_manifest status` (no
  `--status` skill flag).
