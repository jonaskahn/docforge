# Planning

Owns: repository inspection, tier and profile selection, dynamic-document
discovery, manifest initialization, the dry-run tree, and the plan
checkpoint with document cards.

## 1. Precheck and inspect

Lock one CLI engine for this session (see [`../rules.md`](../rules.md)), then
confirm a readable code graph:

```sh
python3 runtime/cli/python/precheck_graph.py --repo <repo> --need code
# or, if the session locked node:
node runtime/cli/js/precheck_graph.js --repo <repo> --need code
```

A flow graph is required only when a selected manifest document lists
`flow_graph` in `requires`. Before writing the first such document, run:

```sh
python3 runtime/cli/python/precheck_graph.py --repo <repo> --need flow
# or, if the session locked node:
node runtime/cli/js/precheck_graph.js --repo <repo> --need flow
```

Detection and reading are read-only and may be agent-run. Building or
refreshing a repository index requires explicit user approval. Global
installation, MCP wiring, and restart-requiring setup remain user-run.

Do not stop at the readiness flag. Select one ready provider according to the
provider sufficiency rule ([`../rules.md`](../rules.md), `intake.md`) and use its native
retrieval path before planning. Provider-specific dispatch belongs in
[`../references/graph/graph-sources.md`](../references/graph/graph-sources.md);
do not present missing competitors during ordinary repository analysis.

Collect a graph-grounded inventory of boundaries, entry points, public
surfaces, functional areas, candidate flows, tests, configuration, hotspots,
and operational paths. Exact preparation and query dispatch live in
[`../references/graph/graph-sources.md`](../references/graph/graph-sources.md).
Use the bounded evidence ladder in
[`../references/source-analysis.md`](../references/source-analysis.md). Fan out
independent read-only evidence questions according to
[`../references/parallel-execution.md`](../references/parallel-execution.md);
only the orchestrator mutates the manifest.

Inspect repository manifests, code, existing documentation, CI/deployment
configuration, git history, and child repositories. Existing documents are
evidence: propose keep, migrate, merge, archive, or delete decisions and obtain
explicit approval before moving or removing them. When a non-trivial
repo-root `README.md` already exists, do not announce overwrite — require an
explicit migrate / skip / rewrite choice (see Existing-doc actions below).

## 2. Select scope

Choose exactly one catalog tier:

- `spine`: the universal root routers, documentation index, product overview,
  architecture map, setup/testing, configuration, and limitations.
- `diligence`: Spine plus flows, detailed architecture, risks, security,
  operations, contributing, dependencies, and decision records.
- `portfolio`: Diligence plus the complete cross-repository
  `docs-portfolio/` layer.

Select shape, platform, framework, concern, and audience identifiers only from
`.metadata/catalog/profiles/` (via `query_catalog.{py,js} --profile`; see
[`../runtime/catalog/README.md`](../runtime/catalog/README.md)). Aliases are
accepted only at CLI input and normalize to canonical IDs. Shapes own durable
document packs; platforms add platform constraints; frameworks tailor
detection, terminology, evidence queries, and commands; concerns add
conditional content; audiences add reader views. A document shared by
selected profiles appears once, with every applicable selection origin
retained. Selected child paths automatically pull in their cataloged
ancestor indexes.

Conditional entries are selected only when their evidence exists. Actual flow
documents, decisions, runbooks, datasets, concepts, migrations, backlog
traceability, and portfolio decisions are dynamic and must be added after
discovery. Harvest every evidenced flow candidate into
`.docforge/flow-index.json` during analysis; after the plan gate, render it as
`docs/flows/README.md` when that document reaches its write turn. On revise
flow, upsert all candidates as `placeholder` with stubs, update existing
documented flows, and add dynamic deep-dive flow documents only for
main-priority rows (with a user NOTICE — see [`revision.md`](revision.md)).
Never seed an example artifact to stand in for discovery.

## 3. Initialize and preview

