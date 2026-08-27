# `architecture-high-level`

**Reader question** — "What does this system do, what surrounds it, what's inside the box, and how is it deployed?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | working | answer-first |

The capability this system owns and its top architectural drivers are the L0 claim, stated before any structure; context and containers are the L1 whole-subject pass, mapped onto C4's top two levels. It is a **stable overview**: subsystem internals, detailed failure taxonomies, and implementation tours stay out. A deployment view and failure-domain summary are included only when execution actually spans multiple nodes, processes, devices, environments, or containers.

For `infrastructure-platform`-shaped repos, "deployable block" reads as "provisioned resource / environment."

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | The capability this system owns and its top architectural drivers, stated before any structure | L0 | mechanism or structure stated before the capability |
| 2 | System frame: external actors and deployable/provisioned blocks, each with responsibility, technology, directional active relationships | L1 | a container-level block sprouting component-level detail |
| 3 | Two separate diagrams — Context, then Containers — never combined | L1 | one diagram standing in for both C4 views |
| 4 | Evidenced protocol/channel per relationship, or an explicit `unknown` | L2 | a relationship with no direction or verb, or a generic verb (`calls`, `uses`) |
| 5 | A compact relationship matrix (direction, active verb, protocol/channel, owner), and a link to `tech_stack` for each block's technology | L2 | technology invented instead of linked from `tech_stack` |
| 6 | System-wide invariants | L2 | an invariant stated as a description of current behavior instead of an absence-based fact |
| 7 | A compact failure-domain summary when execution spans multiple nodes/processes/containers: failed element, blast radius, degradation, recovery owner | L2 | failure domains asserted with no evidence, or silently omitted when plainly applicable |
| 8 | A deployment view when execution spans multiple nodes, processes, devices, environments, or containers | L2 | a deployment mapping asserted with no evidence, or absent when plainly applicable |
| 9 | Quality/change drivers only when supported by requirements, limits, benchmarks, tests, or extension points | L3 | an estimated figure presented as a driver |
| 10 | A routing map to selected subsystem and specialized architecture documents | L3 | a link to an unmaterialized path |
| 11 | Explicit omissions when deployment, quality, or failure views are inapplicable or unsupported | L3 | a missing view that reads as "handled" instead of "deliberately omitted" |
| 12 | The forces that shaped this shape, named and linked to the records that settled them | L3 | a decision record's argument or rejected alternatives repeated here |

## Keep out

| Not here | Lives in |
|---|---|
| A decision record's argument or its rejected alternatives | the linked decision record |
| Component detail or code listings | `arch_low_level`, `architecture_subsystem` |
| Subsystem internals or implementation tours | the subsystem deep dive |
| Detailed failure taxonomies | `arch_low_level`, `architecture_subsystem` |
| Mixed context/container diagrams | nowhere — always two separate diagrams |
| Known shortcuts and hard bounds | `tech_debt`, `architecture_constraints` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Context, blocks, boundaries, communication, invariants, deployment mapping, failure-domain summary | `arch_low_level` | low-level is this document's zoom-in; a block named here must trace to a component write-up there |
| Which blocks become subsystem deep dives | `architecture_subsystem` (via `subsystems/`) | a significant block is decomposed in its own deep dive; this document names the block and routes to it |
| — | decision records | rationale for why a block is shaped this way lives in decisions, never restated here |
| — | `tech_debt`, `architecture_constraints` | known shortcuts and hard bounds are tracked in their own registers, not folded into this stable document |
| Each deployable block's implementing technology | `tech_stack` | what the repository is built with is owned there; this document only labels each block with it |
