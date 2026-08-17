# Planning

Owns: repository inspection, tier and profile selection, dynamic-document
discovery, manifest initialization, the dry-run tree, the plan checkpoint
with document cards, and the write-start flow gate on a fresh start.

## Precheck and inspect

1. Lock one CLI engine for this session (see [`../rules.md`](../rules.md)).
2. Confirm a readable code graph:

   ```sh
   python3 runtime/cli/python/precheck_graph.py --repo <repo> --need code
   # or, if the session locked node:
   node runtime/cli/js/precheck_graph.js --repo <repo> --need code
   ```

**Portfolio-collection exception (root only, never a member).** Root has at
least one nested `.git` directory → run (or reuse intake's already-run
result of) `discover_child_repos.{py,js} --root <repo> --json` and read its
`root_profile_evidence` field. A BLOCKED result above is not yet
session-blocking when `root_profile_evidence` is empty — `detect_profiles`
found no shape, platform, framework, or concern evidence for the root
itself, so there is no source of its own for any provider to graph. Carry
this forward without stopping the session. The exception only takes effect
once Step 2 confirms `portfolio` as the tier **and** the Readiness gate
([`../references/portfolio.md`](../references/portfolio.md) "Readiness
gate") confirms every included member already holds its own graph-grounded
Diligence-or-higher baseline. Once both hold, report the root's own code
graph as **N/A — no source of its own** instead of BLOCKED, and continue.
BLOCKED stands exactly as before when: the tier resolves to `spine` or
`diligence` for this root, any included member fails the Readiness gate, or
`root_profile_evidence` is non-empty — tell the user which source to build a
code graph with and do not analyze or write anything for this repository
until one exists. This exception never applies to a member repository —
every included member still needed its own real code graph to reach
Diligence in the first place.

A flow graph is required only when a selected manifest document lists
`flow_graph` in `requires`. Before writing the first such document, run:

```sh
python3 runtime/cli/python/precheck_graph.py --repo <repo> --need flow
# or, if the session locked node:
node runtime/cli/js/precheck_graph.js --repo <repo> --need flow
```

Rules:

- Detection and reading are read-only and may be agent-run. Building or
  refreshing a repository index requires explicit user approval. Global
  installation, MCP wiring, and restart-requiring setup remain user-run.
- Do not stop at the readiness flag. Select one ready provider per the
  provider sufficiency rule ([`../rules.md`](../rules.md), `intake.md`) and
  use its native retrieval path before planning. Provider-specific dispatch
  lives in [`../references/graph/graph-sources.md`](../references/graph/graph-sources.md);
  do not present missing competitors during ordinary repository analysis.
- Collect a graph-grounded inventory of boundaries, entry points, public
  surfaces, functional areas, candidate flows, tests, configuration,
  hotspots, and operational paths. Exact preparation and query dispatch live
  in [`../references/graph/graph-sources.md`](../references/graph/graph-sources.md).
  Use the bounded evidence ladder in
  [`../references/source-analysis.md`](../references/source-analysis.md).
  Fan out independent read-only evidence questions per
  [`../references/parallel-execution.md`](../references/parallel-execution.md);
  only the orchestrator mutates the manifest.
- Inspect repository manifests, code, existing documentation, CI/deployment
  configuration, git history, and child repositories. Existing documents
  are evidence: propose keep, migrate, merge, archive, or delete decisions
  and obtain explicit approval before moving or removing them. A
  non-trivial repo-root `README.md` already exists → never announce
  overwrite; require an explicit migrate / skip / rewrite choice (see
  Existing-doc actions below).
- While inventorying, also detect **unmanaged documents** and run their
  triage exactly as owned in
  [`../references/docs-tree.md`](../references/docs-tree.md) "Unmanaged
  documents". Its results surface in the plan presentation's Existing-doc
  actions below.

## Select scope

Tier — choose exactly one catalog tier:

- `spine`: the universal root routers, documentation index, product
  overview, architecture map, setup/testing, configuration, limitations.
- `diligence`: Spine + flows, detailed architecture, risks, security,
  operations, contributing, dependencies, decision records.
- `portfolio`: Diligence + the complete cross-repository `docs-portfolio/`
  layer.

Profiles — select shape, platform, framework, concern, and audience
identifiers only from `.metadata/catalog/profiles/` (via
`query_catalog.{py,js} --profile`; see
[`../runtime/catalog/README.md`](../runtime/catalog/README.md)). Aliases are
accepted only at CLI input and normalize to canonical IDs. Shapes own
durable document packs; platforms add platform constraints; frameworks
tailor detection, terminology, evidence queries, and commands; concerns add
conditional content; audiences add reader views. A document shared by
selected profiles appears once, with every applicable selection origin
retained. Selected child paths automatically pull in their cataloged
ancestor indexes.

Conditional entries are selected only when their evidence exists. Actual
flow documents, decisions, runbooks, datasets, concepts, migrations, backlog
traceability, and portfolio decisions are dynamic and must be added after
discovery. Harvest every evidenced flow candidate into
`.docforge/flow-index.json` during analysis; after the plan gate, render it
as `docs/flows/README.md` when that document reaches its write turn. Which
harvested candidates become deep-dive flow documents is not settled here —
that is the write-start selection gate below, a mandatory user decision even
under `--auto-accept`. Never seed an example artifact to stand in
for discovery.

## Planning over an existing manifest

When the goal is **replace the plan** — or any new plan over a manifest
that already exists — planning starts from the existing record, never
from a blank slate:

1. Run `migrate_metadata.{py,js}` first — unconditional and idempotent
   (see [`validation.md`](validation.md) "Manifest and provenance"); an
   already-current manifest reports a clean no-op.
2. Prefer `manage_manifest.{py,js} reconcile` with the new scope
   ([`revision.md`](revision.md) "Applying the answers to the manifest").
   Written documents that fall out of the new selection are reported as
   `retire` candidates — their statuses, provenance, and audit records
   stay in the manifest; reconcile itself never deletes content.
3. `init --force` is the blank-slate escape hatch only: it replaces the
   manifest record entirely, so previous statuses and audit history are
   lost and any written `docs/` files without entries become foreign
   documents that flow through the unmanaged-doc triage. Use it only
   when the user explicitly asks to discard the current plan record,
   and only after explicit confirmation — never silently, never under
   `--auto-accept`.

## Initialize and preview

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
  --audience coding-agents \
  --graph-provider <id-only-if-intake-asked-and-the-user-chose-one>

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

`init` locks the graph provider into the manifest as part of this same call
— automatically, in registry-priority order, unless `--graph-provider`
carries an explicit choice from intake's "several ready providers" question.
Omit the flag whenever that question didn't fire (no separate locking step
in the common case). See
[`../references/graph/graph-sources.md`](../references/graph/graph-sources.md)
"Session persistence" for the mechanics every later step, including spawned
parallel writers, relies on.

