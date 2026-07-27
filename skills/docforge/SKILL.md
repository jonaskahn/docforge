---
name: docforge
description: Design and generate a repository's documentation set — the docs/ tree, README and ARCHITECTURE, decision records (ADRs), a known-limitations register, a third-party dependency inventory, security policy, API error catalogs, data contracts and runbooks, plus audience overlays that speak to Business Analyst (BA) and Product Owner (PO) readers. Grounds every document in a knowledge-graph analysis of the actual source before writing, so nothing is invented, and stamps each document with git-hash provenance so staleness is decided by comparison, not by re-guessing. Host-neutral — works on any git host and never hardcodes one forge's paths, and checks for child repos (declared submodules or nested/vendored repos) before any multi-repo review. Use this skill whenever the user mentions documenting a repo or codebase, a docs folder, README or ARCHITECTURE files, ADRs or decision records, onboarding docs, runbooks, known limitations, dependency or licence inventories, technical due diligence or audit readiness, standardizing documentation across several repos, documentation for a Business Analyst or Product Owner, business rules or process flows or requirements traceability, feature catalogs or release notes or success metrics, or whether existing generated docs have drifted from the code — including loose phrasings like "write docs for this project", "our repo has no documentation", "make this repo legible to a new engineer", "docs for BA/PO", "which docs are stale", "should we regenerate this", or "does every repo in here have docs".
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
4. **Everything lives under `docs/`.** Repo root carries only the handful of files that ecosystem tooling and package registries look for by convention, and those are thin pointers into `docs/`. See "Root vs docs/" below.
5. **Stamp provenance in the same pass you write.** Every generated document records the specific source files (by git blob hash) each section draws from. Staleness is later decided by hash comparison, never by re-reading and re-guessing; a change in one recorded file regenerates the section that cites it, not the whole document. See `references/provenance-tracking.md`.
6. **Write for durability, not for the current code.** Describe what the logic *does* at the flow and behaviour level; a same-behaviour refactor must not falsify a document. Never paste code, never link a line number, never anchor a claim to an internal symbol a rename would break — reference files and modules by path instead. State every fact once and link to it; never duplicate it across documents or audience folders. See `references/document-composition.md`.

## Source analysis — run this first

Every document in the tree makes claims about the source. Producing those claims from directory names and file extensions is how documentation ends up describing a system that does not exist. The knowledge graph replaces guessing with retrieval: it gives you the module map, the architectural layers, the call and import edges, the business domains and flows, and a queryable interface for everything the graph does not already state.

**Before any other step**, build or refresh it:

```
/understand
```

That runs a multi-agent pipeline over the project and writes the graph to `.ua/knowledge-graph.json` (older projects keep using `.understand-anything/`). Re-runs are incremental — only changed files are re-analysed — so refreshing an existing graph is cheap. Notes that matter in practice:

- **Check for an existing graph first.** If `.ua/knowledge-graph.json` is present and newer than the last substantive commit, use it as is. If it is stale, `/understand` updates it incrementally rather than starting over.
- **Large repos**: scope the analysis to the part being documented — `/understand src/frontend` — rather than paying for a full pass you do not need. First runs on large codebases consume significant tokens; say so before starting one.
- **`/understand` is a skill, not universally a slash command.** Some coding agents expose it as `/understand`; Codex uses `$understand`; others surface no command at all until the understand-anything skill or plugin is loaded. Before assuming it is missing, load or enable it the way this agent loads skills (a skill listing, a plugin registry, a `Skill`/load call), then invoke it — in plain language where no command exists: *"Use the understand skill to analyze this project."* A missing command means "not loaded yet," not "not installed"; a genuinely absent plugin is the case in §"When the graph is unavailable".
- **Read the graph directly** once built. `python scripts/graph_extract.py --graph .ua/knowledge-graph.json --summary` prints the module inventory, layer assignment and external dependency list in a form that seeds the code map and the dependency inventory.

### Hard gate: flows, product overview, and BA/PO content require the domain graph — no fallback

Everything under `docs/flows/`, `product/overview.md`, `product/capabilities.md`, and any BA/PO overlay document is sourced from `/understand-domain`'s output (the domain graph at the project root, conventionally `$PROJECT_ROOT/.ua/domain-graph.json`), never hand-typed from route files, folder names, or a plausible guess. This is stricter than non-negotiable 1's general fallback allowance — that fallback (direct inspection when the graph is unavailable) applies to architecture/spine documents, **not** to flows.

Before touching any of those documents:

```
python scripts/check_preconditions.py --repo <path> --need domain
```

