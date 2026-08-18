# Low-level architecture

_Last reviewed: {{YYYY-MM-DD}}_

Component-level decomposition. Zooms into named blocks in
[high-level.md](high-level.md). It never becomes a Level-4 code or class document.

## Layout

```text docforge-role=structure
{{repository}}/
├── {{source directory}}/    {{one-line responsibility}}
├── {{service directory}}/   {{one-line responsibility}}
└── {{test directory}}/      {{one-line responsibility}}
```

{{One sentence: what the grouping reveals about ownership or runtime boundaries.}}

## Selected whiteboxes

_Repeat per high-level block worth a component-level decomposition — not every block
named in high-level.md needs one._

### {{High-level parent block}}

**Motivation for decomposition:** {{what decision, review, diagnosis, or risk judgment this decomposition enables.}}

**Allowed dependency direction:** {{direction and rationale.}}

```mermaid
%% Component map for this whitebox only. Every node is a component written up
%% below; arrows show the dependency direction the block permits.
accTitle: Component map for {{high-level parent block}}
accDescr: {{One sentence: which components this block contains and how they depend on each other.}}
flowchart LR
  Inbound["{{component}}"] -->|"{{active verb}}"| Core["{{component}}"]
  Core -->|"{{active verb}}"| Outbound["{{component}}"]
```

{{One or two sentences: what the grouping reveals about responsibility, and
which dependency the direction above deliberately forbids. Omit this diagram
only when the whitebox holds fewer than three components.}}

## Components

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

## Runtime scenario

_Repeat per architecturally relevant scenario — **one to three**, chosen for
relevance, never one per code path. Document the important, surprising, risky,
or volatile paths and leave the routine ones out._

### {{Architecturally relevant intra-block path}}

{{Why this scenario matters and its successful outcome. Every message maps to a named component above.}}

```mermaid
accTitle: Runtime scenario — {{architecturally relevant intra-block path}}
accDescr: {{One sentence: which components collaborate, in what order, and how the path can fail.}}
sequenceDiagram
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

## Data model

{{The main entities and how they relate, described. Not a schema dump — a routine column
rename must not falsify this. Link the generated schema if one exists.}}

```mermaid
%% Delete this whole block when no persistent model exists; the declared view is
%% evidence-conditional and is never demanded of a stateless component.
accTitle: Data model for {{this decomposition}}
accDescr: {{One sentence: which durable entities the components own and how they relate.}}
erDiagram
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

_Rows below are the common cross-cutting concerns; add or drop rows to match what
this repo actually has — a row with no evidenced path is deleted, not filled with
`unknown`._

| Concern | Where it lives | Notes |
|---|---|---|
| Configuration | `{{path}}` | See [../reference/configuration.md](../reference/configuration.md) |
| Error handling | `{{path}}` | |
| Logging | `{{path}}` | |
| Authentication | `{{path}}` | |
| Persistence | `{{path}}` | |
