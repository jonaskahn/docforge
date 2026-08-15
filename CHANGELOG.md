# Changelog

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

## 2.16.0 - Cosmetic-drift detection via normalized and range evidence hashes

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

## Dashboard (local Fumadocs site)

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

## Enforced coding-agents kernel lint

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

## Two-mode fluency and de-duplication pass

- Standardized mode terminology to canonical "fresh start" for `/docforge` vs "revise" for `/docforge-revise`.
- Harmonized the interactive question pack across `intake.md`, `revision.md`, and `docforge-revise/SKILL.md` to identical order, profile dimensions (`shape / platform / framework / concern`), and gate sentence (`never proceed on silent defaults`).
- Smoothed prose in `intake.md` and `docforge-revise/SKILL.md`, aligned flag table descriptions with `flags.md`, and mirrored cross-references between the two skills for symmetry.

## 2.7.0 - Model-native depth ladders

- Added model-depth routing, evidence locators, illustration budgets, deterministic PROV core projection, and the conditional STRIDE interaction register.
- Normalized target depths and added body-preserving metadata reconciliation prerequisites.

## 2.6.1 — Trusted sources and root README policy

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

## 2.6.0 — Claude-native Docforge agents

- Added six read-only, Claude-plugin-native `docforge-*` agents: audit,
  tree-review, graph-precheck, catalog-validator, flow, and ground.
- Agents are thin advisory wrappers over `_shared`; workflows retain inline
  fallbacks so non-Claude hosts follow the same canonical procedure.

## 2.5.0 — Context-bounded repository refactor

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