- If it reports **MISSING knowledge graph** or **MISSING domain graph**, stop. Do not proceed to flow, product, or BA/PO work. Tell the user exactly which command is missing (the script prints it) and wait for it to be run — do not substitute inspection, do not enumerate flows from route definitions as a stand-in.
- The script cannot verify the understand-anything skill itself is installed — confirm that separately (it should appear in your own skill listing; if `/understand` is not recognized at all, the plugin is absent and installation comes first).
- Once both files exist, re-run the check after any `/understand` or `/understand-domain` re-run to confirm freshness before writing.

Architecture and spine documents (`high-level.md`, `setup.md`, `limitations.md`, etc.) may still fall back to direct inspection per non-negotiable 1 and §6 of `references/source-analysis.md` when the knowledge graph alone is unavailable — that latitude does not extend to anything the domain graph feeds.

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

If the graph is unavailable — the plugin is not installed, or the source is not accessible to you — say so plainly and fall back to direct inspection. Do not proceed silently, and do not fabricate a tree from the repo name.

## Workflow

### Step 0 — Interaction mode: when scope is open-ended, plan first, then write part by part

If the user named exactly what to write ("regenerate the security policy", "just the setup doc"), write that and skip to the relevant step. **Otherwise — any open-ended request ("document this repo", "write docs for the project", "our repo has no docs") — do not silently generate the whole tree in one shot.**

1. **Present a plan first — grounded in the analysis, not a generic checklist.** Do the graph analysis (Steps 1–3) *before* the plan: understand the actual code, the knowledge graph, the domain graph's flows, and the business logic, then lay out the ordered set of documentation parts those findings justify — the real subsystems, flows, and domains you found, grouped by area (architecture, flows, product, operations, reference, security, …). One line per part: what it will cover (naming the concrete subsystem/flow, per `references/document-catalog.md`) and why a reader needs it. State the tier and overlays in the same message. Get the user's confirmation on the plan before writing prose.
2. **Then write one part at a time, in dependency order** (Step 5). For each part, in order:
   - **Re-ground before you write.** Pull every must-present element for that document (`references/document-catalog.md`) from the knowledge graph, the domain graph, and the code. If a fact the document needs is not yet in the graph, retrieve it — a narrow `/understand-chat`, an `/understand-explain <path>`, or direct inspection — *before* writing, not around it. Never write a part on thin context: if the source genuinely cannot answer a required element, that atomic value becomes a typed `<UPPER_SNAKE>` token (non-negotiable 1), and everything around it is still written in full.
   - Write to the default depth (deep-dive — see Step 5 and `references/depth-and-audience.md`), stamp provenance as you write, present the finished part, and **pause** for the user to confirm or redirect before starting the next. Fold feedback on part N into parts N+1…
3. **This cadence never relaxes non-negotiable 1.** Every part you hand over is *complete* — no punted derivable facts, no unfilled `{{…}}` scaffolds, only typed `<UPPER_SNAKE>` tokens for genuinely external values. The confirmation gate governs *scope and ordering*, not fill-completeness. The goal is a reviewable, steerable stream — not a thirty-file dump the user must audit at once, and not a scaffold they must finish.

When the user explicitly says "just generate everything," honor it: skip the per-part pauses, still present the one-line plan first so they can catch a wrong tier or a missing overlay before you spend the tokens.

### Step 1 — Build the graph, then read the repo

Run the analysis above, then fill the gaps it does not cover:

- **Manifests and build files** — `pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`, `pom.xml`, `*.csproj`. Version pins and dependency ranges come from here, not from the graph.
- **Repo type signals** — a web framework, an HTTP server, DAG or scheduler definitions, a published package config, infrastructure-as-code, embedded business logic (validation rules, approval thresholds, eligibility conditions). These select your overlays; the graph's layer assignment usually makes them obvious.
- **What documentation already exists** — an existing `README`, `docs/`, wiki exports, comments that read like design notes, ADR-ish files. Existing content is evidence about what people needed to write down; migrate it, do not replace it.
- **Operational reality** — CI config, container and deploy manifests, and the environment variables the code actually reads.
- **History for the "why"** — `git log` on architecturally significant paths, and merge commits with substantive messages. This is where backfilled decision records come from, and it is the one thing the graph cannot supply.
- **Business flows** — run `python scripts/check_preconditions.py --repo <path> --need domain` first; it must report READY for both the knowledge graph and the domain graph before you enumerate flows. Then read `/understand-domain`'s output to enumerate the domains, flows and steps in the code's own terms. That list *is* the set of flow documents to build under `docs/flows/` — never hand-type it, since the point of the analysis is to surface flows a writer would miss. Each flow starts as a flat file (`docs/flows/<flow>.md`); it is promoted to a folder only when you write real audience depth for it in the same pass. See `references/document-composition.md`.
- **Child repos** — before any multi-repo work, and as a cheap sanity check otherwise, run `python scripts/discover_repos.py --root <path>`. It reports declared submodules and, more importantly, nested repos present on disk but *not* declared in `.gitmodules` (vendored copies, `git subtree` merges, hand-cloned submodules). For single-repo work this just confirms scope; for diligence it is load-bearing — see Step 2 and `references/diligence-collection.md`.

