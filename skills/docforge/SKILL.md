---
name: docforge
description: >-
  Design and generate a repository's documentation set — the docs/ tree, README and ARCHITECTURE, decision records (ADRs), a known-limitations register, a third-party dependency inventory, security policy, API error catalogs, data contracts and runbooks, AI-agent context files (AGENTS.md, CLAUDE.md, docs/agents/), plus audience overlays that speak to Business Analyst (BA) and Product Owner (PO) readers. Grounds every document in a knowledge-graph analysis of the actual source before writing, so nothing is invented, and stamps each document with git-hash provenance so staleness is decided by comparison, not by re-guessing. Host-neutral — works on any git host and never hardcodes one forge's paths, and checks for child repos (declared submodules or nested/vendored repos) before any multi-repo review. Use this skill whenever the user mentions documenting a repo or codebase, a docs folder, README or ARCHITECTURE files, ADRs or decision records, onboarding docs, runbooks, known limitations, dependency or licence inventories, technical due diligence or audit readiness, standardizing documentation across several repos, documentation for a Business Analyst or Product Owner, business rules or process flows or requirements traceability, feature catalogs or release notes or success metrics, generating AGENTS.md or CLAUDE.md or making a repo AI-agent-ready, or whether existing generated docs have drifted from the code — including loose phrasings like "write docs for this project", "our repo has no documentation", "make this repo legible to a new engineer", "docs for BA/PO", "which docs are stale", "should we regenerate this", "generate an AGENTS.md", or "does every repo in here have docs". Supports invocation flags to control scope and pacing — "--revise all" / "--revise <area>" (regenerate only stale sections, whole tree or one area), "--auto-accept" (show each plan/part but skip confirmation pauses), "--plan-only" (scaffold + manifest, no content), "--resume" (continue from manifest state), "--status" (print progress only) — see Step 0.
---

# Docforge — Repository Documentation Architect

Documentation fails in two directions: too little (nobody can onboard, diligence stalls) and too much of the wrong kind (a hand-written reference that drifts from the code and quietly becomes a liability). This skill produces the shape that survives — a small, predictable spine that every repo shares, plus overlays chosen by what the repo actually is and who has to read it.

Three rules organize every decision here. **Separate documents that change once or twice a year from documents that change every release**, and let generated artifacts carry the facts that machines can verify. **Read the codebase through a knowledge graph before writing a word about it** — the difference between documentation that is trusted and documentation that is quietly ignored is whether its claims are true. And **record which code each claim came from**, so "has this drifted?" is answered by a hash comparison instead of a re-read and a guess.

## Non-negotiables

Six rules that hold regardless of tier, repo type, ecosystem, or audience. Violating them is what makes documentation rot.

1. **Never invent — and never punt what you can derive.** Every claim must be traceable to the knowledge graph, to code, to config, to commit history, or to something the user told you. A confidently wrong doc costs more than a missing one, because readers stop trusting the whole set. But the far more common failure is the opposite: leaving a section for "the team to fill later" when the answer was in the source all along. **You generate the complete set; a human reviews it for accuracy afterward.** "Complete" is about fill-state, not delivery cadence: it means no derivable fact is ever punted to a human, whether you write the whole tree at once or part by part under the plan-first cadence (Step 0). So there are exactly two fill states, and no third:
   - **Derivable** — anything obtainable from the graph, source, config, or history (retry policy, config vars, business rules, failure modes, the flow's steps). Write it *in full*, now. Handing a derivable fact to a human is a defect, not humility. If you are tempted to punt, query the graph again (`references/source-analysis.md`) — the answer is almost always retrievable.
   - **Externally unknowable** — a fact that lives in no source you can read: a disclosure contact address, an on-call rotation, a production URL, an org-set SLA number, a team/owner name, a roadmap date. Write the entire surrounding sentence and leave only the atomic unknown as a **typed placeholder token** — `<SECURITY_CONTACT>`, `<ONCALL_ROTATION>`, `<PROD_BASE_URL>`, `<SLA_RESPONSE_HOURS>`, `<TEAM_OWNER>`: angle-bracketed, `UPPER_SNAKE_CASE`, semantically named. A token stands in for one *value*, never a paragraph — its shape structurally forbids punting a whole section. Do not use the retired `> TODO(owner): …` prose form; it invited exactly the "team fills this later" scaffold this skill exists to prevent.
2. **Analyse before writing.** The knowledge graph is a precondition, not an optimization. See "Source analysis" below and `references/source-analysis.md`.
3. **Host-neutral by default.** Nothing in generated prose names a specific forge. Write "the issue tracker", "the CI pipeline", "a merge request or pull request". Forge-specific paths are confined to the one place described in `references/host-neutrality.md`.
4. **Everything lives under `docs/`.** Repo root carries only the handful of files that ecosystem tooling and package registries look for by convention, and those are thin pointers into `docs/`. See "Root vs docs/" below. The `agent-context` overlay (`references/overlay-agent-context.md`) adds further named exceptions in this same category — `AGENTS.md`/`CLAUDE.md`/`CLAUDE.local.md` at root (a capped kernel that links into `docs/agents/` for depth, the same thin-pointer shape) and `.claude/`, `.cursor/`, `.github/`, `.codex/`, `.windsurf/` as tooling-config directories in the same non-`docs/` bucket as `.docforge/`.
5. **Stamp provenance in the same pass you write.** Every generated document records the specific source files (by git blob hash) each section draws from. Staleness is later decided by hash comparison, never by re-reading and re-guessing; a change in one recorded file regenerates the section that cites it, not the whole document. See `references/provenance-tracking.md`.
6. **Write for durability, not for the current code.** Describe what the logic *does* at the flow and behaviour level; a same-behaviour refactor must not falsify a document. Never paste code, never link a line number, never anchor a claim to an internal symbol a rename would break — reference files and modules by path instead. State every fact once and link to it; never duplicate it across documents or audience folders. See `references/document-composition.md`.

## Precheck — mandatory before every invocation

**This runs first, before any other step, every single time.** Both required graph files must be present and ready before docforge proceeds — from either of two sources, checked in priority order. See `references/graph-sources.md` for the full capability-to-source dispatch table.

Every script in `scripts/` ships as both a Python file (`scripts/<name>.py`) and a Node.js file (`scripts/<name>.js`) — same flags, same output, same exit codes, standard-library/built-ins only on either side, no install step. Examples below show the Python form; use `node scripts/<name>.js …` with identical flags if Python 3 is not available (or vice versa). Pick whichever runtime is already on the machine — `python3 --version` / `node --version` to check.

### Run the graph check first — it reports READY/MISSING and, on a miss, which source to build from

```
python scripts/check_preconditions.py --repo <path> --need domain
```

This single call reports READY/MISSING for the knowledge graph *and* the domain graph — no need to run it twice. It checks `.ua/knowledge-graph.json` / `.ua/domain-graph.json` (or their legacy `.understand-anything/` counterparts) regardless of which tool produced them, then branch on what it prints:

**READY for both:** Precheck passes — proceed to Step 1. Skip the rest of this section entirely; which source built the graph does not matter downstream.

**MISSING, and the script's output shows "GitNexus index detected":** a GitNexus index already exists for this repo — building `.ua/*.json` from it is usually cheaper than a first `/understand` run. **Ask for explicit permission first**, same rule as below. If the user agrees, follow `references/gitnexus-bridge.md` end to end (it ends with the same re-check above). If they decline, fall through to the understand-anything path.

**MISSING, and no GitNexus index exists:** fall back to understand-anything.
1. **Skill-callable check: `understand-anything:understand` and `understand-anything:understand-domain`.** Confirm that both skills appear in your own available-skill listing. The command name varies by agent (slash command `/understand`, Codex `$understand`, or plain language where no command exists: *"use the understand skill"*). If you don't see the skill listed, try to load it (via Skill tool, plugin registry, or your agent's load/enable mechanism) and re-check the listing.
   - **If genuinely absent after load attempt:** Stop. Tell the user to install the `understand-anything` plugin *or* set up GitNexus for this repo (`npx gitnexus analyze` to index, `npx gitnexus setup` to connect the editor — see `references/gitnexus-bridge.md` Step 0), then return here. Do not take any further docforge step without one of the two.
