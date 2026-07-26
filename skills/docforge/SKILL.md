---
name: docforge
description: Design and generate a repository's documentation set — the docs/ tree, README and ARCHITECTURE, decision records (ADRs), a known-limitations register, a third-party dependency inventory, security policy, API error catalogs, data contracts and runbooks, plus audience overlays that speak to Business Analyst (BA) and Product Owner (PO) readers. Grounds every document in a knowledge-graph analysis of the actual source before writing, so nothing is invented, and stamps each document with git-hash provenance so staleness is decided by comparison, not by re-guessing. Host-neutral — works on any git host and never hardcodes one forge's paths, and checks for child repos (declared submodules or nested/vendored repos) before any multi-repo review. Use this skill whenever the user mentions documenting a repo or codebase, a docs folder, README or ARCHITECTURE files, ADRs or decision records, onboarding docs, runbooks, known limitations, dependency or licence inventories, technical due diligence or audit readiness, standardizing documentation across several repos, documentation for a Business Analyst or Product Owner, business rules or process flows or requirements traceability, feature catalogs or release notes or success metrics, or whether existing generated docs have drifted from the code — including loose phrasings like "write docs for this project", "our repo has no documentation", "make this repo legible to a new engineer", "docs for BA/PO", "which docs are stale", "should we regenerate this", or "does every repo in here have docs".
---

# Docforge — Repository Documentation Architect

Documentation fails in two directions: too little (nobody can onboard, diligence stalls) and too much of the wrong kind (a hand-written reference that drifts from the code and quietly becomes a liability). This skill produces the shape that survives — a small, predictable spine that every repo shares, plus overlays chosen by what the repo actually is and who has to read it.

Three rules organize every decision here. **Separate documents that change once or twice a year from documents that change every release**, and let generated artifacts carry the facts that machines can verify. **Read the codebase through a knowledge graph before writing a word about it** — the difference between documentation that is trusted and documentation that is quietly ignored is whether its claims are true. And **record which code each claim came from**, so "has this drifted?" is answered by a hash comparison instead of a re-read and a guess.

## Non-negotiables

Five rules that hold regardless of tier, repo type, ecosystem, or audience. Violating them is what makes documentation rot.

1. **Never invent.** Every claim must be traceable to the knowledge graph, to code, to config, to commit history, or to something the user told you. If a fact is needed but unknown, write a visible placeholder — `> TODO(owner): confirm retry policy for the ingest stage` — rather than a plausible guess. A confidently wrong doc costs more than a missing one, because readers stop trusting the whole set.
2. **Analyse before writing.** The knowledge graph is a precondition, not an optimization. See "Source analysis" below and `references/source-analysis.md`.
3. **Host-neutral by default.** Nothing in generated prose names a specific forge. Write "the issue tracker", "the CI pipeline", "a merge request or pull request". Forge-specific paths are confined to the one place described in `references/host-neutrality.md`.
4. **Everything lives under `docs/`.** Repo root carries only the handful of files that ecosystem tooling and package registries look for by convention, and those are thin pointers into `docs/`. See "Root vs docs/" below.
5. **Stamp provenance in the same pass you write.** Every generated document records the specific source files (by git blob hash) each section draws from. Staleness is later decided by hash comparison, never by re-reading and re-guessing; a change in one recorded file regenerates the section that cites it, not the whole document. See `references/provenance-tracking.md`.

## Source analysis — run this first

Every document in the tree makes claims about the source. Producing those claims from directory names and file extensions is how documentation ends up describing a system that does not exist. The knowledge graph replaces guessing with retrieval: it gives you the module map, the architectural layers, the call and import edges, the business domains and flows, and a queryable interface for everything the graph does not already state.

**Before any other step**, build or refresh it:

```
/understand
```

That runs a multi-agent pipeline over the project and writes the graph to `.ua/knowledge-graph.json` (older projects keep using `.understand-anything/`). Re-runs are incremental — only changed files are re-analysed — so refreshing an existing graph is cheap. Notes that matter in practice:

- **Check for an existing graph first.** If `.ua/knowledge-graph.json` is present and newer than the last substantive commit, use it as is. If it is stale, `/understand` updates it incrementally rather than starting over.
- **Large repos**: scope the analysis to the part being documented — `/understand src/frontend` — rather than paying for a full pass you do not need. First runs on large codebases consume significant tokens; say so before starting one.
- **Invocation prefix varies by platform.** Most use `/understand`; Codex uses `$understand`. Where neither is recognized, invoke it in plain language: *"Use the understand skill to analyze this project."*
- **Read the graph directly** once built. `python scripts/graph_extract.py --graph .ua/knowledge-graph.json --summary` prints the module inventory, layer assignment and external dependency list in a form that seeds the code map and the dependency inventory.

