# The `docs/` tree — canonical taxonomy

Contents:
1. Naming rules
2. The full tree
3. Per-folder specification
4. Per-file specification (spine files)
5. Placement decision table
6. Migrating an existing docs folder

---

## 1. Naming rules

These exist so that two people documenting two repos six months apart produce the same structure.

- **Lowercase kebab-case** for every file and folder: `data-contracts.md`, not `dataContracts.md` or `Data Contracts.md`. Spaces in paths break tooling and URL-encode badly.
- **Plural for collections, singular for subjects.** `decisions/`, `runbooks/`, `tasks/`, `contracts/` hold many peer documents. `security/`, `product/`, `architecture/` are subject areas.
- **Every folder gets a `README.md`.** Forges render it when the folder is browsed, so the folder describes itself. A folder without one is a dead end for anyone navigating the tree in a browser.
- **No numeric prefixes except ADRs.** `01-setup.md`, `02-testing.md` forces renumbering on every insert. Order belongs in the folder's `README.md` index, where it is cheap to change. ADRs are the exception: they are append-only and immutable once accepted, so `0007-adopt-event-sourcing.md` is safe and makes sorting meaningful.
- **Name by reader intent, not by internal jargon.** `engineering/setup.md` over `engineering/bootstrap-procedure.md`. The reader searching for it does not know your vocabulary yet.
- **No `misc/`, `other/`, `general/`, or `notes/`.** These become the folder where documents go to be forgotten. If a document has no home, either the taxonomy needs a real new folder or the document needs deleting.
- **Assets sit beside what uses them**, in `_assets/` within the owning folder — `docs/architecture/_assets/data-flow.svg`. The underscore prefix sorts it away from content and marks it as non-prose. Do not create one global `docs/images/`; it decouples images from the documents that reference them and guarantees orphans.

---

## 2. The full tree

Tier 1 items are marked ▲, Tier 2 adds ●, Tier 3 adds ◆. Overlays add further files (see `overlay-*.md`).

```
docs/
├── README.md                       ▲ index + audience router
│
├── product/                        ▲ business readers, external consumers
│   ├── README.md
│   ├── overview.md                 ▲ what it does, who for, why it exists
│   ├── capabilities.md             ● feature catalog in business language
│   ├── roadmap.md                  ● direction + explicit not-yet-supported list
│   ├── business-analyst/           (audience overlay) audience-specific BA documents
│   └── product-owner/              (audience overlay) audience-specific PO documents
│
├── flows/                          ● aligned topic folders, one per business flow
│   ├── README.md                   ● index of every flow
│   └── <flow>/                     ● document-as-folder (see document-composition.md)
│       ├── README.md               ● common: L0 what+why, L1 flow plain, all notices
│       ├── business-analyst.md     ● BA depth: rules, thresholds, exceptions (if any)
│       ├── engineering.md          ● engineering depth: mechanism, failure modes (if any)
│       └── product-owner.md        ● PO depth: value, metrics (if any)
│
├── architecture/                   ▲ engineers, technical reviewers
│   ├── README.md                   ▲ index — routes to high-level / low-level / concepts
│   ├── high-level.md               ▲ system context, building blocks, boundaries (C4 L1–L2)
│   ├── low-level.md                ● component decomposition, data model (C4 L3)
│   ├── data-flow.md                ● how information moves, end to end
│   ├── dependencies.md             ● third-party inventory + integration contracts
│   ├── tech-debt.md                ● known shortcuts, cost, remediation
│   ├── constraints.md              ● hard architectural limits, ceilings, non-goals
│   ├── concepts/                   ● deep-dive subsystems, one folder each
│   │   ├── README.md
│   │   └── <subsystem>/            ● document-as-folder: README + engineering.md
│   ├── decisions/                  ● ADRs
│   │   ├── README.md               ● index with status column
│   │   └── 0001-<slug>.md
│   └── _assets/                    diagrams
│
├── engineering/                    ▲ contributors
│   ├── README.md
│   ├── setup.md                    ▲ zero to running locally
│   ├── testing.md                  ▲ how to run tests, what coverage means here
│   ├── conventions.md              ● code style, naming, commit format
│   └── release.md                  ● how a change reaches production
│
├── operations/                     ● on-call, SRE, whoever gets paged
│   ├── README.md
│   ├── deployment.md               ● environments, topology, rollback
│   ├── observability.md            ● logs, metrics, traces, dashboards, alerts
│   └── runbooks/                   ● one file per recurring incident or procedure
│       ├── README.md
│       └── <symptom-or-procedure>.md
│
├── reference/                      ▲ lookup material, not narrative
│   ├── README.md
│   ├── configuration.md            ▲ every env var and config key
│   ├── limitations.md              ▲ known limitations, known issues, not-supported
│   ├── glossary.md                 ● domain terms, especially overloaded ones
│   └── errors.md                   (API overlay) error catalog
│
├── security/                       ● security reviewers, diligence
│   ├── README.md                   ● posture summary + disclosure process
│   ├── threat-model.md             ● assets, actors, trust boundaries, mitigations
│   └── data-handling.md            ● what data, classification, retention, residency
│
└── contributing/                   ● contributors, maintainers
    ├── README.md                   ● workflow: branch, review, merge, release
    ├── ownership.md                ● who owns which paths and decisions
    └── templates/                  ● host-neutral issue/change templates
        ├── bug-report.md
        ├── feature-request.md
        └── change-proposal.md
```

