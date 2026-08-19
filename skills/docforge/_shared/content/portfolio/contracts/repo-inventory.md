# `repo-inventory`

**Reader question** — "What repositories make up this portfolio, and what's known about each one?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | coverage-matrix |

Full coverage means every discovered repository has a row — including one excluded from the portfolio — recorded as excluded and why, rather than leaving no trace it was considered.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | One row per discovered repository, traced to a named discovery mechanism | the table | a hand-typed addition with no discovery trace |
| 2 | Role, owner token, documentation state (undocumented / spine / diligence / portfolio-aware), and evidence per field | the table | a role or owner filled with a plausible guess instead of `undetermined` |
| 3 | An explicit inclusion or exclusion decision and reason for every discovered repository | the table | an excluded repo omitted from the table instead of recorded as excluded |

## Keep out

| Not here | Lives in |
|---|---|
| A hand-typed collection omission | nowhere — every row must trace to `discover_child_repos` or the manifest |
| A plausible guess filling an undetermined field | nowhere — state `undetermined` |
| Dependency and boundary relationships between repos | `portfolio_system_context` |
| A repo's own documentation content | that repo's own `docs/README.md` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Discovered repositories, role, owner token, documentation state, evidence | `portfolio_system_context` | dependency and boundary relationships between repos are owned there; this document owns only the flat inventory |
| A gap in a repository's evidence | `portfolio_diligence_index` | confidence and follow-up gaps are tracked there, not resolved here |
