# Docforge Dashboard skill

Slash command: `/docforge-dashboard`. Thin entrypoint into the
[`docforge`](../docforge/SKILL.md) skill — it has no runtime of its own. The
dashboard capability (workflow, Python/Node runtime, and the Fumadocs app
template) lives in the shared cartridge at
[`../docforge/_shared/workflows/dashboard.md`](../docforge/_shared/workflows/dashboard.md)
and [`../docforge/_shared/runtime/dashboard/`](../docforge/_shared/runtime/dashboard/).

Installing this skill alone is not supported: it requires the `docforge`
skill for rules, flags, retrieval, and the dashboard runtime. It exists only
so hosts can offer a dedicated `/docforge-dashboard` activation.

## CLI reference

Run from the cartridge root (`../docforge/_shared/`):

```sh
python3 runtime/cli/python/dashboard.py <subcommand> --repo <repo> [flags]
node runtime/cli/js/dashboard.js <subcommand> --repo <repo> [flags]
```

Global flags: `--repo` (default: current directory), `--manifest`
(default: `<repo>/.docforge/manifest.json`), `--dashboard`
(default: `<repo>/.docforge/dashboard`), `--json`.

| Subcommand | Purpose | Extra flags |
|---|---|---|
| `start` | Reconcile metadata, rebuild generated output when the signature changed, serve, and open | `--force`, `--plan-only`, `--no-open`, `--skip-install`, `--port N` |
| `status` | Dashboard existence, render-signature match, server state, included-document count | |
| `stop` | Stop the recorded background dev server | |

Exit codes: `0` success, `1` error (manifest missing, plan/validate problems,
conversion errors, npm failures), `2` usage. Python and JS peers are
equivalent; see
[`../docforge/_shared/workflows/dashboard.md`](../docforge/_shared/workflows/dashboard.md)
for the full lifecycle and isolation rules.
