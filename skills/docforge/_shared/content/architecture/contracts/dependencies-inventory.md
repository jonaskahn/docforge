# `dependencies-inventory`

**Reader question** — "Which dependency would hurt most if it broke or disappeared?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | deep-dive | lookup |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | A risk-oriented table ordered by criticality — the dependency whose failure would hurt most goes first | lead | alphabetical ordering instead of criticality |
| 2 | An "if it disappeared" column or equivalent prose, per dependency | the table | package metadata presented as an operational claim |
| 3 | License for every direct dependency | the table | an unverified license, failure mode, or replacement assumption presented as fact |
| 4 | Grouping by runtime library, external service, build/tooling, generated inventory | the table | judgment (criticality, failure handling) squeezed into a table cell instead of prose beside it |

## Keep out

| Not here | Lives in |
|---|---|
| A generated lockfile dump | nowhere — automate the exhaustive inventory, hand-write only direct dependencies and assessment |
| What the repository is built with | `tech_stack` |
| A network boundary a dependency crosses | `infra_network` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Direct dependencies/integrations, purpose, criticality, failure behavior | `tech_stack` | tech-stack states what the repository is built with; this document adds the failure-framing judgment tech-stack omits |
| A dependency's known weakness or accepted risk | `tech_debt` or `threat_model`'s accepted-risk section | route by whether it's fixable (debt) or an accepted external risk (threat model), never both |
| A network boundary a dependency crosses | `infra_network` | the trust-zone crossing is owned there; this document owns the dependency's criticality judgment |
