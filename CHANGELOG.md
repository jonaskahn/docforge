# Changelog

## 2.23.0

- **Source mentions become links a reader can follow.** A mention is still a
  readable noun phrase first, but when the reader must open the file that
  phrase is now the link text of a **commit-pinned permalink**. The writer
  writes the authoring form (`[readable label](src/worker.py#L97-L104)`) and
  the new `link_sources` pass expands it against the repository base declared
  in `project.repository`, validating that every path exists and every range
  is inside its file — a stale reference fails at write time instead of
  404ing for a reader. Generated output previously carried over a thousand
  unchecked `path:line` strings pinned to a commit that had already moved.
  - New `manage_manifest set-repository` declares the base, forge flavor, and
    permalink template. Line-anchor syntax differs per forge, so a self-hosted
    host's flavor is asked for once, never guessed.
  - `host-neutrality.md` gains a fourth confinement location for that
    declaration; the linters exempt links built from it (`source-code-link`
    and `forge-leakage` no longer fire on a sanctioned permalink) and add
    `unpinned-source-link` for an authoring-form link that was never expanded.
    A bare `path:line` in prose remains a defect, and agent-context outputs
    remain link-free and URL-free.
  - `provenance.git_commit` — schema-declared and validated since 2.0 but
    never produced — is now stamped with the commit a document's links pin to.
- **Illustration count follows declared obligations, not document length.**
  A type now declares `illustration_views`: every view it owes, each with the
  reader question it answers. The gate checks coverage **by form**, so a
  pre-baked ASCII layout tree no longer satisfies a declared
  `sequenceDiagram` — the way a 30 KB low-level document shipped carrying one
  diagram. Three one-diagram caps that contradicted `illustration.md`'s own
  "no cap" rule are gone: high-level owes both a C4 context **and** container
  diagram, low-level owes layout, component map, one to three runtime
  scenarios, and a data model, and a flow may carry its outcome fan-out
  beside its primary form.
  - Templates gained the slots to match, including for `triggers-and-jobs`,
    `observability`, `deployment`, `job-reliability`, `configuration`, and
    `errors` — document types that previously produced tens of kilobytes with
    no visual at all. Reference catalogs stay tabular on purpose.
  - New `decorative illustration` (fewer than three meaningful elements) and
    `undescribed illustration` (no explanatory sentence beside the fence)
    defects. The second is an accessibility floor: screen readers announce a
    Mermaid diagram as an unordered jumble of node labels, so the adjacent
    prose is the only content those readers get. Every Mermaid scaffold now
    carries `accTitle` / `accDescr`.
  - `timeline` is no longer declarable (Mermaid documents it as
    experimental); `journey` and structural `text` are. The `working` budget
    key documented since 2.22 is now actually enforced, and a view may carry
    its own `depth`.
- **Collection folders no longer ship empty.** `concepts/`, `decisions/`, and
  `runbooks/` were guaranteed to appear holding nothing but an index
  explaining its own emptiness on **every** Diligence run — their child types
  are gated on `discovered_*` conditions that no code evaluated and no step
  produced. Seven such indexes now declare `requires_children` and are
  selected only once a child exists; seeding the first child brings the index
  back automatically.
  - New `harvest_candidates` proposes decision and concept candidates from
    the git signals `references/decision-records.md` already prescribed for
    backfilling — a procedure that existed in full and was linked from no
    workflow. Candidates only: nothing is selected, and no rationale is
    invented.
  - The `folder-only promotion` check now covers the collection root itself
    (it previously skipped the very folder it was named for) and all seven
    locations rather than two. `docs/flows/` stays exempt at the root, since
    its index is a discovery report that records deferred candidates too.
- **Generated index tables render as tables.** `expand_children_block`
  discarded the header and separator rows, which sit inside the managed
  markers, so every section README emitted literal pipe text. Each template's
  own header and column count are now preserved.
- **The dashboard reports a document that produced no page.** A written
  record dropped from the page ledger previously became a silent 404 with no
  finding anywhere.

## 2.23.0 (initial)

- **Illustrations are declared, briefed, and enforced.** The catalog now
  declares a `dominant_form` for every document, the writer's execution card
  carries an illustration brief, and `scaffold_docs --audit` reports
  **`missing-illustration`** for any written non-agent document whose declared
  form warrants a visual but carries no `mermaid` or structural `text` fence.
  Manifest 3.10 seeds each document's `dominant_form` (migration hydrates
  existing manifests; reconcile demotes written documents whose declared form
  changed).
  - All 54 one-line "Preferred illustration" hints across the merged group
    instruction files became structured `## Illustration`
    (Form/Renders/Trigger) blocks; `content/compact/instructions.md` gained
    the same blocks for every routed section.
  - Revise now treats illustration coverage as a structural check, never a
    blob check: an already-written, diagram-less document gains its diagram on
    the next revise even when its sources are `FRESH`.
  - Flow templates carry a second diagram slot — an ASCII trigger-to-outcome
    fan-out — for flows with two or more terminal outcomes, the form
    `illustration.md` already blesses for a different reader question.
- **One source-reference rule, three enforcers.** `evidence-presentation.md`
  now owns "Naming things a reader can find": a readable noun phrase first, a
  backticked parenthesized path only when the reader must open, edit, run, or
  inspect the file — never a Markdown link into source, never a line number.
  The linter gains **`visible-source-line`** for bare `path:line` / `#L<n>`
  citations in prose, closing the hole flow-step guidance previously shipped
  through.
  - The body-text locator subsystem (`evidence_locators`) is retired on policy
    grounds: since locators in prose are forbidden outright, validating them
    was unreachable code that could only ever add defects. The hashing helpers
    (`evidence_hash`) it depended on remain untouched.
