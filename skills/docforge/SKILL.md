---
name: docforge
description: Catalog-driven repository documentation with typed repository profiles, code-graph grounding, conditional flow evidence, manifest 3.0 provenance, independent audits, and equivalent Python/Node tools.
---

# Docforge 2.0

Docforge builds a durable documentation system from repository evidence. The
canonical machine contract is `.metadata/catalog.json`; prose explains that
contract but never replaces it.

## Bare `/docforge` invocation

When the user invokes `/docforge` with no task, flags, tier, or typed profile
document request, begin an **interactive intake**. Do not initialize a
manifest, scaffold a file, build/refresh a graph, install a provider, change
configuration, or archive/delete anything.

First perform only safe discovery: identify the repository root, check whether
`.docforge/manifest.json` exists, run the read-only code-graph precheck, and run
`detect_profiles` to identify candidate shapes, platforms, frameworks, and
concerns. Report matched evidence and recommendations. Detection proposes
profiles; it never confirms them on the user's behalf. When exactly one
readable code-graph provider is ready, use it
as the proposed default and do not ask the user to choose among absent
providers. This read-only provider selection is not permission to build,
refresh, install, or configure anything.

### Scope intake

Present all applicable unresolved questions together in one intake. Explain in
plain language why each question matters, then give every choice a short
consequence so the user can select one answer per question (or multiple answers
where explicitly allowed). Use native single-select and multi-select controls
when the host provides them; otherwise use a concise numbered question set with
lettered options. Do not prescribe an exact screen or require a particular
combined answer syntax.

Ask only what remains unresolved, in this order:

1. **Goal or action.** For a repository without a manifest, offer creating a
   new documentation plan or planning without writing. When a manifest exists,
   also offer resuming it, checking status or staleness, revising a named area,
   or replacing the plan. Briefly distinguish inspection, planning, writing,
   and read-only reporting.
2. **Documentation tier.** For a new or plan-only scope, offer Spine
   (essential repository documentation), Diligence (Spine plus flows, risks,
   security, operations, dependencies, and ADRs), Portfolio (Diligence plus
   `docs-portfolio/` diligence views), or a grounded recommendation that
   Docforge will explain after inspection.
3. **Repository profiles.** Show detected recommendations with evidence, then
   let the user confirm or edit each applicable dimension:
   - shapes describe what the repository delivers;
   - platforms describe where it runs;
   - frameworks describe how it is built and tailor evidence queries without
     adding framework-specific trees;
   - concerns describe evidenced cross-cutting behavior;
   - audiences describe whom the documentation serves.
   Permit multiple values in every dimension. Offer Engineers + beginners as
   the default audience starting point (and the manifest CLI default when no
   audience flag is supplied); BA + PO, coding agents, operators, and security
   reviewers add their catalog-owned views.
4. **Graph source, only when unresolved.** With several ready providers, offer
   only those providers. With no ready provider, explain setup paths and their
   approval requirements. With exactly one ready provider, record it as the
   proposed source and skip this question; include it in the final confirmation
   so the user can still ask to compare or change it.
5. **Execution mode.** Offer Review (pause after every new or changed tree),
   Auto-accept (always display trees and updates, then continue without routine
   conversational pauses), or Plan only (stop after the completed tree and
   document cards). Explain that Auto-accept never approves installation,
   configuration, indexing, refreshes, or destructive work.

Collect the applicable answers as one response. If the user supplied one or
more choices in the original request, retain them and include only unresolved
questions in the intake. For Resume, Status, or Revise, omit tier, audience,
and shape questions that the existing manifest already resolves. If the reply
leaves a material choice missing or ambiguous, ask one concise follow-up
containing only those unresolved choices.

After resolving the answers, display one confirmation summary containing the
action, tier, every selected profile dimension, selected graph provider and its
code/flow capabilities, and execution mode. Ask whether to continue, edit a
choice, or cancel. Always wait for explicit confirmation of this intake
summary, including when Auto-accept was selected. Only after confirmation may
Docforge initialize or replace a manifest or begin deeper planning. Later
plan-tree pauses follow the selected execution mode.

Show only currently valid choices. Do not offer Resume, Status, or Revise when
no manifest exists, and do not present a provider that needs setup as ready. If
no code graph is ready, explain that global installation/MCP wiring is user-run
and that an agent-run repository index build or refresh needs separate explicit
approval; selecting a setup path is not that approval. If a manifest exists,
include its tier, typed profiles, and incomplete count in the first explanation.
Report existing documentation and candidate repository shapes with a brief
evidence note, such as an API schema, web framework manifest, library package
manifest, pipeline configuration, or infrastructure files.

