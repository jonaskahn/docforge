# Tools

Owns: every public CLI, its Python and JS invocation forms, inputs, outputs,
side effects, and exit-code expectations.

Paths are relative to the cartridge root (`skills/docforge/_shared/`). Launchers live
under [`../runtime/cli/`](../runtime/cli/README.md); implementations under
`../runtime/<subsystem>/{js,python}/`.

## Installation

The cartridge may live in a **global** skill dir (`~/.agents/skills/docforge/_shared`,
`~/.claude/skills/docforge/_shared`, or `~/.config/opencode/skills/docforge/_shared`)
or be checked out **inside the repo** (`<repo>/skills/docforge/_shared`). Tools run
with the cartridge root as the working directory.

To make the plain documented invocations below work from the repo root
without the cartridge checked out in-repo, link the runtime once (user-run,
commit the link only if it points at a location shared by the team):

```sh
ln -s <cartridge>/runtime <repo>/runtime
```

A symlinked runtime resolves its own real path, so catalog and provenance
lookups stay correct. Always resolve the cartridge explicitly; never guess
from `PATH` or an ambient environment variable.

Every public command has a standard-library Python peer and a built-in-only
JS peer with the same flags, messages, JSON shapes, filesystem effects, and
exit codes. Unknown flags exit `2`.

## Session runtime (agent-owned)

Do **not** run a dedicated runtime-precheck script. Once per Docforge
session, the agent detects what is on `PATH` and locks **one** engine for
all Docforge tool calls until the session ends:

1. `python3` if present and ≥ 3.10, else `python` if ≥ 3.10.
2. Else `node` (18+), else `bun`, else `deno`.
3. If none work, stop and ask the user to install Python or a JS engine.

State the chosen engine briefly (e.g. “using python3 for this session”),
then use only that family’s launchers. Do not mix Python and JS peers in
one session.

## How to invoke

Always: **engine → launcher path → subcommand (if any) → flags**.

```sh
# Python session
python3 runtime/cli/python/<name>.py <subcommand?> --flag …

# JS session (exactly one of these for the whole session)
node runtime/cli/js/<name>.js <subcommand?> --flag …
bun  runtime/cli/js/<name>.js <subcommand?> --flag …
deno run -A runtime/cli/js/<name>.js <subcommand?> --flag …
```

## Public commands

When maintaining `_shared/.metadata`, `docforge:docforge-catalog-validator`
(bare `docforge-catalog-validator` from `.claude/agents/`) is the
isolated read-only way to run the catalog integrity checks, with the absolute
cartridge root passed to it.

- `query_catalog.{py,js}`: read the catalog (`--tier`, `--id`, `--ids`,
  `--profile`, `--applicable`, `--validate`, `--category <group>`,
  `--route <id>`). Every workflow step uses this instead of opening catalog
  files directly.
- `generate_indexes.{py,js}`: regenerate catalog routers (`--write`,
  `--check`). `--check` exits `1` without writing when generated output is
  stale.
- `manage_manifest.{py,js}`: `init`, `add`, `set`, `audit`, `status`, and `reconcile`.
- `detect_profiles.{py,js}`: read-only shape/platform/framework/concern
  recommendations with strong/weak match strength, cue bags, and
  `confirmed|candidate` confidence; `--emit-gate-pack` for agent intake.
- `discovery_gate.{py,js}`: validate/apply discovery-gate judgment JSON
  (offline; fail-open).
- `scaffold_docs.{py,js}`: exact dry-run, one-document materialization, and
  manifest-backed audit.
- `precheck_graph.{py,js}`: `--need code|flow`.
- `check_staleness.{py,js}`: `--document <id|path>`, `--section`, JSON output,
  and provenance sync.
- `migrate_metadata.{py,js}`: dry-run, report, and idempotent metadata upgrade;
  incomplete or unconvertible written documents are reported as `FAILED` and
  demoted to `in_progress` for agent regeneration.
- `flow_index.{py,js}`: harvest, revise (label/candidate dedup, compact
  communities summary, placeholder stubs, main NOTICE), and render the flow
  matrix; GitNexus input uses deterministic MCP-export JSON.
- `validate_metadata.{py,js}`: registry/schema/path/version/peer validation,
  including generated-router drift (`generate_indexes --check`).
- `dashboard.{py,js}`: `start` (reconcile metadata → rebuild generated
  output when the working-tree signature changed → serve → open), `status`,
  `stop`. The dev server runs detached. See
  [`../workflows/dashboard.md`](../workflows/dashboard.md) for the lifecycle
  and flags (`--force`, `--plan-only`, `--no-open`, `--skip-install`,
  `--port`).
- Graph adapters, readers, derivation, document lint, and child-repository
  discovery retain paired contracts.

## Canonical example

```sh
# After locking python3 for the session:
python3 runtime/cli/python/query_catalog.py --route <document-id>

# Or, if the session locked node instead:
node runtime/cli/js/query_catalog.js --route <document-id>
```

Returns the document's group, summary, definition path, contract,
instruction (or `null`), template, owning workflow, and required
capabilities in one call — see the retrieval protocol in
[`../retrieval.md`](../retrieval.md).