- **Sections connect; sections sound consistent.** A `## Connections` table
  now accompanies every routed document section across all eight group
  instruction files, and `scaffold_docs --audit` enforces **section
  cohesion**: in any section folder with two or more non-router documents, no
  document is an island. New `references/voice.md` owns one voice per group
  (rules plus do/don't pairs); every instruction file carries a `## Voice`
  line, the execution card carries it, and the independent audit checks it.

## 2.22.0

- **Agent documentation is permanently isolated.** The conditional
  linked/standalone model from 2.20 is removed. Every agent-context output now
  owns a concise, evidence-backed copy of the facts its reader question needs;
  duplication is intentional, and generated agent documents contain no links,
  imports, URLs, or references to any other documentation. Generated human
  documentation remains unable to reference agent outputs.
  - `project.agent_context`, catalog variants, route-time variant flags, and
    `manage_manifest agent-mode` are gone. Manifest 3.9 migrates every retained
    agent document to the canonical contract and demotes previously written
    copies for re-grounding.
  - `docs/agents/README.md` is no longer generated. Standard layout writes
    independent topic files; compact layout writes one independent aggregate.
  - `CLAUDE.md` is a complete kernel generated from the same contract as
    `AGENTS.md`, not an `@AGENTS.md` shim.
  - Audits enforce both sides of the boundary, including references in fences
    and comments. Agent pages are excluded from dashboard pages, navigation,
    projections, and signatures; an agent-only tree is a clean no-render state.
  - Group-scoped generation remains. Dynamic additions, compact previews, and
    scoped plans now consistently respect `project.groups`.

## 2.21.0

- **One deterministic cartridge root, and an explicit untrusted-data
  boundary.** The entrypoints used to carry a three-branch lookup — repo-local
  self-host first, then the plugin root, then an enumerated set of global skill
  dirs (`~/.agents/skills`, `~/.claude/skills`, `~/.config/opencode/skills`).
  Two problems with that.

  **It was a real hole, not just a smell.** Branch 1 said: if the working repo
  contains `skills/<entrypoint>/SKILL.md`, the cartridge is
  `<repo>/skills/docforge/_shared`. Cloning a repository that ships that layout
  was enough to make a Docforge command execute *that repository's* Python or
  Node. Repository contents are untrusted input and now never supply the
  scripts these skills run.

  **It read as dynamic code loading.** Gen Agent Trust Hub's audit of
  `docforge-dashboard` on skills.sh flagged exactly this — `DYNAMIC_EXECUTION`
  and `REMOTE_CODE_EXECUTION`, MEDIUM — because a search across home
  directories for scripts that are then executed cannot be told apart from the
  malicious version of the same pattern.

  - The cartridge is now resolved against the directory the entrypoint was
    loaded from, and there is exactly one candidate. A plugin install and a
    skill-directory install keep the same layout, so the relative path is
    identical in every host and nothing has to be searched for. No absolute
    home directory is named anywhere under `skills/` any more.
  - A Docforge checkout in the working repo became a **working-copy override**:
    used only when the user explicitly asks for it, after the absolute path is
    printed and confirmed. Dogfooding still works; it just cannot happen
    silently.
  - Runtime scripts are stated to be the copies shipped in the installed
    package, byte-for-byte — never downloaded, fetched, or generated at run
    time, never executed from the working directory.
  - New `rules.md` section **Untrusted repository data** covering the four
    things an injection review asks for: ingestion points, trust boundary
    (repository content is *data, never instructions* — text that reads like a
    prompt or a command is inert), sanitization (structural validation, with
    unsupported metadata skipped rather than interpreted), and the capability
    inventory. All three entrypoints restate the boundary;
    `docforge-dashboard` carries the full inventory, including the existing
    `ensure_dependencies` guard that hashes the repository's `package.json` /
    `package-lock.json` around `npm install` and aborts if either changed.
  - Corrected a claim added in the previous release: the dashboard does **not**
    validate a repository's manifest against the shipped
    `manifest-schema.json` / `provenance-schema.json`. Those drive a
    release-time self-check of the cartridge. What actually runs is structural
    validation in `scan`/`reconcile_metadata` against the supported provenance
    `schema` versions (2.0 / 2.1), and that is what the text now says.
  - `workflows/tools.md` §Installation follows the same rule, and its optional
    `ln -s` runtime link is marked plainly as user-run, never something the
    agent does.
  - Tests pin the new contract: no file under `skills/` may enumerate global
    skill dirs, every entrypoint must carry the single-candidate rule, the
    working-copy override, and the trust boundary, and the capability claims
    must match the guards in both runtime peers.

## 2.20.0

- **Agent documentation is a one-way overlay, and can be generated on its own
  (manifest 3.8).** Two related changes.

  **References run one way.** No human-facing document may link, mention, or
  `@`-reference an agent-context output — `docs/agents/`, `docs/agents.md`,
  `AGENTS.md`, `CLAUDE.md`, `CLAUDE.local.md`, `.claude/settings.json`. Agent
  documents still link the whole human tree. The outbound half was already
  policy; the inbound half was mechanically forced *against* it, because
  `readme_child_coverage` required `docs/README.md` to link
  `docs/agents/README.md` and `child_rows` wrote that row automatically.
  - `routable_children` filters both enumerations relative to the referencing
    document, so `docs/agents/README.md` still routes its own children.
  - New whole-tree finding **`agent-context leak`** in `scaffold_docs --audit`.
    Targets are derived from the manifest, never hardcoded: a repository that
    owns `agents/` or `.claude/settings.json` itself cannot trip it, and a
    fenced `cat AGENTS.md` is not a reference.
  - Reachability is amended: agent documents are reachable from `AGENTS.md`,
    not from `docs/README.md`, and appear in no human index in either layout.

  **`--group` scopes a run to catalog groups.** Repeatable, alias-accepting
  (`agents`, `arch`, `ops`, `adr`, …), include-list only, and strictly
  subtractive — omitting it reproduces the previous selection exactly. Added to
  `manage_manifest init|preview|reconcile`, `query_catalog --applicable`, and
  `scaffold_docs --dry-run`; `query_catalog --groups` lists every group with
  its aliases and unlocking audiences.
  - Out-of-scope indexes are not pulled back in as ancestors, so an agents-only
    run writes no `docs/README.md` — which would otherwise have to index the
    agent overlay.
  - A scope that selects nothing now fails, naming the audience that would
    unlock it, instead of writing an empty manifest.
  - `project.groups` and `project.agent_context` are new optional manifest
    fields (**schema 3.8**). Both stay absent when they carry no information,
    so a pre-3.8 manifest reads identically.

  **Standalone agent documentation.** When the agent-context group is all a run
  writes, its documents *own* their facts instead of linking human documents
  that were never generated. Selected through a new catalog `variants` block
  (axes: `agent_context_mode`, `layout`), resolved at manifest-build time so
  `scaffold_docs` needs no mode awareness. Standalone stays agent-sufficient —
  durable paths, boundaries, entry points, verified commands, observable
  hazards — and never claims design rationale, business context, or operational
  procedure, none of which is derivable from a graph.
  - A later run that adds human documentation reports an **`agent-mode`**
    reconcile delta and stops. `manage_manifest agent-mode --decision
    convert|keep` applies the answer: `convert` demotes the agent documents for
    re-grounding, `keep` records `decided_by: "user"` so reconcile never asks
    again. Reconcile reports and never demotes — the `retire` precedent, not
    the `sync_presentations` one.
  - A linked → standalone → linked round trip is **not** content-preserving,
    unlike compact ↔ standard.

  **Fixed: `AGENTS.md` emitted dangling `@` refs in compact layout.**
  `agents_kernel` declares no `compact_group`, so it is written in every
  layout, but its §7 fan-out hardcoded `@docs/agents/*.md` — files compact never
  materializes. A kernel written faithfully from its own template produced seven
  `dangling-at-ref` defects. Fixed with a layout variant referencing
  `@docs/agents.md`; the linter was correct and is unchanged.

  **Fixed: the dashboard told agents-only repositories to "revise again".**
  Nothing was broken — there is simply no human-facing documentation to render.
  `dashboard scan` now reports `agent-context only` and says so.

  `/docforge-revise <area>` is finally defined: the catalog group ids plus
  aliases, listed by `query_catalog --groups`, with unknown areas an error
  rather than a silent full-tree fallback. `flow`/`flows` stays reserved for the
  flow pipeline. **`<area>` never passes `--group` to reconcile** — that is a
  persistent scope whose narrowing correctly retires every out-of-area written
  document, while `<area>` is only a transient work filter.

- **Illustrations are no longer capped per document.** The depth table in
  `references/illustration.md` fused two unrelated limits: a count budget per
  document (orientation 1 / working 2 / deep-dive 3 / reference 1 / router 0)
  and a complexity bound per illustration. The count budget contradicted its
  own neighbouring rule — "split any illustration that exceeds its bound" adds
  an illustration, which then tripped the cap, making the prescribed remedy for
  an over-dense diagram a violation and pushing writers toward the single
  overloaded diagram instead. It also had no external support: of ~20 primary
  sources surveyed (Google, Microsoft, GitLab, Kubernetes, The Good Docs
  Project, Diátaxis, C4, arc42, ISO/IEC/IEEE 42010, SEI *Views and Beyond*,
  Mermaid/PlantUML), **none caps diagrams per document**, and three prescribe
  the opposite as the remedy for complexity. Count is an output of per-diagram
  scope in every framework surveyed, never an input.
  - `illustration_metrics.{py,js}` drop the `illustrations` counter and the
    per-document check; `BUDGETS` is now a plain depth → max-elements map.
  - `router` gains a real element bound (12). Its previous `(0, 0)` made any
    illustration in a router document a defect — a count ban in disguise.
  - The relevance test under "Choose the smallest useful form" is now the only
    thing limiting how many illustrations a document carries, which is what the
    literature actually supports.
  - Per-illustration bounds, the sequence/state/ER/journey sub-limits, the
    mandatory surrounding prose, and the audit's illustration-continuity rule
    are all unchanged.

- **Compact layout is now actually compact (catalog 2.19.0).** Previously only
  documents carrying a `compact_group` folded, so every profile-driven,
  audience-driven, and dynamically discovered document stayed a file of its
  own: compact Diligence on an API-service repository with six flows and four
  decisions emitted 44 files. Everything foldable now folds, and **the compact
  file count is a function of layout and tier alone** — confirming a shape or
  discovering ten more flows adds sections, not files. Compact Diligence is 15
  files for a bare repository and 22 with three shapes and all seven audiences
  (against 34 and 67 standard).
  - Five new merged files: `docs/flows.md`, `docs/decisions.md`,
    `docs/concepts.md`, `docs/business-analyst.md`, `docs/product-owner.md`.
    Each audience pack folds to one file of its own rather than swelling a
    neighbour, as `docs/agents.md` already did.
  - Dynamic instances fold as `##` sections. In compact layout
    `manage_manifest add --type <t>` records `{id, slug, title}` on the
    group's merged entry instead of creating a document (manifest schema
    updated); every discovered instance still appears in the merged file's
    candidate matrix, and the first six per type
    (`COMPACT_DYNAMIC_CAP`) are expanded into full sections. The command
    refuses past the budget rather than silently dropping the instance.
  - `COMPACT_MEMBER_CAP` splits into `COMPACT_CORE_CAP` (8, tier-driven
    members a group may declare, checked by `query_catalog --validate`) and
    `COMPACT_SECTION_CAP` (14, sections a project materializes, checked by
    `manage_manifest` when it folds). A group past the section cap **spills**:
    its overflow keeps its own standard paths, linked from the merged file.
  - `manage_manifest preview` reports the densest merged files and names any
    spilled group; intake states both before the confirmation gate.
