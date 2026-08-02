# CLI launchers

Public entrypoints for Docforge tools. Each file is a thin re-export of the
matching implementation under `runtime/<subsystem>/{js,python}/`. Business
logic never lives here.

Paths below are relative to the cartridge root (`skills/docforge/_shared/`).
In a repo where the runtime is linked at the root (`ln -s <cartridge>/runtime
<repo>/runtime`), the same paths work from the repo root too.

## Session runtime (agent-owned)

There is no runtime-precheck CLI. At the start of a Docforge session the
agent probes the host once (`command -v` / equivalent) and **locks one
engine for every Docforge tool call in that session**:

1. Prefer Python: `python3`, else `python` (3.10+).
2. Else JS: `node` (22+), else `bun`, else `deno`.
3. If none are available, stop and tell the user to install one family.

Do not switch engines mid-session. Python and JS peers are behaviorally
equivalent; a few JS implementations are execution shims (they exit on
`require`) rather than importable re-exports, which does not affect CLI use.

### Invocation forms

```sh
# Python (session locked to python3 or python)
python3 runtime/cli/python/<name>.py <subcommand-or-flags…>

# JS (session locked to one of node / bun / deno)
node runtime/cli/js/<name>.js <subcommand-or-flags…>
bun  runtime/cli/js/<name>.js <subcommand-or-flags…>
deno run -A runtime/cli/js/<name>.js <subcommand-or-flags…>
```

Always put the command/subcommand before flags (e.g.
`manage_manifest init --repo <repo> --tier spine`, never flags before `init`).

## Layout

| Path | Owns |
|---|---|
| [`python/`](python/) | Python 3 launchers |
| [`js/`](js/) | Node/Bun/Deno launchers (`package.json` keeps CommonJS) |

## Public commands

| Command | Purpose |
|---|---|---|
| `precheck_graph` | Require a readable code or flow graph (`--need code\|flow`) |
| `query_catalog` | Read catalog records, categories, and `--route` packs |
| `generate_indexes` | Regenerate catalog routers (`--write` / `--check`) |
| `validate_metadata` | Catalog, schema, peer, and release-metadata validation |
| `detect_profiles` | Shape/platform/framework/concern recommendations (writes `.docforge/scratch/manifest-deps.json`) |
| `manage_manifest` | `init` / `add` / `set` / `presentation` / `status` / `audit` / `reconcile` / `finish` |
| `scaffold_docs` | Dry-run tree, one-document materialize, manifest audit |
| `check_staleness` | Provenance blob drift + optional sync |
| `migrate_metadata` | Idempotent metadata / provenance upgrade |
| `flow_index` | Harvest / revise / organize / render flow matrix |
| `derive_flow_graph` | Provisional flow-graph prepare/write |
| `diagnose_graphs` | Multi-provider graph readiness report |
| `read_graph` | JSON code-graph probe helpers (not DB providers) |
| `lint_document` | Mechanical document lint |
| `lint_agents_kernel` | AGENTS.md / agent-kernel lint |
| `discover_child_repos` | Portfolio child-repository discovery |
| `dashboard` | `scan` / `start` / `status` / `stop` for the local Fumadocs site |
| `graph_source_codegraph` / `graph_source_gitnexus` | Per-provider `detect` readiness probes |
| `graph_source_gitnexus_reader` | Offline LadybugDB inventory reader |
| `graph_source_registry` / `graph_source_understand_anything` / `graph_storage` | Library-only (no useful standalone CLI) |
| `discovery_gate` | Library-only: validate/apply gate judgment JSON (no CLI parser) |
| `provenance_frontmatter` | Provenance YAML codec (library; not a CLI) |
| `manifest_deps` | Manifest dependency helpers (library) |
| `_util` | Shared helpers (library; not a CLI) |

Python-only one-shot migrations (no JS peer): `split_catalog`,
`split_document_catalog` — historical tools; see
[`../migrations/README.md`](../migrations/README.md) before running them.

Per-script detail (flags, side effects, exit codes): the subsystem READMEs
under `../<subsystem>/README.md`, plus
[`../../workflows/tools.md`](../../workflows/tools.md). Each subsystem README's
"Where invoked" section lists the exact workflow/reference that calls that
command — if no file invokes a script, the README says so explicitly
(e.g. the historical `migrations/` tools).
