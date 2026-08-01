# Docforge Dashboard skill

Slash command: `/docforge-dashboard` — a local, generated Fumadocs site that
renders the repository's written Docforge documentation. Entrypoint:
[`SKILL.md`](SKILL.md).

## Layout

Everything in this directory is **dashboard-specific**. The shared cartridge
(`../docforge/_shared/`) is loaded for rules, flags, retrieval, and the
provenance codec/util — nothing dashboard-only lives there.

| Path | Owns |
|---|---|
| [`SKILL.md`](SKILL.md) | Command entrypoint and load order |
| [`workflows/dashboard.md`](workflows/dashboard.md) | The full lifecycle (preflight → fingerprint → metadata reconcile → optional revise → route plan → MDX convert → navigation → validate → serve → open) |
| [`runtime/dashboard.py`](runtime/dashboard.py) | Python implementation of the dashboard CLI |
| [`runtime/dashboard.js`](runtime/dashboard.js) | Node implementation of the dashboard CLI (peer) |
| [`runtime/template/`](runtime/template/) | Static Fumadocs application shell copied into `.docforge/dashboard/` |
| [`runtime/cli/python/dashboard.py`](runtime/cli/python/dashboard.py) | Thin Python launcher |
| [`runtime/cli/js/dashboard.js`](runtime/cli/js/dashboard.js) | Thin JS launcher |

Both runtime peers consume the shared cartridge's `runtime.common` codec and
util (provenance frontmatter, manifest loading, gitignore helpers) but are
otherwise self-contained; `runtime/template/` is the single source of the
app shell.

## CLI reference

Run from this skill root:

```sh
python3 runtime/cli/python/dashboard.py <subcommand> --repo <repo> [flags]
node runtime/cli/js/dashboard.js <subcommand> --repo <repo> [flags]
```

Global flags: `--repo` (default: current directory), `--manifest`
(default: `<repo>/.docforge/manifest.json`), `--dashboard`
(default: `<repo>/.docforge/dashboard`), `--json`.

| Subcommand | Purpose | Extra flags |
|---|---|---|
| `status` | Dashboard existence, fingerprint match, server state, included-document count | |
| `fingerprint` | Print the current fingerprint (HEAD + manifest + flow-index + `docs/` + template + root package hashes) | |
| `metadata` | Reconcile public `id` / `title` / provenance identity from the manifest, preserving bodies | `--dry-run` |
| `plan` | Route ledger with duplicate-URL detection; exit 1 on problems | |
| `build` | Metadata reconcile + scaffold + MDX convert + navigation + assets + state + install | `--force`, `--skip-install`, `--no-metadata` |
| `validate` | URLs, meta coverage, internal links/anchors, assets, docs index; exit 1 on errors | |
| `serve` | Start (or reuse) the localhost-only dev server | `--port N` |
| `stop` | Stop the recorded dev server | |

Exit codes: `0` success, `1` error (manifest missing, plan/validate problems,
conversion errors, npm failures), `2` usage. Python and JS peers are
equivalent; see [`workflows/dashboard.md`](workflows/dashboard.md) for the
full lifecycle and isolation rules.