```sh
python3 runtime/cli/python/manage_manifest.py init \
node runtime/cli/js/manage_manifest.js init \
# bun  runtime/cli/js/manage_manifest.js init \
# deno run -A runtime/cli/js/manage_manifest.js init \
  --repo <repo> --tier spine \
  --shape desktop-app --shape library-sdk \
  --platform macos \
  --framework swiftui --framework appkit \
  --concern accessibility \
  --audience coding-agents

python3 runtime/cli/python/manage_manifest.py add \
node runtime/cli/js/manage_manifest.js add \
# bun  runtime/cli/js/manage_manifest.js add \
# deno run -A runtime/cli/js/manage_manifest.js add \
  --repo <repo> --type flow \
  --id flow-checkout --path docs/flows/checkout.md

python3 runtime/cli/python/scaffold_docs.py \
node runtime/cli/js/scaffold_docs.js \
# bun  runtime/cli/js/scaffold_docs.js \
# deno run -A runtime/cli/js/scaffold_docs.js \
  --repo <repo> --manifest <repo>/.docforge/manifest.json --dry-run
```

The dry run is the exact active manifest tree and prints, for every selected
document, its group/type, target depth, required evidence, selection origin,
and write order.

## Pre-write structure checkpoint

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

Section READMEs are scaffolded early but finalized bottom-up in the writing
closeout (see [`writing.md`](writing.md)), after their child documents are
materialized and audited — the plan tree lists them in write order, but their
grounding waits for their children.

In review mode, wait for confirmation of this updated tree. In auto-accept
mode, display the same update and continue only when no separate side effect or
destructive action needs approval. Never write against an undisplayed manifest
revision.

Present a human-readable plan before writing. It must contain:

1. **Evidence readiness** — selected primary graph provider and its persisted
   artifact from `precheck_graph.{py,js}` (see
   [`../runtime/graph/README.md`](../runtime/graph/README.md)), current/stale
   state, native or provisional
   flow status, and manifest/history evidence available. Name **only** providers
   that `precheck_graph.{py,js}` reported READY, per the provider sufficiency
   rule ([`../rules.md`](../rules.md)); do not list absent competitors.
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
   Docforge-derived. Call flow evidence **native** only when Understand
   Anything’s domain graph or GitNexus Process nodes are READY; name that one
   provider (or ask which is primary if both native-flow sources are ready).
   If the selected code graph is CodeGraph-only (or any ready code graph with
   no native flow capability), say **Docforge-derived (provisional)** — never
   “Native flow source: CodeGraph” and never “Understand Anything + GitNexus”
   unless both were actually READY and the user chose both for corroboration.
6. **Existing-doc actions** — keep/migrate/merge/archive/delete proposals for
   ordinary paths, with destructive or moving actions still awaiting separate
   approval. For an existing repo-root `README.md` that is non-trivial /
   valuable (substantial user-facing content, not an empty stub), present
   exactly **migrate** / **skip** / **rewrite** and wait for confirmation
   before any write to that path:
   - **migrate** — reshape into the `root_readme` contract/template; preserve
     purpose, audience, install/quickstart, and other key facts from the file;
   - **skip** — leave `README.md` untouched; do not write `root_readme` over it
     this run (mark that catalog path skipped);
   - **rewrite** — replace with the Docforge `root_readme` template from fresh
     graph/repo evidence.
   Never announce “Docforge will overwrite” as a fait accompli. Stub or
   placeholder READMEs may default to rewrite after stating that assessment.
   `--auto-accept` never silently overwrites a valuable root README — this
   three-way choice remains mandatory.

This presentation is the plan gate; a bare list of filenames is insufficient.
Confirm it unless `--auto-accept` is present. Under `--auto-accept`, display the
same plan and continue. `--plan-only` stops after the full presentation and
does not create placeholder documents.

Immediately before materializing each document, show the current structure
summary (or "tree unchanged since the displayed checkpoint") and a compact
execution card: path, reader, owned topics, evidence query, links to owning
documents, and acceptance checks. This is derived from the manifest and the
document's route (`query_catalog.{py,js} --route <id>`), not a second plan file.

Next: for each document in `write_order`, proceed to
[`writing.md`](writing.md).