Then, whenever a document needs a fact the graph does not already state, query rather than infer. Full command-to-document mapping in `references/source-analysis.md`; the essentials:

| You are about to write | Get the facts from |
|---|---|
| `architecture/overview.md` (code map, layers, invariants) | the graph itself, plus `/understand-explain <path>` per significant module |
| `architecture/data-flow.md` | `/understand-domain` for flows and steps; `/understand-chat` for a specific path |
| `product/overview.md`, `capabilities.md` | `/understand-domain` — business domains in the code's own terms |
| `product/business-analyst/*` (rules, flows, traceability) | `/understand-domain` per flow, then `/understand-chat "what business rules gate <flow>"` |
| `product/product-owner/*` (features, metrics, release notes) | `/understand-domain` for the feature set; `git log` merge commits for release framing |
| `engineering/setup.md` | `/understand-onboard`, then verify every command by running it |
| `architecture/dependencies.md` | graph import edges, then `/understand-chat` for failure handling per integration |
| `reference/configuration.md` | `/understand-chat "which environment variables does this read, and where"` |
| `reference/limitations.md` | `/understand-chat` for unhandled cases, TODO and FIXME clusters, hard-coded bounds |
| Decision records | `/understand-chat "why …"` cross-checked against `git log` |
| Any overlay document (routes, error codes, datasets) | targeted `/understand-chat` questions — see the overlay reference |

Two habits make this pay off. **Ask narrow questions** — "which modules write to the database, and through what" retrieves cleanly where "explain the architecture" returns prose you then have to verify. And **treat the answers as evidence, not as prose to paste**: they are a source to write from, in the document's own voice and structure.

If the graph is unavailable — the plugin is not installed, or the source is not accessible to you — say so plainly and fall back to direct inspection. Do not proceed silently, and do not fabricate a tree from the repo name.

## Workflow

### Step 1 — Build the graph, then read the repo

Run the analysis above, then fill the gaps it does not cover:

- **Manifests and build files** — `pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`, `pom.xml`, `*.csproj`. Version pins and dependency ranges come from here, not from the graph.
- **Repo type signals** — a web framework, an HTTP server, DAG or scheduler definitions, a published package config, infrastructure-as-code, embedded business logic (validation rules, approval thresholds, eligibility conditions). These select your overlays; the graph's layer assignment usually makes them obvious.
- **What documentation already exists** — an existing `README`, `docs/`, wiki exports, comments that read like design notes, ADR-ish files. Existing content is evidence about what people needed to write down; migrate it, do not replace it.
- **Operational reality** — CI config, container and deploy manifests, and the environment variables the code actually reads.
- **History for the "why"** — `git log` on architecturally significant paths, and merge commits with substantive messages. This is where backfilled decision records come from, and it is the one thing the graph cannot supply.
- **Child repos** — before any multi-repo work, and as a cheap sanity check otherwise, run `python scripts/discover_repos.py --root <path>`. It reports declared submodules and, more importantly, nested repos present on disk but *not* declared in `.gitmodules` (vendored copies, `git subtree` merges, hand-cloned submodules). For single-repo work this just confirms scope; for diligence it is load-bearing — see Step 2 and `references/diligence-collection.md`.

### Step 2 — Choose a tier

Documentation weight should be proportionate to team size and external scrutiny; heavy structure on a two-person repo costs more than it returns.

| Tier | When it fits | What gets built |
|---|---|---|
| **1 — Spine** | Any repo. Small teams, internal tools, early projects | Root pointers, `docs/README.md` index, `docs/architecture/overview.md`, `docs/engineering/setup.md`, `docs/reference/limitations.md`, `CHANGELOG` |
| **2 — Diligence** | Repo has external consumers, paying customers, or a compliance or audit surface | Tier 1 + `docs/architecture/decisions/`, `docs/architecture/dependencies.md`, `docs/security/`, `docs/operations/runbooks/`, contribution docs |
| **3 — Portfolio** | Several repos reviewed as one system; fundraising, acquisition, vendor assessment | Tier 2 across every repo + a cross-repo portfolio layer (`references/diligence.md`) |

