<div align="center">
  <img src="logo.png" alt="Docforge" width="200" />

  <h1>DOCFORGE</h1>

  <p><strong>INSERT REPOSITORY. GENERATE DOCUMENTATION. NO INVENTED LORE.</strong></p>
  <p>An Agent Skill that designs, writes, audits, and maintains documentation grounded in the actual source.</p>

  [![Version](https://img.shields.io/badge/version-1.0.2-10b981?style=flat-square)](meta.json)
  [![Agent Skill](https://img.shields.io/badge/format-Agent_Skill-10b981?style=flat-square)](https://agentskills.io)
  [![MIT License](https://img.shields.io/badge/license-MIT-10b981?style=flat-square)](LICENSE)
</div>

---

Created by [Jonas Kahn](https://github.com/jonaskahn), Docforge is a source-grounded documentation cartridge for AI coding agents. It ships as an Agent Skill and a Claude Code plugin: instructions, references, templates, schemas, and paired Python/Node tools—not a Markdown generator library.

## ▓▒░ WORLD MAP ░▒▓

- [Boot sequence](#-boot-sequence-)
- [Start game](#-start-game-)
- [Core loop](#-core-loop-)
- [Graph cartridges](#-graph-cartridges-)
- [Stage select](#-stage-select-)
- [Controller mapping](#-controller-mapping-)
- [Inventory](#-inventory-)
- [System requirements](#-system-requirements-)

## ▓▒░ BOOT SEQUENCE ░▒▓

Prerequisites for the Agent Skills install path:

- a compatible coding agent
- Node.js 18+ with `npm`/`npx`
- `git`
- network access

```sh
# Install in the current project
npx skills add jonaskahn/docforge

# Install globally for supported agents
npx skills add jonaskahn/docforge -g -y
```

Package metadata declares support for Claude Code, Codex, OpenCode, and Gemini CLI. The commands above come from [`meta.json`](meta.json); they require external network access and were not executed during this README update.

### CLAUDE CODE CARTRIDGE

Docforge also ships a native [Claude Code marketplace manifest](.claude-plugin/marketplace.json):

```text
/plugin marketplace add jonaskahn/docforge
/plugin install docforge@docforge
```

Both install paths load the same [`SKILL.md`](skills/docforge/SKILL.md). These package-declared plugin commands were not executed during this README update.

## ▓▒░ START GAME ░▒▓

Describe the documentation quest in plain language:

```text
Document this repository from scratch.
Create diligence documentation for this service.
Generate ADRs from the repository history.
Add the API and Business Analyst overlays.
Make this repository ready for AI coding agents.
Check which generated docs have drifted from source.
```

Slash-command support depends on the host. Where registered, use `/docforge`; plain-language requests work across compatible agents.

### FIRST MISSION

```text
/docforge
```

Expected result:

1. Docforge performs only read-only discovery: repository/manifest state and
   available graph sources.
2. It presents all applicable unresolved scope questions together: goal,
   documentation tier, audience, repository shape, graph source only when it
   is unresolved, and execution mode. Each question explains its choices;
   native selection controls are used when the host provides them.
3. After you answer the set, it summarizes the complete scope and asks you to
   confirm, edit, or cancel. This confirmation is required even when
   Auto-accept is selected. It does not create a manifest, documents, or a
   graph index during intake.
4. After you confirm the scope, it reuses the selected provider’s persisted graph
   and native skill/MCP queries to inventory the repository.
5. It always shows the exact manifest-backed tree plus a one-line
   content/evidence card for every document before writing. Auto-accept skips
   only the pause, not the displayed tree.
6. If discovery changes the manifest later, it shows the path/requirement delta
   and refreshed tree before writing continues.

If no code graph exists, Docforge explains the setup choices. It never installs
or wires a provider automatically, and it requests separate approval before an
agent runs a repository index build or refresh.

## ▓▒░ CORE LOOP ░▒▓

```text
PRECHECK → ANALYZE → PLAN → WRITE → AUDIT → TRACK
```

1. **PRECHECK** — require one supported code graph.
2. **ANALYZE** — read graph data, source, config, manifests, existing docs, CI, deployment files, git history, and child repositories.
3. **PLAN** — choose a named tier and overlays, initialize manifest v2, then preview its exact tree.
4. **WRITE** — generate one document at a time in dependency order.
5. **AUDIT** — use a fresh artifact-only reviewer when supported, otherwise a recorded cold artifact-only pass; derivable gaps force a rewrite.
6. **TRACK** — stamp section-level source paths and git blob hashes so later runs update only what drifted.

Docforge writes behavior and boundaries, not prose tied to private symbols or line numbers. Derivable facts must be completed; only truly external values may remain as typed tokens such as `<SECURITY_CONTACT>`.

Read the full [workflow](skills/docforge/SKILL.md#workflow), [document contracts](skills/docforge/references/document-catalog.md), [audit gate](skills/docforge/references/document-audit.md), and [provenance model](skills/docforge/references/provenance-tracking.md).

## ▓▒░ GRAPH CARTRIDGES ░▒▓

A code graph is the universal key. Docforge reuses, rather than replaces, the
provider’s pre-generated index:

- Understand Anything’s shareable structural and domain/flow JSON, queried
  through its skills or the deterministic JSON reader;
- GitNexus’s LadybugDB knowledge graph and indexed processes, queried through
  its MCP/skills or project-local CLI;
- CodeGraph’s auto-synchronized SQLite index, queried through
  `codegraph_explore` for relevant source, call paths, and blast radius.

Only one readable provider is required. When GitNexus, Understand Anything, or
CodeGraph is ready, the normal intake reports and uses that provider; absent
competitor indexes are not gaps and stay hidden unless you request provider
comparison or troubleshooting.

Only catalog entries declaring `flow_graph` require flow data. They prefer native flow data; when only a code graph is available, Docforge derives a provisional, entry-point-first flow graph in the git-ignored `.docforge/tmp/` workspace.

Provider capabilities and setup live in [graph dispatch](skills/docforge/references/graph-sources.md); the reasoning loop lives in [flow derivation](skills/docforge/references/flow-derivation.md).

## ▓▒░ STAGE SELECT ░▒▓

Choose **Spine** for a repository baseline, **Diligence** for external scrutiny, or **Portfolio** for a multi-repository review. Add repo-type power-ups (`api`, `web`, `library`, `data-pipeline`, `infrastructure`) and audience power-ups (`business-analyst`, `product-owner`, `agent-context`) as needed.

The Business Analyst overlay generates a business process view, rule catalog,
and requirements traceability. The Product Owner overlay generates feature
value/status, success metrics, release impact, and ticket traceability only
when ticket evidence exists. Select `agent-context` for a compact `AGENTS.md`
kernel, Claude shims/settings, and token-budgeted `docs/agents/` views; it
writes after the human-facing documents it links to.

The tier rules, overlay signals, and complete level layout live in the [canonical docs tree](skills/docforge/references/docs-tree.md) and [`SKILL.md`](skills/docforge/SKILL.md).

## ▓▒░ CONTROLLER MAPPING ░▒▓

Use `--revise all` or `--revise <area>` for stale content, `--plan-only` to stop after manifest initialization and preview, `--resume` to continue a saved run, and `--status` for a read-only progress report.

`--auto-accept` uses defaults and skips conversational pauses. It does not authorize installation, global configuration, graph construction or refresh, archive/delete actions, or other separately approved side effects; it also does not skip grounding, plan display, audits, or final checks.

The exact flag semantics and composition rules live in the [workflow](skills/docforge/SKILL.md#workflow).

## ▓▒░ INVENTORY ░▒▓

[`SKILL.md`](skills/docforge/SKILL.md) is the entry cartridge. [`.metadata/catalog.json`](skills/docforge/.metadata/catalog.json) is the canonical registry; [`references/`](skills/docforge/references/) holds owned prose contracts, [`instructions/`](skills/docforge/instructions/) holds writing craft, and [`assets/templates/`](skills/docforge/assets/templates/) holds output scaffolds.

[`scripts/`](skills/docforge/scripts/) contains paired Python and Node tools for graph adapters, flow derivation, scaffolding, linting, manifest state, staleness checks, and child-repository discovery. [`.claude-plugin/`](.claude-plugin/) and [`meta.json`](meta.json) package the same skill for its two distribution paths.

## ▓▒░ SYSTEM REQUIREMENTS ░▒▓

- a compatible AI coding agent
- `git`
- one supported code-graph producer
- Python 3.10+ **or** Node.js 18+ for the bundled tools

Core tools use only the selected runtime's standard library or built-ins. The optional offline GitNexus reader is the exception: it needs `@ladybugdb/core` or a compatible LadybugDB Python binding. GitNexus MCP tools are preferred.

## ▓▒░ MULTIPLAYER ░▒▓

Found a bug or missing rule? [Open an issue](https://github.com/jonaskahn/docforge/issues) with the request, actual output, and expected output.

To contribute, edit the relevant workflow, reference, template, schema, and Python/Node pair together, then [open a pull request](https://github.com/jonaskahn/docforge/pulls). New graph providers follow the [graph-source extension contract](skills/docforge/references/adding-a-graph-source.md).

## ▓▒░ CREDITS ░▒▓

SPDX-License-Identifier: MIT — [LICENSE](LICENSE)
