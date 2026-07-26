# Document composition — one topic, many readers, no duplication

Purpose: how a single topic serves several audiences without splitting into parallel
folders that re-state the same subject, and how to write documents that survive routine
code change. Read this alongside `audience-matrix.md` (which class a document is) and
`depth-and-audience.md` (which depth level each reader consumes).

The organizing principle is **document-first**: organize by topic — a flow, a subsystem, a
capability — not by audience. Because most of a topic is shared, the shared body is the
main document and audience-specific depth is pushed out into subfiles. The document is what
presents; the audience is a filter on how deep a given reader goes.

## The document-as-folder pattern

Each topic that more than one audience cares about is a **folder**. The common document is
`README.md`; audience deep-dives are sibling files. This fits the existing rule that every
folder carries a `README.md` index.

```
<topic>/                       flows/<flow>/  or  architecture/concepts/<subsystem>/
├── README.md          the common document — plain, easy, COMPLETE. Everyone reads it.
│                        · L0: what it is and why
│                        · L1: how it flows, in plain language
│                        · every notice / warning / critical constraint
│                        · a one-line gist + link for each deep-dive below
├── business-analyst.md   BA depth — exact rules, thresholds, exceptions, traceability
├── engineering.md        engineering depth — mechanism, data model, failure modes, trade-offs
└── product-owner.md      PO depth — value, metrics, release framing
```

- **README carries L0 + L1; subfiles carry L2 + L3.** See `depth-and-audience.md` for the
  ladder.
- **A subfile exists only when real depth exists for that reader.** An empty audience file
  is the scaffold-dump anti-pattern in miniature — omit it, and drop its link.
- **Templates:** `assets/templates/topic-readme.md` and `assets/templates/audience-deepdive.md`.

## Two invariants

These are what make the split safe. Violating either loses information or hides a hazard.

1. **No information lost — the README stands alone.** A reader who never opens a subfile
   still gets the whole picture, only shallower. Every fact that lives in a subfile is
   summarized and linked from the README. Detail is pushed deeper, never dropped.

2. **Notices are never stranded.** Every warning, caveat, critical constraint, irreversible
   behaviour, or safety note appears in the README. A subfile may expand a notice, but must
   never be the *only* place it lives — a reader who reads only the README must still see
   every hazard. **Depth goes to subfiles; importance stays common.**

Plus: the README is plain-language. Gloss domain terms or link the glossary. Dense jargon
and internals belong in the subfiles, not the README.

## Durability rules — documents that survive code churn

Governing principle: **write at the layer that changes slowest.** A flow or a business rule
outlives the code that implements it. A same-behaviour refactor — a rename, an extraction, a
file move — must not falsify any document. If it does, the document was written too close to
the code.

**R1 — No code, durable references.**
- Never paste code or code-like snippets into prose documents. (The only exceptions are
  `reference/errors.md` and `reference/configuration.md`, which may show a value's *shape* —
  `sk_live_<32 hex>` — never logic.)
- Never link a line number, and never hang a claim on an internal or private symbol whose
  rename would break the doc.
- **Do** name files and modules by path to locate a thing ("handled in the `<module>`
  module"). **Do** describe what a function or rule *does*, in behavioural prose.
- Anchor a load-bearing claim to a **stable public interface** or a **file/module path** —
  never to a private function name. Prefer describing behaviour over naming the implementer.

**R2 — No duplication, no redundancy.**
- Every fact is stated **once**, in the document that owns it; everywhere else links.
- A README may carry a one-line, behaviour-level **gist plus a link**; the authoritative
  detail lives once, in the deep-dive or the glossary. The gist must be stable enough not to
  drift — it is not a copy of the detail.
- Domain terms are defined once in `reference/glossary.md`. No document restates a definition.
- The same subject is never written into two audience subfiles — split by depth or angle,
  never copied.

**R3 — Durability drives provenance.**
- Because prose is behaviour-level, a refactor that changes a source file's hash but not its
  behaviour should resolve to a **re-stamp** — confirm the behaviour is unchanged, update the
  hash — not a rewrite. Write so that re-stamp is the common outcome of a `PARTIAL` flag.
- Deep-dive (L2/L3) sections legitimately track mechanism and will churn more. Accept it, and
  keep them out of the README so the README stays durable.

## Classification decision tree

For any document or section, in order:

1. **Does more than one audience need this exact fact?**
   - No → it belongs in that one reader's **audience-specific** document (its own folder).
   - Yes → continue.
2. **Is it a lookup fact (a term, a value, a code) rather than a narrative?**
   - Yes → it belongs in the **shared-fact spine** (`glossary.md`, `configuration.md`,
     `dependencies.md`), stated once, linked from everywhere.
   - No → it belongs in an **aligned topic folder**: the common part in `README.md`, the
     per-reader depth in a subfile.
3. **Is it a warning or critical constraint?** → it goes in the README regardless of the
   above (invariant 2), with any expansion in the relevant subfile.

See `audience-matrix.md` for the three classes and their examples.
