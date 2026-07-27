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

**Deep-dive is the default; filler is the only thing cut.** Go as far down as helps a newcomer
actually understand and approach the subsystem — the *why*, the mechanism, the edge cases, the
data model, the failure modes, and the related pieces a reader must hold in their head to make
sense of it. Default to L2/L3 for any subsystem a new engineer has to understand to be
productive, not only the handful that are "architecturally significant." Add the adjacent
context that makes a document self-standing (what feeds it, what it feeds, what breaks it) —
that is the "more aspects, related things" a deep reader needs, not padding.

The single brake is **value, never a quota.** Cut anything that lengthens without helping a
reader: restating the obvious, narrating the file tree, ceremony, a deep-dive on a trivial or
fast-churning module no one needs to understand. "Detailed" means *more useful signal*, not
more words. Two guards keep depth from becoming churn: write at the flow/behaviour level so a
same-behaviour refactor can't falsify a deep section (non-negotiable 6), and state each fact
once and link to it — depth is never duplication across audience folders.

**Deep by default is not "deep-dive everything."** A subsystem earns an L2/L3 deep-dive by a
reader *needing* it to be productive, not by existing. Depth goes *down* into what matters, not
*wide* across every module — going deep on the three load-bearing subsystems while leaving the
trivial ones at L1 is correct, and produces a set a human can actually follow. The number of
documents is bounded the same way: by the tier and by genuine reader need, not by how many
files the taxonomy *could* hold. When one coherent document covers a subject well, that is the
right answer — do not split it into many thin files a reader then has to reassemble. Detail
lives in the *depth of the right documents*, not in the *count* of them.

## Which understand-anything command feeds which cell

The knowledge graph gives breadth (the map). Depth comes from the deeper commands —
`/understand-explain` is the engine for L2/L3 and is required there, not optional.

| Document / layer | Depth | Command | What it yields |
|---|---|---|---|
| `architecture/high-level.md` (context, blocks) | L1 | `/understand` (the graph) | module map, layers, boundaries |
| `architecture/low-level.md` (components) | L1–L2 | graph + `/understand-explain <path>` | component decomposition |
| `architecture/concepts/<subsystem>/engineering.md` | L2–L3 | `/understand-explain <module>` | internals, how it actually works |
| invariants, failure modes, concurrency | L3 | `/understand-chat "what breaks <x> / concurrency assumptions"` | the absences code can't show |
| `flows/<flow>.md` (steps) | L0–L1 | `/understand-domain` | flow skeleton in business terms |
| `flows/<flow>/business-analyst.md` (rules, once promoted) | L1–L2 | `/understand-chat "what business rules gate <flow>"` | thresholds, exceptions |
| `flows/<flow>/engineering.md` (mechanism, once promoted) | L2 | `/understand-explain <flow module>` | execution detail |
| `flows/<flow>/product-owner.md` (once promoted), PO docs | L0 | `/understand-domain` + `/understand-diff` | feature set, release framing |
| `engineering/setup.md` | how-to | `/understand-onboard` | zero-to-running (verify every command) |
| `reference/configuration.md`, `limitations.md` | reference | targeted `/understand-chat` | env vars, unhandled cases |

Treat every answer as evidence, not prose to paste — write in the document's own voice, at
its own depth. See `source-analysis.md` for the full command reference.

## Discovering the flows

A file under `docs/flows/` exists per business flow — flat by default, `<flow>.md`. Enumerate
the flows before writing them: `python scripts/check_preconditions.py --repo <path> --need
domain` must report READY, then `/understand-domain` returns the domains, flows and steps in
the code's own terms — that list *is* the set of flow documents to build. Never hand-type the
flow list; the point of the analysis is to find the flows a writer would otherwise miss. A
flow only becomes a folder (`<flow>/README.md` + subfile) in the same pass its deep-dive
content is written — see `document-composition.md`.
