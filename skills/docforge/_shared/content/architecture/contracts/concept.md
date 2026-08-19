# `concept`

**Reader question** — "What does this concept mean in this codebase, and what may I assume is always true of it?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | answer-first |

The concept's responsibility is the governing claim, named in one sentence before any mechanism.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | The concept and the responsibility it owns, in one sentence | L0 | opening with the class that implements it instead of the responsibility |
| 2 | What it models and its lifecycle/states, every state named before any is explained | L1 | one state explained fully while its siblings are still unnamed |
| 3 | Invariants stated as rules that must always hold, not descriptions of current behavior | L2 | an invariant asserted for a concept that never actually transitions |
| 4 | Relationships and the boundary where a neighbouring concept takes over | L2 | a neighbouring concept's own invariants folded into this one |
| 5 | The failure boundary: what this concept guarantees will not happen, and what it does not protect against | L2 | a lifecycle asserted for a concept that never transitions |
| 6 | Where it lives | L3 | a symbol-by-symbol implementation tour |

## Keep out

| Not here | Lives in |
|---|---|
| A symbol-by-symbol implementation tour | the code itself |
| A neighbouring concept's invariants | that concept's own document |
| A lifecycle asserted for a concept that never transitions | nowhere — state that it has none |
| A shortcut affecting this concept | `tech_debt` |
| A hard bound affecting this concept | `architecture_constraints` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| This concept's responsibility, relationships, invariants | `arch_high_level` (the block it belongs to) | the concept is the deep-dive version of one block named there |
| — | `arch_low_level` | low-level traces the mechanism that implements this concept's invariants |
| A shortcut affecting this concept | `tech_debt` | fixable-by-us shortcuts are never described here as if permanent |
| A hard bound affecting this concept | `architecture_constraints` | externally imposed limits are owned there, not repeated per concept |