- **Fixed: compact Spine resurrected standard-layout indexes.** The
  ancestor-index pass skipped only ids folded on that run, so a Diligence-only
  index such as `security_index` — never selected at Spine, therefore never
  folded — was re-added as a bare `docs/security/README.md` inside a compact
  tree. It now skips every id that declares a `compact_group`.
- **Fixed: a merged file's coverage audit used its own path.** `docs/decisions.md`
  stands for `docs/architecture/decisions/`, and `docs/operations.md` for both
  `docs/operations/` and `docs/operations/runbooks/`. `scaffold_docs --audit`
  now takes the folders a merged file covers from the members it merged.

- **Smarter scale classification (manifest 3.7).** `small` is now under 50
  source files (was 15), and classification weighs three signals: source-file
  count (base class), declared-dependency breadth (40+ deps promote
  `small` → `medium`, 200+ promote `medium` → `large`), and flow breadth
  (10+ / 40+ harvested flow-index candidates). Promotions cap at one class
  above the source-file base and never demote. The two new measurements —
  `declared_dependencies` and `flow_candidates` — join `project.scale.signals`;
  `migrate_metadata` refreshes signals on upgrade while never re-deriving a
  `decided_by: "user"` class or layout.
- **Scale surfaces at intake and revise.** `detect_profiles --emit-gate-pack`
  now carries a `scale` field (class, suggested layout, signals) reusing its
  own walk, so the intake discovery brief and the revise confirmation summary
  can state and re-check the detected scale without another tree pass.
  `reconcile` accepts `--scale-class` (layout follows the class default unless
  `--layout` is also named), and revise re-detects scale drift on every
  detection pass — recommended as a change when `decided_by: "detected"`,
  reported as a fact when `decided_by: "user"`.

