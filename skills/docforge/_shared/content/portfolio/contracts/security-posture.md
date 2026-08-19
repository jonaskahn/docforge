# `security-posture`

**Reader question** — "Which security controls cover the whole portfolio, and which member repos are missing one?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | coverage-matrix |

Full coverage means every control × repo cell filled with a status, including repos not yet reviewed, not just the ones with a finding.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | A coverage table: control × repo, not a narrative | lead | a narrative substituting for the coverage table |
| 2 | Status per cell: `covered`, `absent`, `not applicable`, or `unknown` | the table | a cell left blank instead of `unknown` |
| 3 | Evidence and as-of date, cross-repo blast radius, accountable follow-up per row | the table | assessment scope left unstated — what was not reviewed |

## Keep out

| Not here | Lives in |
|---|---|
| A finding that is really about one repository's internals | that repo's own `threat_model` |
| Member-level detail that adds no cross-repo information | nowhere — omit it |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Cross-repo control coverage and gaps | each member repo's own `threat_model` document | member-internal findings are owned there; this document owns only the cross-repo seam |
| An unresolved cross-repo gap | `portfolio_diligence_index` | tracks the confidence gap until a member closes it |
