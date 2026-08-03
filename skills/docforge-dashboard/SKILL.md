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
| *(none)* | `dashboard.{py,js} start` (scripts and README: [`${CLAUDE_SKILL_DIR}/../docforge/_shared/runtime/dashboard/README.md`](<${CLAUDE_SKILL_DIR}/../docforge/_shared/runtime/dashboard/README.md>)): reconcile metadata → rebuild generated output when the working-tree signature changed → serve → open |
| `--force` | Ignore signatures: always regenerate generated output (`content/docs`, assets, navigation, app shell), keeping `node_modules` |
| `--plan-only` | Preflight, metadata dry-run, signatures, and route plan; no conversion, no writes, no server. On a legacy manifest, the metadata dry-run is the `migrate_metadata.{py,js} --dry-run` preview (see [`${CLAUDE_SKILL_DIR}/../docforge/_shared/runtime/manifest/README.md`](<${CLAUDE_SKILL_DIR}/../docforge/_shared/runtime/manifest/README.md>)) |
| `--auto-accept` | Skip the revise-vs-render prompt and routine pauses; never authorizes npm install of new packages without its own confirmation gate (see [`${CLAUDE_SKILL_DIR}/../docforge/_shared/flags.md`](<${CLAUDE_SKILL_DIR}/../docforge/_shared/flags.md>)) |
| `--help` | Print this command's purpose and full parameter reference — [`${CLAUDE_SKILL_DIR}/../docforge/_shared/help.md`](<${CLAUDE_SKILL_DIR}/../docforge/_shared/help.md>) — then stop; run no workflow |

Subcommands: `scan` (read-only diagnostics: missing metadata, incomplete or
missing documents, stale provenance sources, broken links, untracked `docs/`
files), `start` (build-if-changed → serve → open), `status` (read-only
state), `stop` (shut down the background dev server). See
[`${CLAUDE_SKILL_DIR}/../docforge/_shared/workflows/dashboard.md`](<${CLAUDE_SKILL_DIR}/../docforge/_shared/workflows/dashboard.md>)
for the full lifecycle and isolation rules.

## Preflight gates

`start` runs three gates before it opens the dashboard; the full procedure and
exact wording are owned by
[`${CLAUDE_SKILL_DIR}/../docforge/_shared/workflows/dashboard.md`](<${CLAUDE_SKILL_DIR}/../docforge/_shared/workflows/dashboard.md>),
which this entrypoint's load order already pulls in. `--auto-accept` bypasses
none of them.

- **Legacy manifest** — a pre-3.0 `.docforge/manifest.json` (1.1
  `project_context` / `document_groups`, 2.0 flat `documents`, or any other
  legacy shape) stops with a three-option gate: revise all, update metadata
  only (`migrate_metadata` re-registers **any** legacy version as 3.1), or
  stop. `--plan-only` runs the `migrate_metadata.{py,js} --dry-run` preview.
- **Scan** — findings (missing metadata, incomplete documents, stale sources,
  broken links, untracked `docs/` files) print in full and recommend
  `/docforge-revise` before the dashboard is trusted; a clean scan means ready
  to render.
- **Build failure** — a failed `start` is **not** opened and no previous build
  is presented as current; revise first, then re-run once the whole-tree gate
  passes.

## Not this command

- Fresh-start documentation plan → `/docforge`
  ([`${CLAUDE_SKILL_DIR}/../docforge/SKILL.md`](<${CLAUDE_SKILL_DIR}/../docforge/SKILL.md>)).
- Structural revise of the documentation itself → `/docforge-revise`
  ([`${CLAUDE_SKILL_DIR}/../docforge-revise/SKILL.md`](<${CLAUDE_SKILL_DIR}/../docforge-revise/SKILL.md>)).
- Read-only progress → plain language or `manage_manifest.{py,js} status` (no
  `--status` skill flag; scripts and README:
  [`${CLAUDE_SKILL_DIR}/../docforge/_shared/runtime/manifest/README.md`](<${CLAUDE_SKILL_DIR}/../docforge/_shared/runtime/manifest/README.md>)).