## 2.18.0 - Project scale, compact layout at every tier, retirement, and a markdown-only-JSON provenance store

- **Project scale awareness.** `manage_manifest init` classifies a repository
  as `small` / `medium` / `large` from its tracked/source-file counts and
  confirmed profile count, and suggests a layout — `compact` for small,
  `standard` otherwise — recorded in `project.scale` (manifest 3.5) as a
  proposed default the user can override (`decided_by: "user"`). `reconcile
  --layout` and `init --layout` force either layout explicitly.
- **Compact layout now covers Diligence too**, not just Spine: Diligence gains
  six merged files (`docs/architecture.md`, `docs/engineering.md`,
  `docs/reference.md`, `docs/operations.md`, `docs/security.md`,
  `docs/contributing.md`) folding 18 statics — a Diligence fixture goes from
  34 written documents to 16. Dynamic-child indexes (`concepts/`,
  `decisions/`, `runbooks/`) and conditional members never fold. A merged file
  hosts at most 8 member sections (`COMPACT_MEMBER_CAP`), enforced by
  `query_catalog --validate`. *(Superseded during this release cycle: an
  interim build also folded the Portfolio layer into `docs-portfolio.md`;
  that was reverted before release, and Portfolio is always `standard`.)*
- **Document retirement.** A tier downgrade, profile/audience removal, or
  layout switch that drops a written document out of selection is reported
  as a `retire` candidate by `reconcile`; `manage_manifest retire` then moves
  it to `.docforge/obsolete/<year>/` (git-ignored, default) or deletes it
  (explicit choice only) — never silently, never under `--auto-accept`. The
  manifest entry is kept with `status: retired`; re-selecting it later
  returns it to `planned`.
- **Selection-change previews.** A revise that names a tier, or
  `/docforge-revise all`, always shows the tier control and the selection
  delta (adds, retires, contract-updated) even with no detected drift, so a
  tier-naming run can never change the tree silently.
- **Provenance storage is now JSON-only.** The `markdown` inline-frontmatter
  storage mode is removed entirely — manifest 3.6 narrows
  `provenance_storage` to a single legal value, and generated markdown is
  unconditionally frontmatter-free. `migrate_metadata` strips any
  surviving inline frontmatter into the folder sidecar
  (`.docforge/provenance/<folder>.json`) in the same pass it upgrades the
  schema, so no document survives a migrate run still carrying frontmatter.
  `set-storage` and `init --storage` are gone.
- **Eight runtime defects fixed**, each with a regression test: `manage_manifest
  set` on a retired document crashed instead of transitioning it back to
  `planned`; the metadata bucket counts didn't sum to `total_documents` once
  a document was retired; dashboard reconcile reported noise for retired
  documents; `reconcile --layout` on a manifest with no scale record wrote a
  schema-invalid one; the compact-member sort crashed (Python) or ignored
  `compact_order` (Node) when two members tied; a non-object `project.scale`
  was repaired by one peer and left broken by the other; and
  evidence-locator validation (`validate_locators`) had been silently dead
  since 2.16.0's move to sidecars — it parsed frontmatter that json-mode
  documents no longer have, so every locator defect class went undetected
  until the caller was fixed to hand it the already-resolved provenance
  instead.
