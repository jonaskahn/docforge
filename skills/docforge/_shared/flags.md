# Shared skill flags

`/docforge` and `/docforge-revise` share these flags (combinable with a
scope argument on revise where noted):

| Flag | Effect |
|---|---|
| `--plan-only` | Analyze and show the plan / dry-run tree; do not write or re-ground document bodies. On `/docforge`, precheck, analyze, init/update manifest, show dry-run tree. On `/docforge-revise`, run revise analysis (migrate, staleness, detect/catalog, audience prompt, dry-run tree / structure update). |
| `--auto-accept` | Display plans/trees/results, then continue without routine conversational pauses; never authorizes provider installation, graph build/refresh, manifest initialization, root `README.md` migration choices, file archive/deletion, or other side effects (see [`rules.md`](rules.md)) |
| `--no-dashboard` | Skip the automatic dashboard build/serve at run completion ([`workflows/validation.md`](workflows/validation.md) §7). The run still validates and completes; render later with `/docforge-dashboard` (or the internal `dashboard start`). |
| `--help` | Print this command's purpose and full parameter reference — the canonical text lives in [`help.md`](help.md) — then stop without loading a workflow. |

`--no-dashboard` does not apply to `/docforge-dashboard` (its purpose is the
dashboard itself).

There is no `--resume` or `--status` skill flag.

- Continue an incomplete run via interactive intake (Resume goal) or
  plain language → [`workflows/writing.md`](workflows/writing.md).
- Read-only progress: plain language or
  `manage_manifest status --repo <repo>`.
