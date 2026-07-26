# Document composition — one topic, many readers, no duplication

Purpose: how a single topic serves several audiences without splitting into parallel
folders that re-state the same subject, and how to write documents that survive routine
code change. Read this alongside `audience-matrix.md` (which class a document is) and
`depth-and-audience.md` (which depth level each reader consumes).

The organizing principle is **document-first**: organize by topic — a flow, a subsystem, a
capability — not by audience. Because most of a topic is shared, the shared body is the
main document and audience-specific depth is pushed out into subfiles. The document is what
presents; the audience is a filter on how deep a given reader goes.

## Flat by default, folder only when earned

Each topic that more than one audience cares about — a flow, a subsystem concept — starts as
a **single flat file**: `flows/<flow>.md` or `architecture/concepts/<subsystem>.md`. This file
carries everything most topics ever need: L0 (what and why), L1 (how it flows, in plain
language), every notice, a diagram, error modes. Most topics never earn more than this, and a
folder built for a topic that never gets a deep-dive is pure overhead — it is also exactly how
a stale "Go deeper → engineering.md" link ends up pointing at a file nobody wrote.

**Promotion to a folder happens atomically, in the same pass that writes the subfile — or not
at all.** A topic moves from `<topic>.md` to `<topic>/README.md` + subfile(s) only at the
moment you are actually producing L2/L3 content for a specific audience. The folder and the
subfile are created together, in the same edit sequence. Never create the folder, add a "Go
deeper" link, and leave the target for a later pass — if you are not writing the subfile's
content right now, do not create the folder and do not reference a file that isn't there.

```
Flat (default — no deep-dive earned yet):
flows/login.md                 the whole topic in one file: L0, L1, notices, diagram, errors

Promoted (only once a subfile carries real content):
flows/signup/                  flows/<flow>/  or  architecture/concepts/<subsystem>/
├── README.md          the common document — plain, easy, COMPLETE. Everyone reads it.
│                        · L0: what it is and why
│                        · L1: how it flows, in plain language
│                        · every notice / warning / critical constraint
│                        · a one-line gist + link for each deep-dive below
├── business-analyst.md   BA depth — exact rules, thresholds, exceptions, traceability
├── engineering.md        engineering depth — mechanism, data model, failure modes, trade-offs
└── product-owner.md      PO depth — value, metrics, release framing
```

- **README/flat file carries L0 + L1; subfiles carry L2 + L3.** See `depth-and-audience.md`
  for the ladder.
- **No promise without content.** A flat file never links to a subfile path that does not
  exist in this same pass. A subfile exists only when real depth exists for that reader — an
  empty or dangling audience file is the scaffold-dump anti-pattern in miniature.
- **Migrating up is mechanical, not incremental.** When a later pass finds real depth an
  earlier flat file lacked: move `<topic>.md` → `<topic>/README.md` verbatim, write the new
  subfile with real content, and update the one incoming reference (the flows/concepts index).
  All of that lands in one pass — there is no valid intermediate state where the folder exists
  without its subfile.
- **A folder holding only a README is a defect, not a stage.** If you find one — your own
  work or inherited — either the promotion happened without content (demote back to a flat
  file) or the content is simply missing (write it now, in this pass). `docs_scaffold.py
  --audit` flags this as `folder-only-readme`.
- **Diagrams are not optional for a flow with more than one step or any branch/error path.**
  Include a Mermaid sequence or flowchart diagram showing the step order and decision points.
  The prose above it must still stand alone without the diagram — the diagram supplements,
  per durability rule R1; it never carries information the prose omits.
- **Templates:** `assets/templates/topic-readme.md` (used for both the flat file and, once
  promoted, the folder's `README.md`) and `assets/templates/audience-deepdive.md`.

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
   - No → it belongs in an **aligned topic**: the flat file if no deep-dive is being written
     now, or the common `README.md` plus a per-reader subfile once one is.
3. **Is it a warning or critical constraint?** → it goes in the README regardless of the
   above (invariant 2), with any expansion in the relevant subfile.

See `audience-matrix.md` for the three classes and their examples.
