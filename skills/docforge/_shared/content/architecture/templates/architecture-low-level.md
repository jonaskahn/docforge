# Low-level architecture

_Last reviewed: {{YYYY-MM-DD}}_

<!-- L0 — the answer. See ../../../references/progressive-disclosure.md. -->

Component-level decomposition. Zooms into named blocks in
[high-level.md](high-level.md). It never becomes a Level-4 code or class document.

**This decomposition exists to support:** {{the decisions, reviews, or diagnoses a reader comes here to make}}

## Layout

<!-- L1 — the shape. -->


```text docforge-role=structure
{{repository}}/
├── {{source directory}}/    {{one-line responsibility}}
├── {{service directory}}/   {{one-line responsibility}}
└── {{test directory}}/      {{one-line responsibility}}
```

{{One sentence: what the grouping reveals about ownership or runtime boundaries.}}

## Selected whiteboxes

<!-- L1 — still the shape: name every block worth decomposing before explaining
any component below. -->

_Repeat per high-level block worth a component-level decomposition — not every block
named in high-level.md needs one._

### {{High-level parent block}}

**Motivation for decomposition:** {{what decision, review, diagnosis, or risk judgment this decomposition enables.}}

**Allowed dependency direction:** {{direction and rationale.}}

```mermaid
%% Component map for this whitebox only. Every node is a component written up
%% below; arrows show the dependency direction the block permits.
flowchart LR
  accTitle:Component map for {{high-level parent block}}
  accDescr: {{One sentence: which components this block contains and how they depend on each other.}}
  Inbound["{{component}}"] -->|"{{active verb}}"| Core["{{component}}"]
  Core -->|"{{active verb}}"| Outbound["{{component}}"]
```

{{One or two sentences: what the grouping reveals about responsibility, and
which dependency the direction above deliberately forbids. Omit this diagram
only when the whitebox holds fewer than three components.}}

## Components

<!-- L2 — per-item detail begins here. -->

_Repeat per component inside this whitebox — the ones material to the decomposition's
motivation above, not an exhaustive file listing._

### {{Component name}}

**Responsibility:** {{what it does and the boundary it owns.}}

**Technology:** {{library/framework}}

**Public contract:** `{{signature or protocol}}`

- **Talks to:** -> {{component}} — {{specific active verb and protocol when evidenced}}
- **Owns:** {{the data or responsibility that is exclusively its}}
- **Invariant:** {{what is deliberately absent or always enforced — the fact a reader
  cannot recover by reading code, because it is the absence of something}}
- **Failure boundary:** {{what this component contains when it fails — the error or
  exception a caller must handle, and what happens to in-flight state on the way out}}
- **Key paths:** `{{stable file/module path(s) that orient implementation work}}`

## Module wiring

<!-- L2 — per-edge detail, across whitebox boundaries: which components talk
across whitebox boundaries, and which high-level edge each crossing realizes.
Never a parallel decomposition of high-level.md's Relationship matrix — this
is the downward half of the same edge. -->

_Every edge in [high-level.md](high-level.md)'s Relationship matrix that
crosses into more than one whitebox decomposed here gets a row below. A
high-level edge realized entirely inside one whitebox — never crossing to a
sibling whitebox at this level — has no row; it is internal to that
whitebox's own Components diagram above._

```mermaid
%% Cross-boundary map only: every node here is a component already written up
%% above, in a different whitebox than at least one of its neighbors. Never
%% redraw a single whitebox's own Components diagram.
flowchart LR
  accTitle:Cross-boundary component wiring
  accDescr: {{One sentence: which components in different whiteboxes talk to each other, in what direction, and over what protocol.}}
  Origin["{{component}} ({{origin whitebox}})"] -->|"{{specific active verb · evidenced protocol}}"| Target["{{component}} ({{destination whitebox}})"]
```

{{One or two sentences: which cross-boundary path matters most and why a
change on one side of it risks the other.}}

