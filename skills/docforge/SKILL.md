---
name: docforge
description: Catalog-driven repository documentation with code-graph grounding, conditional flow evidence, manifest v2 planning and provenance, independent audits, and equivalent Python/Node tools.
---

# Docforge 1.0

Docforge builds a durable documentation system from repository evidence. The
canonical machine contract is `.metadata/catalog.json`; prose explains that
contract but never replaces it.

## Bare `/docforge` invocation

When the user invokes `/docforge` with no task, flags, tier, overlay, or
document request, begin an **interactive intake**. Do not initialize a
manifest, scaffold a file, build/refresh a graph, install a provider, change
configuration, or archive/delete anything.

First perform only safe discovery: identify the repository root, check whether
`.docforge/manifest.json` exists, run the read-only code-graph precheck, and
inspect manifests/directories for likely repository shapes. Report the detected
state and recommendations, but never select an audience, overlay, or graph
source on the user's behalf. Then ask the user to select from the following
menu, adapting the graph-source choices and repository-shape recommendation to
the evidence actually detected:

```text
Docforge needs a scope before it can create a plan. Reply with the option
letters/numbers you want, for example: 1A, 2B, 3C, 4A, 5A, 6B.

1. What do you want to do?
   A. Create a new documentation plan — inspect first, then show the proposed tree.
   B. Plan only — create/update the manifest and show the tree; write no documents.
   C. Resume an existing manifest — continue its next eligible document.
   D. Check status or staleness — read-only progress/drift report.
   E. Revise an existing area — re-ground stale documentation in a named area.

2. How much documentation do you need? (for A or B)
   A. Spine — essential README, product, architecture, setup, testing, configuration, limits.
   B. Diligence — Spine plus flows, risks, security, operations, dependencies, and ADRs.
   C. Portfolio — Diligence plus cross-repository diligence under docs-portfolio/.
   D. Recommend for me — Docforge will inspect and explain its recommendation.

3. Who should the documentation serve? (choose one starting point)
   A. Engineers + beginners — the default: README, setup, testing, architecture,
      configuration, and limits for people new to the repository.
   B. Engineers + Business Analysts + Product Owners — adds process/rules/
      requirements plus feature value, metrics, and release views.
   C. Engineers + coding agents — adds AGENTS.md, safe shims/settings, and
      concise editing context under docs/agents/.
   D. Everyone — engineers/beginners, BA, PO, and coding-agent views.
   E. Custom — name any combination of BA, PO, coding agents, and extra readers.

4. Which repository shapes should Docforge include?
   A. Use the detected recommendation — Docforge will explain the evidence.
   B. API/service — endpoint and integration documentation.
   C. Web application — rendering, state, components, and browser support.
   D. Library — public surface, compatibility, publishing, and migrations.
   E. Data pipeline or infrastructure — contracts/lineage or environments/state.
   F. None or custom — use only the base/audience documentation.

5. Which graph source should be primary?
   A. Use the ready source Docforge reports.
   B. Understand Anything — structural JSON and native domain/flow views.
   C. GitNexus — LadybugDB structure, processes, context, and impact queries.
   D. CodeGraph — SQLite-backed source, call paths, routes, and blast radius.
   E. Help me choose — Docforge will compare the ready/missing choices.

6. How should Docforge proceed after showing the complete tree?
   A. Review mode (default) — wait for approval after every new/changed tree.
   B. Auto-accept — always show the tree and updates, then continue without
      conversational pauses. It never approves setup, indexing, or destructive work.
   C. Plan only — stop after the complete tree and document cards.
```

If no code graph is ready, say so before presenting the menu and mark graph
choices as setup paths, not actions already taken. Explain that global
installation/MCP wiring is user-run and a repository index build or refresh
requires a separate explicit approval. Do not treat a menu selection as that
approval. If a manifest exists, include its tier, overlays, and incomplete
count in the intake and make options 1C–1E prominent. Also report detected
graph sources, existing documentation, and candidate repository shapes with a
short “why detected” note (for example, an API schema, web framework manifest,
library package manifest, pipeline configuration, or infrastructure files).

After the user replies, restate the resolved choices and ask only for any
materially missing value. Explicit requests such as “create diligence API
documentation” skip answered questions but still ask for any missing scope;
`--auto-accept` skips only the later plan confirmation, never this missing
scope intake or side-effect approval.

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
4. Stamp provenance while writing. JSON-compatible frontmatter starts at byte
   one for Markdown documents that support it. Exceptions record provenance in
   the manifest.
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
- `--resume`: load the version-2 manifest and continue the first non-complete,
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

Do not stop at the readiness flag. Select and use the provider’s native
retrieval path before planning:

- Understand Anything skills plus its structural/domain JSON;
- GitNexus skills/MCP over its LadybugDB graph and indexed processes;
- CodeGraph’s `codegraph_explore` over its SQLite-backed index.

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

Select overlay identifiers only from `.metadata/catalog.json`. A document
shared by selected overlays appears once, with every applicable selection
origin retained.

Conditional entries are selected only when their evidence exists. Actual
flows, decisions, runbooks, datasets, concepts, migrations, backlog
traceability, and portfolio decisions are dynamic and must be added after
discovery. Never seed an example artifact to stand in for discovery.

### 3. Initialize and preview

```sh
python scripts/manage_manifest.py init \
  --repo <repo> --tier spine \
  --overlay api

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
2. **Scope decision** — chosen tier, each overlay, depth, and one evidence-based
   sentence explaining why it applies.
3. **Exact tree** — every static and discovered dynamic path from the manifest;
   label conditional items that were omitted and why.
4. **Document cards** — one line per path stating the reader question/content
   contract, depth, evidence capabilities, and write order. For audience
   overlays, group cards under Business Analyst, Product Owner, and Coding
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
   markers, and stamp section provenance.
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
Its schema version is `2.0`; there is no secondary runtime state file.

Check staleness with:

```sh
python scripts/check_staleness.py \
  --manifest <repo>/.docforge/manifest.json

python scripts/check_staleness.py \
  --manifest <repo>/.docforge/manifest.json \
  --section configuration --sync-provenance
```

`FRESH` means recorded sources still match, `PARTIAL` identifies a changed or
missing source for one section, and `UNTRACKED` means provenance is absent.
Synchronization reads every manifest path, including root documents, and
changes only each document's provenance section.

## Public tools

Every script has standard-library Python and built-in-only Node peers with the
same flags, messages, JSON shapes, filesystem effects, and exit codes. Unknown
flags exit `2`.

- `manage_manifest.{py,js}`: `init`, `add`, `set`, `status`, and `audit`.
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
