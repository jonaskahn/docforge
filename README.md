<div align="center">
  <img src="logo.png" alt="docforge" width="200" />

  <p><b>PRESS START</b> — an AI agent skill that designs and writes a repository's whole documentation set, grounded in the actual source. No invented lore.</p>

  [![MIT License](https://img.shields.io/badge/license-MIT-10b981?style=flat-square)](LICENSE)
  [![Claude Code](https://img.shields.io/badge/works_with-Claude_Code-10b981?style=flat-square)](https://docs.claude.com/claude-code/skills)
  [![agentskills](https://img.shields.io/badge/format-Agent_Skill-10b981?style=flat-square)](https://agentskills.io)
</div>

---

## ▓▒░ STAGE SELECT ░▒▓

Point it at a repo and it designs and writes the [`docs/`](skills/docforge/references/docs-tree.md) tree that survives — organized by *topic*, not by audience, so a fact is written once and every reader gets routed to it. Pick a world:

| World | What's inside |
|---|---|
| **[`product/`](skills/docforge/references/docs-tree.md)** | overview, feature catalog, roadmap, plus [Business Analyst](skills/docforge/references/overlay-business-analyst.md) and [Product Owner](skills/docforge/references/overlay-product-owner.md) side-quest overlays for readers who never touch the code |
| **`flows/`** | one file per business flow, sourced from the domain graph (never hand-typed) — flat by default, promoted to a per-flow folder with BA/engineering/PO deep-dive subfiles only once real depth is written — [`document-composition.md`](skills/docforge/references/document-composition.md) |
| **`architecture/`** | a two-altitude map: [`high-level.md`](skills/docforge/assets/templates/architecture-high-level.md) (the stable overworld — context, building blocks, boundaries) and [`low-level.md`](skills/docforge/assets/templates/architecture-low-level.md) (the dungeon — component decomposition, deep mechanism, its own faster lifecycle), plus a dependency inventory, a **tech-debt register**, a **constraints register**, and [decision records (ADRs)](skills/docforge/references/decision-records.md) |
| **`engineering/`** | setup, testing, conventions, release process — the path from clone to first merge |
| **`operations/`** | deployment, observability, one runbook per recurring incident (boss fight guide) |
| **`reference/`** | config keys, a **known-limitations register**, a glossary, and (for API-shaped repos) an **error catalog** |
| **`security/`** | posture summary, threat model, data handling, disclosure process |
| **`contributing/`** | workflow, ownership, host-neutral issue/change templates |
| **AI-agent context** *(on by default — [`agent-context`](skills/docforge/references/overlay-agent-context.md) bonus level, opt out with `--no-agent-context`)* | a ≤100-line `AGENTS.md` kernel plus `CLAUDE.md`, `.claude/settings.json`, and brief `docs/agents/` stubs that link back to the human docs above instead of re-deriving them. The one exception, `docs/agents/patterns.md`, carries real content because it has no other home. Written *last*, once every human doc it links to already exists |

## ▓▒░ POWER-UPS ░▒▓

Four buffs make the output trustworthy rather than just plausible-looking:

- **🛡 GROUNDED.** Reads the codebase through a knowledge graph before writing a word, so every claim is verifiable — no invention, no drift. Flows and product content are hard-gated on the *domain* graph specifically; no fallback to guessing from folder names.
- **⚔ INDEPENDENTLY AUDITED.** Each finished document faces a fresh reviewer pass against the source it claims to describe — not the agent that wrote it — before it's marked complete. See [`document-audit.md`](skills/docforge/references/document-audit.md).
- **🗺 PROVENANCE-TRACKED.** Each document records the exact source files it draws from by git blob hash in a per-repo [`.docforge/manifest.json`](skills/docforge/.metadata/manifest.json), so "has this drifted?" is answered by comparison, not a re-read and a guess — only the stale section gets rewritten. Format in [`provenance-tracking.md`](skills/docforge/references/provenance-tracking.md).
- **🌐 HOST-NEUTRAL.** Works on any git host; never hardcodes one forge's paths (see [`host-neutrality.md`](skills/docforge/references/host-neutrality.md)). For multi-repo diligence it discovers the full collection first — declared submodules and undeclared nested/vendored repos alike, via [`discover_child_repos.py`](skills/docforge/scripts/discover_child_repos.py) — see [`diligence-collection.md`](skills/docforge/references/diligence-collection.md).

## ▓▒░ HOW TO PLAY ░▒▓

```sh
npx skills add jonaskahn/docforge        # this world only
npx skills add jonaskahn/docforge -g -y  # unlock everywhere
```

Claude Code and compatible agents load the skill automatically once installed.

> **NOTE FROM THE GAME MASTER:** PromptScript does not support global skill installs, so it is skipped during `-g` installation (`Failed to install 1`). Expected, doesn't affect any other agent. To use docforge with PromptScript, install per-project (omit `-g`).

### Alt install — Claude Code plugin cartridge

This repo also ships as a native Claude Code [plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces) ([`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json)) — same game, different cartridge slot:

```
/plugin marketplace add jonaskahn/docforge
/plugin install docforge@docforge
```

## ▓▒░ GAME PLAN ░▒▓

It activates on its own when you're documenting a repo. Or invoke it directly with `/docforge`, or just describe the quest:

> "Document this repo from scratch — Python API service, Postgres backend"
>
> "Audit this repo for diligence before the partner signs"
>
> "Generate ADRs from this service's git history"
>
> "Add the API-service overlay onto our existing docs/"
>
> "Write BA docs for this repo — business rules and process flows"
>
> "Which of our generated docs have drifted from the code?"

Only the reference files relevant to your task load into context, so the agent stays fast and doesn't lag.

### How a run actually plays out

Every invocation follows the same cadence, defined in [`SKILL.md`](skills/docforge/SKILL.md)'s Step 0: read enough of the codebase to plan, present the planned folder tree, present each document's intended content, get confirmation, then write — one part at a time, never a silent whole-tree dump (no save-scumming the boss). Flags below change *scope* or *pacing*, never which of those steps fires:

### ▓▒░ CONTROLLER MAPPING ░▒▓

| Button | Effect |
|---|---|
| `--revise all` | Re-check the whole existing tree against source and regenerate only what has drifted |
| `--revise <area>` | Same check, scoped to one manifest entry or group — e.g. `--revise security` |
| `--auto-accept` | Skip the confirmation pauses, but still show the plan and every finished part in order |
| `--plan-only` | Stop after the structure and per-document plan are recorded — no content written |
| `--resume` | Continue from the manifest's first unfinished entry instead of restarting the plan |
| `--status` | Print current progress and stop — no scaffolding, no writing |
| `--no-agent-context` | Opt out of the `agent-context` overlay, which is otherwise scaffolded and written by default on every run |

## ▓▒░ INVENTORY ░▒▓

| Item | Purpose |
|---|---|
| [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json), [`plugin.json`](.claude-plugin/plugin.json) | Native Claude Code plugin manifests — the `/plugin marketplace add` install path |
| [`skills/docforge/SKILL.md`](skills/docforge/SKILL.md) | Entry point — non-negotiables, source analysis, tier + overlay selection, invocation flags, workflow, anti-patterns |
| [`references/source-analysis.md`](skills/docforge/references/source-analysis.md) | Build and query the knowledge graph; which command answers which document |
| [`references/docs-tree.md`](skills/docforge/references/docs-tree.md) | Canonical taxonomy — naming rules, the full tree, per-folder spec, placement decision table, migrating an existing `docs/` |
| [`references/document-catalog.md`](skills/docforge/references/document-catalog.md) | The content contract for every document type — what must appear, what must not, its Diátaxis mode, its source of truth |
| [`references/document-audit.md`](skills/docforge/references/document-audit.md) | The independent per-document audit gate that runs before a document is marked complete |
| [`references/provenance-tracking.md`](skills/docforge/references/provenance-tracking.md) | Frontmatter schema, manifest format, staleness algorithm, partial rewrites |
| [`references/host-neutrality.md`](skills/docforge/references/host-neutrality.md) | Language rules so docs outlive any one forge |
| [`references/decision-records.md`](skills/docforge/references/decision-records.md) | ADR format, numbering, backfilling from history |
| [`references/risk-docs.md`](skills/docforge/references/risk-docs.md) | Limitations register, dependency inventory, security policy |
| [`references/quality-bar.md`](skills/docforge/references/quality-bar.md) | Review checklist and rubric for finished docs |
| [`references/document-composition.md`](skills/docforge/references/document-composition.md) | One topic, many readers — the document-as-folder pattern, no-loss/notice invariants, durability rules (no code, no duplication) |
| [`references/depth-and-audience.md`](skills/docforge/references/depth-and-audience.md) | The depth ladder (L0–L3), which reader reads which depth, and which understand-anything command feeds each |
| [`references/audience-matrix.md`](skills/docforge/references/audience-matrix.md) | The three document classes (aligned / audience-specific / shared-fact spine), the BA/PO split, and which folder owns which fact |
| [`references/diligence.md`](skills/docforge/references/diligence.md) | Multi-repo portfolio layer for audits, acquisitions, vendor review |
| [`references/diligence-collection.md`](skills/docforge/references/diligence-collection.md) | Discover the repo collection and gap-check every member first |
| [`references/overlay-api-service.md`](skills/docforge/references/overlay-api-service.md), [`overlay-data-pipeline.md`](skills/docforge/references/overlay-data-pipeline.md), [`overlay-web-app.md`](skills/docforge/references/overlay-web-app.md), [`overlay-library.md`](skills/docforge/references/overlay-library.md), [`overlay-infrastructure.md`](skills/docforge/references/overlay-infrastructure.md) | Repo-type overlays — the extra documents each kind of project needs |
| [`references/overlay-business-analyst.md`](skills/docforge/references/overlay-business-analyst.md), [`overlay-product-owner.md`](skills/docforge/references/overlay-product-owner.md) | Audience overlays for BA/PO readers |
| [`references/overlay-agent-context.md`](skills/docforge/references/overlay-agent-context.md) | The `AGENTS.md`/`CLAUDE.md`/`docs/agents/` overlay — the AI coding agent as a fourth reader class |
| [`instructions/`](skills/docforge/instructions/) | Writing-craft layer for select document types — layout, data sources, provenance tagging. Covers [README](skills/docforge/instructions/README.md), [product overview](skills/docforge/instructions/product-overview.md), [product capabilities](skills/docforge/instructions/product-capabilities.md), [flows](skills/docforge/instructions/flows.md), [high-level](skills/docforge/instructions/architecture-high-level.md) and [low-level](skills/docforge/instructions/architecture-low-level.md) architecture, [decision records](skills/docforge/instructions/decision-records.md), [dependencies](skills/docforge/instructions/dependencies-inventory.md), [tech-debt](skills/docforge/instructions/tech-debt-register.md), [limitations](skills/docforge/instructions/limitations-register.md), [security policy](skills/docforge/instructions/security-policy.md), [setup guide](skills/docforge/instructions/setup-guide.md), and [`agents-kernel`](skills/docforge/instructions/agents-kernel.md) for the `AGENTS.md` cartridge itself. The content contract lives in `document-catalog.md` above |
| [`.metadata/`](skills/docforge/.metadata/) | Manifest, template, and status schemas that drive the plan-first workflow — [`manifest-schema.json`](skills/docforge/.metadata/manifest-schema.json), [`template-schema.json`](skills/docforge/.metadata/template-schema.json), [`status-schema.json`](skills/docforge/.metadata/status-schema.json), and worked examples ([`manifest.json`](skills/docforge/.metadata/manifest.json), [`document-templates.json`](skills/docforge/.metadata/document-templates.json), [`generation-status.json`](skills/docforge/.metadata/generation-status.json)). Copied into a target repo as its durable `.docforge/manifest.json` fill-state record |

Plus [`assets/templates/`](skills/docforge/assets/templates/) — a scaffold file for every spine and overlay document, including the `agent-context` set (`agents-kernel.md`, `agents-architecture.md`, `agents-patterns.md`, `agents-glossary.md`, `agents-testing.md`, `agents-tech-debt.md`, `agents-flow.md`, `agents-conventions.md`, `claude-md.md`, `claude-local-md.md`, `claude-settings.json`) — and [`scripts/`](skills/docforge/scripts/), the tool belt:

Source-specific graph modules carry a `graph_source_<name>` prefix; source-agnostic tools carry none.

| Script | Purpose |
|---|---|
| [`precheck_graph.py`](skills/docforge/scripts/precheck_graph.py) / [`.js`](skills/docforge/scripts/precheck_graph.js) | Gate every invocation on a code graph existing (and, for `--need flow`, a flow graph); report every ready source and how each is read |
| [`graph_source_registry.py`](skills/docforge/scripts/graph_source_registry.py) / [`.js`](skills/docforge/scripts/graph_source_registry.js) | The ordered registry of graph sources — resolve a capability to a ready source, or list them all |
| [`graph_source_understand_anything.py`](skills/docforge/scripts/graph_source_understand_anything.py) / [`.js`](skills/docforge/scripts/graph_source_understand_anything.js) | Understand-Anything source (JSON): detect `.ua/*.json` |
| [`graph_source_gitnexus.py`](skills/docforge/scripts/graph_source_gitnexus.py) / [`.js`](skills/docforge/scripts/graph_source_gitnexus.js) | GitNexus source (ladybug DB): detect `.gitnexus/lbug` + staleness |
| [`graph_source_gitnexus_reader.py`](skills/docforge/scripts/graph_source_gitnexus_reader.py) / [`.js`](skills/docforge/scripts/graph_source_gitnexus_reader.js) | Optional offline reader for GitNexus's ladybug DB (via `@ladybugdb/core` / a ladybug Python binding); the gitnexus MCP is the preferred read path |
| [`graph_source_codegraph.py`](skills/docforge/scripts/graph_source_codegraph.py) / [`.js`](skills/docforge/scripts/graph_source_codegraph.js) | CodeGraph source (SQLite DB): detect `.codegraph/codegraph.db`. No staleness check (auto-sync) and no offline reader — read only via the `codegraph_explore` MCP tool |
| [`read_graph.py`](skills/docforge/scripts/read_graph.py) / [`.js`](skills/docforge/scripts/read_graph.js) | Read a JSON code graph and extract the module inventory, layer assignment, and external dependency list that seed the code map |
| [`derive_flow_graph.py`](skills/docforge/scripts/derive_flow_graph.py) / [`.js`](skills/docforge/scripts/derive_flow_graph.js) | Derive a provisional flow graph from a code graph when a source has no native flows (writes to git-ignored `.docforge/tmp/`) |
| [`diagnose_graphs.py`](skills/docforge/scripts/diagnose_graphs.py) / [`.js`](skills/docforge/scripts/diagnose_graphs.js) | Diagnose "graph not found" false positives by scanning for graph files at the repo root |
| [`scaffold_docs.py`](skills/docforge/scripts/scaffold_docs.py) / [`.js`](skills/docforge/scripts/scaffold_docs.js) | Scaffold the `docs/` tree for a chosen tier and overlay set (dry-run preview or real write), and audit an existing tree against the taxonomy |
| [`manage_manifest.py`](skills/docforge/scripts/manage_manifest.py) / [`.js`](skills/docforge/scripts/manage_manifest.js) | Create and maintain `.docforge/manifest.json` — the durable plan and per-document fill-state record |
| [`check_staleness.py`](skills/docforge/scripts/check_staleness.py) / [`.js`](skills/docforge/scripts/check_staleness.js) | Compare recorded git blob hashes against the working tree to decide whether a document (or one of its sections) needs rewriting |
| [`lint_document.py`](skills/docforge/scripts/lint_document.py) / [`.js`](skills/docforge/scripts/lint_document.js) | Run the mechanical pre-checks that feed the independent per-document audit |
| [`lint_agents_kernel.py`](skills/docforge/scripts/lint_agents_kernel.py) / [`.js`](skills/docforge/scripts/lint_agents_kernel.js) | `AGENTS.md`-specific rubric — the 100-line cap, 7-section shape, tagline/test-sentence conventions, and dangling `@docs/agents/…` references |
| [`discover_child_repos.py`](skills/docforge/scripts/discover_child_repos.py) / [`.js`](skills/docforge/scripts/discover_child_repos.js) | Assemble the full repo collection for a diligence job — parent, declared submodules, and undeclared nested/vendored repos |

## ▓▒░ SYSTEM REQUIREMENTS ░▒▓

Every script under [`scripts/`](skills/docforge/scripts/) ships in two equivalent forms — `<name>.py` and `<name>.js` — same flags, same output, same exit codes. Nothing to install: each uses only its runtime's standard library / built-in modules. You need one of:

- **Python 3.9+** (`python3 --version`), or
- **Node.js 18+** (`node --version`)

`git` on `PATH` is also required (used for blob hashing and submodule discovery). The skill picks whichever runtime is present; if both are, either works.

## ▓▒░ MULTIPLAYER MODE ░▒▓

References live in [`skills/docforge/references/`](skills/docforge/references/), one topic per file. To change one: fork, edit the `.md`, open a PR.

To add a reference: create `references/<topic>.md`, then register it in [`SKILL.md`](skills/docforge/SKILL.md) and the table above.

Content is read by an agent, not a human — keep it dense:

- Lead with the common pattern, not the simplest case
- One complete, runnable example per concept
- Gotchas inline, no separate warnings section
- No intros, no marketing — just the technical substance

Wrong or missing guidance? Open an issue with what you asked, what the skill produced, and what it should have said. High-score table is community-maintained.

## ▓▒░ CREDITS ░▒▓

[MIT](LICENSE)