- **Instruction corpus de-duplication and conflict resolution.** Thirteen
  confirmed contradictions in the always-loaded skill instructions are
  resolved — migration-confirmation wording, dashboard auto-serve's
  compact-layout exception, the undefined "revise-vs-render prompt," stale
  version/subcommand/path-count references, a section-numbering collision
  across `planning.md`/`writing.md`/`validation.md`, and a wrong catalog
  group description, among others — plus the clearest repeated passages
  (session-engine lock ladder, legacy-manifest re-registration mechanics)
  collapsed to one owner with a link, and ownership-registry gaps filled for
  scale/layout, retirement, and template conformance.
- **Release self-checks fixed:** `plugin.json` / `marketplace.json` /
  `skills/docforge/SKILL.md`'s descriptions had drifted apart; the catalog
  JSON Schema's version constant was stale against the catalog itself; and a
  "no nested `README.md` files" validator check — written for an earlier,
  flatter layout — flagged every legitimate navigational README in
  `content/`, `references/`, and `.metadata/catalog/` (all ~50 of them) and
  is removed.
- Manifest 3.5 → 3.6; catalog and package version → 2.18.0.

## 2.17.0 - Unmanaged documents (self-managed or archive)

- Foreign `.md` / `.mdx` files under `docs/` or `docs-portfolio/` — docs
  Docforge never generated — now get an explicit triage on fresh-start
  planning and at revise start: **Keep self-managed** (recommended) or
  **Archive** to `docs/_archive/<year>/`. Decisions persist in
  `project.unmanaged_docs` (manifest 3.4), so a file is never re-asked,
  never tracked, and never scaffolded over.
- `manage_manifest unmanaged list|add|remove|archive` applies the triage
  mechanically; `archive` performs the file move itself and records the
  target. Both runtimes, full parity.
- Self-managed and archived docs are known, never findings:
  `scaffold_docs --audit` stops listing them under `unexpected`, and
  `dashboard scan` stops reporting them as `untracked` (it now also skips
  `docs/_archive/` entirely and prints an `unmanaged` info line instead).
- Updating a named unmanaged doc (natural-language update/refresh) rewrites
  its content with normal grounding and writing quality but never adds a
  manifest entry and never stamps provenance — the file keeps belonging to
  the user.
- Manifest 3.4: `project.unmanaged_docs` (`[{path, decided_at}]`);
  `migrate_metadata` upgrades 3.3 → 3.4 by seeding the empty list, and
  schema/README/tests are bumped across Python and JS peers.

## 2.16.0 - External provenance store (markdown-clean output)

- Converted dashboard pages now carry **`id`, `title`, and `description`**
  frontmatter only: `docforge_provenance` is no longer emitted into the
  rendered site — the sidecar / manifest stay the authoritative metadata
  store.
- Manifest 3.3 adds `project.provenance_storage` — `json` (default) or
  `markdown`. In `json` mode generated files carry **no frontmatter at all**;
  each docs folder's public identity (`id`, `title`, `description`) and
  `docforge_provenance` live in one git-tracked sidecar,
  `.docforge/provenance/<folder>.json` (repo root → `root.json`), and the
  whole pipeline — scaffold, lint, staleness, audit, flows, dashboard build,
  planning — reads and writes through it.
- `migrate_metadata` upgrades 3.2 → 3.3 and, under `json` storage, moves
  existing inline frontmatter into the sidecars and strips it from the
  markdown (`--dry-run` previews every move); `check_staleness
  --sync-provenance` moves any straggler inline document it meets.
- `manage_manifest init` seeds the storage mode (`--storage markdown` for the
  legacy inline layout) and the new `set-storage json|markdown` subcommand
  flips the whole tree in either direction with a `--dry-run` preview.
- The dashboard reconciles metadata in the sidecars or frontmatter per the
  storage mode, re-emits full frontmatter into the built site, and its render
  signature now covers the provenance tree.
- New Python/JS parity tests for the sidecar store, storage moves, migration,
  sync auto-move, lint/audit on sidecars, and mode flipping.

## 2.15.0 - Cosmetic-drift detection via normalized and range evidence hashes

- Provenance schema 2.1 adds optional per-source evidence hashes:
  `git_blob_normalized` (CRLF/CR -> LF, trailing whitespace and blank-line
  normalization) and `evidence_range` + `range_blob` (1-indexed inclusive
  line-span hash), both emitted by the writers and enforced by the schema.
- `check_staleness` now classifies each cited source as fresh, cosmetic
  (whitespace/EOL-only drift or an untouched cited span), or stale instead
  of a binary blob match, so line-ending and whitespace churn no longer
  block a doc as stale; missing files and malformed blobs stay blocking.
- Dashboard `start`/`export` short-circuit on scan findings before staging a
  build, and both runtimes gained the `hash_evidence` CLI for hashing a file
  or line range with raw/normalized/range variants.
- New Python/JS parity tests for cosmetic classification, evidence hash
  normalization, and evidence locators.

## 2.14.0 - Deeper source grounding, graph provider session lock

- The graph provider is now locked into the manifest once, automatically, by
  `manage_manifest.{py,js} init` (registry-priority pick; pass
  `--graph-provider <id>` to thread an explicit intake choice). Every later
  step — including spawned parallel writers — reads that lock from
  `manifest["graph"]` instead of re-detecting or re-asking; a manifest missing
  the lock self-heals via the new `set-graph` subcommand
  (`--provider`/`--force` to switch), and `status` reports the locked
  provider and flow.
- Writers re-ground required claims deeper: native graph-provider interface
  first, whole-file reads last, following the bounded source-analysis ladder;
  parallel workers receive the locked provider read-only and never call
  `precheck_graph` or `set-graph` themselves.
- Illustrations gain Mermaid `journey` (≤ 4 sections) and `timeline` forms,
  an ASCII fan-out ladder example, and matching `illustration_metrics`
  budgets in both runtimes.
