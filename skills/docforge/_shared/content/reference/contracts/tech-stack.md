# `tech-stack`

**Reader question** — "What is this repository actually built with?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | lookup |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Detected languages/versions, runtimes/SDKs, primary frameworks per layer, datastores/messaging, build/package/dependency tooling, test/CI tooling, key runtime libraries with role | the table | a version derived from a lockfile or import instead of a declared source |
| 2 | Rows grouped by the layer a maintainer would change together | the table | alphabetical grouping instead of by layer |

## Shape-conditional must-present

For `infrastructure-platform`, replace row 1 with: IaC tool + version, cloud provider(s) targeted, orchestration platform, environments defined, promotion/release tooling, secret-management approach.

## Keep out

| Not here | Lives in |
|---|---|
| A full lockfile dump | nowhere — declared versions only |
| An invented version or marketing comparison | nowhere |
| Operational-failure framing | `dependencies` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| What the repository is built with | `dependencies` | what it depends on operationally and what breaks is owned there |
| Each deployable block's implementing technology | `arch_high_level` | the blocks built with this stack are named there; this document only labels each block with it |
