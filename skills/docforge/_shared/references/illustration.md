# Illustration

This reference owns visual form selection and illustration constraints. An
illustration compresses evidence; it never replaces the evidence-backed prose.
Every visual must be introduced or followed by prose that explains its point,
important relationships, and any exception a reader must understand. This is
required for accessibility and for readers whose renderer does not support the
visual.

## Choose the smallest useful form

- Use prose when fewer than three elements or steps are involved.
- Use a Markdown table for enumerable facts with stable, repeated fields.
- Use an ASCII `text` fence for directory trees, layered stacks, record
  layouts, and timelines.
- Use an ASCII `text` fence for a short linear flow (at most four steps, no
  branch) when the reader's question is only what happens, in order, and a
  full diagram would add chrome without adding information; promote to
  Mermaid once a branch appears.
- Use a Mermaid `flowchart` for branching choices or relationship maps.
- Use a Mermaid `sequenceDiagram` when order across actors or systems matters.
- Use a Mermaid `journey` when the reader's question is how effort or
  satisfaction changes across an end-to-end process for one actor, not just
  the order of steps.
- Use a Mermaid `stateDiagram-v2` for lifecycle states and transitions.
- Use a Mermaid `erDiagram` for durable data relationships.

Only these forms. Mermaid documents `timeline`, `mindmap`, `sankey`, `treemap`,
and `C4` as experimental — "the syntax and properties can change in future
releases" — and `architecture-beta` / `block-beta` still require a `-beta`
keyword. A diagram that stops rendering on a dependency bump is worse than the
prose it replaced, so none of them is available here.

Do not turn a list into a diagram merely for decoration. If two forms could
work, choose the one that answers the reader's question with fewer elements.

## How many illustrations a document owes

**Count obligations, not pages.** A document owes one illustration per distinct
reader question it answers, drawn from the closed list its type declares; it
owes nothing for length. A long document does not earn a diagram by being long,
and a short one does not lose the two it needs.

This cuts both ways, and the second direction matters as much as the first:

- **Too few** is the common failure. A document that answers four questions
  with one picture has three unanswered. Splitting is always available and is
  the recommended remedy for density — complexity goes into *more* diagrams,
  never into a bigger one.
- **Too many** measurably harms. Adding an interesting-but-inessential visual
  is not neutral: the seductive-detail effect is small, negative, and
  reproduced across dozens of studies, and the coherence principle — people
  learn better when extraneous pictures are excluded — is among the
  best-supported findings in multimedia learning. A diagram added to break up
  text costs the reader comprehension.

So the test for every candidate diagram is a question, never a quota: *which
reader question does this answer, that no other view here answers?* If there is
no such question, the diagram is decoration and must not be emitted. If a
prose paragraph conveying the same relationships cannot be written, the diagram
was not conveying anything either — delete it rather than ship it.

Three practical consequences:

1. **Relevance over completeness.** Draw the important, surprising, risky,
   complex, or volatile parts. Leave out the normal, simple, and standardized.
2. **A representative selection, not a catalogue.** One to three runtime
   scenarios is the right number for a deep-dive document, not one per code
   path.
3. **Every diagram is a maintenance liability.** An inaccurate diagram is worse
   than no diagram, so prefer the stable parts of a system and retire a view
   that no longer answers a live question.

## Every illustration carries its own prose

A diagram is never the only carrier of a fact. Each one is introduced or
followed — **adjacent to it**, not in a separate section — by prose that states
its point, the relationships that matter, and any exception the reader must
understand.

This is not optional politeness. Screen readers announce a Mermaid diagram as
an unordered jumble of node labels with no relationships between them, so for
those readers the adjacent prose is the only content. Accessibility guidance is
explicit that non-text content needs an equivalent text alternative and that
new information must never appear only in a picture. Keeping the prose beside
the diagram rather than elsewhere also avoids splitting the reader's attention
between two places.

Give every Mermaid diagram an `accTitle:` and an `accDescr:` as well; they
become the rendered figure's accessible name and description.

## Complexity budgets

The depth vocabulary is defined in
[`depth-and-audience.md`](depth-and-audience.md): Orientation, Working depth,
Deep dive, Reference, and Router. Catalog machine values include `orientation`,
`deep-dive`, `reference`, and `router`; do not invent `target_depth: working`.
Apply the Working depth budget to content whose purpose is ordered behavior,
important rules, inputs/outputs, and common failures.