- New tests for manifest `set-graph`, depth ladders, graph/flows, structure,
  and CLI parity.

## 2.13.1 - Dashboard `export` subcommand

- The static HTML export is now its own standalone `dashboard export`
  subcommand (`dashboard export --repo <repo>`) instead of
  `dashboard start --export`. It runs the same preflight/scan/reconcile/
  signature pipeline as `start`, then `next build` emits `index.html` per
  page under `<dashboard>/out/`; it takes no flags (`start` no longer
  accepts `--export`).
- `--skip-install` is gone: `start` and `export` always install the
  dashboard's npm dependencies when `node_modules` is missing.

## 2.13.0 - Manifest 3.2 with document descriptions

- Manifest schema bumped to `3.2`: every document entry gains a catalog-owned
  `description` (≤ 160 chars), seeded from the catalog `summary` at init,
  `migrate_metadata`, and `reconcile`.
- Generated documents now carry public `description` frontmatter; the
  dashboard reconciles it from the manifest, lints require a non-empty
  description on written documents, and the site emits per-page
  `<meta name="description">`.
- `migrate_metadata` upgrades manifest 3.1 (and 3.0) to 3.2 in place, seeding
  descriptions; any pre-3.0 shape is re-registered as 3.2.
- The dashboard reads only each file's frontmatter head (never the body) for
  metadata reconcile, route planning, and navigation ordering — bodies are
  read only for MDX conversion and link validation.
- `dashboard start --export` emits `index.html` per page (`trailingSlash`):
  `/docs` → `out/docs/index.html`, a page at `/docs/a/b` →
  `out/docs/a/b/index.html`; no more flat `docs.html` / `<page>.html`.

## 2.12.0 - Audience-aware presentation

- Routes now resolve an audience-aware presentation policy and manifests retain
  that policy with an optional per-document `presentation` override command.
  A meaningful presentation change returns an audited document to
  `in_progress`; legacy manifests hydrate without a forced rewrite.
- Repository source paths, line ranges, and blob hashes remain in provenance
  rather than reader-facing citations. Generated documents may instead use a
  compact `Related` footer linking to existing owning documentation.
- Added fenced-content roles and linting for source-code links, visible source
  locators, and high-confidence explanatory prose placed in code-oriented
  fences. Dashboard conversion now leaves links inside fenced examples intact.
- Flow, data-flow, architecture, BA, conventions, migration, and permissions
  contracts use the new presentation rules through targeted `2.12.0` revision
  markers; unaffected documents adopt the policy on their next revision.

## 2.11.0 - Legacy manifest re-registration

- `migrate_metadata` now re-registers **any** pre-3.0 legacy manifest (1.1
  `project_context` / `document_groups`, 2.0 flat `documents` with overlays,
  or any other shape) as 3.1: written documents are adopted as `generated`
  with provenance 2.0, bodies preserved, plan entries kept, never `complete`.
- `/docforge-dashboard` gained a three-option legacy-manifest gate — revise
  all, update metadata only (`migrate_metadata`), or stop; `--plan-only`
  previews the migration and `--auto-accept` never bypasses the choice.
- Python and Node peers stay equivalent; added adoption, dry-run,
  idempotency, and parity tests.

## 2.10.0 - Inline workflow execution

- Removed the optional Claude Code wrapper files and their dispatch paths.
  Precheck, grounding, flow analysis, document audit, and whole-tree review now
  always run through the existing inline workflow procedures.
- Simplified audit provenance to the single `cold-pass` mode across the
  manifest schema, Python and JavaScript tools, templates, and tests.
- Kept the complete `PRECHECK → ANALYZE → PLAN → WRITE → AUDIT → TRACK` flow
  identical across Claude Code plugin and Agent Skills installs.
- **Dashboard completion is now a required part of every run.** `/docforge`
  and `/docforge-revise` must start the dashboard (unless `--plan-only` or
  `--no-dashboard`) and report its URL in the final response; the contract
  lives in `rules.md`, both `SKILL.md` entrypoints, `workflows/revision.md`,
  and `workflows/validation.md` §7.
- **`AGENTS.md` renders in the dashboard.** Manifest-provenance
  (`provenance_mode: manifest`) root documents without YAML frontmatter are
  now included, routed to `/docs/root/<slug>`, and emitted with dashboard-only
  frontmatter, so `docs/agents` links to `../../AGENTS.md` resolve to
  `/docs/root/agents` instead of rendering a broken repository-relative link.
- **HTML comments no longer leak into the generated site.** Management
  markers such as `<!-- docforge-children:start -->` are stripped during
  conversion (outside fenced and inline code) while the content between them
  is kept; markers stay in source Markdown for scaffold re-expansion.
- **Sidebar labels are meaningful.** The flows section is titled `Flows`
  (catalog, template, and both flow renderers), and the JavaScript title
  extractor matches the Python peer by accepting only H1 headings.
- **Unresolved internal Markdown links fail the dashboard build** (targets
  normalizing inside `docs/` or to a repository-root `.md`/`.mdx` file);
  other unresolved targets remain warnings.

## 2.9.0 - Standalone core and dashboard simplification

- **`docforge` is now the required core bundle.** The dashboard capability
  (workflow, Python/Node runtime, and the Fumadocs app template) moved from
  `skills/docforge-dashboard/` into the shared cartridge
  (`skills/docforge/_shared/workflows/dashboard.md`,
  `runtime/dashboard/`, and the `dashboard` launcher pair under
  `runtime/cli/`). Installing only `docforge` is enough to plan, write,
  revise, and render documentation; `docforge-revise` and
  `docforge-dashboard` are thin optional entrypoints that declare the core
  dependency. Core files no longer dereference sibling skill directories.
