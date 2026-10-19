# Shared skill flags

`/docforge` and `/docforge-revise` share these flags (combinable with a
scope argument on revise where noted):

| Flag | Effect |
|---|---|
| `--plan-only` | Analyze and show the plan / dry-run tree; do not write or re-ground document bodies. On `/docforge`, precheck, analyze, init/update manifest, show dry-run tree. On a scoped `/docforge-revise` (`flow` / `<area>` / `all`) **with no task clause**, run revise analysis (migrate, staleness, detect/catalog, audience prompt, dry-run tree / structure update). On a **bare** `/docforge-revise`, stop after the `migrate_metadata --dry-run` preview and never apply it (see [`workflows/revision.md`](workflows/revision.md) "Bare `/docforge-revise`"). Metadata is not a document body: whenever the scope reaches the flow gate, the gate still fires and `.docforge/flow-index.json` plus its main-standalone stubs are written, so the tree carries a real flow-document count — a targeted revise (a stated task clause; see [`workflows/revision.md`](workflows/revision.md) "Revise objective") never reaches the flow gate at all unless the task itself changes which flows are documented, so that guarantee narrows with it. |
| `--auto-accept` | Display plans/trees/results, then continue without routine conversational pauses. What it never waives is owned by the [Flag → gate matrix](#flag--gate-matrix) below — every other document links here instead of restating the list. |
| `--no-dashboard` | Skip the automatic dashboard build/serve at run completion ([`workflows/validation.md`](workflows/validation.md) "Dashboard auto-serve") — suppresses both the forced serve and, in compact layout, the dashboard offer. The run still validates and completes; render later with `/docforge-dashboard` (or the internal `dashboard start`). |
| `--research <mode>` | Authorize external web research for this run. Modes: `official-primary` (standards bodies and normative specs, then official framework/platform/protocol/vendor documentation, then primary research papers; recommended), `official-only` (official documentation only, no primary research), `off` (no web access). An explicit flag is prior user confirmation for that run. Without it, planning agents that identify material external questions show them and ask before any web access — and `--auto-accept` never grants web access implicitly. On `--plan-only`, the selected policy is recorded but actual web research is deferred until a writing run |
| `--vendor <id>` | Repeatable; selects which AI coding-agent vendors receive shim context files (`claude`, `codex`, `cursor`, `copilot`, `windsurf`, `aider`, `gemini`). Without it, only Claude outputs materialize (the existing default); each flag fans out one additional vendor's shim from the same kernel ([`references/profiles/audience-coding-agents.md`](references/profiles/audience-coding-agents.md) "Vendor fan-out") |
| `--help` | Print this command's purpose and full parameter reference — the canonical text lives in [`help.md`](help.md) — then stop without loading a workflow. |

## Flag → gate matrix

`--auto-accept` waives *routine conversational pauses* and nothing else. The
tables below are the complete list of what it does not waive; every other file
links here rather than repeating it, so this stays the one place a gate's
waiver status is decided.

**Side-effect gates** — each needs its own approval:

| Gate | Why it is not routine |
|---|---|
| Provider installation, global setup, MCP wiring | Changes the user's machine, not the repository |
| Repository index build / refresh | Expensive and environment-affecting |
| Root `README.md` migrate / skip / rewrite | Overwrites or reshapes a file the user may own |
| File archive / deletion — `unmanaged archive` moves, `retire` moves or deletes | Removes content from its current location |
| External web research | Reaches outside the repository; authorize with `--research` |

**Mandatory selection gates** — each is a scope decision the user must make:

| Gate | Owner |
|---|---|
| Flow selection gate (which flows become documents) | [`references/graph/flow-derivation.md`](references/graph/flow-derivation.md) "Selection gate and write-back" |
| Architecture-pack gate | [`workflows/planning.md`](workflows/planning.md) "Architecture-pack gate" |
| Agent-context selection gate (which agent documents are added / updated / removed) | [`workflows/planning.md`](workflows/planning.md) "Agent-context selection gate (write-start)" |
| Final intake confirmation | [`workflows/intake.md`](workflows/intake.md) "Confirmation summary" |

The plan-tree view is *displayed* under `--auto-accept` but not paused on;
the architecture pack is confirmed at that same checkpoint and is not waived.
A targeted revise ([`workflows/revision.md`](workflows/revision.md) "Revise
objective") never reaches the flow pipeline, so there is no gate there to
waive.

Manifest initialization is an ordinary, ungated planning step in both Review
and Auto-accept — it is not on either list above.

`--no-dashboard` does not apply to `/docforge-dashboard` (its purpose is the
dashboard itself).

There is no `--resume` or `--status` skill flag.

- Continue an incomplete run via interactive intake (Resume goal) or
  plain language → [`workflows/writing.md`](workflows/writing.md).
- Read-only progress: plain language or
  `manage_manifest status --repo <repo>`.
