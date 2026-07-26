# {{Topic name — a flow or a subsystem, in business or plain-technical words}}

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
Reference files or modules by path when locating something ("handled in the <module>
module") — never paste code, never link a line number, never anchor to a private symbol
a rename would break.}}

1. {{step — what happens, in behavioural terms}}
2. {{step}}
3. {{step}}

{{Optional: one Mermaid diagram of the flow. Prose above must stand without it.}}

## Go deeper

Each fact below lives once, in its own file. This section links; it does not restate.

- {{Business rules — exact logic, thresholds, exceptions}} → [business-analyst.md](business-analyst.md)
- {{Mechanism — how it runs, data model, failure modes}} → [engineering.md](engineering.md)
- {{Value, metrics, release framing}} → [product-owner.md](product-owner.md)
- {{Why it is built this way}} → [{{../../architecture/decisions/NNNN-slug.md}}]({{../../architecture/decisions/}})

_Create a deep-dive file only when real depth exists for that reader. An empty audience
file is a false promise — omit it and drop its bullet._