The budget bounds a single illustration. **There is no cap on how many
illustrations a document may carry.** Every illustration must earn its place
under "Choose the smallest useful form" above, and that relevance test is the
only thing that limits the count. A document needing six diagrams to answer
six distinct reader questions should carry six.

| Depth | Bound per illustration |
|---|---|
| Orientation (`orientation`) | At most 5 meaningful elements |
| Working depth | At most 8 meaningful elements |
| Deep dive (`deep-dive`) | At most 12 meaningful elements |
| Reference (`reference`) | At most 12 meaningful elements |
| Router (`router`) | At most 12 meaningful elements |

Reference documents normally use tables; reach for a relationship illustration
when lookup fields cannot express the relationship clearly. Router documents
normally use prose and links, because their reader wants a destination rather
than a picture. Both are form preferences, not quotas.

The views a document type owes are **declared** in the catalog and restated in
the type's writing-craft instruction. `dominant_form` names the primary form;
`illustration_views` lists every view the type owes, each with the reader
question it answers. A written document must carry a diagram of each declared
view's form — the mechanical gate reports `illustration-coverage` when one is
missing, on a fresh run and on revise alike, and it checks the *form*, so an
ASCII layout tree no longer satisfies a declared `sequenceDiagram`.

A view may carry its own `depth`, which bounds that view alone. A high-level
container diagram is budgeted at working depth even though its document is
orientation depth, because the container view of a real system does not fit in
five elements and dropping it is worse than sizing it correctly.

This file still owns which forms exist, when each fits, and the budgets; the
declaration only names the views, never overrides them.

Split any illustration that exceeds its bound into linked views with one stated
question each. **Splitting is always available** — the resulting views are
additional illustrations, and that is the intended outcome, not a violation.
Before splitting, check whether the content is actually enumerable,
independent, stable-field data — a roster of named items with repeated
attributes and no real sequence or branching between them — rather than a flow
or relationship; that shape belongs in a table instead.

A sequence diagram also has at most 5 participants; a state diagram at most 8
named states; an ER diagram at most 8 entities; a journey diagram at most 4
sections.

## Mermaid constraints

- Use identifiers without spaces, such as `PaymentService`.
- Quote labels containing punctuation, spaces, or placeholder braces.
- Do not use the reserved identifiers `end`, `graph`, or `subgraph`, including
  as differently cased stand-alone IDs.
- Do not use `style`, `classDef`, colors, themes, or `click` directives.
- Keep direction and zoom consistent. Prefer `LR` for peer relationships and
  `TD` for ordered branching.
- Keep labels short and explain detail in the surrounding prose.
- Every meaningful relationship is directional and carries a specific active
  verb; include a protocol or channel when evidence establishes one.
- Prefer a second complementary form answering a different reader question to
  enlarging a diagram. Never use deprecated `stateDiagram` syntax.

Use stable semantic IDs even when the visible label is reader-facing:

```mermaid
flowchart LR
  Caller["{{Calling system}}"] --> Service["{{Owned service}}"]
  Service --> Store["{{Durable store}}"]
```

The prose around this scaffold must say what crosses each boundary and why the
relationship matters.

## ASCII constraints

Use a fenced `text` block, align content with spaces, and keep every line at or
below 100 characters. Use only these structural glyphs:

- trees: `│`, `├`, `└`, `─`;
- boxes and layered stacks: `┌`, `┐`, `└`, `┘`, `─`, `│`, `├`, `┤`, `┬`, `┴`;
- timelines and arrows: `─`, `│`, `├`, `└`, `>`.

Do not mix Unicode and ASCII substitutes for the same connector. Check the
rendered alignment in a monospace font. Labels may use ordinary text, but
connectors must come from the fixed set above.

```text
{{repository}}/
├── {{source directory}}/    {{one-line responsibility}}
└── {{test directory}}/      {{one-line responsibility}}
```

Follow the fence with a sentence explaining what the grouping reveals; do not
assume indentation alone communicates ownership or runtime boundaries.

```text
{{trigger event}}
├─ {{condition A}} ──> {{step}} ──> {{outcome A}}
└─ {{condition B}} ──> {{step}} ──> {{outcome B}}
```

Follow the fence with a sentence stating that a single trigger fans out to
these outcomes and nothing branches further; a second-level branch, or a step
that needs to name which actor performs it, is the signal to promote to a
Mermaid flowchart or sequenceDiagram instead.