### Step 2 — Choose a tier

Documentation weight should be proportionate to team size and external scrutiny; heavy structure on a two-person repo costs more than it returns.

| Tier | When it fits | What gets built |
|---|---|---|
| **1 — Spine** | Any repo. Small teams, internal tools, early projects | Root pointers, `docs/README.md` index, `docs/architecture/high-level.md`, `docs/engineering/setup.md`, `docs/reference/limitations.md`, `CHANGELOG` |
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

Audience content follows the three-class model in `references/audience-matrix.md`: a subject two or more audiences share is written **once**, as an aligned topic — `flows/<flow>.md` or `architecture/concepts/<subsystem>.md` — while genuinely single-reader material stays in that audience's own folder (`product/business-analyst/`, `product/product-owner/`). An aligned topic is a **flat file by default**; it becomes a folder (`<topic>/README.md` + deep-dive subfiles) only at the moment real per-reader depth is written, in the same pass — never a folder with a promised subfile that isn't there yet. Every fact is owned once and linked, never pasted into two folders. Do not produce an unrequested audience folder or an empty deep-dive subfile; an empty or promised-but-missing overlay is the same anti-pattern as an unfilled scaffold. Read `references/audience-matrix.md`, `references/document-composition.md` and `references/depth-and-audience.md` before writing any flow or audience content.

### Step 4 — Build the tree

Read `references/docs-tree.md` for the canonical taxonomy, folder naming rules, and what belongs in each file. Then either:

- **Scaffold mechanically** — `python scripts/docs_scaffold.py --repo <path> --tier 2 --overlay api --overlay business-analyst` creates the directories and drops templated files with placeholders in place. Use this when starting from nothing; it is faster and more consistent than writing files by hand.
- **Write directly** — when the repo already has partial documentation, or when only a few files are needed. Pull templates from `assets/templates/`.

Either way, the templates are starting points, not output. A scaffold left full of `{{…}}` placeholders is not a deliverable — those markers mean "not yet written," and every one must be replaced with derived content before presenting. The only marks that legitimately survive into a finished document are typed `<UPPER_SNAKE>` tokens standing in for genuinely external facts (non-negotiable 1); everything else you have evidence for, you write.

### Step 5 — Write the content, in dependency order

