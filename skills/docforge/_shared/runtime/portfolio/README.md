# Portfolio runtime

Cross-repository discovery for portfolio-tier diligence: parent repository,
declared submodules, undeclared nested Git repositories, baseline status, and
cross-member dependency edges. A paired Python/JS public command with a
launcher in [`runtime/cli/`](../cli/README.md).

## Load this when

- Establishing the repository collection for a portfolio run before any scope
  decision → `discover_child_repos`.

It is **discovery, not a scope decision**: detected members still require
explicit inclusion/exclusion judgment.

## Scripts

| Script | js/py | Kind | Purpose |
|---|---|---|---|
| `discover_child_repos` | both | CLI | Parent/submodule/nested repo inventory, baseline status, dependency edges |

## Details

### `discover_child_repos`

```sh
python3 runtime/cli/python/discover_child_repos.py --root <parent-repo> \
  [--exclude <dir-name> ...] [--json]
```

Inputs: `<root>/.gitmodules`, `.git` markers, per-repo
`docs/architecture/{high-level,overview}.md`, `.docforge/manifest.json`
(status and `project.tier`), `.docforge/flow-index.json`, optional
`.metadata/portfolio/repo-identity.json`, package manifests across
children (npm, Composer, pip, Cargo, Go, Ruby gems, Maven/Gradle, NuGet, pub).

Output (JSON mode): `root`, `collection` (membership:
`parent | declared | detected`, plus per-repo status and `tier:
spine | diligence | portfolio | null`), `needs_generation`,
`dependency_edges` (`repo`, `depends_on`, `coupling_type`, `resolution:
mapping | heuristic`, `ecosystem`, `package`), and `flow_edges` (`repo`,
`counterpart`, `channel_kind`, `signature`, `resolution: mapping |
heuristic`). Human mode prints the same information as text.

Tier readiness (are all included members already at Diligence or higher, so
Portfolio can be suggested?) is deliberately **not** computed here — a
detected member still needs an explicit inclusion decision first
(see `portfolio.md`'s Collection procedure), and this script only reports
the mechanical facts that decision is made from.

Flow edges are resolved the same way dependency edges are (mapping file
first, then heuristic, never invented) but never by querying a graph across
repo boundaries — each member's `.docforge/flow-index.json` is already
materialized by that member's own Diligence run.

**Read-only**: no files are written and no mutating Git commands run. The
parent is excluded from both dependency-edge and flow-edge extraction.
`--exclude` matches directory basenames (affects nested-repo discovery
only).

## Where invoked

| Script | Documented callers |
|---|---|
| `discover_child_repos` | [`references/portfolio.md`](../../references/portfolio.md) |

## Boundaries

Consumes `common/manifest_deps` for dependency extraction. The identity-mapping
schema lives at `_shared/.metadata/portfolio/repo-identity-schema.json`.
Portfolio *workflow* guidance: [`../../references/portfolio.md`](../../references/portfolio.md).