---

## 3. Per-folder specification

**`product/`** — Written for someone who will never read the code. No jargon without a gloss, no implementation detail, no code blocks except example inputs and outputs a customer would recognize. If a sentence requires knowing the stack to parse, it belongs in `architecture/`.

**`flows/`** — Aligned topic folders, one per business flow (`/understand-domain` enumerates them). Each is a document-as-folder: a plain `README.md` every audience reads, plus per-reader deep-dive subfiles created only where real depth exists. The shared body and every critical notice live in the README; depth lives in the subfiles. See `document-composition.md`.

**`architecture/`** — The system as built, at two altitudes. `high-level.md` is the stable map — system context, building blocks, boundaries — that changes once or twice a year. `low-level.md` and `concepts/<subsystem>/` carry component decomposition and deep mechanism on their own, faster lifecycle. `tech-debt.md` and `constraints.md` record shortcuts and hard limits respectively (distinct from `reference/limitations.md`, which is feature gaps). Rationale goes in `decisions/`; anything that churns per release belongs in `reference/` or is generated.

**`engineering/`** — Everything a contributor does before their first merge. The test of `setup.md` is literal: follow it on a clean machine and the repo runs. If a step depends on credentials or access, say exactly who grants it.

**`operations/`** — Written for someone under pressure at an inconvenient hour. Runbooks are imperative, numbered, and start from the symptom the pager reported, not from the system's internal name for the fault.

**`reference/`** — Lookup, not narrative. Tables, lists, exhaustive enumerations. A reader arrives knowing what they want and leaves in thirty seconds. Prefer generating anything here that has a machine-readable source of truth.

**`security/`** — Two audiences: an external reporter who needs a disclosure channel, and a reviewer assessing posture. Never place credentials, internal hostnames, or unremediated vulnerability details here; reference the private tracker instead.

**`contributing/`** — Process. The one place where a forge-specific pointer is permitted, confined as described in `host-neutrality.md`.

---

## 4. Per-file specification (spine files)

### `docs/README.md` — the index

The single entry point. Its job is routing, not content. Include: one-line repo description, a table mapping audience to starting document, then the folder map with one line each. If a reader has to guess which folder to open, this file has failed.

### `docs/product/overview.md`

Answers three questions in this order: what problem this solves, who has that problem, and where this component sits relative to the rest of the system. Two to five paragraphs. If the repo is one of several, link to the portfolio-level system context.

### `docs/architecture/high-level.md` and `low-level.md` — the two-altitude map

The code map, split by altitude so the stable part does not churn with the volatile part.
Templates: `architecture-high-level.md`, `architecture-low-level.md`.