- **Dashboard CLI simplified to three subcommands:** `start`, `status`,
  `stop`. The previous public `fingerprint`, `metadata`, `plan`, `build`,
  `validate`, and `serve` subcommands became internal stages of `start`.
- **`start` is one idempotent command:** reconcile metadata → compare two
  working-tree signatures → rebuild generated output when changed (or
  `--force`) → install dependencies only when missing → start (or reuse) the
  detached dev server → open the browser → exit.
- **Two signatures replace the old fingerprint.** `render_sig` hashes
  `docs/` file bytes, included root-document bytes, and the manifest
  projection that affects rendering (`id`, `title`, `path`, `status`,
  `write_order`); `shell_sig` hashes the app template, project name, and
  repository URL. Git `HEAD`, the flow index, and repository package files
  no longer trigger rebuilds. Both are working-tree hashes, so dirty or
  freshly generated docs invalidate immediately.
- **`start --force` regenerates generated output only** (`content/docs`,
  `public/docs-assets`, navigation, app shell, `.next`) and keeps
  `node_modules`; it does not reinstall dependencies.
- **Staged, validated swaps.** Conversion and navigation are written under
  `content/.staging/`, validated against the staged output (links, anchors,
  coverage, assets), and then swapped in atomically; a failed conversion or
  validation leaves the previous dashboard untouched.
- **Detached dev server.** `start` exits after the server is healthy; the
  server keeps running in the background until `dashboard stop` (which stops
  the whole process group). The attached-serve signal handling is gone.
- Updated tests: `tests/test_dashboard.py` covers start idempotency,
  plan-only routing and duplicate detection, conversion, `--force`,
  failure-preserves-previous-build, signature parity/sensitivity, and the
  detached serve/stop lifecycle; `tests/test_structure.py` asserts the core
  bundle carries the dashboard capability with no sibling runtime
  dependencies and that the entry skills declare the core dependency.

## 2.8.0 - Revise re-ask deltas and attached dashboard serve

- Revise re-asks persisted manifest choices as changes only: current tier,
  profiles, and audiences are displayed as the baseline, and controls offer
  `Change to` for tier and `Add` / `Remove` for profiles and audiences —
  never a `Keep` option or re-selection of current values; an empty change set
  preserves the manifest only after explicit confirmation.
- `dashboard serve` now stays attached to the terminal and stops the whole
  server process group on `Ctrl+C`, `Ctrl+Z`, terminal closure, or termination
  signals (graceful stop with forced escalation), clearing PID/port state;
  Python and Node peers stay equivalent and are covered by an end-to-end signal
  test in `tests/test_dashboard.py`.

## 2.8.0 - Dashboard (local Fumadocs site)

- Added `/docforge-dashboard` (`skills/docforge-dashboard/SKILL.md`,
  `commands/docforge-dashboard.md`, registered in both plugin manifests)
  backed by the `dashboard` runtime CLI (Python/Node parity) with
  subcommands `metadata`, `fingerprint`, `plan`, `build`, `validate`,
  `serve`, `stop`, and `status`.
- The dashboard runtime is **self-contained under `skills/docforge-dashboard/`**
  (workflow, launchers, and the Fumadocs app template); the shared cartridge
  keeps only what all skills consume (rules, flags, retrieval, provenance
  codec, `_util`). The dashboard declares its own `.docforge/.gitignore`
  rule (`dashboard/`) instead of extending the shared rule list.
- The generated site lives in `.docforge/dashboard/` (git-ignored via the
  new `dashboard/` rule in `DOCFORGE_GITIGNORE_RULES`): its own
  `package.json`, lockfile, and `node_modules`; every npm command runs with
  `--prefix`, and the repository's own package files are hashed before and
  after install and must not change.
- `dashboard metadata` reconciles each written document's public `id` /
  `title` frontmatter and `docforge_provenance.doc_id` / `path` against the
  manifest, preserving the Markdown body byte-for-byte.
- `dashboard build` scaffolds a pinned Fumadocs shell (Next.js 16, Fumadocs
  UI/MDX, Tailwind 4, local search, Mermaid), converts `docs/` Markdown to
  MDX with code-fence-aware escaping and route-ledger link rewriting, writes
  one `meta.json` per folder, and copies bounded image assets; converted
  content is staged and swapped atomically.
- `dashboard validate` gates duplicate URLs, meta coverage, internal links
  and heading anchors, assets, and the docs index; `dashboard serve` binds
  a localhost-only dev server, reuses a healthy recorded server, and records
  PID/port in `.docforge/dashboard/.docforge-dashboard.json`.
- The fingerprint (HEAD + manifest + flow-index + `docs/` + template + root
  package hashes) is byte-identical between the Python and JS peers; an
  unchanged fingerprint performs no content writes and reuses the server.
- Added `tests/test_dashboard.py` (9 tests, Python/Node parity asserted).

## 2.8.0 - Enforced coding-agents kernel lint

- Wired the orphaned `lint_agents_kernel` into the completion gate: the
  document-audit mechanical gate now runs it in place of `lint_document` for
  AGENTS.md-shaped outputs, documented end to end in `document-audit`,
  `ownership`, the coding-agents audience profile, and `writing.md`; fixed
  shims remain literal and unlinted by design.
- Strengthened `lint_agents_kernel` (Python/Node parity) with hard rubric
  defects `title-shape` (1–4 words, Title Case, no trailing `?`) and
  `tagline-length` (5–12 words), plus advisory warnings `weak-tagline`,
  `low-negation-ratio`, and `bullet-length` scoped to guidance sections
  2/5/6 — the shipped kernel template stays clean.
