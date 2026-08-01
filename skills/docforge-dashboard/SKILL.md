---
name: docforge-dashboard
description: Local Fumadocs dashboard for Docforge documentation — start, stop, or check the generated site at /docs. Thin entrypoint into the Docforge cartridge.
---

# Docforge Dashboard

Slash command: `/docforge-dashboard`. Thin entrypoint into the `docforge`
skill — this skill has no runtime of its own. It requires the `docforge`
skill to be installed and loads its shared cartridge:
[`${CLAUDE_SKILL_DIR}/../docforge/_shared/README.md`](<${CLAUDE_SKILL_DIR}/../docforge/_shared/README.md>).

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
4. Follow [`${CLAUDE_SKILL_DIR}/../docforge/_shared/workflows/dashboard.md`](<${CLAUDE_SKILL_DIR}/../docforge/_shared/workflows/dashboard.md>)
   for the full dashboard lifecycle.
5. For execution rules and CLI syntax, use
   [`${CLAUDE_SKILL_DIR}/../docforge/_shared/workflows/tools.md`](<${CLAUDE_SKILL_DIR}/../docforge/_shared/workflows/tools.md>).

Run tools from the cartridge root (`${CLAUDE_SKILL_DIR}/../docforge/_shared/`). Lock one session
engine first; see
[`${CLAUDE_SKILL_DIR}/../docforge/_shared/workflows/tools.md`](<${CLAUDE_SKILL_DIR}/../docforge/_shared/workflows/tools.md>).

```sh
# After locking python3 for this session:
python3 runtime/cli/python/dashboard.py scan --repo <repo> [--json]
python3 runtime/cli/python/dashboard.py start --repo <repo> [--force] [--plan-only] [--no-open]

# After locking node instead:
node runtime/cli/js/dashboard.js scan --repo <repo> [--json]
node runtime/cli/js/dashboard.js start --repo <repo> [--force] [--plan-only] [--no-open]
```

## `/docforge-dashboard`

| Flag | Effect |
|---|---|
| *(none)* | `dashboard start`: reconcile metadata → rebuild generated output when the working-tree signature changed → serve → open |
| `--force` | Ignore signatures: always regenerate generated output (`content/docs`, assets, navigation, app shell), keeping `node_modules` |
| `--plan-only` | Preflight, metadata dry-run, signatures, and route plan; no conversion, no writes, no server |
| `--auto-accept` | Skip the revise-vs-render prompt and routine pauses; never authorizes npm install of new packages without its own confirmation gate (see [`${CLAUDE_SKILL_DIR}/../docforge/_shared/flags.md`](<${CLAUDE_SKILL_DIR}/../docforge/_shared/flags.md>)) |
| `--help` | Print this command's purpose and full parameter reference — [`${CLAUDE_SKILL_DIR}/../docforge/_shared/help.md`](<${CLAUDE_SKILL_DIR}/../docforge/_shared/help.md>) — then stop; run no workflow |

Subcommands: `scan` (read-only diagnostics: missing metadata, incomplete or
missing documents, stale provenance sources, broken links, untracked `docs/`
files), `start` (build-if-changed → serve → open), `status` (read-only
state), `stop` (shut down the background dev server). See
[`${CLAUDE_SKILL_DIR}/../docforge/_shared/workflows/dashboard.md`](<${CLAUDE_SKILL_DIR}/../docforge/_shared/workflows/dashboard.md>)
for the full lifecycle and isolation rules.

## Scan first: you should revise again

Every `/docforge-dashboard` run starts with the diagnostic scan (also printed
by `start` before it builds). If the scan reports problems — missing
metadata, incomplete or missing documents, stale sources, broken links,
untracked `docs/` files — do not silently open the dashboard: present the
full findings and tell the user **you should revise again**, recommending
`/docforge-revise` (scoped to the failing documents or `all`), and ask
whether to run the revision now. `--auto-accept` still prints the findings
and the recommendation before proceeding. A clean scan means the
documentation is ready to render.

## Validation failure

If `dashboard start` fails (route plan problems, conversion errors, or
validation errors), the dashboard is **not** opened and the previous build
must not be presented as current. Show every error, then ask the user to
**revise the documentation first** — `/docforge-revise` (scoped to the
failing area, or `all`) — and only re-run `dashboard start` after the
revision passes the whole-tree gate. `--auto-accept` never skips this
request.

## Not this command

- Fresh-start documentation plan → `/docforge`
  ([`${CLAUDE_SKILL_DIR}/../docforge/SKILL.md`](<${CLAUDE_SKILL_DIR}/../docforge/SKILL.md>)).
- Structural revise of the documentation itself → `/docforge-revise`
  ([`${CLAUDE_SKILL_DIR}/../docforge-revise/SKILL.md`](<${CLAUDE_SKILL_DIR}/../docforge-revise/SKILL.md>)).
- Read-only progress → plain language or `manage_manifest status` (no
  `--status` skill flag).