State the chosen tier and the reasoning in one sentence before generating. If the user gives a deadline-driven signal ("we're in diligence next month"), invert the order: build the Tier 3 skeleton and the security and dependency documents first, backfill the rest after.

**Tier 3 discovers its collection before it builds anything.** A multi-repo review's scope *is* the collection `scripts/discover_repos.py` returns — never a hand-typed list, since the whole point of a review is to find what the team forgot to mention. Gap-check every member (does each already carry a docforge baseline, or must one be generated first?), and record the collection honestly in `docs-portfolio/repo-inventory.md`. Read `references/diligence-collection.md` in full before proceeding.

### Step 3 — Select overlays by repo type and audience

The spine is universal; the overlay is what makes documentation actually useful for a given kind of software and a given reader. Read the matching reference file — only the matching ones — and layer its additions onto the tree.

**Repo-type overlays:**

| Signal in the repo | Overlay | Reference |
|---|---|---|
| DAGs, schedulers, extract/transform/load stages, warehouse targets | Data pipeline | `references/overlay-data-pipeline.md` |
| HTTP handlers, route definitions, an OpenAPI or gRPC spec, published endpoints | API service | `references/overlay-api-service.md` |
| Component tree, router, bundler, browser entry point | Web application | `references/overlay-web-app.md` |
| Published to a package registry, semantic version, public exported surface | Library / SDK | `references/overlay-library.md` |
| Terraform, Pulumi, Helm, Ansible, cluster manifests | Infrastructure | `references/overlay-infrastructure.md` |

Repos frequently match two type overlays (an API that also runs scheduled jobs). Apply both; do not force a single choice.