**Consult the document catalog for each document before writing it, and re-ground it in the source.** `references/document-catalog.md` is the content contract for every doc type — what it must present, what to keep out (so two documents don't overlap), and the one Diátaxis mode it stays in. Before writing any document — plan-first path or a single explicitly-requested doc — confirm the graph and code actually supply every must-present element, and retrieve what's missing rather than writing around it (the re-ground rule in Step 0 applies to every document, not only the plan-first cadence). **One document, one mode:** a tutorial doesn't explain, a reference doesn't teach, an explanation doesn't enumerate steps; when material spans modes, section and cross-link rather than blend. Orientation documents (the READMEs, `product/overview.md`) are the only ones that summarize across modes, and only as a router that delegates depth.

**Default depth is deep-dive, not orientation.** Within each document's mode, write to the depth that lets a stranger to the repo genuinely understand and approach the subsystem — mechanism, edge cases, failure modes, and the adjacent pieces (what feeds it, what it feeds, what breaks it) that make it self-standing. The only thing you cut is filler, never signal; "detailed" means more useful information, not more words. See `references/depth-and-audience.md` for the depth ladder and the value brake, and non-negotiable 6 for keeping deep sections durable (behaviour-level, no code, no line numbers).

Later documents cite earlier ones, so order matters:

1. `docs/architecture/high-level.md` — the stable map, built from the graph. Everything else references it. Then `low-level.md` and `architecture/concepts/<subsystem>.md` deep-dives for the significant subsystems (same flat-then-promoted rule as flows).
2. `docs/flows/<flow>.md` — one flat file per flow: L0, plain-language L1 steps, every notice, a diagram whenever the flow has more than one step or a branch. Promote a specific flow to `docs/flows/<flow>/README.md` + subfile only in the same pass you write that subfile's real content — never split the write across passes.
3. `docs/README.md` — the index, once you know what it indexes.
4. Root `README.md` — the audience router, written after the "front door" set because it summarizes the others.
5. Overlay and audience-specific documents — data contracts, error catalog, route map, BA requirements-traceability, PO feature catalog and metrics, whichever apply.
6. Risk documents — `reference/limitations.md`, `architecture/tech-debt.md`, `architecture/constraints.md`, dependency inventory, security policy.
7. Decision records — backfill the load-bearing choices found in history.

**Stamp provenance as you write, not afterward.** The source files you just read to write a section *are* its provenance, so record them then — each document gets the frontmatter block and the source-files-per-section list described in `references/provenance-tracking.md`, aggregated into `.docforge/manifest.json`. Retrofitting hashes as a cleanup pass invites guessing about which files a section actually drew from.

### Step 6 — Verify before presenting

Run the checklist in `references/quality-bar.md`. Its core test: could a competent engineer who has never seen this repo go from the root README to a running local instance without asking a human a question? If not, the setup documentation is incomplete regardless of how polished the rest looks.

Check each document against its `references/document-catalog.md` contract: every must-present element is there, nothing that belongs in another document leaked in, and the document stayed in its one Diátaxis mode.

Then `python scripts/docs_scaffold.py --repo <path> --audit` to catch dead cross-references, empty templated sections, and forge-specific strings that leaked into prose.

For anything the documentation asserts about behaviour, spot-check it against the graph — `/understand-explain <path>` on two or three modules the code map describes is enough to catch a systematic misreading.

## Updating existing docs — check before you rewrite

When asked to refresh docs that already carry docforge provenance, do not re-read and re-guess. Compare hashes:

1. `python scripts/check_provenance.py --manifest .docforge/manifest.json`.
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
- **Orientation masquerading as documentation.** A page that says what a subsystem *is* but never how it works, why it's built that way, what its edge cases and failure modes are. Deep-dive is the default; shallow is only correct for a genuinely trivial part. Cut filler, never signal (`references/depth-and-audience.md`).
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
| `references/docs-tree.md` | Always — the canonical taxonomy, folder naming, and placement rules |
| `references/document-catalog.md` | Before writing any document — what each doc type must present and must keep out, its Diátaxis mode, and its source-of-truth |
| `references/provenance-tracking.md` | Always — frontmatter schema, manifest format, the staleness algorithm, partial-rewrite mechanics |
| `references/host-neutrality.md` | Writing anything that touches issues, reviews, CI, or ownership |
| `references/decision-records.md` | Writing or backfilling ADRs |
| `references/risk-docs.md` | Writing limitations, dependencies, or security documents |
| `references/quality-bar.md` | Before presenting anything — review checklist and rubric |
| `references/audience-matrix.md` | The three document classes (aligned / audience-specific / shared-fact spine), the BA/PO split, and which folder owns which fact |
| `references/document-composition.md` | Always when writing flow or audience content — the flat-file-by-default and atomic-promotion rule, the two invariants, and the durability rules (no code, no duplication, write at the slowest layer) |
| `references/depth-and-audience.md` | The depth ladder (L0–L3), which reader consumes which depth, and which understand-anything command feeds which cell |
| `references/overlay-business-analyst.md` | Writing anything under `docs/product/business-analyst/` |
| `references/overlay-product-owner.md` | Writing anything under `docs/product/product-owner/` |
| `references/diligence.md` | Multi-repo portfolios, audits, acquisitions, vendor review — the portfolio layer |
| `references/diligence-collection.md` | Any multi-repo job — assembling the collection, gap-checking members, recording composition honestly |
| `references/overlay-*.md` | The repo-type overlay matching the repo (Step 3) |

Templates live in `assets/templates/`. Scripts:
- `scripts/check_preconditions.py` — gate flow/product/BA/PO work on the knowledge graph and domain graph actually existing; run before Step 1's business-flows bullet
- `scripts/validate_graphs.py` — the diagnostic probe for when `check_preconditions.py` reports a graph missing but `.ua/` holds data; lists both graph folders' contents with sizes, JSON validity and node/edge counts
- `scripts/graph_extract.py` — read the knowledge graph
- `scripts/docs_scaffold.py` — create and audit the tree
- `scripts/check_provenance.py` — recompute git blob hashes for every file recorded in the manifest; report `FRESH` / `PARTIAL` / `MISSING` per document and section
- `scripts/discover_repos.py` — walk a root for declared submodules and undeclared nested repos, reporting each member's docforge status so gaps surface before a review, not during it

---

## When a graph "isn't found" but the `.ua/` folder exists

If `check_preconditions.py` or a workflow step reports the graph missing while `.ua/` clearly holds data, the file on disk and the file the step expects have diverged — a partial write, an unreadable JSON, or the wrong filename. Diagnose before re-running anything expensive:

```bash
python scripts/validate_graphs.py --repo . --verbose
```

It prints what actually sits in `.ua/` and `.understand-anything/` — filenames, sizes, timestamps, JSON validity, node/edge counts — so a false "not found" separates cleanly from a genuinely absent or truncated graph. Where `check_preconditions.py` is the gate, this is the probe you reach for when the gate's answer surprises you. The two most common causes: `/understand` reported success but wrote nothing (re-run it — the pass is incremental and cheap), or the JSON is truncated from an interrupted write (re-run to rewrite it). Both graph locations and every parent up to the git root are searched, so subdirectory invocation is not the cause.
