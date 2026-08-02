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
`docs/architecture/{high-level,overview}.md` and `.docforge/manifest.json`,
optional `.metadata/portfolio/repo-identity.json`, package manifests across
children (npm, Composer, pip, Cargo, Go, Ruby gems, Maven/Gradle, NuGet, pub).

Output (JSON mode): `root`, `collection` (membership:
`parent | declared | detected`, plus per-repo status), `needs_generation`, and
`dependency_edges` (`repo`, `depends_on`, `coupling_type`, `resolution:
mapping | heuristic`, `ecosystem`, `package`). Human mode prints the same
information as text.

**Read-only**: no files are written and no mutating Git commands run. The
parent is excluded from dependency-edge extraction. `--exclude` matches
directory basenames (affects nested-repo discovery only).

## Where invoked

| Script | Documented callers |
|---|---|
| `discover_child_repos` | [`references/portfolio.md`](../../references/portfolio.md) |

## Boundaries

Consumes `common/manifest_deps` for dependency extraction. The identity-mapping
schema lives at `_shared/.metadata/portfolio/repo-identity-schema.json`.
Portfolio *workflow* guidance: [`../../references/portfolio.md`](../../references/portfolio.md).
