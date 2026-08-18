# {{Concept name}}

_Last reviewed: {{YYYY-MM-DD}}_

<!-- L0 — the answer. A reader who stops here must be able to say what this
concept is for. See ../../../references/progressive-disclosure.md. -->

{{One sentence naming the concept and the responsibility it owns: what would
break, or who would be confused, if this concept did not exist.}}

**Belongs to:** {{the high-level block this concept is the deep-dive of — link it}}

## What it models

<!-- L1 — the shape. -->

{{What this concept represents in the domain, in the repository's own
vocabulary. Say why the codebase needs the distinction — a concept that could
be replaced by a plain field is a field, not a concept.}}

## Lifecycle and states

{{The states this concept moves through and what moves it between them, named
in order. Name every state here; the rules that hold at each one are below.
When the concept has no lifecycle — it is created once and never transitions —
say so in a sentence and delete the diagram.}}

<!-- A stateDiagram-v2 only once the concept has three or more states and at
least one non-linear transition; otherwise the ordered prose above is the
smaller useful form. See ../../../references/illustration.md. -->

```mermaid
stateDiagram-v2
  accTitle:Lifecycle of {{concept name}}
  accDescr: {{One sentence: which states this concept moves through and what moves it between them.}}
  [*] --> {{State1}}
  {{State1}} --> {{State2}}: {{what causes the transition}}
  {{State2}} --> [*]
```

{{One or two sentences: which transition is irreversible, and which state a
reader will most often encounter.}}

## Invariants

<!-- L2 — per-item detail begins here. -->

{{What must always be true of this concept, stated as rules rather than as
descriptions of current behavior. A reader must be able to tell the difference
between "this is how it works today" and "this must never change without
breaking a caller's assumption." Prefer absence-based facts a reader cannot
recover by reading code ("an entry is never re-keyed once written").}}

- **{{Invariant}}** — {{what enforces it, and what would break if it stopped holding}}

## Relationships

{{What this concept depends on, what depends on it, and the boundary at which
its responsibility ends and a neighbouring concept's begins. Name the
neighbouring concept and link it. Never restate the neighbour's own
invariants.}}

<!-- A small flowchart only once three or more related concepts need their
boundaries shown together — this concept as one node among its immediate
dependencies and dependents, never its internal structure. Delete otherwise. -->

## Failure boundary

{{What this concept guarantees will not happen, and what it explicitly does not
protect against — the second half is the one a reader cannot get from the code.
Name the owner that handles what falls outside the boundary and link it.}}

## Where it lives

<!-- L3 — the boundary: where to go next, not what happens there. -->

{{The stable module or package paths that orient implementation work, and the
documents that own adjacent mechanism — persistence for its storage, the flow
that creates it, the decision record that introduced it. Link them; never
summarize them.}}