### Provider sufficiency rule

Docforge needs one readable `code_graph`, not one index from every supported
provider. Missing competitors are normal and must not appear in the standard
intake, plan summary, or readiness table.

- One ready provider: state it once and proceed with it as the proposed
  default.
- Several ready providers: list only those ready providers and ask which should
  be primary.
- No ready provider: explain the available setup paths and ask the user to
  choose one.
- Selected flow-dependent documents: first use the chosen provider's native
  flow capability; derive provisionally only when it has none.

For example, `.gitnexus/lbug` with indexed Process nodes satisfies both
`code_graph` and native `flow_graph`. Do not mention absent Understand Anything
or CodeGraph indexes in that case unless the user asks to compare or switch.
The all-provider output of `diagnose_graphs` is troubleshooting detail and is
never the default `/docforge` intake.

Explicit requests such as “create diligence API documentation” skip answered
questions; present any materially missing scope questions together. The final
intake confirmation and all side-effect approvals remain mandatory under
`--auto-accept`.

## Entry conditions

Run the code-graph precheck before every documentation invocation:

```sh
python scripts/precheck_graph.py --repo <repo> --need code
```

A code graph is universal. A flow graph is required only when a selected
manifest document lists `flow_graph` in `requires`. Before writing the first
such document, run:

```sh
python scripts/precheck_graph.py --repo <repo> --need flow
```

Use only the terms **code graph** and **flow graph**. Provider dispatch, read
mechanisms, setup, and refresh behavior belong to
[`references/graph-sources.md`](references/graph-sources.md).

## Non-negotiables

1. Do not invent. Derive every available fact from a graph, source, manifest,
   history, existing documentation, or user-provided evidence. Reserve typed
   `<UPPER_SNAKE_CASE>` tokens for atomic external values only.
2. Build and show the plan before writing. `--auto-accept` skips conversational
   pauses, not planning, evidence checks, linting, audit, or safety approvals.
3. Write one document at a time in catalog `write_order`.
4. Stamp provenance while writing. Multiline provenance-v1 JSON frontmatter
   starts at byte one for Markdown documents that support it. Replace every
   scaffold token with concrete write metadata and source blobs. Exceptions
   record the same full provenance shape in the manifest.
5. A writer does not mark its own artifact complete. Mechanical lint is
   necessary but never sufficient.
6. State a fact once in its owning document and link to it elsewhere. Describe
   durable behavior and boundaries, not private symbols or line numbers.
7. Generated prose is provider-neutral and host-neutral. Provider commands live
   only in graph-source references; host-specific links stay in explicit
   integration zones.

## Invocation modes

- `--plan-only`: precheck, analyze, initialize the complete static manifest,
  add discovered dynamic documents, and display the dry-run tree. Do not create
  placeholder documents.
- `--auto-accept`: display each plan and result but continue without
  conversational confirmation pauses. It never authorizes installation, global
  configuration, graph construction or refresh, archive/delete actions, or any
  other separately approved side effect.
- `--resume`: load the version-3 manifest and continue the first non-complete,
  non-skipped document in write order.
- `--status`: print manifest state only.
- `--revise all` / `--revise <area>`: check provenance, re-ground stale
  sections in scope, and preserve fresh sections.

An explicit single-document request still requires graph precheck, re-grounding,
mechanical lint, independent audit, and manifest state updates.

## Workflow

### 1. Precheck and inspect

Confirm a readable code graph. Detection and reading are read-only and may be
agent-run. Building or refreshing a repository index requires explicit user
approval. Global installation, MCP wiring, and restart-requiring setup remain
user-run.

Do not stop at the readiness flag. Select one ready provider according to the
provider sufficiency rule and use its native retrieval path before planning.
Provider-specific dispatch belongs in `references/graph-sources.md`; do not
present missing competitors during ordinary repository analysis.

Collect a graph-grounded inventory of boundaries, entry points, public
surfaces, functional areas, candidate flows, tests, configuration, hotspots,
and operational paths. Exact preparation and query dispatch live in
[`references/graph-sources.md`](references/graph-sources.md).

Inspect repository manifests, code, existing documentation, CI/deployment
configuration, git history, and child repositories. Existing documents are
evidence: propose keep, migrate, merge, archive, or delete decisions and obtain
explicit approval before moving or removing them.

### 2. Select scope

