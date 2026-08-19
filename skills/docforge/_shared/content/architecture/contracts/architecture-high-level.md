# `architecture-high-level`

**Reader question** — "What does this system do, what surrounds it, and what's inside the box?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | orientation | answer-first |

The capability this system owns is the L0 claim, stated before any structure; context and containers are the L1 whole-subject pass, mapped onto C4's top two levels.

For `infrastructure-platform`-shaped repos, "deployable block" reads as "provisioned resource / environment."

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | The capability this system owns, stated before any structure | L0 | mechanism or structure stated before the capability |
| 2 | System frame: external actors and deployable/provisioned blocks, each with responsibility, technology, directional active relationships | L1 | a container-level block sprouting component-level detail |
| 3 | Two separate diagrams — Context, then Containers — never combined | L1 | one diagram standing in for both C4 views |
| 4 | Evidenced protocol/channel per relationship, or an explicit `unknown` | L2 | a relationship with no direction or verb, or a generic verb (`calls`, `uses`) |
| 5 | A compact relationship matrix, and a link to `tech_stack` for each block's technology | L2 | technology invented instead of linked from `tech_stack` |
| 6 | The forces that shaped this shape, named and linked to the records that settled them | L3 | a decision record's argument or rejected alternatives repeated here |

## Keep out

| Not here | Lives in |
|---|---|
| A decision record's argument or its rejected alternatives | the linked decision record |
| Component detail or code listings | `arch_low_level` |
| Mixed context/container diagrams | nowhere — always two separate diagrams |
| Known shortcuts and hard bounds | `tech_debt`, `architecture_constraints` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Context, blocks, boundaries, communication, invariants | `arch_low_level` | low-level is this document's zoom-in; a block named here must trace to a component write-up there |
| — | decision records | rationale for why a block is shaped this way lives in decisions, never restated here |
| — | `tech_debt`, `architecture_constraints` | known shortcuts and hard bounds are tracked in their own registers, not folded into this stable document |
| Each deployable block's implementing technology | `tech_stack` | what the repository is built with is owned there; this document only labels each block with it |
