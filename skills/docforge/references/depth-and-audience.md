# Depth and audience — the two axes

Documentation has two independent axes. Confusing them is why docs end up uniformly shallow
(everything at one depth) or organized so that each audience re-reads another's material.

- **Depth (vertical):** how far down a document goes, from orientation to deep mechanism.
- **Audience (horizontal):** who reads which depth.

A document declares which cells of the grid it fills. `document-composition.md` puts the
shallow, shared cells in a topic `README.md` and the deep, per-reader cells in subfiles.

## The depth ladder

| Level | Reader | Content | Lives in |
|---|---|---|---|
| **L0 Orientation** | PO, stranger, exec | What it is, why it matters. A paragraph. | topic `README.md` |
| **L1 Map / flow** | new engineer, reviewer, BA (skim) | Where things are; how the flow runs, in plain language. | topic `README.md` |
| **L2 Mechanism** | contributor | How a subsystem works; data model; edge cases. | audience subfile (`engineering.md`) |
| **L3 Deep-dive** | staff, maintainer, auditor | Algorithm; invariants and why they hold; concurrency; failure modes; trade-offs. | audience subfile |

Business rules are the one case where a non-engineer wants L1–L2 depth: the exact thresholds
and exceptions go in `business-analyst.md`, not the README, but a plain statement of each
rule and every critical one's notice stays in the README (invariant 2).

**Depth is selective.** Only architecturally significant, slow-changing subsystems earn an
L2/L3 deep-dive. Deep-diving every module inflates provenance churn for no reader's benefit.

## Which understand-anything command feeds which cell

The knowledge graph gives breadth (the map). Depth comes from the deeper commands —
`/understand-explain` is the engine for L2/L3 and is required there, not optional.

| Document / layer | Depth | Command | What it yields |
|---|---|---|---|
| `architecture/high-level.md` (context, blocks) | L1 | `/understand` (the graph) | module map, layers, boundaries |
| `architecture/low-level.md` (components) | L1–L2 | graph + `/understand-explain <path>` | component decomposition |
| `architecture/concepts/<subsystem>/engineering.md` | L2–L3 | `/understand-explain <module>` | internals, how it actually works |
| invariants, failure modes, concurrency | L3 | `/understand-chat "what breaks <x> / concurrency assumptions"` | the absences code can't show |
| `flows/<flow>/README.md` (steps) | L0–L1 | `/understand-domain` | flow skeleton in business terms |
| `flows/<flow>/business-analyst.md` (rules) | L1–L2 | `/understand-chat "what business rules gate <flow>"` | thresholds, exceptions |
| `flows/<flow>/engineering.md` (mechanism) | L2 | `/understand-explain <flow module>` | execution detail |
| `flows/<flow>/product-owner.md`, PO docs | L0 | `/understand-domain` + `/understand-diff` | feature set, release framing |
| `engineering/setup.md` | how-to | `/understand-onboard` | zero-to-running (verify every command) |
| `reference/configuration.md`, `limitations.md` | reference | targeted `/understand-chat` | env vars, unhandled cases |

Treat every answer as evidence, not prose to paste — write in the document's own voice, at
its own depth. See `source-analysis.md` for the full command reference.

## Discovering the flows

A topic folder under `docs/flows/` exists per business flow. Enumerate the flows before
writing them: `/understand-domain` returns the domains, flows and steps in the code's own
terms — that list *is* the set of flow folders to build. Never hand-type the flow list; the
point of the analysis is to find the flows a writer would otherwise miss.
