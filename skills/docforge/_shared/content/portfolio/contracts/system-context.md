# `system-context`

**Reader question** — "Where do this portfolio's repository boundaries sit, and what crosses them?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | answer-first |

The portfolio-wide boundary is the governing claim, held at Context-level zoom; member-repo internals are explicitly out of scope.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Repository and system boundaries at Context level: member repos, shared services, external systems | L0 | member-repo internals described in depth, losing the portfolio altitude |
| 2 | Cross-repo flows, each stated as trigger → repos involved → outcome | L1 | a flow's steps re-derived instead of linked to the owning member document |
| 3 | Directed dependency edges between members, each with coupling type and resolution confidence | L2 | a heuristic edge presented as confirmed |
| 4 | Edge resolution order stated and followed: identity mapping, then heuristic signature/convention match, then omit | L2 | an invented edge with no resolution path |

## Keep out

| Not here | Lives in |
|---|---|
| Repo-local internals | that repo's own `arch_high_level`, `arch_low_level` |
| A member-internal call graph | that member's own `flow` document |
| A heuristic edge presented without a confidence marker | nowhere — mark it heuristic or omit it |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Portfolio-level repo/system boundaries, cross-repo flows, dependency edges and their resolution | each member's own `arch_high_level` | member-internal container detail is owned there; this document only borders it |
| A cross-repo flow's steps | that flow's owning member document | this document states trigger → repos → outcome only; step detail is never re-derived here |
| A repo not yet resolved to an identity mapping | `portfolio_repo_inventory` | inventory evidence is owned there; this document consumes it to draw edges |
