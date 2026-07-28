<div align="center">
  <img src="logo.png" alt="Docforge" width="200" />

  <h1>DOCFORGE</h1>

  <p><strong>INSERT REPOSITORY. GENERATE DOCUMENTATION. NO INVENTED LORE.</strong></p>
  <p>An Agent Skill that designs, writes, audits, and maintains documentation grounded in the actual source.</p>

  [![Version](https://img.shields.io/badge/version-0.9.0-10b981?style=flat-square)](meta.json)
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
Document this repository --plan-only
```

Expected result:

1. Docforge checks for a readable code graph.
2. It asks for the graph source, tier, audience overlays, and depth.
3. It shows the proposed tree and per-document plan.
4. It writes the scaffold and `.docforge/manifest.json`, but no finished prose.

If no code graph exists, Docforge stops and shows the available setup paths instead of guessing from directory names.

## ▓▒░ CORE LOOP ░▒▓

```text
PRECHECK → ANALYZE → PLAN → WRITE → AUDIT → TRACK
```

1. **PRECHECK** — require one supported code graph.
2. **ANALYZE** — read graph data, source, config, manifests, existing docs, CI, deployment files, git history, and child repositories.
3. **PLAN** — choose a tier and overlays, preview the tree, then record the accepted layout.
4. **WRITE** — generate one document at a time in dependency order.
5. **AUDIT** — send every document to a fresh reviewer; derivable gaps force a rewrite.
6. **TRACK** — stamp section-level source paths and git blob hashes so later runs update only what drifted.

Docforge writes behavior and boundaries, not prose tied to private symbols or line numbers. Derivable facts must be completed; only truly external values may remain as typed tokens such as `<SECURITY_CONTACT>`.

Read the full [workflow](skills/docforge/SKILL.md#workflow), [document contracts](skills/docforge/references/document-catalog.md), [audit gate](skills/docforge/references/document-audit.md), and [provenance model](skills/docforge/references/provenance-tracking.md).

## ▓▒░ GRAPH CARTRIDGES ░▒▓

A code graph is the universal key. Docforge can read Understand-Anything JSON, a GitNexus LadybugDB index, or a CodeGraph SQLite index through its MCP tool.

Flow and product docs prefer native flow data. When only a code graph is available, Docforge derives a provisional, entry-point-first flow graph in the git-ignored `.docforge/tmp/` workspace. It never fabricates the code graph itself.

Provider capabilities and setup live in [graph dispatch](skills/docforge/references/graph-sources.md); the reasoning loop lives in [flow derivation](skills/docforge/references/domain-derivation.md).

## ▓▒░ STAGE SELECT ░▒▓

Choose **Spine** for a repository baseline, **Diligence** for external scrutiny, or **Portfolio** for a multi-repository review. Add repo-type power-ups (`api`, `web`, `library`, `data-pipeline`, `infrastructure`) and audience power-ups (`business-analyst`, `product-owner`, `agent-context`) as needed.

`agent-context` is equipped by default. It generates a compact `AGENTS.md` kernel, `CLAUDE.md`, `CLAUDE.local.md`, `.claude/settings.json`, and `docs/agents/` links after the human-facing docs are finished. Unequip it with `--no-agent-context`.

The tier rules, overlay signals, and complete level layout live in the [canonical docs tree](skills/docforge/references/docs-tree.md) and [`SKILL.md`](skills/docforge/SKILL.md).

## ▓▒░ CONTROLLER MAPPING ░▒▓

Use `--revise all` or `--revise <area>` for stale content, `--plan-only` to stop before prose, `--resume` to continue a saved run, `--status` for a read-only progress report, and `--no-agent-context` to disable the default agent overlay.

`--auto-accept` uses questionnaire defaults, displays each planned and completed part without pausing, and runs permitted side effects after a notice. It does not skip graph grounding, plan display, per-document audits, or final consistency checks for documents it generates.

The exact flag semantics and composition rules live in the [workflow](skills/docforge/SKILL.md#workflow).

## ▓▒░ INVENTORY ░▒▓

[`SKILL.md`](skills/docforge/SKILL.md) is the entry cartridge. [`references/`](skills/docforge/references/) holds policy, [`instructions/`](skills/docforge/instructions/) holds writing craft, [`assets/templates/`](skills/docforge/assets/templates/) holds scaffolds, and [`.metadata/`](skills/docforge/.metadata/) holds schemas and tracking shapes.

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
