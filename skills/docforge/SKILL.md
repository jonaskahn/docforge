---
name: docforge
description: Design and generate a repository's documentation set — the docs/ tree, README and ARCHITECTURE, decision records (ADRs), a known-limitations register, a third-party dependency inventory, security policy, API error catalogs, data contracts and runbooks. Grounds every document in a knowledge-graph analysis of the actual source before writing, so nothing is invented. Host-neutral — works on any git host and never hardcodes one forge's paths. Use this skill whenever the user mentions documenting a repo or codebase, a docs folder, README or ARCHITECTURE files, ADRs or decision records, onboarding docs, runbooks, known limitations, dependency or licence inventories, technical due diligence or audit readiness, or standardizing documentation across several repos — including loose phrasings like "write docs for this project", "our repo has no documentation", or "make this repo legible to a new engineer".
---

# Docforge — Repository Documentation Architect

Documentation fails in two directions: too little (nobody can onboard, diligence stalls) and too much of the wrong kind (a hand-written reference that drifts from the code and quietly becomes a liability). This skill produces the shape that survives — a small, predictable spine that every repo shares, plus overlays chosen by what the repo actually is.

Two rules organize every decision here. **Separate documents that change once or twice a year from documents that change every release**, and let generated artifacts carry the facts that machines can verify. And **read the codebase through a knowledge graph before writing a word about it** — the difference between documentation that is trusted and documentation that is quietly ignored is whether its claims are true.

## Non-negotiables

Four rules that hold regardless of tier, repo type, or ecosystem. Violating them is what makes documentation rot.

1. **Never invent.** Every claim must be traceable to the knowledge graph, to code, to config, to commit history, or to something the user told you. If a fact is needed but unknown, write a visible placeholder — `> TODO(owner): confirm retry policy for the ingest stage` — rather than a plausible guess. A confidently wrong doc costs more than a missing one, because readers stop trusting the whole set.
2. **Analyse before writing.** The knowledge graph is a precondition, not an optimization. See "Source analysis" below and `references/source-analysis.md`.
3. **Host-neutral by default.** Nothing in generated prose names a specific forge. Write "the issue tracker", "the CI pipeline", "a merge request or pull request". Forge-specific paths are confined to the one place described in `references/host-neutrality.md`.
4. **Everything lives under `docs/`.** Repo root carries only the handful of files that ecosystem tooling and package registries look for by convention, and those are thin pointers into `docs/`. See "Root vs docs/" below.

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
- **Repo type signals** — a web framework, an HTTP server, DAG or scheduler definitions, a published package config, infrastructure-as-code. These select your overlays; the graph's layer assignment usually makes them obvious.
- **What documentation already exists** — an existing `README`, `docs/`, wiki exports, comments that read like design notes, ADR-ish files. Existing content is evidence about what people needed to write down; migrate it, do not replace it.
- **Operational reality** — CI config, container and deploy manifests, and the environment variables the code actually reads.
- **History for the "why"** — `git log` on architecturally significant paths, and merge commits with substantive messages. This is where backfilled decision records come from, and it is the one thing the graph cannot supply.

### Step 2 — Choose a tier

Documentation weight should be proportionate to team size and external scrutiny; heavy structure on a two-person repo costs more than it returns.

| Tier | When it fits | What gets built |
|---|---|---|
| **1 — Spine** | Any repo. Small teams, internal tools, early projects | Root pointers, `docs/README.md` index, `docs/architecture/overview.md`, `docs/engineering/setup.md`, `docs/reference/limitations.md`, `CHANGELOG` |
| **2 — Diligence** | Repo has external consumers, paying customers, or a compliance or audit surface | Tier 1 + `docs/architecture/decisions/`, `docs/architecture/dependencies.md`, `docs/security/`, `docs/operations/runbooks/`, contribution docs |
| **3 — Portfolio** | Several repos reviewed as one system; fundraising, acquisition, vendor assessment | Tier 2 across every repo + a cross-repo portfolio layer (`references/diligence.md`) |

State the chosen tier and the reasoning in one sentence before generating. If the user gives a deadline-driven signal ("we're in diligence next month"), invert the order: build the Tier 3 skeleton and the security and dependency documents first, backfill the rest after.

### Step 3 — Select overlays by repo type

The spine is universal; the overlay is what makes documentation actually useful for a given kind of software. Read the matching reference file — only the matching one — and layer its additions onto the tree.

| Signal in the repo | Overlay | Reference |
|---|---|---|
| DAGs, schedulers, extract/transform/load stages, warehouse targets | Data pipeline | `references/overlay-data-pipeline.md` |
| HTTP handlers, route definitions, an OpenAPI or gRPC spec, published endpoints | API service | `references/overlay-api-service.md` |
| Component tree, router, bundler, browser entry point | Web application | `references/overlay-web-app.md` |
| Published to a package registry, semantic version, public exported surface | Library / SDK | `references/overlay-library.md` |
| Terraform, Pulumi, Helm, Ansible, cluster manifests | Infrastructure | `references/overlay-infrastructure.md` |

