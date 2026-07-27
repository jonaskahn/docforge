# Instruction Templates

Each file here is a **writing-craft layer** for one document type: how to lay the content out,
which `/understand-*` command feeds it, and how to tag provenance. It is **not** the content
contract. The complete per-type contract — what each document must present, what to keep out,
and the one Diátaxis mode it stays in — lives in `references/document-catalog.md`; depth lives in
`references/depth-and-audience.md`. Instruction files defer to those and must never restate or
contradict them.

The catalog covers every document type in the taxonomy. This directory covers only the subset
that has extra craft guidance worth writing down; the absence of an instruction file for a type
is not a gap — the catalog is authoritative for all of them.

## By Category

### Architecture
- `architecture-high-level.md` — System overview, blocks, boundaries
- `architecture-low-level.md` — Detailed mechanism, subsystem internals

### Business Flows
- `flows.md` — Step-by-step business process flows

### Product
- `product-overview.md` — Business capabilities and domains, curated narrative
- `product-capabilities.md` — The exhaustive feature catalog, business language

### Operations & Onboarding
- `setup-guide.md` — Environment setup, installation, verification

### Reference
- `limitations-register.md` — Known constraints and bounds
- `dependencies-inventory.md` — External libraries and services
- `tech-debt-register.md` — Architectural debt and workarounds

### Security & Governance
- `security-policy.md` — Vulnerability reporting and contacts
- `decision-records.md` — Architecture Decision Record index and format

## Template Structure

Each template contains:
- **Purpose** — what the document achieves (one line)
- **Contract** — pointer to the matching entry in `references/document-catalog.md` for
  must-present elements, keep-out boundaries, and Diátaxis mode
- **Depth** — pointer to `references/depth-and-audience.md` (the L0–L3 ladder owns the level)
- **Data Requirements** — which graph / `/understand-*` command feeds this document
- **Template Structure** — how to lay the content out (order, diagrams, phrasing)
- **Provenance Requirements** — what to tag with source hashes
- **Notes** — additional writing guidance

The craft sections (Template Structure, Provenance, Data, Notes) are what these files add.
Must-present / keep-out / mode / depth are **never** duplicated here — they are cited.

## Using Templates

Scripts referenced below ship as both `.py` and `.js` (`scripts/docs_scaffold.py` /
`scripts/docs_scaffold.js`, same flags, same output) — use whichever runtime (Python 3 or
Node.js) is available.

During Step 0 of docforge generation (see `SKILL.md` for the full gated cadence):
1. Build/refresh the knowledge and domain graphs
2. **Gate 1 — structure:** preview the empty tree (`docs_scaffold.py --dry-run`), present the
   layout, record it in `.docforge/manifest.json` (`manifest_sync.py init`, all `status: planned`),
   confirm, then scaffold
3. **Gate 2 — detail:** per document, present what it will cover (contract + depth + sources),
   confirm or adjust
4. **Write one at a time**, in dependency order, updating manifest status as each lands. For each
   document read **both** its `references/document-catalog.md` entry (the contract) and its
   instruction file here (the craft) before writing
5. **Audit each document independently before it is `complete`** — a fresh subagent that did not
   write it checks it against its contract, target depth, and the quality bar
   (`references/document-audit.md`). A derivable gap FAILs and forces a rewrite; only an external
   gap (a typed `<UPPER_SNAKE>` token or an explicit waiver) may pass

Templates are instructions *for the AI writing the document*, not scaffolds to fill in. They guide:
- What data sources to consult
- How to lay the content out (order, diagrams, phrasing)
- How to tag source material for provenance tracking

They do **not** define must-present sections, keep-out boundaries, Diátaxis mode, or depth —
those come from `references/document-catalog.md` and `references/depth-and-audience.md`.

## Updating Templates

When a template needs refinement:
- Edit the `.md` file directly
- Keep structure: Purpose → Contract pointer → Depth pointer → Data → Template Structure → Provenance → Notes
- Never add must-present/keep-out/mode/depth prose — fix it in `references/document-catalog.md` or `references/depth-and-audience.md` instead
- Update version in `.metadata/document-templates.json` if schema changes