Choose exactly one catalog tier:

- `spine`: the universal root routers, documentation index, product overview,
  architecture map, setup/testing, configuration, and limitations.
- `diligence`: Spine plus flows, detailed architecture, risks, security,
  operations, contributing, dependencies, and decision records.
- `portfolio`: Diligence plus the complete cross-repository
  `docs-portfolio/` layer.

Select shape, platform, framework, concern, and audience identifiers only from
`.metadata/catalog.json`. Aliases are accepted only at CLI input and normalize
to canonical IDs. Shapes own durable document packs; platforms add platform
constraints; frameworks tailor detection, terminology, evidence queries, and
commands; concerns add conditional content; audiences add reader views. A
document shared by selected profiles appears once, with every applicable
selection origin retained. Selected child paths automatically pull in their
cataloged ancestor indexes.

Conditional entries are selected only when their evidence exists. Actual
flows, decisions, runbooks, datasets, concepts, migrations, backlog
traceability, and portfolio decisions are dynamic and must be added after
discovery. Never seed an example artifact to stand in for discovery.

### 3. Initialize and preview

```sh
python scripts/manage_manifest.py init \
  --repo <repo> --tier spine \
  --shape desktop-app --shape library-sdk \
  --platform macos \
  --framework swiftui --framework appkit \
  --concern accessibility \
  --audience coding-agents

python scripts/manage_manifest.py add \
  --repo <repo> --type flow \
  --id flow-checkout --path docs/flows/checkout.md

python scripts/scaffold_docs.py \
  --repo <repo> --manifest <repo>/.docforge/manifest.json --dry-run
```

The dry run is the exact active manifest tree and prints, for every selected
document, its group/type, target depth, required evidence, selection origin,
and write order.

### Pre-write structure checkpoint

For **every new plan**, finish repository inspection and dynamic-document
discovery, update the manifest, and show the final dry-run tree before the
first document is materialized. Include selected paths, omitted conditionals,
dynamic additions, document count, and the number waiting for a flow graph.
This happens in review mode and with `--auto-accept`; auto-accept skips the
pause after the tree, never the tree itself.

If inspection or later writing discovers a real flow, decision, runbook,
dataset, migration, ticket traceability record, or other item that changes the
manifest, update it first and show a structure update before writing resumes:

- added paths and why they were discovered;
- removed/skipped paths and why;
- changed requirements, selection origins, or write order;
- the refreshed exact tree and updated document count.

In review mode, wait for confirmation of this updated tree. In auto-accept
mode, display the same update and continue only when no separate side effect or
destructive action needs approval. Never write against an undisplayed manifest
revision.

Present a human-readable plan before writing. It must contain:

1. **Evidence readiness** — selected graph provider and persisted artifact,
   current/stale state, native or provisional flow status, and manifest/history
   evidence available.
2. **Scope decision** — chosen tier, each profile, depth, and one evidence-based
   sentence explaining why it applies.
3. **Exact tree** — every static and discovered dynamic path from the manifest;
   label conditional items that were omitted and why.
4. **Document cards** — one line per path stating the reader question/content
   contract, depth, evidence capabilities, and write order. For audience
   profiles, group cards under Business Analyst, Product Owner, and Coding
   Agent headings.
5. **Capability schedule** — which documents can proceed from the code graph
   now, which wait for `flow_graph`, and whether flow evidence will be native or
   Docforge-derived.
6. **Existing-doc actions** — keep/migrate/merge/archive/delete proposals,
   with destructive or moving actions still awaiting separate approval.

This presentation is the plan gate; a bare list of filenames is insufficient.
Confirm it unless `--auto-accept` is present. Under `--auto-accept`, display the
same plan and continue. `--plan-only` stops after the full presentation and
does not create placeholder documents.

Immediately before materializing each document, show the current structure
summary (or “tree unchanged since the displayed checkpoint”) and a compact
execution card: path, reader, owned topics, evidence query, links to owning
documents, and acceptance checks. This is derived from the manifest and
[`references/document-catalog.md`](references/document-catalog.md), not a
second plan file.

### 4. Write one document

For the next document in `write_order`:

1. Check every capability in its `requires` list.
2. Read its content contract in
   [`references/document-catalog.md`](references/document-catalog.md), then its
   optional `instruction_file` for writing craft.
3. Materialize that document and selected ancestor indexes:

   ```sh
   python scripts/scaffold_docs.py \
     --repo <repo> --manifest <repo>/.docforge/manifest.json \
     --document <id>
   ```