2. **Knowledge graph missing:** the user must generate it. **Ask for explicit permission first** before running `/understand` yourself — do not invoke it unprompted. If the user declines, stop and wait. If they agree, run `/understand` (or `/understand <path>` to scope to a subdirectory; large first runs consume tokens — say so before starting), then re-run the check above to confirm READY before continuing to the domain-graph branch.
3. **Domain graph missing** (knowledge graph READY): **do not offer to run `/understand-domain` yourself** — tell the user they must run it, using the exact command the script prints. Stop and wait; no document of any kind is written until this exists.

### Universal requirement — no fallback

Both `.ua/knowledge-graph.json` and `.ua/domain-graph.json` (or their legacy `.understand-anything/` counterparts) are **required for every docforge invocation**, regardless of tier, scope, or which documents are planned, and regardless of which of the two sources above built them. This means: architecture/spine documents, flow documents, product content, BA/PO overlays, and agent-context files all require the domain graph. No inspection fallback exists for architecture-only work anymore — "no fallback" means the graph requirement itself can never be skipped, not that only one tool may satisfy it.

### Operational notes on graphs

Every document in the tree makes claims about the source. The knowledge graph replaces guessing with retrieval: it gives you the module map, the architectural layers, the call and import edges, the business domains and flows, and a queryable interface for everything the graph does not already state.

- **Check for existing graphs first.** If `.ua/knowledge-graph.json` and `.ua/domain-graph.json` are both present and newer than the last substantive commit, use them as-is. If either is stale, `/understand` and `/understand-domain` update them incrementally rather than starting over — re-runs are cheap. If the graph came from GitNexus instead, refresh via `references/gitnexus-bridge.md`'s steps (`npx gitnexus analyze` then re-run the bridge) — see `references/graph-sources.md` for the full per-source refresh mapping.
- **Large repos**: scope the analysis to the part being documented — `/understand src/frontend` — rather than paying for a full pass you do not need. First runs on large codebases consume significant tokens; say so before starting one.
- **After any regeneration**, re-run the Precheck to confirm freshness:
  ```
  python scripts/check_preconditions.py --repo <path> --need domain
  ```
- **Read the graph directly** once confirmed ready. `python scripts/graph_extract.py --graph .ua/knowledge-graph.json --summary` prints the module inventory, layer assignment and external dependency list in a form that seeds the code map and the dependency inventory.

Then, whenever a document needs a fact the graph does not already state, query rather than infer. Full command-to-document mapping in `references/source-analysis.md`; the essentials:

| You are about to write | Get the facts from |
|---|---|
| `architecture/high-level.md` (context, blocks, boundaries) | the graph itself — module map, layers, edges |
| `architecture/low-level.md`, `architecture/concepts/<subsystem>/` (deep mechanism) | `/understand-explain <path>` per significant subsystem — **required** for depth, not optional |
| `architecture/data-flow.md` | `/understand-domain` for flows and steps; `/understand-chat` for a specific path |
| `flows/<flow>.md` (plain steps, L1) | `/understand-domain` — enumerate flows first; each flow is a flat file, promoted to a folder only when a deep-dive is written in the same pass (see `references/document-composition.md`) |
| `flows/<flow>/business-analyst.md` (rules, once promoted) | `/understand-chat "what business rules gate <flow>"` |
| `flows/<flow>/engineering.md` (mechanism, once promoted) | `/understand-explain <flow module>` |
| `product/overview.md`, `capabilities.md` | `/understand-domain` — business domains in the code's own terms |
| `product/product-owner/*` (metrics, release notes) | `/understand-domain` for the feature set; `/understand-diff` and `git log` merge commits for release framing |
| `engineering/setup.md` | `/understand-onboard`, then verify every command by running it |
| `architecture/dependencies.md` | graph import edges, then `/understand-chat` for failure handling per integration |
| `architecture/tech-debt.md`, `constraints.md` | `/understand-chat` for TODO/FIXME clusters, hard-coded bounds, scale ceilings; `git log` for why |
| `reference/configuration.md` | `/understand-chat "which environment variables does this read, and where"` |
| `reference/limitations.md` | `/understand-chat` for unhandled cases, TODO and FIXME clusters, hard-coded bounds |
| Decision records | `/understand-chat "why …"` cross-checked against `git log` |
| Any overlay document (routes, error codes, datasets) | targeted `/understand-chat` questions — see the overlay reference |

Full depth-to-command mapping in `references/depth-and-audience.md`.

Two habits make this pay off. **Ask narrow questions** — "which modules write to the database, and through what" retrieves cleanly where "explain the architecture" returns prose you then have to verify. And **treat the answers as evidence, not as prose to paste**: they are a source to write from, in the document's own voice and structure.

## Workflow

### Step 0 — Interaction mode: structure first, then detail, then write one part at a time

**This cadence is mandatory and never relaxes — not when the user says "just generate everything," not when they say "no need to confirm." Every run, without exception: read enough context to plan, build the plan, show the plan, get confirmation, *then* write. There is no path that skips the plan-and-show step.** A user who asks you not to confirm is asking you not to *interrupt* — you still plan and still show the plan; you may then proceed without waiting only if they explicitly waived the pauses (`--auto-accept`, below), and even then you write part by part with status tracked, never a silent whole-tree dump.

If the user named exactly one document ("regenerate the security policy", "just the setup doc"), write that and skip to the relevant step — but still re-ground it first (Step 5). Everything below governs any open-ended request ("document this repo", "our repo has no docs").