Repos frequently match two overlays (an API that also runs scheduled jobs). Apply both; do not force a single choice.

### Step 4 — Build the tree

Read `references/docs-tree.md` for the canonical taxonomy, folder naming rules, and what belongs in each file. Then either:

- **Scaffold mechanically** — `python scripts/docs_scaffold.py --repo <path> --tier 2 --overlay api` creates the directories and drops templated files with placeholders in place. Use this when starting from nothing; it is faster and more consistent than writing twelve files by hand.
- **Write directly** — when the repo already has partial documentation, or when only a few files are needed. Pull templates from `assets/templates/`.

Either way, the templates are starting points, not output. A scaffold left full of placeholders is not a deliverable; fill every section the graph gives you evidence for and flag the rest.

### Step 5 — Write the content, in dependency order

Later documents cite earlier ones, so order matters:

1. `docs/architecture/overview.md` — the code map, built from the graph. Everything else references it.
2. `docs/README.md` — the index, once you know what it indexes.
3. Root `README.md` — the audience router, written after the "front door" set because it summarizes the others.
4. Overlay documents — data contracts, error catalog, route map, whichever apply.
5. Risk documents — limitations register, dependency inventory, security policy.
6. Decision records — backfill the load-bearing choices found in history.

### Step 6 — Verify before presenting

Run the checklist in `references/quality-bar.md`. Its core test: could a competent engineer who has never seen this repo go from the root README to a running local instance without asking a human a question? If not, the setup documentation is incomplete regardless of how polished the rest looks.

Then `python scripts/docs_scaffold.py --repo <path> --audit` to catch dead cross-references, empty templated sections, and forge-specific strings that leaked into prose.

For anything the documentation asserts about behaviour, spot-check it against the graph — `/understand-explain <path>` on two or three modules the code map describes is enough to catch a systematic misreading.

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
├── architecture/          # for engineers and technical reviewers
│   ├── overview.md        # the code map
│   ├── decisions/         # ADRs — the durable "why"
│   └── dependencies.md    # third-party inventory and integration contracts
├── engineering/           # for contributors: setup, testing, conventions
├── operations/            # for whoever is on call: runbooks, observability
├── reference/             # lookup material: config, errors, limitations, glossary
├── security/              # threat model, data handling, disclosure process
└── contributing/          # workflow, review, issue and change templates
```

Two naming rules prevent most drift: **every folder has a `README.md` acting as its index** (forges render it automatically, so the folder explains itself when browsed), and **folder names are plural nouns for collections** (`decisions/`, `runbooks/`, `contracts/`) **and singular for single-subject areas** (`security/`, `product/`).

The taxonomy is a floor, not a ceiling. If the repo already carries directories under `docs/` that this skill does not define, leave them where they are and index them from `docs/README.md` — displacing a folder another tool owns breaks that tool and gains nothing.

## Anti-patterns

- **The scaffold dump.** Twenty files of unfilled headings. Worse than nothing: it signals documentation exists when it does not, and readers stop checking.
- **Writing before analysing.** A code map produced from directory names describes a plausible system rather than this one, and every downstream document inherits the error.
- **Rationale in the code map.** `architecture/overview.md` says *what is where*; ADRs say *why it was chosen*. Mixing them makes the code map churn every time an opinion changes.
- **Hidden limitations.** Burying known issues protects nobody and reads as evasion under scrutiny. A frank limitations register reads as competence.
- **Hand-written API reference.** Generate it from the source of truth (spec, schema, type annotations). Hand-written reference drifts within one sprint.
- **Forge lock-in in prose.** "Open a GitHub issue" in a doc that outlives the migration to a self-hosted forge.
- **Documenting aspiration.** Describing the intended architecture rather than the shipped one. Document what runs; put the target state in a decision record or roadmap where it is clearly labelled as future.

## Reference map

Load only what the current task needs.

| File | Read it when |
|---|---|
| `references/source-analysis.md` | Always — how to build and query the knowledge graph, and which command answers which document |
| `references/docs-tree.md` | Always — the canonical taxonomy and per-file specification |
| `references/host-neutrality.md` | Writing anything that touches issues, reviews, CI, or ownership |
| `references/decision-records.md` | Writing or backfilling ADRs |
| `references/risk-docs.md` | Writing limitations, dependencies, or security documents |
| `references/quality-bar.md` | Before presenting anything — review checklist and rubric |
| `references/diligence.md` | Multi-repo portfolios, audits, acquisitions, vendor review |
| `references/overlay-*.md` | The overlay matching the repo type (Step 3) |

Templates live in `assets/templates/`. Scripts: `scripts/graph_extract.py` (read the knowledge graph), `scripts/docs_scaffold.py` (create and audit the tree).