4. Set it `in_progress`, re-ground every required claim, replace all scaffold
   markers and provenance tokens, and stamp the complete provenance-v1 shape
   with heading-matched sections and concrete source blobs.
5. Set it `generated`.
6. Run the document linter and any audit-profile-specific mechanical checks.
7. Independently audit it using
   [`references/document-audit.md`](references/document-audit.md).
8. Record the result:

   ```sh
   python scripts/manage_manifest.py audit \
     --repo <repo> --id <id> --mode subagent \
     --verdict PASS --report .docforge/audits/<id>.md
   ```

9. A passing artifact may transition to `complete`. A failed artifact becomes
   `needs_review`, then returns to `in_progress` for revision.

Status transitions are:

```text
planned → in_progress → generated → complete
                       ↘ needs_review → in_progress
```

`skipped` is explicit. `complete` is rejected unless the manifest contains a
passing `subagent` or `cold-pass` audit record.

### 5. Independent audit

Use a fresh artifact-only subagent when supported. Give it the artifact, its
catalog contract, target depth, relevant quality checks, and cited sources—no
writer reasoning. When subagents are unavailable, perform a separate cold,
artifact-only pass and record `mode: cold-pass`. Mechanical checks alone never
produce a completion verdict.

### 6. Whole-tree gate

After all selected documents pass individually:

```sh
python scripts/scaffold_docs.py \
  --repo <repo> --manifest <repo>/.docforge/manifest.json --audit
```

The command exits nonzero for any defect. Then apply the cross-document checks
owned by [`references/quality-bar.md`](references/quality-bar.md): reachability,
onboarding, location, reviewer, stranger, duplication, and host neutrality. A
whole-tree discovery that changes one artifact sends that artifact through its
independent audit again.

## Manifest and provenance

`.docforge/manifest.json` is the sole plan, state, provenance, and audit record.
Its schema version is `3.0`; there is no secondary runtime state file.
Manifest v2 is intentionally unsupported in Docforge 2.0 and must be replaced
after the user confirms a new profile-backed plan.

Check staleness with:

```sh
python scripts/check_staleness.py \
  --manifest <repo>/.docforge/manifest.json

python scripts/check_staleness.py \
  --manifest <repo>/.docforge/manifest.json \
  --section configuration --sync-provenance
```

`FRESH` means recorded sources still match; `PARTIAL` identifies `STALE`,
`MISSING`, or `NO_BLOB` sources for one section; `UNPARSEABLE` identifies
malformed document frontmatter; and `UNTRACKED` means provenance is absent,
empty, or legacy.
Synchronization reads every manifest path, including root documents, and
changes only each document's provenance section.

## Public tools

Every script has standard-library Python and built-in-only Node peers with the
same flags, messages, JSON shapes, filesystem effects, and exit codes. Unknown
flags exit `2`.

- `manage_manifest.{py,js}`: `init`, `add`, `set`, `status`, and `audit`.
- `detect_profiles.{py,js}`: read-only shape/platform/framework/concern
  recommendations with evidence and `confirmed|candidate` confidence.
- `scaffold_docs.{py,js}`: exact dry-run, one-document materialization, and
  manifest-backed audit.
- `precheck_graph.{py,js}`: `--need code|flow`.
- `check_staleness.{py,js}`: `--section`, JSON output, and provenance sync.
- `validate_metadata.{py,js}`: registry/schema/path/version/peer validation.
- Graph adapters, readers, derivation, document lint, and child-repository
  discovery retain paired contracts.

Use Node by replacing `python scripts/name.py` with
`node scripts/name.js`.

## Canonical ownership

- [`references/docs-tree.md`](references/docs-tree.md): paths, naming, tiers,
  and placement.
- [`references/document-catalog.md`](references/document-catalog.md):
  must-present content, keep-out boundaries, mode, and depth.
- [`references/graph-sources.md`](references/graph-sources.md): capability
  dispatch and provider selection.
- [`references/document-composition.md`](references/document-composition.md):
  topic ownership, promotion, durability, and no-duplication.
- [`references/provenance-tracking.md`](references/provenance-tracking.md):
  metadata format and staleness semantics.
- [`references/document-audit.md`](references/document-audit.md): independent
  completion gate.
- [`references/quality-bar.md`](references/quality-bar.md): mechanical and
  whole-tree acceptance.
- `instructions/*.md`: document-specific writing craft only.
- `assets/templates/*`: output scaffolds only.

When a rule changes, update its owner and replace other repetitions with links.