- **`high-level.md`** — system context, the major building blocks and their responsibilities,
  the boundaries between them, and how data and control move end to end. The "part of a
  business" view: what this system is and what it borders. A reader should be able to draw the
  box diagram from it. Restrict it to what changes once or twice a year.
- **`low-level.md`** — component decomposition beneath the building blocks, the data model
  described (not dumped from schema), and an index into `concepts/<subsystem>/` for the
  subsystems that earn a full deep-dive.

Three techniques make the difference:

- **Reference by file/module path and describe behaviour; do not paste code or link symbols.**
  `src/ingest/` locates a thing durably; a private function name or line-number link rots on
  the next refactor. Describe what the logic does, not the branch that implements it. (See
  the durability rules in `document-composition.md`.)
- **State invariants explicitly.** These are the facts a reader cannot recover by reading
  code, because they are usually the *absence* of something: "nothing under `core/` performs
  I/O", "the model layer never imports from the view layer", "handlers never touch the
  database directly". Absences are invisible in a codebase and expensive to rediscover after
  someone violates one.
- **Keep depth out of `high-level.md`.** Mechanism, algorithm and failure modes belong in
  `low-level.md` or a `concepts/<subsystem>/engineering.md` deep-dive, on their own lifecycle.

### `docs/flows/<flow>/README.md` — an aligned topic document

The common document for one business flow: L0 (what and why), L1 (how it flows, in plain
language), every critical notice, and a one-line gist plus link for each deep-dive subfile.
It must stand alone — a reader who never opens a subfile still understands the flow. Template:
`topic-readme.md`. Full mechanics in `document-composition.md`.

### `docs/engineering/setup.md`

Prerequisites with exact versions, then numbered steps, then a verification command whose expected output is shown. Close with a troubleshooting section covering the failures that actually happened to real people. Include the wall-clock time a first run takes so nobody kills a build they think has hung.

### `docs/reference/limitations.md`

See `risk-docs.md` for the full treatment. The shape:

```markdown
## Known limitations
| Area | Limitation | Impact | Workaround | Tracking |
|---|---|---|---|---|

## Known issues
Defects under investigation, with tracker references.

## Not supported
Things a reasonable person might expect and will not find. This section
prevents more wasted hours than any other in the tree.
```

### `docs/reference/configuration.md`

Every environment variable and configuration key the code actually reads — verify by grepping for the accessor, not by copying an old `.env` file. Columns: name, purpose, required, default, example, and where it is consumed. Never include real secret values; show shape (`sk_live_<32 hex chars>`) instead.

---

## 5. Placement decision table

When unsure where a document belongs:

| The document answers… | Folder |
|---|---|
| What is this and why does it exist? | `product/` |
| How is it built, and where is the thing that does X? | `architecture/` |
| Why did we choose this over the alternative? | `architecture/decisions/` |
| How do I change it safely? | `engineering/` |
| It is broken in production — what now? | `operations/runbooks/` |
| What is the exact value/name/code for X? | `reference/` |
| What could an attacker do, and what data do we hold? | `security/` |
| How does a change get proposed and reviewed? | `contributing/` |

If a document plausibly fits two folders, place it where its **primary audience** looks first and cross-link from the other. Do not copy it into both.

---

## 6. Migrating an existing docs folder

Existing content is evidence about what people actually needed to write down. Treat it accordingly:

1. **Inventory before moving.** List every existing document with its last-modified date and a one-line summary of what it covers.
2. **Classify**: current and accurate / stale but salvageable / obsolete.
3. **Map** each surviving document to a taxonomy slot using the table above. Split documents that serve two audiences rather than filing them under one.
4. **Leave forwarding pointers** at old paths for a release cycle if anything external links to them — a one-line file containing the new location.
5. **Archive rather than delete** genuinely obsolete material: move it under `docs/_archive/<year>/` with a `README.md` explaining that nothing inside is maintained. Deleting design history that someone will want in an audit is a decision you cannot reverse.
