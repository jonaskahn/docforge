---
docforge_provenance:
  schema: "2.1"
  doc_id: "<DOC_ID>"
  path: "<DOCUMENT_PATH>"
  generated_at: "<GENERATED_AT>"
  generator:
    name: "docforge"
    version: "2.17.0"
  tier: "<TIER>"
  target_depth: "<TARGET_DEPTH>"
  graph:
    provider: "<GRAPH_PROVIDER>"
    flow: "<FLOW_CAPABILITY>"
  sections: []
---
# {{Topic name — a flow or a subsystem, in business or plain-technical words}}

<!-- This template is used both as a flat file (docs/flows/<flow>.md) and, once a
     deep-dive subfile is written, as docs/flows/<flow>/README.md. Do not create the
     folder or the "Go deeper" links below until the linked subfile is written in
     this same pass — see document-composition.md. -->

_Last reviewed: {{YYYY-MM-DD}}_

{{One or two sentences: what this is and why it exists. Plain language. No code.}}

> {{⚠ **Notice:** any warning, hard constraint, or irreversible behaviour a reader must
> know before going further. Every critical notice lives HERE, never only in a deep-dive.
> Delete this block if there is genuinely nothing to flag.}}

## What it does, and why (L0)

{{Two to four sentences a non-specialist understands. The problem it solves, who relies
on it, what changes when it runs. Describe behaviour, not implementation.}}

## How it flows (L1, plain)

{{The steps or moving parts, in the order they happen, in words a domain reader recognises.
Reference files or modules by path when locating something ("handled in the module") —
never paste code, never link a line number, never anchor to a private symbol
a rename would break.}}

1. {{step — what happens, in behavioural terms}}
2. {{step}}
3. {{step}}

{{Include a Mermaid sequence or flowchart diagram whenever this has more than one step or
any branch/error path — not optional at that point. Prose above must still stand alone
without it. Omit only for a genuinely single-step topic. Follow illustration.md.}}

```mermaid
sequenceDiagram
  participant Actor as {{actor}}
  participant System as {{this system}}
  Actor->>System: {{request}}
  System-->>Actor: {{result}}
```

## Go deeper

<!-- Delete this whole section if no deep-dive is being written right now — a flat file
     with no "Go deeper" section is correct and complete. Only add a bullet at the exact
     moment you write its target file in this same pass. -->

Each fact below lives once, in its own file. This section links; it does not restate.

- {{Business rules — exact logic, thresholds, exceptions}} → [business-analyst.md](business-analyst.md)
- {{Mechanism — how it runs, data model, failure modes}} → [engineering.md](engineering.md)
- {{Value, metrics, release framing}} → [product-owner.md](product-owner.md)
- {{Why it is built this way}} → [{{../../architecture/decisions/NNNN-slug.md}}]({{../../architecture/decisions/}})

_A bullet here with no corresponding file is a defect, not a placeholder — `scaffold_docs.py
--audit` will catch it as a broken link. Write the subfile and add the bullet together, or
add neither._