#### Invocation flags

These change *scope* or *pacing* — never which non-negotiables apply. A flag can skip a pause; none skips the plan-and-show itself, the re-ground step, or fill-completeness.

| Flag | Effect |
|---|---|
| `--revise all` | Skip Gate 1/2 planning (the tree already exists). Run `check_provenance.py` across the full manifest, regenerate every `PARTIAL` section, and re-ground in full any document reporting a document-level `STALE` (adopted, no section granularity) — per "Updating existing docs" below. |
| `--revise <area>` | Same provenance check, scoped to one manifest entry or group — `--revise security`, `--revise flows/checkout`. Only that entry's sections are checked and, if stale, regenerated. |
| `--auto-accept` | Do not wait at any pause. Gate 1's tree, Gate 2's per-document detail, and each finished part are still displayed in full, in order — only the *wait-for-confirmation* step is skipped, not the display. **The independent per-document audit still runs** (it gates `complete`, not the user pause — see Step 0's write loop and `references/document-audit.md`). Written parts are still tracked in the manifest one at a time; a stale or wrong part discovered later is corrected the normal way (re-ground, rewrite that part), not silently. |
| `--plan-only` | Stop after Gate 2: manifest populated (`planned` status throughout), empty scaffold on disk. No content written this run. |
| `--resume` | Read `.docforge/manifest.json` and continue from its first `planned` or `in_progress` entry instead of restarting Gate 1. |
| `--status` | Print `manifest_sync.py status` and stop — no scaffolding, no writing. |
| `--no-agent-context` | Opt out of the `agent-context` overlay (Step 3), which `docs_scaffold.py`/`.js` and `manifest_sync.py`/`.js` otherwise add by default on every run. |

Flags compose: `--revise api --auto-accept` regenerates only the API overlay's stale sections, showing each before moving to the next without pausing. `--auto-accept --plan-only` shows the full plan and populates the manifest without pausing, then stops before content.

**Do the graph analysis (Steps 1–3) before any gate.** You cannot plan a structure you have not grounded, and you cannot detail a document whose facts you have not retrieved.

**Gate 1 — Structure (empty layout, tracked in metadata).**
1. **Preview the tree without writing:** `python scripts/docs_scaffold.py --repo <path> --tier <n> --overlay <o> --dry-run`. This prints every file the chosen tier + overlays imply — the layout, no content.
2. **Present that layout** to the user: the folder tree plus one line per document — name, path, and what it will cover (name the concrete subsystem/flow, per `references/document-catalog.md`). State tier and overlays once at the top. Group by area (architecture, flows, product, operations, reference, security, records).
3. **Record the plan in `.docforge/manifest.json`** — `python scripts/manifest_sync.py init --repo <path> --tier <n> --name <repo>` writes it with every spine document `status: "planned"`. Add discovered flows and overlay documents with `manifest_sync.py add`. This is the durable tracking record: which documents the plan contains, where each lives, and where each stands. (`.metadata/manifest.json` is the shape it follows.)
4. **Pause for explicit confirmation of the structure.** The user may add/remove documents, reorder, change tier/overlays, or propose overlays. Fold feedback into the manifest and re-present if the change is significant.
5. **On confirmation, create the scaffold for real** (drop `--dry-run`). The empty files now exist; the manifest tracks each as `planned`.

**Gate 2 — Content detail (what each document will actually say).**
Before writing prose, present — per document, in dependency order — what it will contain: the must-present elements from its `references/document-catalog.md` contract, the target depth, and the sources you will draw from. This is where the user steers depth and where you **propose** additions or cuts rather than assuming. Confirm or adjust. For a small set, fold this into Gate 1's presentation; for a large tree, do it per area so the user is never handed everything at once.

**Then — write one part at a time, in dependency order (Step 5).** For each document, in order:
- Set its manifest status to `in_progress` — `python scripts/manifest_sync.py set --repo <path> --id <id> --status in_progress` — and open a `generation-status.json` runtime entry (`querying` → `writing`).
- **Re-ground before you write.** Retrieve every must-present element for that document (`references/document-catalog.md`) from the knowledge graph, the domain graph, and the code. If a needed fact is not yet in the graph, query it — a narrow `/understand-chat`, an `/understand-explain <path>`, or direct inspection — *before* writing, not around it. Never write on thin context: if the source genuinely cannot answer a required element, that atomic value becomes a typed `<UPPER_SNAKE>` token (non-negotiable 1); everything around it is still written in full.
- Write to deep-dive depth (Step 5, `references/depth-and-audience.md`), stamp provenance as you write, and set manifest status `generated` (`manifest_sync.py set … --status generated`; runtime `complete`). A `generated` document is *written*, not yet *done*.
- **Audit it independently before presenting it as done (`references/document-audit.md`).** Spawn a **fresh subagent that did not write this document** and give it only artifacts — the finished file, its `document-catalog.md` contract, its target depth, the single-document quality-bar subset, and the sources its frontmatter cites. It returns a structured verdict (`assets/templates/audit-report.md`).
  - **PASS** — present the finished part *together with its verdict* and **pause** for the user to confirm or redirect before the next. Fold feedback on part N into parts N+1…
  - **FAIL, derivable gap** — set `needs_review`, re-ground and rewrite that document, then **re-audit**. It is never presented as done while a derivable gap stands, and a derivable gap is never waived to a human.
  - **FAIL, external gap only** — the atomic unknown becomes a typed `<UPPER_SNAKE>` token (or the user's explicit waiver is recorded), then it PASSes.
  - This audit is not optional and no flag skips it: `--auto-accept` skips the user's *pause*, never the audit (the same rule that already forbids skipping the plan-and-show).
- After the user accepts a part, set its manifest status to `complete`; anything they flag stays `needs_review`. `manifest_sync.py status --repo <path>` prints the plan and the remaining count at any time.

**Fill-completeness never bends (non-negotiable 1).** Every part you hand over is *complete* — no punted derivable facts, no unfilled `{{…}}` scaffolds, only typed `<UPPER_SNAKE>` tokens for genuinely external values. The gates govern *structure, scope, and ordering*; they never license a half-filled document. The goal is a reviewable, steerable stream — not a thirty-file dump the user must audit at once, and not a scaffold they must finish.

#### `.metadata/` templates and the two tracking files

The `.metadata/` directory holds the templates and schemas that drive Step 0. Two of them are *tracking* files you copy into the target repo's `.docforge/` and update as you go — they answer different questions and use different status vocabularies:

- `manifest.json` → the shape of `.docforge/manifest.json`, which `scripts/manifest_sync.py` writes and maintains. The **durable plan and fill-state** of the whole tree: one entry per planned document, its group, path, template, and `status` (`planned` → `in_progress` → `generated` → `needs_review` → `complete`, or `skipped`). This is the record you present at Gate 1 and update (via `manifest_sync.py set`) as each part lands. Also carries per-section provenance once written (see `references/provenance-tracking.md`). Its `project_context.tier` is stored under a different vocabulary than Step 2's table: `1 — Spine` / `2 — Diligence` / `3 — Portfolio` (the CLI's numeric `--tier`) are recorded as the strings `"core"` / `"standard"` / `"extended"` respectively — the same three tiers, spelled differently for storage.
- `generation-status.json` → the **live session log** while you write: per document `status` (`planned` → `querying` → `writing` → `complete`, or `skipped`), timing, tokens, and any error. Ephemeral; the manifest is the record that outlives the session. **The token `complete` means different things in the two files** and they must not be equated: runtime-`complete` means "finished writing" (the doc is now `generated` in the manifest and awaits its independent audit); manifest-`complete` is the *later* state a document reaches only after it passes the audit and the user accepts it. Runtime-`complete` therefore maps to manifest-`generated`, never straight to manifest-`complete`.
- `manifest-schema.json` / `status-schema.json` — schemas validating the two above.
- `document-templates.json` — maps each document type to its instruction file and required data sources (a craft pointer; the content contract is `references/document-catalog.md`). `template-schema.json` validates it.

Manifest document paths must match the taxonomy in `references/docs-tree.md` and what `scripts/docs_scaffold.py` emits — they are the same tree seen from the plan side and the disk side.

### Step 1 — Build the graph, then read the repo

Run the analysis above, then fill the gaps it does not cover:

- **Manifests and build files** — `pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`, `pom.xml`, `*.csproj`. Version pins and dependency ranges come from here, not from the graph.
- **Repo type signals** — a web framework, an HTTP server, DAG or scheduler definitions, a published package config, infrastructure-as-code, embedded business logic (validation rules, approval thresholds, eligibility conditions). These select your overlays; the graph's layer assignment usually makes them obvious.
- **What documentation already exists** — an existing `README`, `docs/`, wiki exports, comments that read like design notes, ADR-ish files. Existing content is evidence about what people needed to write down; migrate it, do not replace it — see "Migrate pre-existing documentation" immediately below.
- **Operational reality** — CI config, container and deploy manifests, and the environment variables the code actually reads.
- **History for the "why"** — `git log` on architecturally significant paths, and merge commits with substantive messages. This is where backfilled decision records come from, and it is the one thing the graph cannot supply.
- **Business flows** — the Precheck already confirms both graphs exist before this step (see "Precheck" above). Read `/understand-domain`'s output to enumerate the domains, flows and steps in the code's own terms. That list *is* the set of flow documents to build under `docs/flows/` — never hand-type it, since the point of the analysis is to surface flows a writer would miss. Each flow starts as a flat file (`docs/flows/<flow>.md`); it is promoted to a folder only when you write real audience depth for it in the same pass. See `references/document-composition.md`.
- **Child repos** — before any multi-repo work, and as a cheap sanity check otherwise, run `python scripts/discover_repos.py --root <path>`. It reports declared submodules and, more importantly, nested repos present on disk but *not* declared in `.gitmodules` (vendored copies, `git subtree` merges, hand-cloned submodules). For single-repo work this just confirms scope; for diligence it is load-bearing — see Step 2 and `references/diligence-collection.md`.

#### Migrate pre-existing documentation — before Gate 1, when the repo has any

This is the **first docforge run** against a repo that already has hand-written docs (a `README`, a `docs/` tree, wiki exports, design-note-shaped comments, ADR-ish files) that carry no docforge provenance yet. Do this before Gate 1 presents its tree, so the plan the user confirms already reflects what's carried over, what's net-new, and what's being archived — not a scaffold that silently skips every path that happens to already exist. Full procedure: `references/docs-tree.md` §6 "Migrating an existing docs folder". In brief:

1. **Inventory** every existing document — path, last-modified date, one-line summary of what it covers.
2. **Classify** each as current-and-accurate / stale-but-salvageable / obsolete / **merge-candidate** (two or more documents covering the same ground that should become one).
3. **Map** surviving documents to their taxonomy slot (`references/docs-tree.md`'s placement table); split a document that serves two audiences rather than filing it under one.
4. **Present the classification to the user and get an explicit decision before touching anything** — one line per old document: keep-in-place / migrate-to-`<slot>` / merge-into-`<target>` / archive / delete-outright. Never auto-archive, auto-merge, or silently drop a document on the strength of your own classification; "obsolete" and "stale" are your proposal, not a verdict the user already gave. Fold this decision into Gate 1's presentation rather than running it as a separate silent pass.
5. **Leave a forwarding pointer** at any old path something external still links to.
6. **Archive**, per the user's decision, genuinely obsolete material under `docs/_archive/<year>/` with a `README.md` explaining nothing inside is maintained — never delete design history outright unless the user explicitly says delete; `docs_scaffold.py --audit` already excludes `_archive/` from its checks.
7. **Merge**, per the user's decision, documents they confirmed as duplicates into the single surviving target, then archive (not delete) the superseded originals so the merge is reversible.

This is a distinct scenario from "Updating existing docs" (below): that section refreshes docs that **already carry docforge provenance** from a prior run, using hash comparison. This procedure runs once, on first contact with a repo's own hand-written docs; every later run on the same repo uses the provenance-hash path instead.

### Step 2 — Choose a tier

Documentation weight should be proportionate to team size and external scrutiny; heavy structure on a two-person repo costs more than it returns.

The numeric `--tier {1,2,3}` the CLI takes is stored in the manifest as a **string** — `1 → "core"`, `2 → "standard"`, `3 → "extended"` (`project_context.tier`, and the enum in `.metadata/manifest-schema.json`). Same three tiers, one spelling for the command line and one for storage.

| Tier (CLI → stored) | When it fits | What gets built |
|---|---|---|
| **1 — Spine** (`--tier 1` → `"core"`) | Any repo. Small teams, internal tools, early projects | Root pointers, `docs/README.md` index, `docs/architecture/high-level.md`, `docs/engineering/setup.md`, `docs/reference/limitations.md`, `CHANGELOG` |
| **2 — Diligence** (`--tier 2` → `"standard"`) | Repo has external consumers, paying customers, or a compliance or audit surface | Tier 1 + `docs/architecture/decisions/`, `docs/architecture/dependencies.md`, `docs/security/`, `docs/operations/runbooks/`, contribution docs |
| **3 — Portfolio** (`--tier 3` → `"extended"`) | Several repos reviewed as one system; fundraising, acquisition, vendor assessment | Tier 2 across every repo + a cross-repo portfolio layer (`references/diligence.md`) |

State the chosen tier and the reasoning in one sentence before generating. If the user gives a deadline-driven signal ("we're in diligence next month"), invert the order: build the Tier 3 skeleton and the security and dependency documents first, backfill the rest after.

**Tier 3 discovers its collection before it builds anything.** A multi-repo review's scope *is* the collection `scripts/discover_repos.py` returns — never a hand-typed list, since the whole point of a review is to find what the team forgot to mention. Gap-check every member (does each already carry a docforge baseline, or must one be generated first?), and record the collection honestly in `docs-portfolio/repo-inventory.md`. Read `references/diligence-collection.md` in full before proceeding.

### Step 3 — Select overlays by repo type and audience

The spine is universal; the overlay is what makes documentation actually useful for a given kind of software and a given reader. Read the matching reference file — only the matching ones — and layer its additions onto the tree.

**Repo-type overlays:**

The `--overlay` flag value (the literal `docs_scaffold.py`/`manifest_sync.py` accept) is in the middle column — pass that string, not the display name.

| Signal in the repo | Overlay (`--overlay` value) | Reference |
|---|---|---|
| DAGs, schedulers, extract/transform/load stages, warehouse targets | Data pipeline — `data-pipeline` | `references/overlay-data-pipeline.md` |
| HTTP handlers, route definitions, an OpenAPI or gRPC spec, published endpoints | API service — `api` | `references/overlay-api-service.md` |
| Component tree, router, bundler, browser entry point | Web application — `web` | `references/overlay-web-app.md` |
| Published to a package registry, semantic version, public exported surface | Library / SDK — `library` | `references/overlay-library.md` |
| Terraform, Pulumi, Helm, Ansible, cluster manifests | Infrastructure — `infrastructure` | `references/overlay-infrastructure.md` |

Repos frequently match two type overlays (an API that also runs scheduled jobs). Apply both; do not force a single choice.

**Human audience overlays** — build these only when a specific reader is asked for, or when the repo clearly warrants one (see each reference's "Applies when"):

| Reader (`--overlay` value) | Cares about | Folder | Reference |
|---|---|---|---|
| Business Analyst (BA) — `business-analyst` | business rules, process flows, requirements traceability | `docs/product/business-analyst/` | `references/overlay-business-analyst.md` |
| Product Owner (PO) — `product-owner` | feature value, release framing, success metrics | `docs/product/product-owner/` | `references/overlay-product-owner.md` |

**Agent-context overlay — on by default, every run.** Unlike the two above, `agent-context` (`--overlay` value `agent-context`) is not conditional on a signal or a request — `docs_scaffold.py`/`.js` and `manifest_sync.py`/`.js` add it automatically unless `--no-agent-context` is passed. It produces `AGENTS.md`, `CLAUDE.md`, `CLAUDE.local.md`, `.claude/settings.json`, and `docs/agents/` (root + `docs/agents/`, see `references/overlay-agent-context.md`) — a token-budgeted orientation kernel, not a human reader. State it in the Gate 1 tree like any other overlay; only drop it when the user explicitly opts out (pass `--no-agent-context` to both scripts, and say so in the manifest).

**Ordering constraint: agent-context writes last.** Every `docs/agents/*` file and `AGENTS.md`'s "Deeper Context" section are brief stubs that link into the human-facing documents this run produces (`architecture/`, `flows/`, `reference/`, decision records, etc.) — see the overlay reference's "governing rule." Those link targets must exist and be finished before the stub pointing at them is written, or the audit gate (Step 0) fails it as a dangling reference. `manifest_sync.py`'s `GROUPS` list places `agent-context` last for this reason; do not reorder Step 5's write loop to interleave agent-context documents earlier.

Audience content follows the three-class model in `references/audience-matrix.md`: a subject two or more audiences share is written **once**, as an aligned topic — `flows/<flow>.md` or `architecture/concepts/<subsystem>.md` — while genuinely single-reader material stays in that audience's own folder (`product/business-analyst/`, `product/product-owner/`). An aligned topic is a **flat file by default**; it becomes a folder (`<topic>/README.md` + deep-dive subfiles) only at the moment real per-reader depth is written, in the same pass — never a folder with a promised subfile that isn't there yet. Every fact is owned once and linked, never pasted into two folders. Do not produce an unrequested audience folder or an empty deep-dive subfile; an empty or promised-but-missing overlay is the same anti-pattern as an unfilled scaffold. Read `references/audience-matrix.md`, `references/document-composition.md` and `references/depth-and-audience.md` before writing any flow or audience content.

### Step 4 — Build the tree

Read `references/docs-tree.md` for the canonical taxonomy, folder naming rules, and what belongs in each file. Then either:

- **Scaffold mechanically** — `python scripts/docs_scaffold.py --repo <path> --tier 2 --overlay api --overlay business-analyst` creates the directories and drops **scaffold templates** (`assets/templates/`) with `{{…}}` placeholders in place. Use this when starting from nothing; it is faster and more consistent than writing files by hand.
- **Write directly** — when the repo already has partial documentation, or when only a few files are needed. Pull scaffold templates from `assets/templates/`.

*Two things are called "template" in this skill — keep them distinct.* A **scaffold template** (`assets/templates/*.md`) is a starting-point file with `{{…}}` placeholders that the scaffold drops on disk. An **instruction file** (`instructions/*.md`) is writing-craft guidance for the agent, never written to disk — and it is what the manifest's `template` field and `document-templates.json`'s `instruction_file` point to. They sometimes share a base name (`architecture-high-level.md` exists in both), so resolve the manifest's `template` field against `instructions/`, not `assets/templates/`.

Not every scaffold template is emitted by `docs_scaffold.py`. A few are **hand-pulled** at the moment they're needed rather than at scaffold time: `topic-readme.md` and `audience-deepdive.md` at flow/concept promotion (`references/document-composition.md`), and `repo-inventory.md` for the Tier-3 portfolio layer (`references/diligence-collection.md`). That's expected — reach for them from `assets/templates/` when you write those specific documents.

Either way, the templates are starting points, not output. A scaffold left full of `{{…}}` placeholders is not a deliverable — those markers mean "not yet written," and every one must be replaced with derived content before presenting. The only marks that legitimately survive into a finished document are typed `<UPPER_SNAKE>` tokens standing in for genuinely external facts (non-negotiable 1); everything else you have evidence for, you write.

### Step 5 — Write the content, in dependency order

**Consult the document catalog for each document before writing it, and re-ground it in the source.** `references/document-catalog.md` is the content contract for every doc type — what it must present, what to keep out (so two documents don't overlap), its primary Diátaxis mode, and its target depth. **Read both layers before writing:** the catalog entry (the *contract*) and, where one exists for that type, its craft guide in `instructions/<type>.md` (the *how to lay it out* — the manifest's `template` field and `.metadata/document-templates.json`'s `instruction_file` name it). The catalog is authoritative for all types; `instructions/` covers only the subset with extra craft guidance, and it never restates the contract. Before writing any document — plan-first path or a single explicitly-requested doc — confirm the graph and code actually supply every must-present element, and retrieve what's missing rather than writing around it (the re-ground rule in Step 0 applies to every document, not only the plan-first cadence). **One document, one primary mode:** each document declares a single *primary* Diátaxis mode and stays in it. Many types are legitimately hybrid — a flow doc explains *and* walks its steps, `high-level.md` is Explanation/Reference — and `document-catalog.md` records each type's primary mode. When material genuinely spans modes, **section it explicitly and cross-link** (steps under a how-to heading, rationale under an explanation heading) rather than blending the prose. Orientation documents (the READMEs, `product/overview.md`) are the only ones that summarize freely across modes, and only as a router that delegates depth.

**Default depth is deep-dive, not orientation.** Within each document's mode, write to the depth that lets a stranger to the repo genuinely understand and approach the subsystem — mechanism, edge cases, failure modes, and the adjacent pieces (what feeds it, what it feeds, what breaks it) that make it self-standing. The only thing you cut is filler, never signal; "detailed" means more useful information, not more words. See `references/depth-and-audience.md` for the depth ladder and the value brake, and non-negotiable 6 for keeping deep sections durable (behaviour-level, no code, no line numbers).

Later documents cite earlier ones, so order matters:

1. `docs/architecture/high-level.md` — the stable map, built from the graph. Everything else references it. Then `low-level.md` and `architecture/concepts/<subsystem>.md` deep-dives for the significant subsystems (same flat-then-promoted rule as flows).
2. `docs/flows/<flow>.md` — one flat file per flow: L0, plain-language L1 steps, every notice, a diagram whenever the flow has more than one step or a branch. Promote a specific flow to `docs/flows/<flow>/README.md` + subfile only in the same pass you write that subfile's real content — never split the write across passes.
3. `docs/README.md` — the index, once you know what it indexes.
4. Root `README.md` — the audience router, written after the "front door" set because it summarizes the others.
5. Overlay and audience-specific documents — data contracts, error catalog, route map, BA requirements-traceability, PO feature catalog and metrics, whichever apply.
6. Risk documents — `reference/limitations.md`, `architecture/tech-debt.md`, `architecture/constraints.md`, dependency inventory, security policy.
7. Decision records — backfill the load-bearing choices found in history.
8. **Agent-context overlay, last, always.** `AGENTS.md`, `CLAUDE.md`, `CLAUDE.local.md`, `.claude/settings.json`, and `docs/agents/*` — after everything above, since every one of these is a brief stub or module map that links into documents 1–7 (see `references/overlay-agent-context.md`). Writing this earlier produces stubs pointing at documents that don't exist yet; the independent audit (Step 0) catches that as a dangling reference, so don't front-run the order to save a pass. Cross-vendor mirrors (`GEMINI.md`, `.cursor/rules/agents.mdc`, …) are hand-pulled immediately after `AGENTS.md` is finalized, same as today.

**Stamp provenance as you write, not afterward.** The source files you just read to write a section *are* its provenance, so record them then — each document gets the frontmatter block and the source-files-per-section list described in `references/provenance-tracking.md`, aggregated into `.docforge/manifest.json`. Retrofitting hashes as a cleanup pass invites guessing about which files a section actually drew from.

### Step 6 — Final whole-tree consistency pass

**Per-document completeness, depth, mode purity, and grounding are already settled** — each document passed its independent audit (`references/document-audit.md`) before it was marked `complete` in the Step 0 write loop. Step 6 is **not** a second per-document review, and it is emphatically not the moment to first check whether a document is deep enough; that gate has already fired, one document at a time. Step 6 is the pass for the checks that are only meaningful **across the whole set**:

- `python scripts/docs_scaffold.py --repo <path> --audit` — dead cross-references between documents, empty templated sections, folder-only-readme promotions, and forge-specific strings that leaked into prose.
- The **whole-tree** items of `references/quality-bar.md`: the four tests (onboarding, location, reviewer, stranger), index reachability (every document reachable from `docs/README.md` in two hops), and no fact duplicated across two files.
- The onboarding test specifically: could a competent engineer who has never seen this repo go from the root README to a running local instance without asking a human a question? If not, `engineering/setup.md` is incomplete regardless of how polished the rest looks.

If a whole-tree check surfaces a per-document defect the audit somehow missed, fix that document and **re-audit it** — do not patch it silently at the tree level.

## Updating existing docs — check before you rewrite

This section is for docs that **already carry docforge provenance** from a prior run. If the repo instead has hand-written docs that have never been through docforge, that's Step 1's "Migrate pre-existing documentation" — run that first; this section starts from the second run onward. This is also what `--revise all` / `--revise <area>` (Step 0) invoke — `--revise <area>` just scopes step 1 below to the matching manifest entries instead of the whole file.

When asked to refresh docs that already carry docforge provenance, do not re-read and re-guess. Compare hashes:

1. `python scripts/check_provenance.py --manifest .docforge/manifest.json`.
2. For every `PARTIAL  <doc>  section=<id>  STALE: <file>` line, regenerate only that section — re-run its narrow graph query, replace only that section's prose, re-stamp only its hashes. See "Partial rewrite" in `provenance-tracking.md`.
3. For every `FRESH` result, leave the file untouched — do not re-open it or bump its timestamp.
4. For a `MISSING` file-status inside a `PARTIAL` line (a recorded source file no longer exists), do not delete the claim — the logic likely moved rather than vanished. Flag it for a human to confirm.
5. For a document-level `STALE  <doc>  (no section granularity recorded)` — an adopted doc whose frontmatter never recorded section-level provenance — re-ground the whole document, then stamp section-level provenance so future checks are incremental. This is the one case a whole-document pass is correct even when little changed, because there is no finer signal to act on.
6. Re-run the checker to confirm every touched document now reports `FRESH`.

A whole-document rewrite is warranted only when most sections are stale at once, or the document's own structure changed (a rule added or removed, not merely modified).

**Before writing any of the above, ask the user what to do with what the refresh makes obsolete.** A refresh routinely surfaces documents the current pass supersedes — a document whose structure changed so much the old file no longer matches the taxonomy slot, two documents a consolidation is about to merge into one, or a file the manifest still lists but the repo no longer needs. Do not silently overwrite, orphan, or delete any of these. Present the list (superseded / merge-candidate / no-longer-needed) and get an explicit keep / archive / merge / delete decision, same as the first-run migration gate above — a refresh is not exempt from that confirmation just because provenance already exists. Archive whatever the user confirms as obsolete under `docs/_archive/<year>/` (never delete outright unless they say so), and only then proceed with steps 1–6.

## Root vs `docs/`

Documentation lives in `docs/`. The complication is that a handful of root files are load-bearing for tooling rather than for readers: package registries render root `README.md`, and forges surface `LICENSE` and `SECURITY.md`. Fighting those conventions creates friction with no upside.

The resolution: **root files are thin routers, `docs/` holds the substance.**

```
repo-root/
├── README.md          # ~40 lines: what this is, quickstart, links into docs/
├── LICENSE            # full text — legal artifact, stays whole at root
├── CHANGELOG.md       # release-facing, conventionally at root
├── CONTRIBUTING.md    # one screen, then → docs/contributing/
├── SECURITY.md        # disclosure address + SLA, then → docs/security/
└── docs/              # everything else
```

Each root stub follows the same shape: the 20% a reader needs immediately, then an explicit link. Never duplicate content between a root stub and its `docs/` counterpart — duplication is how the two versions start disagreeing.

The `agent-context` overlay is on by default (Step 3), so `AGENTS.md`, `CLAUDE.md`, `CLAUDE.local.md`, and `.claude/settings.json` join this root list on every run unless the user opts out — the same thin-router shape, aimed at an AI agent instead of a human reader. See `references/overlay-agent-context.md` for the full file set.

## The `docs/` taxonomy, in brief

Full specification in `references/docs-tree.md`. The shape:

```
<repo root>/
├── .docforge/manifest.json    # provenance index — which source files each doc section cites
└── docs/
    ├── README.md              # index and audience router — the one entry point
    ├── product/               # for business readers and external consumers
    │   ├── business-analyst/  # (audience overlay) single-reader BA documents
    │   └── product-owner/     # (audience overlay) single-reader PO documents
    ├── flows/                 # one per business flow — flat file, promoted to a folder only when a deep-dive is written
    │   ├── login.md           # flat by default
    │   └── signup/            # promoted: common README + a real per-reader deep-dive subfile
    │       ├── README.md
    │       └── engineering.md
    ├── architecture/          # for engineers and technical reviewers
    │   ├── high-level.md      # system context, building blocks, boundaries (stable map)
    │   ├── low-level.md       # component decomposition, data model
    │   ├── concepts/          # deep-dive subsystems — same flat-then-promoted rule as flows
    │   ├── tech-debt.md       # known shortcuts + remediation
    │   ├── constraints.md     # hard architectural limits and non-goals
    │   ├── decisions/         # ADRs — the durable "why"
    │   └── dependencies.md    # third-party inventory and integration contracts
    ├── engineering/           # for contributors: setup, testing, conventions
    ├── operations/            # for whoever is on call: runbooks, observability
    ├── reference/             # lookup material: config, errors, limitations, glossary
    ├── security/              # threat model, data handling, disclosure process
    └── contributing/          # workflow, review, issue and change templates
```

Two naming rules prevent most drift: **every folder has a `README.md` acting as its index** (forges render it automatically, so the folder explains itself when browsed), and **folder names are plural nouns for collections** (`decisions/`, `runbooks/`, `contracts/`) **and singular for single-subject areas** (`security/`, `product/`, `business-analyst/`).

The taxonomy is a floor, not a ceiling. If the repo already carries directories under `docs/` that this skill does not define, leave them where they are and index them from `docs/README.md` — displacing a folder another tool owns breaks that tool and gains nothing.

## Anti-patterns

- **The scaffold dump.** Twenty files of unfilled headings. Worse than nothing: it signals documentation exists when it does not, and readers stop checking.
- **The silent whole-tree dump.** Generating the entire tree in one shot on an open-ended request, with no plan and no confirmation gate, so the user faces thirty files to audit at once and can't steer before the tokens are spent. Open-ended scope means plan first, then part by part (Step 0).
- **Orientation masquerading as documentation.** A page that says what a subsystem *is* but never how it works, why it's built that way, what its edge cases and failure modes are. Deep-dive is the default; shallow is only correct for a genuinely trivial part. Cut filler, never signal (`references/depth-and-audience.md`). This is exactly the defect the per-document audit gate exists to catch (`references/document-audit.md`).
- **The writer grading its own work.** Marking a document `complete` on the strength of the same agent that wrote it — no independent check. A writer cannot see the gap it never knew to fill, and a same-graph misreading gets re-confirmed rather than caught. Completion is decided by a *fresh* auditor that did not write the document (`references/document-audit.md`), not by the author's confidence.
- **Batch verification hiding per-doc gaps.** Deferring all checking to one whole-tree pass at the end, so a shallow or ungrounded document is never independently caught before it's marked done. The audit fires **per document, at `generated`, before `complete`**; Step 6 is only the cross-document consistency pass, not the first time depth is checked.
- **Over-fragmentation / stub sprawl.** Splitting a subject across many thin files a reader must reassemble, or deep-diving every module because the taxonomy has a slot for it. Depth belongs in the *depth of the right documents*, not the *count* of them — prefer the fewest documents that each hold a complete, single-mode subject, and let reader need and tier bound how many exist. A set no human can navigate fails even if every file is accurate.
- **Punting a derivable fact to a human.** "`> TODO: document the retry policy`" when the retry policy is in the source you already analysed. The AI generates the full set; humans review, they do not author. If a fact is retrievable, retrieve it — a token or TODO is only ever for a value that lives in no readable source.
- **Writing before analysing.** A code map produced from directory names describes a plausible system rather than this one, and every downstream document inherits the error.
- **Rationale in the code map.** `architecture/high-level.md` says *what is where*; ADRs say *why it was chosen*. Mixing them makes the map churn every time an opinion changes.
- **Prose bound to code.** A claim anchored to a private symbol or a line number, so a routine rename falsifies the document. Describe behaviour and reference files by path instead.
- **Notice stranded in a subfile.** A warning that only an audience deep-dive carries, invisible to a reader who stops at the topic `README.md`. Critical notices belong in the common README.
- **A folder promising a deep-dive that isn't there.** A "Go deeper → engineering.md" link, or a folder created for a flow, with no `engineering.md` on disk. Worse than not offering depth at all — it tells the reader analysis happened when it didn't. A topic is a flat file until the moment its subfile is written, in the same pass; if you're not writing that content right now, don't create the folder or the link.
- **Enumerating flows by hand.** Listing business flows from route files, screen names, or a guess instead of `/understand-domain`'s output. Flows are discovered, not authored — see the hard gate in "Source analysis."
- **Same subject in two audience folders.** The definition of drift. Write it once in the owning document; link from the other.
- **Hidden limitations.** Burying known issues protects nobody and reads as evasion under scrutiny. A frank limitations register reads as competence.
- **Hand-written API reference.** Generate it from the source of truth (spec, schema, type annotations). Hand-written reference drifts within one sprint.
- **Forge lock-in in prose.** "Open a GitHub issue" in a doc that outlives the migration to a self-hosted forge.
- **Documenting aspiration.** Describing the intended architecture rather than the shipped one. Document what runs; put the target state in a decision record or roadmap where it is clearly labelled as future.
- **BA and PO merged into one "business" folder.** They ask different questions in a different order — see `audience-matrix.md`. One folder averaged across both serves neither.
- **Whole-document rewrite on a one-section change.** Regenerating a whole file because one recorded source file changed throws away good, unaffected prose; hash provenance exists precisely so you don't.
- **Provenance that names a directory or "the codebase" instead of specific files and blob hashes.** Unverifiable, and it makes nearly every doc "stale" on any nearby unrelated change.

## Reference map

Load only what the current task needs.

| File | Read it when |
|---|---|
| `references/source-analysis.md` | Always — how to build and query the knowledge graph, and which command answers which document |
| `references/graph-sources.md` | Always — which source (understand-anything or GitNexus) is active, and the capability-to-command dispatch table for each |
| `references/gitnexus-bridge.md` | Precheck reports a GitNexus index but no `.ua/*.json` yet — the build recipe |
| `references/docs-tree.md` | Always — the canonical taxonomy, folder naming, and placement rules |
| `references/document-catalog.md` | Before writing any document — what each doc type must present and must keep out, its primary Diátaxis mode, its target depth, and its source-of-truth |
| `instructions/<type>.md` | Alongside the catalog when writing a document of a type that has one — the writing-craft layer (layout, which `/understand-*` feeds it, how to tag provenance); `instructions/README.md` indexes them. Craft only; the contract stays in `document-catalog.md` |
| `references/provenance-tracking.md` | Always — frontmatter schema, manifest format, the staleness algorithm, partial-rewrite mechanics |
| `references/host-neutrality.md` | Writing anything that touches issues, reviews, CI, or ownership |
| `references/decision-records.md` | Writing or backfilling ADRs |
| `references/risk-docs.md` | Writing limitations, dependencies, or security documents |
| `references/quality-bar.md` | Before presenting anything — the review checklist and rubric (per-document subset + whole-tree items) |
| `references/document-audit.md` | Before marking any document `complete` — the independent per-document audit protocol, the derivable-vs-external gate, and the verdict schema |
| `references/audience-matrix.md` | The three document classes (aligned / audience-specific / shared-fact spine), the BA/PO split, and which folder owns which fact |
| `references/document-composition.md` | Always when writing flow or audience content — the flat-file-by-default and atomic-promotion rule, the two invariants, and the durability rules (no code, no duplication, write at the slowest layer) |
| `references/depth-and-audience.md` | The depth ladder (L0–L3), which reader consumes which depth, and which understand-anything command feeds which cell |
| `references/overlay-business-analyst.md` | Writing anything under `docs/product/business-analyst/` |
| `references/overlay-product-owner.md` | Writing anything under `docs/product/product-owner/` |
| `references/overlay-agent-context.md` | Writing `AGENTS.md`, `CLAUDE.md`, `.claude/settings.json`, or anything under `docs/agents/` |
| `references/diligence.md` | Multi-repo portfolios, audits, acquisitions, vendor review — the portfolio layer |
| `references/diligence-collection.md` | Any multi-repo job — assembling the collection, gap-checking members, recording composition honestly |
| `references/overlay-*.md` | The repo-type overlay matching the repo (Step 3) |

Templates live in `assets/templates/`. Scripts (each has a `.py` and an equivalent `.js` — see the note at the top of "Precheck"):
- `scripts/check_preconditions.{py,js}` — gate all docforge work on both the knowledge graph and domain graph actually existing; run as the first step of every invocation (see "Precheck" above). Orchestrates the two source modules below — READY/MISSING reporting only, source-agnostic
- `scripts/graph_common.{py,js}` — shared helpers used by `check_preconditions` and every `graph_source_*` module: locating a graph file up to the git root, display formatting, and writing a freshly-built graph to `.ua/`
- `scripts/graph_source_ua.{py,js}` — understand-anything source: detection only (it always builds its own output)
- `scripts/graph_source_gitnexus.{py,js}` — GitNexus source: `detect` (is an index present) and `build` (materialize `.ua/*.json` from raw Cypher dumps — see `references/gitnexus-bridge.md`)
- `scripts/validate_graphs.{py,js}` — the diagnostic probe for when `check_preconditions` reports a graph missing but `.ua/` holds data; lists both graph folders' contents with sizes, JSON validity and node/edge counts
- `scripts/graph_extract.{py,js}` — read the knowledge graph
- `scripts/docs_scaffold.{py,js}` — create and audit the tree
- `scripts/manifest_sync.{py,js}` — create and maintain `.docforge/manifest.json`: `init` the plan (all `planned`), `add` discovered flows/overlays, `set` a document's status as it lands, `status` for a summary
- `scripts/check_provenance.{py,js}` — recompute git blob hashes for every source file recorded in the manifest's per-document `sections`. Emits one of three **document-level** statuses: `FRESH`; `PARTIAL` (one line per offending file — `PARTIAL  <doc>  section=<id>  <file_status>: <file>`, where `<file_status>` is `STALE` for a changed file or `MISSING` for a deleted one); or a document-level `STALE  <doc>  (no section granularity recorded)` for an adopted doc without section-level frontmatter. `MISSING` is never a document-level result — only a per-file substatus inside a `PARTIAL` line. Exit 0 only if every checked document is `FRESH`; documents still `planned`/`in_progress` are skipped
- `scripts/discover_repos.{py,js}` — walk a root for declared submodules and undeclared nested repos, reporting each member's docforge status so gaps surface before a review, not during it
- `scripts/check_document.{py,js}` — mechanical pre-audit of one document (`--file <path>`): flags `{{…}}` markers, empty headings, dead relative links, unlinked file mentions, and any `--require-heading` that's absent; lists typed `<UPPER_SNAKE>` tokens separately as non-defects. Run it before the independent audit (`references/document-audit.md`) so the auditing agent spends effort on judgement, not mechanics
- `scripts/check_agents_kernel.{py,js}` — `AGENTS.md`-specific rubric (`agent-context` overlay): the 100-line cap, the 7-section shape, tagline/test-sentence conventions, and dangling `@docs/agents/…` references. Run alongside `check_document.{py,js}`, not instead of it

---

## When a graph "isn't found" but the `.ua/` folder exists

If `check_preconditions.py` or a workflow step reports the graph missing while `.ua/` clearly holds data, the file on disk and the file the step expects have diverged — a partial write, an unreadable JSON, or the wrong filename. Diagnose before re-running anything expensive:

```bash
python scripts/validate_graphs.py --repo . --verbose
```

It prints what actually sits in `.ua/` and `.understand-anything/` — filenames, sizes, timestamps, JSON validity, node/edge counts — so a false "not found" separates cleanly from a genuinely absent or truncated graph. Where `check_preconditions.py` is the gate, this is the probe you reach for when the gate's answer surprises you. The two most common causes: `/understand` reported success but wrote nothing (re-run it — the pass is incremental and cheap), or the JSON is truncated from an interrupted write (re-run to rewrite it). Both graph locations and every parent up to the git root are searched, so subdirectory invocation is not the cause.