**Audience overlays** — build these only when a specific reader is asked for, or when the repo clearly warrants one (see each reference's "Applies when"):

| Reader | Cares about | Folder | Reference |
|---|---|---|---|
| Business Analyst (BA) | business rules, process flows, requirements traceability | `docs/product/business-analyst/` | `references/overlay-business-analyst.md` |
| Product Owner (PO) | feature value, release framing, success metrics | `docs/product/product-owner/` | `references/overlay-product-owner.md` |

Audience overlays behave differently from type overlays: **isolated by default** — name one audience, produce only that folder — and **combined only on an explicit multi-audience request** ("docs for BA and PO", "align docs for the product team"), where each fact is owned once and cross-linked, never pasted into both folders. Do not produce an unrequested audience folder; an empty overlay is the same anti-pattern as an unfilled scaffold. The isolation/combination rules and the fact-ownership table live in `references/audience-matrix.md`.

### Step 4 — Build the tree

Read `references/docs-tree.md` for the canonical taxonomy, folder naming rules, and what belongs in each file. Then either:

- **Scaffold mechanically** — `python scripts/docs_scaffold.py --repo <path> --tier 2 --overlay api --overlay business-analyst` creates the directories and drops templated files with placeholders in place. Use this when starting from nothing; it is faster and more consistent than writing files by hand.
- **Write directly** — when the repo already has partial documentation, or when only a few files are needed. Pull templates from `assets/templates/`.

Either way, the templates are starting points, not output. A scaffold left full of placeholders is not a deliverable; fill every section the graph gives you evidence for and flag the rest.

### Step 5 — Write the content, in dependency order

Later documents cite earlier ones, so order matters:

1. `docs/architecture/overview.md` — the code map, built from the graph. Everything else references it.
2. `docs/README.md` — the index, once you know what it indexes.
3. Root `README.md` — the audience router, written after the "front door" set because it summarizes the others.
4. Overlay documents — data contracts, error catalog, route map, BA business rules and process flows, PO feature catalog, whichever apply.
5. Risk documents — limitations register, dependency inventory, security policy.
6. Decision records — backfill the load-bearing choices found in history.

**Stamp provenance as you write, not afterward.** The source files you just read to write a section *are* its provenance, so record them then — each document gets the frontmatter block and the source-files-per-section list described in `references/provenance-tracking.md`, aggregated into `docs/.docforge/manifest.json`. Retrofitting hashes as a cleanup pass invites guessing about which files a section actually drew from.

### Step 6 — Verify before presenting

Run the checklist in `references/quality-bar.md`. Its core test: could a competent engineer who has never seen this repo go from the root README to a running local instance without asking a human a question? If not, the setup documentation is incomplete regardless of how polished the rest looks.

Then `python scripts/docs_scaffold.py --repo <path> --audit` to catch dead cross-references, empty templated sections, and forge-specific strings that leaked into prose.

For anything the documentation asserts about behaviour, spot-check it against the graph — `/understand-explain <path>` on two or three modules the code map describes is enough to catch a systematic misreading.

## Updating existing docs — check before you rewrite

When asked to refresh docs that already carry docforge provenance, do not re-read and re-guess. Compare hashes:

1. `python scripts/check_provenance.py --manifest docs/.docforge/manifest.json`.
2. For every `PARTIAL — <section> stale` result, regenerate only that section — re-run its narrow graph query, replace only that section's prose, re-stamp only its hashes. See "Partial rewrite" in `provenance-tracking.md`.
3. For every `FRESH` result, leave the file untouched — do not re-open it or bump its timestamp.
4. For every `MISSING` (a recorded source file no longer exists), do not delete the claim — the logic likely moved rather than vanished. Flag it for a human to confirm.
5. Re-run the checker to confirm every touched document now reports `FRESH`.

A whole-document rewrite is warranted only when most sections are stale at once, or the document's own structure changed (a rule added or removed, not merely modified).

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

## The `docs/` taxonomy, in brief

Full specification in `references/docs-tree.md`. The shape:

```
docs/
├── README.md              # index and audience router — the one entry point
├── product/               # for business readers and external consumers
│   ├── business-analyst/  # (audience overlay) business rules, flows, traceability
│   └── product-owner/     # (audience overlay) feature value, metrics, release notes
├── architecture/          # for engineers and technical reviewers
│   ├── overview.md        # the code map
│   ├── decisions/         # ADRs — the durable "why"
│   └── dependencies.md    # third-party inventory and integration contracts
├── engineering/           # for contributors: setup, testing, conventions
├── operations/            # for whoever is on call: runbooks, observability
├── reference/             # lookup material: config, errors, limitations, glossary
├── security/              # threat model, data handling, disclosure process
├── contributing/          # workflow, review, issue and change templates
└── .docforge/manifest.json # provenance index — which source files each doc section cites
```

Two naming rules prevent most drift: **every folder has a `README.md` acting as its index** (forges render it automatically, so the folder explains itself when browsed), and **folder names are plural nouns for collections** (`decisions/`, `runbooks/`, `contracts/`) **and singular for single-subject areas** (`security/`, `product/`, `business-analyst/`).

The taxonomy is a floor, not a ceiling. If the repo already carries directories under `docs/` that this skill does not define, leave them where they are and index them from `docs/README.md` — displacing a folder another tool owns breaks that tool and gains nothing.

## Anti-patterns

- **The scaffold dump.** Twenty files of unfilled headings. Worse than nothing: it signals documentation exists when it does not, and readers stop checking.
- **Writing before analysing.** A code map produced from directory names describes a plausible system rather than this one, and every downstream document inherits the error.
- **Rationale in the code map.** `architecture/overview.md` says *what is where*; ADRs say *why it was chosen*. Mixing them makes the code map churn every time an opinion changes.
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
| `references/docs-tree.md` | Always — the canonical taxonomy and per-file specification |
| `references/provenance-tracking.md` | Always — frontmatter schema, manifest format, the staleness algorithm, partial-rewrite mechanics |
| `references/host-neutrality.md` | Writing anything that touches issues, reviews, CI, or ownership |
| `references/decision-records.md` | Writing or backfilling ADRs |
| `references/risk-docs.md` | Writing limitations, dependencies, or security documents |
| `references/quality-bar.md` | Before presenting anything — review checklist and rubric |
| `references/audience-matrix.md` | Deciding isolated vs. combined audience overlays, and which folder owns which fact |
| `references/overlay-business-analyst.md` | Writing anything under `docs/product/business-analyst/` |
| `references/overlay-product-owner.md` | Writing anything under `docs/product/product-owner/` |
| `references/diligence.md` | Multi-repo portfolios, audits, acquisitions, vendor review — the portfolio layer |
| `references/diligence-collection.md` | Any multi-repo job — assembling the collection, gap-checking members, recording composition honestly |
| `references/overlay-*.md` | The repo-type overlay matching the repo (Step 3) |

Templates live in `assets/templates/`. Scripts:
- `scripts/graph_extract.py` — read the knowledge graph
- `scripts/docs_scaffold.py` — create and audit the tree
- `scripts/check_provenance.py` — recompute git blob hashes for every file recorded in the manifest; report `FRESH` / `PARTIAL` / `MISSING` per document and section
- `scripts/discover_repos.py` — walk a root for declared submodules and undeclared nested repos, reporting each member's docforge status so gaps surface before a review, not during it