| High-level edge (from the Relationship matrix) | Realized by | Direction | Protocol / channel |
|---|---|---|---|
| {{block}} → {{block}} | {{component}} → {{component}} | {{direction}} | {{evidenced protocol}} |

This table is the upward link that does not leak downward: high-level states
*that* two blocks relate; this row states *which components* realize that
relationship and how. Only one whitebox is selected for decomposition, or
every high-level edge stays inside a single whitebox → state that
explicitly ("no edge crosses a whitebox boundary in this decomposition")
and omit the diagram and table rather than drawing an empty flowchart —
the declared view is satisfied by the stated fact, not by decoration.

## Runtime scenario

_Repeat per architecturally relevant scenario — **one to three**, never one per
code path. Document the important, surprising, risky, or volatile paths and
leave the routine ones out._

_Choose from these four areas rather than from whatever the graph surfaced
first: (a) an important use case or feature — how do the blocks execute it;
(b) an interaction at a critical external interface; (c) operation and
administration — launch, start-up, shutdown; (d) an error or exception
scenario. Keep each one schematic: every message maps to a named component
above, and detail that belongs to a component's own write-up stays there._

### {{Architecturally relevant intra-block path}}

{{Why this scenario matters and its successful outcome. Every message maps to a named component above.}}

```mermaid
sequenceDiagram
  accTitle:Runtime scenario — {{architecturally relevant intra-block path}}
  accDescr: {{One sentence: which components collaborate, in what order, and how the path can fail.}}
  participant A as {{component}}
  participant B as {{component}}
  A->>B: {{specific action}}
  alt {{success condition}}
    B-->>A: {{outcome}}
  else {{material error}}
    B-->>A: {{safe failure behavior}}
  end
```

{{One or two sentences restating the order and the failure branch in prose, so
the scenario survives without the diagram.}}

## Quality and change scenarios

{{The load, latency, or volume ceiling this decomposition was built to hold, and
the modification it was shaped to absorb cheaply — each stated as a scenario:
a stimulus, the component that responds, and the evidenced measure or the effort
the change costs. Evidence only: a configured limit, a benchmark, a load test,
an extension point the code actually exposes. Delete this whole section when the
repository evidences neither a quality ceiling nor a change the design
anticipates; never estimate a throughput figure.}}

## Data model

{{The main entities and how they relate, described. Not a schema dump — a routine column
rename must not falsify this. Link the generated schema if one exists.}}

```mermaid
%% Delete this whole block when no persistent model exists; the declared view is
%% evidence-conditional and is never demanded of a stateless component.
erDiagram
  accTitle:Data model for {{this decomposition}}
  accDescr: {{One sentence: which durable entities the components own and how they relate.}}
  ENTITY1 ||--o{ ENTITY2 : "{{relationship}}"
```

{{One or two sentences: which relationship constrains the components above, and
which entity owns the write path.}}

## Significant subsystems

The ones worth a full deep-dive get their own folder under
[concepts/](concepts/README.md):

| Subsystem | Deep-dive |
|---|---|
| {{name}} | [concepts/{{slug}}/](concepts/{{slug}}/README.md) |

## Cross-cutting concerns

<!-- L3 — the boundary: where each concern is owned, not how it works. -->

_Rows below are the common cross-cutting concerns. Delete a row when the concern
does not apply to this system. When it plainly should apply but the evidence
shows no path, write "no evidenced path found" rather than deleting the row —
a silently missing row reads as "handled", and hedging exactly where the
evidence stops is the honest signal. Never fill a cell with `unknown`._

| Concern | Where it lives | Notes |
|---|---|---|
| Configuration | `{{path}}` | See [../reference/configuration.md](../reference/configuration.md) |
| Error handling | `{{path}}` | |
| Logging | `{{path}}` | |
| Authentication | `{{path}}` | |
| Persistence | `{{path}}` | |
