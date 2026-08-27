# High-level architecture

_Last reviewed: {{YYYY-MM-DD}}_

<!-- L0 — the answer. A reader who stops here must be able to state the
capability this system owns and the drivers that shaped its structure. See
../../../references/progressive-disclosure.md and the deep-dive frame in
../../../references/deep-dive-frame.md. -->

**In one sentence:** {{the business capability this system owns, stated before any structure}}

{{One paragraph: what this system is, at the highest level of abstraction, the
business capability it owns, and the top architectural drivers that shaped its
structure (the constraint it lives under, the scale it was built for, the
integration it had to live with).}}

## System in context

<!-- L1 — the shape. Name the neighbours; explain none of them. -->


_C4 context view: this system as one box among the actors and services around it —
name the neighbors and the contracts between them, never the internals._

{{Where this system sits in the wider landscape — who calls it, what it calls, which
external services and systems it borders. The "part of a business" view: name the
neighbours and the contracts between them, not the internals.}}

```mermaid
%% C4 Context. Keep this view outside-in: neighbors only, no internals.
flowchart LR
  accTitle:   System context diagram for {{this system}}
  accDescr: {{One sentence naming each neighbor and what crosses the boundary.}}
  Upstream["{{actor / upstream}}"] -->|"{{active verb · protocol}}"| System["{{this system}}"]
  System -->|"{{active verb · protocol}}"| Datastore["{{datastore / downstream}}"]
  System -->|"{{active verb · protocol}}"| External["{{external service}}"]
```

{{One or two sentences: what crosses each boundary and why the relationship
matters. This prose is not optional — a reader whose renderer drops the diagram,
and every screen-reader user, gets only this.}}

## Containers and blackboxes

<!-- L1 — still the shape. -->

_C4 container view: the deployable pieces inside that one box — never mix this zoom
level with the context diagram above. Detail that does not belong at this altitude
goes to low-level.md, never into this view; see
../../../references/progressive-disclosure.md rule 3._

The major parts and what each is responsible for. One or two sentences each — behaviour,
not code. Deep mechanism lives in [low-level.md](low-level.md),
[concepts/](concepts/README.md), and
[subsystems/](subsystems/README.md). For `infrastructure-platform` repos, a "block" reads
as a provisioned resource or environment (a VPC, a managed database, a compute pool),
not application code.

_One row per block that matters for orientation, not every deployable unit. Technology
cites [reference/tech-stack.md](../reference/tech-stack.md); an unproven choice is
`unknown`, never inferred._

| Block | Responsibility | Technology | External interface | Boundary it owns | Decomposed in |
|---|---|---|---|---|---|
| {{block}} | {{active responsibility}} | {{stack or unknown}} | {{protocol/channel}} | {{trust / API / data boundary, if any}} | [low-level.md](low-level.md#{{whitebox-anchor}}), [subsystems/](subsystems/README.md) or `—` |

The table carries technology, interface, and boundary per block; the diagram
carries what a table cannot — which block talks to which, in which direction.
Both earn their place, and neither substitutes for the other.

```mermaid
%% C4 Container. Every block named in the table above appears here exactly once;
%% never mix in a context-level neighbor or a component-level internal.
flowchart LR
  accTitle:Container diagram for {{this system}}
  accDescr: {{One sentence: which deployable blocks exist and how they communicate.}}
  Entry["{{deployable block}} · {{technology}}"] -->|"{{active verb · protocol}}"| Worker["{{deployable block}} · {{technology}}"]
  Worker -->|"{{active verb · protocol}}"| Store["{{datastore}} · {{technology}}"]
```

{{One or two sentences: which communication paths matter and why, and which
block's absence would stop the system. If this view outgrows its budget, split
it by functional area — never drop it.}}

## Deployment

_Delete this section when execution does not span multiple nodes, processes,
devices, environments, or containers — state that omission explicitly instead._

_C4 deployment view: how the running software instances from Containers map onto
infrastructure nodes. One node per environment or deployment target; show what
runs there and what crosses between nodes._

```mermaid
flowchart LR
  accTitle:Deployment for {{this system}}
  accDescr: {{One sentence: which nodes exist and which running instances are deployed to each.}}
  NodeA["{{environment / node}}"] -->|"{{active verb · protocol}}"| NodeB["{{environment / node}}"]
  NodeB -->|"{{active verb · protocol}}"| NodeC["{{datastore node}}"]
```

{{One or two sentences: which deployment mapping matters and why, and which
node's loss would stop the system.}}

## Relationship matrix

<!-- L2 — per-edge detail. -->

_One row per material edge between blocks, or between a block and an external actor —
directional, one specific active verb, protocol-grounded or `unknown`, with a single
owner._

| Origin | Destination | Action | Protocol / channel | Owner |
|---|---|---|---|---|
| {{block}} | {{block or external actor}} | {{specific active verb}} | {{evidenced protocol or unknown}} | {{owning document or component}} |

## Boundaries and invariants

<!-- L2 — per-boundary detail. -->

{{State stable boundary and invariant facts. A relationship must have a
one-sentence rationale. An invariant is stated as an absence-based fact a reader
cannot recover by reading code ("never retries a non-idempotent write"), not a
description of current behavior. For detailed flow, link
[data-flow.md](data-flow.md) rather than repeating it.}}

## Failure domains

_Delete this section when the system runs as a single process on a single node
and no failure domain is evidenced — state that omission explicitly instead._

{{A compact failure-domain summary: the failed element, how wide the blast radius
is, how the system degrades, and who owns recovery. One row per material failure
domain; detailed failure taxonomies belong to low-level.md or the subsystem deep
dives, never here.}}

| Failed element | Blast radius | Degradation | Recovery owner |
|---|---|---|---|
| {{element}} | {{how wide the failure reaches}} | {{how the system degrades}} | {{who recovers and how}} |

## Quality and change drivers

<!-- L3 — the boundary. -->

{{The requirements, limits, benchmarks, tests, or extension points that drove the
shape — each evidenced. Delete this section when the repository evidences no such
driver; never estimate a figure.}}

## Stable by design

<!-- L3 — the boundary. -->

{{This document changes once or twice a year. If a claim here would be falsified by a
routine refactor, it is written too close to the code — move that detail to low-level.md.}}

## Where to go deeper

{{A routing map to the selected specialized architecture documents and subsystem
deep dives. One row per destination: the document, and the reader question it
answers that this document deliberately leaves out.}}

| Document | Answers |
|---|---|
| [low-level.md](low-level.md) | {{the component zoom-in question}} |
| [subsystems/](subsystems/README.md) | {{the subsystem deep-dive questions}} |
| {{specialized document}} | {{the question it owns}} |

## Why it is like this

{{One short paragraph: which forces shaped this shape — the constraint, the
scale it was built for, the integration it had to live with. Name the force and
link the record that settled it; never restate a decision record's argument
here. Delete this paragraph when the repository evidences no such force, and
keep the routing lines below.}}

Rationale lives in [decisions/](decisions/README.md). Known shortcuts live in
[tech-debt.md](tech-debt.md). Hard limits live in [constraints.md](constraints.md).