**Target readers → init flags** ([`intake.md`](intake.md) "Target readers"):
`Both` adds `--audience coding-agents` to the confirmed audience flags;
`Human readers` adds nothing — agent-context types are audience-gated, so
none are selected; `AI coding agents` passes
`--group agent-context --audience coding-agents`, and the manifest records
`project.groups: ["agent-context"]`. Never pass `--group agent-context`
without the coding-agents audience: that scope selects zero documents and
`init` fails naming the unlocking audience.

`init` also detects project scale and records `project.scale`. Turn 1 of
intake confirms the layout before Turn 2 asks tier, profiles, and audiences
([`intake.md`](intake.md) "Turn structure"):

- User's pick matches the detected layout → no flags; `init` records
  `decided_by: "detected"`.
- Pick differs → pass `--layout <compact|standard>` (and
  `--scale-class <small|medium|large>` when the class also changed); records
  `decided_by: "user"` with the detected class preserved as
  `detected_class`.
- The compact fold is automatic whenever the confirmed layout is `compact`.

`init` rejects `--tier portfolio --layout compact` with a nonzero exit:
compact covers Spine and Diligence only
([`../references/docs-tree.md`](../references/docs-tree.md) "Compact
layout"). At the portfolio tier a detected compact layout is forced to
`standard` and recorded as `decided_by: "tier-constraint"` — never as a
user pick.

The dry run is the exact active manifest tree and prints, for every
selected document, its group/type, target depth, required evidence,
selection origin, and write order. When the confirmed layout is `compact`,
`init` / `selected_static_documents` already returns the folded set — the
merged files stand in for their member groups — so the dry-run tree
displays it verbatim, with the merged entries' `compact_members` traceable
in the manifest.

A compact dry run shows fewer entries than the discovery brief's subject
count implies, and that is correct: every profile- and audience-driven
document folds into its group's merged file, so a confirmed shape adds
sections rather than entries
([`../references/docs-tree.md`](../references/docs-tree.md) "Compact
layout"). Do not add documents back to compensate. The one exception is a
group that spilled past `COMPACT_SECTION_CAP`; `manage_manifest preview`
names it, and its overflow appears in the tree at standard paths.

Dynamic entries behave the same way. In compact layout
`manage_manifest add --type <t>` records the instance as a `##` section on
its group's merged entry instead of creating a document, and refuses past
`COMPACT_DYNAMIC_CAP` — an instance over budget belongs in the merged
file's candidate matrix, not in a new file.

## Pre-write structure checkpoint

For **every new plan**: finish repository inspection and dynamic-document
discovery, update the manifest, and show the final dry-run tree before the
first document is materialized. Include selected paths, omitted
conditionals, dynamic additions, document count, and the number waiting for
a flow graph. This happens in review mode and with `--auto-accept`;
auto-accept skips the pause after the tree, never the tree itself.

If inspection or later writing discovers a real flow, decision, runbook,
dataset, migration, ticket traceability record, or other item that changes
the manifest, update it first and show a structure update before writing
resumes:

- added paths and why they were discovered;
- removed/skipped paths and why;
- changed requirements, selection origins, or write order;
- the refreshed exact tree and updated document count.

Section READMEs are scaffolded early but finalized bottom-up in the writing
closeout (see [`writing.md`](writing.md)), after their child documents are
materialized and audited — the plan tree lists them in write order, but
their grounding waits for their children.

In review mode, wait for confirmation of this updated tree. In auto-accept
mode, display the same update and continue only when no separate side
effect or destructive action needs approval. Never write against an
undisplayed manifest revision.

Present a human-readable plan before writing. It must contain:

1. **Evidence readiness** — selected primary graph provider and its
   persisted artifact from `precheck_graph.{py,js}`
   ([`../runtime/graph/README.md`](../runtime/graph/README.md)),
   current/stale state, native or provisional flow status, and
   manifest/history evidence available. Name **only** providers that
   `precheck_graph.{py,js}` reported READY, per the provider sufficiency
   rule ([`../rules.md`](../rules.md)); do not list absent competitors.
2. **Scope decision** — chosen tier, each profile, depth, and one
   evidence-based sentence explaining why it applies.
3. **Exact tree** — every static and discovered dynamic path from the
   manifest; label conditional items that were omitted and why.
4. **Document cards** — one line per path stating the reader
   question/content contract, depth, evidence capabilities, and write
   order. For audience profiles, group cards under Business Analyst and
   Product Owner headings — and under a Coding Agent heading only when the
   confirmed reader pick generates agent context.
5. **Capability schedule** — which documents can proceed from the code
   graph now, which wait for `flow_graph`, and whether flow evidence will
   be native or Docforge-derived. Call flow evidence **native** only when
   Understand Anything's domain graph or GitNexus Process nodes are READY;
   name that one provider (or ask which is primary if both native-flow
   sources are ready). If the selected code graph is CodeGraph-only (or any
   ready code graph with no native flow capability), say **Docforge-derived
   (provisional)** — never "Native flow source: CodeGraph" and never
   "Understand Anything + GitNexus" unless both were actually READY and the
   user chose both for corroboration.
6. **Existing-doc actions** — keep/migrate/merge/archive/delete proposals
   for ordinary paths, with destructive or moving actions still awaiting
   separate approval, plus the **Unmanaged documents** triage from the
   inspection pass (per foreign file: `Keep self-managed (recommended)` /
   `Archive`). For
   an existing repo-root `README.md` that is non-trivial / valuable
   (substantial user-facing content, not an empty stub), present exactly
   **migrate** / **skip** / **rewrite** and wait for confirmation before
   any write to that path:
   - **migrate** — reshape into the `root_readme` contract/template;
     preserve purpose, audience, install/quickstart, and other key facts
     from the file;
   - **skip** — leave `README.md` untouched; do not write `root_readme`
     over it this run (mark that catalog path skipped);
   - **rewrite** — replace with the Docforge `root_readme` template from
     fresh graph/repo evidence.
   Never announce "Docforge will overwrite" as a fait accompli. Stub or
   placeholder READMEs may default to rewrite after stating that
   assessment. `--auto-accept` never silently overwrites a valuable root
   README — this three-way choice remains mandatory.

This presentation is the plan gate; a bare list of filenames is
insufficient. Confirm it unless `--auto-accept` is present. Under
`--auto-accept`, display the same plan and continue. `--plan-only` continues
through the flow gate below and then stops: it scaffolds no document bodies
and re-grounds nothing, but the flow index and its main-standalone stubs are
metadata and are written, so the final tree carries a real flow-document
count ([`../flags.md`](../flags.md)).

## Flow gate (write-start)

The flow selection gate is a write-start step, not an intake question. It
fires for `diligence` and `portfolio` tiers after the plan gate is
confirmed and before the first document is materialized. Spine has no flow
deep-dives: the harvest still ran during repository inspection, but
`docs/flows/README.md` renders the candidate matrix only — no gate, no
selection prompt.

**Mandatory gate — `--auto-accept` never waives it.** Which flows become
documents is a scope decision like profiles or audiences, not a routine
pause — the selection prompt is always shown and always awaited, exactly
like the intake confirmation and the root-README three-way choice
([`../references/graph/flow-derivation.md`](../references/graph/flow-derivation.md)
"Selection gate and write-back"). Under `--auto-accept` only the pause on
the structure update that follows the gate is skipped; the selection itself
never is.

Run the canonical pipeline — precheck → harvest/import → organize →
analyze → selection gate → apply → write → write-back → render — exactly as
[`../references/graph/flow-derivation.md`](../references/graph/flow-derivation.md)
"Flow pipeline" specifies. It owns every command and flag, the analysis
depth rule, the prompt's contents and `--main-limit` budget, and the
`update` promote/demote/decline mapping. Do not restate them here; do not
reference its steps by number.

Fresh start differs from revise in four places, and only these:

- **Harvest writes the real index.** `flow_index.{py,js} harvest` produces
  `.docforge/flow-index.json` directly, so Apply has no `revise` step —
  the order is `update` per changed row, then
  `manage_manifest.{py,js} add --type flow --id … --path …` for every
  selected standalone.
- **Every candidate is new.** The prompt offers promote / demote / skip,
  not the revise flow's per-row add / remove / update actions, and there
  are no unchanged rows to carry as baseline facts.
- **One analysis, no reuse.** There is no stored analysis to reuse and no
  flow-mode question. CodeGraph-only: the single agent analysis taken at
  harvest time (`derive_flow_graph.{py,js} prepare` → agent →
  `flow_index.{py,js} import --analysis`) **is** the deep pack; the
  Analyze phase must not re-run it.
- **The structure update is the corrected projection.** Its document count
  supersedes the intake estimate, which excluded flow documents on purpose
  ([`intake.md`](intake.md) "Confirmation summary"). Honor the execution
  mode for the pause; never skip the tree itself.

Under `--plan-only` the gate still fires — which flows become documents is a
scope decision, and its answer is what makes the dry-run count real. The
pipeline runs through the selection gate and the structure update, writing
the flow index and its main-standalone stubs (metadata, not document
bodies), then stops before the write phase.

Next: for each document in `write_order`, proceed to
[`writing.md`](writing.md), which opens every document with the structure
summary and execution card it owns.
