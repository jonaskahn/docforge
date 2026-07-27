# The `docs/` tree — canonical taxonomy

Contents:
1. Naming rules
2. The full tree
3. Per-folder specification
4. Per-file specification → the document catalog
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
├── flows/                          ● one file per business flow, flat by default
│   ├── README.md                   ● index of every flow
│   ├── <flow>.md                   ● flat: L0 what+why, L1 flow plain, all notices, diagram
│   └── <flow>/                     ● promoted only once a subfile below has real content
│       ├── README.md               ● common: same content the flat file held
│       ├── business-analyst.md     ● BA depth: rules, thresholds, exceptions (only if written)
│       ├── engineering.md          ● engineering depth: mechanism, failure modes (only if written)
│       └── product-owner.md        ● PO depth: value, metrics (only if written)
│
├── agents/                         (audience overlay — the AI coding agent itself)
│   ├── README.md                   standard folder index (for humans browsing the forge)
│   ├── architecture.md             brief stub — links to architecture/ for the actual map
│   ├── patterns.md                 the one file with real content: hotspots, exemplars
│   ├── glossary.md                 brief stub — links to reference/glossary.md, never redefines
│   ├── testing.md                  brief stub — links to engineering/testing.md for strategy
│   ├── tech-debt.md                brief stub — links to architecture/tech-debt.md
│   ├── flow.md                     brief stub — entry points only, links to flows/ for steps
│   └── conventions.md              (only if CONVENTIONS.md exists) distilled AI directives
│
├── architecture/                   ▲ engineers, technical reviewers
│   ├── README.md                   ▲ index — routes to high-level / low-level / concepts
│   ├── high-level.md               ▲ system context, building blocks, boundaries (C4 L1–L2)
│   ├── low-level.md                ● component decomposition, data model (C4 L3)
│   ├── data-flow.md                ● how information moves, end to end
│   ├── dependencies.md             ● third-party inventory + integration contracts
│   ├── tech-debt.md                ● known shortcuts, cost, remediation
│   ├── constraints.md              ● hard architectural limits, ceilings, non-goals
│   ├── concepts/                   ● deep-dive subsystems, flat by default (same rule as flows/)
│   │   ├── README.md
│   │   ├── <subsystem>.md          ● flat: the whole concept, until a deep-dive is earned
│   │   └── <subsystem>/            ● promoted only once engineering.md has real content
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

**`flows/`** — One file per business flow (`/understand-domain` enumerates them — never hand-typed, and gated on `scripts/check_preconditions.py` reporting the domain graph READY). Each flow starts as a flat `<flow>.md`: plain content every audience reads, a diagram once the flow has more than one step, every critical notice. It is promoted to a `<flow>/` folder with `README.md` + per-reader deep-dive subfiles only in the same pass that writes real subfile content — never a folder created ahead of the content that justifies it. See `document-composition.md`.

**`agents/`** *(agent-context overlay — `overlay-agent-context.md`)* — Written for an AI coding agent's context window, not a person. Every file here is a brief stub linking to the human document that owns the fact, except `patterns.md`, which genuinely has no other home. Gets the standard folder-index `README.md` like any other `docs/` folder (naming rule 3, above), but that index is for humans browsing the forge — the entry kernel an agent actually reads from on demand is root `AGENTS.md` §7, which links straight to the files it needs, not to this folder's index. `AGENTS.md`, `CLAUDE.md`, `CLAUDE.local.md`, and `.claude/settings.json` themselves live at the **repo root**, in the same thin-pointer/tooling-config bucket as root `README.md` and `.docforge/` — not under `docs/`. See "Root vs docs/" in `SKILL.md` and `overlay-agent-context.md` for the full file list.

**`architecture/`** — The system as built, at two altitudes. `high-level.md` is the stable map — system context, building blocks, boundaries — that changes once or twice a year. `low-level.md` and `concepts/<subsystem>/` carry component decomposition and deep mechanism on their own, faster lifecycle. `tech-debt.md` and `constraints.md` record shortcuts and hard limits respectively (distinct from `reference/limitations.md`, which is feature gaps). Rationale goes in `decisions/`; anything that churns per release belongs in `reference/` or is generated.

**`engineering/`** — Everything a contributor does before their first merge. The test of `setup.md` is literal: follow it on a clean machine and the repo runs. If a step depends on credentials or access, say exactly who grants it.

**`operations/`** — Written for someone under pressure at an inconvenient hour. Runbooks are imperative, numbered, and start from the symptom the pager reported, not from the system's internal name for the fault.

**`reference/`** — Lookup, not narrative. Tables, lists, exhaustive enumerations. A reader arrives knowing what they want and leaves in thirty seconds. Prefer generating anything here that has a machine-readable source of truth.

**`security/`** — Two audiences: an external reporter who needs a disclosure channel, and a reviewer assessing posture. Never place credentials, internal hostnames, or unremediated vulnerability details here; reference the private tracker instead.

**`contributing/`** — Process. The one place where a forge-specific pointer is permitted, confined as described in `host-neutrality.md`.

---

## 4. Per-file specification — see the document catalog

What each document must present (and must *not*), the one Diátaxis mode it stays in, and its
source-of-truth live in **`document-catalog.md`** — the single content contract for every doc
type. This file owns *where a document sits and what it is named*; the catalog owns *what goes
inside it*. The deep templates for the risk documents are in `risk-docs.md` and for ADRs in
`decision-records.md`; the catalog cross-links both. Consult the catalog entry for a document
before writing it, and again in Step 6 to confirm it is complete.

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
| What must an AI coding agent know before it edits this code, within a token budget? | `docs/agents/` (entry kernel: root `AGENTS.md`) |

If a document plausibly fits two folders, place it where its **primary audience** looks first and cross-link from the other. Do not copy it into both.

---

## 6. Migrating an existing docs folder

Existing content is evidence about what people actually needed to write down. Treat it accordingly:

1. **Inventory before moving.** List every existing document with its last-modified date and a one-line summary of what it covers.
2. **Classify**: current and accurate / stale but salvageable / obsolete / merge-candidate (duplicate coverage across two or more documents).
3. **Map** each surviving document to a taxonomy slot using the table above. Split documents that serve two audiences rather than filing them under one.
4. **Ask before acting.** Present the classification and get an explicit per-document decision from the user — keep / migrate / merge / archive / delete — before moving or archiving anything. The classification in step 2 is a proposal, not authorization; treat an unconfirmed "obsolete" the same as "current" until the user says otherwise.
5. **Leave forwarding pointers** at old paths for a release cycle if anything external links to them — a one-line file containing the new location.
6. **Archive rather than delete** whatever the user confirmed as obsolete: move it under `docs/_archive/<year>/` with a `README.md` explaining that nothing inside is maintained. Only delete outright if the user explicitly said so — deleting design history someone will want in an audit is a decision you cannot reverse.
7. **Merge** whatever the user confirmed as duplicate coverage into the single surviving document, then archive (not delete) the superseded originals.