- Added a topology-derived "Non-obvious conventions" evidence recipe to the
  coding-agents audience profile (§5 no longer a vibe: every bullet traces to
  a graph edge, linked instead of restated when a human doc owns it).
- Added `tests/test_agents_kernel.py` (clean golden fixture + per-check dirty
  fixtures, Python/Node parity asserted).

## 2.8.0 - Two-mode fluency and de-duplication pass

- Standardized mode terminology to canonical "fresh start" for `/docforge` vs "revise" for `/docforge-revise`.
- Harmonized the interactive question pack across `intake.md`, `revision.md`, and `docforge-revise/SKILL.md` to identical order, profile dimensions (`shape / platform / framework / concern`), and gate sentence (`never proceed on silent defaults`).
- Smoothed prose in `intake.md` and `docforge-revise/SKILL.md`, aligned flag table descriptions with `flags.md`, and mirrored cross-references between the two skills for symmetry.

## 2.7.0 - Model-native depth ladders

- Added model-depth routing, evidence locators, illustration budgets, deterministic PROV core projection, and the conditional STRIDE interaction register.
- Normalized target depths and added body-preserving metadata reconciliation prerequisites.

## 2.6.1 - Trusted sources and root README policy

- Plan reporting names only READY graph providers; Understand Anything,
  GitNexus, and CodeGraph are equally trusted for `code_graph`. Native
  `flow_graph` remains UA/GitNexus only; CodeGraph-only runs schedule
  Docforge-derived flows.
- Existing root `README.md` requires explicit migrate / skip / rewrite —
  no silent overwrite with the `root_readme` template.
- Keep a single tree for Agent Skills and Claude Code: root [`skills/`](skills/)
  and [`agents/`](agents/). Marketplace entry uses an HTTPS git URL plugin
  source (`https://github.com/jonaskahn/docforge.git`) so installs do not
  require SSH host keys; `"source": "./"` failed to register in Claude Code.
- Dropped the experimental `docforge-plugin/` sync mirror to avoid duplicating
  the cartridge in git.
- Register both skills explicitly and add [`commands/`](commands/) wrappers so
  Claude Code exposes `/docforge` and `/docforge-revise` (plugin skills alone
  appear as `/docforge:docforge` and `/docforge:docforge-revise`).

## 2.6.0 - Claude-native Docforge agents

- Added six read-only, Claude-plugin-native `docforge-*` agents: audit,
  tree-review, graph-precheck, catalog-validator, flow, and ground.
- Agents are thin advisory wrappers over `_shared`; workflows retain inline
  fallbacks so non-Claude hosts follow the same canonical procedure.

## 2.5.0 - Context-bounded repository refactor

Internal reorganization for agent retrieval efficiency. No behavior change
for existing users; see "Stable public interfaces" below for what did not
move.

### Internal path changes

- **Catalog records** moved from one flat `.metadata/catalog/types/*.json`
  directory into `.metadata/catalog/documents/<group>/*.json` (large groups)
  or `.metadata/catalog/documents/*.json` (small groups: root, contributing,
  flows, records). Every record gained `summary`, `contract_file`, and
  `template_file` (renamed from `scaffold_template`); `record` paths are now
  explicit in `index.json` rather than derived by convention.
- **Content artifacts** (contracts, writing-craft instructions, output
  templates) moved from three flat directories
  (`references/catalog-contracts/`, `instructions/`, `assets/templates/`)
  into `content/<group>/` per document group, with a `content/shared/` for
  artifacts used by more than one group. Groups with six or more files of one
  kind get a `contracts/`, `instructions/`, or `templates/` subfolder;
  smaller collections stay flat with a `.contract.md`/`.instruction.md`/
  `.template.md` suffix to disambiguate same-named files.
- **`SKILL.md`** shrank from ~525 lines to under 180 by moving its detailed
  procedure into `workflows/{intake,planning,writing,revision,validation,
  tools}.md`. `SKILL.md` now holds only what must always be loaded: what
  Docforge does, the code-graph precondition, provider sufficiency, safety
  boundaries, invocation routing, and the retrieval protocol.
- **References** reorganized: graph-provider docs into `references/graph/`,
  audience/shape guides into `references/profiles/`; both gained routers.
- **Runtime implementations** moved from a single flat `scripts/` directory
  into `runtime/<subsystem>/` (`common`, `catalog`, `graph`, `flows`,
  `manifest`, `documents`, `portfolio`, `validation`, `migrations`).
  `scripts/*.py`/`*.js` are now thin launchers that import and delegate to
  the runtime implementation — never business logic.
- Generated routers (`.metadata/catalog/README.md`,
  `documents/README.md`, and category `index.json`/`README.md` pairs) are
  produced deterministically by the new `scripts/generate_indexes.py`/`.js`.

### Stable public interfaces (unchanged)

- Every existing `scripts/*.py`/`*.js` entrypoint, its flags, and its exit
  codes.
- `query_catalog`'s existing modes (`--tier`, `--id`, `--ids`, `--profile`,
  `--applicable`, `--legacy`, `--validate`) — serialized output is
  byte-identical to 2.4.0, including for the now-renamed `template_file`
  field, which still prints as `scaffold_template` in these modes.
- Manifest schema `3.1` and provenance schema `2.0` — unchanged.
- Document IDs, type IDs, profile IDs, group IDs, tier names, and capability
  names — unchanged.
- Generated documentation paths in downstream repositories — unchanged.

### New

- `query_catalog --category <group>` and `query_catalog --route <id>` —
  resolve a document's contract/instruction/template/workflow in one call.
- `generate_indexes.py`/`.js --write`/`--check` — regenerate or verify
  catalog routers deterministically.
