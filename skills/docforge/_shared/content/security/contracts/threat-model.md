# `threat-model`

**Reader question** — "What can go wrong in this system, and what actually stops it?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | answer-first |

The bounded DFD is the L1 map — assets, trust zones, external entities, processes, data stores, flows — named before any threat is analyzed against it.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | A bounded DFD naming assets, trust zones, and every element type | L1 | a trust boundary drawn around a process node instead of a zone or crossing |
| 2 | A full element-by-STRIDE matrix, every applicable cell `N/A`, `examined-none-found`, or a threat ID | L2 | a cell silently left blank |
| 3 | Concrete threats, each with exactly one disposition (mitigate, eliminate, transfer, accept) tied to a testable control | L2 | a threat with more than one disposition, or a control no one could actually test |
| 4 | An accepted risk carrying a decision link, rationale, review condition, and evidenced owner | L2 | an exposure called "mitigated" with no decision behind it |
| 5 | Residual uncertainty and a top-threat summary | L3 | likelihood, owner, or control effectiveness inferred rather than evidenced |

## Keep out

| Not here | Lives in |
|---|---|
| Disclosure workflow | `security_root` |
| Credentials | nowhere |
| Guessed scores or owners | nowhere — state unscored/unowned instead |
| Unremediated vulnerability detail | nowhere — not safe to publish |
| Scores and exhaustive interactions | `threat_register` |
| Data classification and handling rules, restated | `data_handling` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| The bounded DFD, STRIDE matrix, threats, responses | `threat_register` | scores and exhaustive interactions are owned there, never this narrative |
| — | `data_handling` | data classifications are owned there, linked not restated |
| — | `security_root` | disclosure workflow is owned there; kept out of this document |
