<div align="center">
  <img src="logo.png" alt="Docforge" width="200" />

  <h1>DOCFORGE</h1>

  <p><strong>INSERT REPOSITORY. GENERATE DOCUMENTATION. NO INVENTED LORE.</strong></p>
  <p>An Agent Skill that designs, writes, audits, and maintains documentation grounded in the actual source.</p>

  [![Version](https://img.shields.io/badge/version-2.7.0-10b981?style=flat-square)](.claude-plugin/plugin.json)
  [![Agent Skill](https://img.shields.io/badge/format-Agent_Skill-10b981?style=flat-square)](https://agentskills.io)
  [![MIT License](https://img.shields.io/badge/license-MIT-10b981?style=flat-square)](LICENSE)
</div>

---

Created by [Jonas Kahn](https://github.com/jonaskahn), Docforge is a source-grounded documentation cartridge for AI coding agents. It ships as an Agent Skill and a Claude Code plugin: instructions, references, templates, schemas, and paired Python/Node tools—not a Markdown generator library.

## ▓▒░ WORLD MAP ░▒▓

- [Boot sequence](#-boot-sequence-)
- [Start game](#-start-game-)
- [Core loop](#-core-loop-)
- [Evidence and flows](#-evidence-and-flows-)
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

These commands come from the [Agent Skills](https://agentskills.io) CLI and
install whatever `skills/*/SKILL.md` trees the repo ships.

### CLAUDE CODE CARTRIDGE

Docforge also ships a native [Claude Code marketplace manifest](.claude-plugin/marketplace.json).
The marketplace lists the GitHub repo as the plugin source, so root `skills/` and
`agents/` stay the single tree (shared with Agent Skills — no mirrored package):

```text
/plugin marketplace add jonaskahn/docforge
/plugin install docforge@docforge
```

If a prior add left a broken cache entry, remove and re-add first:

```text
/plugin marketplace remove docforge
/plugin marketplace add jonaskahn/docforge
/plugin install docforge@docforge
```

Claude Code’s GitHub shorthand clones over SSH by default. This marketplace
lists an HTTPS git URL so install does not need `github.com` in
`~/.ssh/known_hosts`. If you still prefer SSH elsewhere, either add the host
key (`ssh-keyscan github.com >> ~/.ssh/known_hosts`) or set
`CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1`.

Both install paths load [`skills/docforge`](skills/docforge/SKILL.md) and
[`skills/docforge-revise`](skills/docforge-revise/SKILL.md). Claude Code
plugin skills are namespaced (`/docforge:docforge`, `/docforge:docforge-revise`);
[`commands/`](commands/) also registers the bare `/docforge` and
`/docforge-revise` slash commands. After updating the marketplace, run
`/plugin marketplace update docforge` then reinstall or `/reload-plugins`.

## ▓▒░ START GAME ░▒▓

Describe the documentation quest in plain language:

```text
Document this repository from scratch.
Create diligence documentation for this service.
Generate ADRs from the repository history.
Add the API-service shape and Business Analyst audience.
Make this repository ready for AI coding agents.
Check which generated docs have drifted from source.
```

Slash-command support depends on the host. Where registered, use `/docforge`
or `/docforge-revise`; plain-language requests work across compatible agents.

### FIRST MISSION

```text
/docforge
```

Expected result:

1. Docforge performs only read-only discovery of repository and manifest state.
2. It presents all applicable unresolved scope questions together: goal,
   documentation tier, the five typed repository-profile dimensions, evidence
   availability only when it is unresolved, and execution mode. Each question
   explains its choices; native selection controls are used when the host
   provides them.
3. After you answer the set, it summarizes the complete scope and asks you to
   confirm, edit, or cancel. This confirmation is required even when
   Auto-accept is selected. It does not create a manifest, documents, or a
   repository analysis during intake.
4. After you confirm the scope, it inventories the repository from approved
   evidence sources.
5. It always shows the exact manifest-backed tree plus a one-line
   content/evidence card for every document before writing. Auto-accept skips
   only the pause, not the displayed tree.
6. If discovery changes the manifest later, it shows the path/requirement delta
   and refreshed tree before writing continues.

If evidence is insufficient, Docforge explains the available setup choices. It
never changes repository analysis tooling automatically.

## ▓▒░ CORE LOOP ░▒▓

```text
PRECHECK → ANALYZE → PLAN → WRITE → AUDIT → TRACK
```

1. **PRECHECK** — confirm sufficient repository evidence.
2. **ANALYZE** — read source, config, manifests, existing docs, CI, deployment files, git history, and child repositories.
3. **PLAN** — choose a named tier and typed profiles, harvest a complete ranked
   flow index, initialize manifest 3.1, then preview its exact tree.
4. **WRITE** — generate one document at a time in dependency order.
5. **AUDIT** — use a fresh artifact-only reviewer when supported, otherwise a recorded cold artifact-only pass; derivable gaps force a rewrite.
6. **TRACK** — stamp section-level source paths and git blob hashes so later runs update only what drifted.

Docforge writes behavior and boundaries, not prose tied to private symbols or line numbers. Derivable facts must be completed; only truly external values may remain as typed tokens such as `<SECURITY_CONTACT>`.

Read the full [workflow](skills/docforge/_shared/workflows/INDEX.md), [document contracts](skills/docforge/_shared/content/INDEX.md), [audit gate](skills/docforge/_shared/references/document-audit.md), and [provenance model](skills/docforge/_shared/references/provenance-tracking.md).

## ▓▒░ EVIDENCE AND FLOWS ░▒▓

Docforge grounds documents in the repository evidence available to the current
session. It writes evidence-backed flow candidates to `.docforge/flow-index.json`
and renders the resulting flow matrix in `docs/flows/INDEX.md`. Main flows are
documented in depth; lower-confidence or deferred candidates remain visible as
clearly labeled placeholders until their evidence improves.

## ▓▒░ STAGE SELECT ░▒▓

Choose **Spine** for a repository baseline, **Diligence** for external scrutiny,
or **Portfolio** for a multi-repository review. Docforge then composes five
independent profile dimensions:

- shapes such as `web-app`, `api-service`, `mobile-app`, `desktop-app`,
  `cli-tui`, `library-sdk`, `data-pipeline`, `infrastructure-platform`,
  `game`, `embedded-iot`, and `smart-contract`;
- platforms such as `browser`, `ios`, `android`, `macos`, `windows`, `linux`,
  wearable/TV/spatial targets, cloud, containers, edge, and RTOS;
- framework detection profiles such as Flutter, React Native, KMP, MAUI,
  Electron, Tauri, SwiftUI/AppKit, popular web/backend/data frameworks, game
  engines, and embedded toolchains;
- evidenced concerns such as accessibility, localization, privacy, secure
  storage, offline sync, payments, notifications, and hardware integration;
- audiences such as engineers, beginners, Business Analysts, Product Owners,
  coding agents, operators, and security reviewers.

Frameworks tailor evidence retrieval, terminology, and verified commands;
shapes and platforms own the durable document tree. Shared paths are selected
once and retain every profile origin. With no audience flag, manifest
initialization records `engineers` and `beginners` as the default audience.

The Business Analyst audience generates a business process view, rule catalog,
and requirements traceability. The Product Owner audience generates feature
value/status, success metrics, release impact, and ticket traceability only
when ticket evidence exists. Select `coding-agents` (aliases include `agent`
and `agent-context`) for a compact `AGENTS.md` kernel, Claude shims/settings,
and token-budgeted `docs/agents/` views.

The tier rules, profile signals, and complete level layout live in the [canonical docs tree](skills/docforge/_shared/references/docs-tree.md) and [`SKILL.md`](skills/docforge/SKILL.md).

## ▓▒░ CONTROLLER MAPPING ░▒▓

Invocation order is always **command → scope args → flags** (never flags
before the command or before a required scope argument):

| Command | Use |
|---|---|
| `/docforge` | New plan, intake, or write |
| `/docforge --plan-only` | Plan / dry-run tree only |
| `/docforge-revise all` | Full-tree structural refresh |
| `/docforge-revise <area>` | Scoped revise (e.g. architecture) |
| `/docforge-revise flow` | Full flow harvest → organize → derive → write |
| `/docforge-revise flow --plan-only` | Revise analysis only (no body writes) |

Shared flags on both commands: `--plan-only` (analyze / dry-run tree only),
`--auto-accept` (skip routine pauses after scope confirm).

There is no `--resume` or `--status` skill flag. Continue an incomplete run via
intake or plain language; for a progress report, ask in plain language or run
`manage_manifest status`.

`--auto-accept` skips routine conversational pauses after the scope has been
explicitly confirmed. It does not silently choose unresolved profiles or
authorize installation, global configuration, evidence tooling changes,
archive/delete actions, or other separately approved side effects; it also
does not skip grounding, plan display, audits, or final checks.

The exact flag semantics and composition rules live in the [workflow](skills/docforge/_shared/workflows/INDEX.md) and [shared flags](skills/docforge/_shared/flags.md).

## ▓▒░ INVENTORY ░▒▓

[`skills/docforge/SKILL.md`](skills/docforge/SKILL.md) and
[`skills/docforge-revise/SKILL.md`](skills/docforge-revise/SKILL.md) are thin
command entrypoints. The shared cartridge lives under
[`skills/docforge/_shared/`](skills/docforge/_shared/INDEX.md):
[`.metadata/catalog/`](skills/docforge/_shared/.metadata/catalog/) is the canonical
registry; [`workflows/`](skills/docforge/_shared/workflows/) holds the step-by-step
procedure; [`references/`](skills/docforge/_shared/references/) holds owned policy
prose; and [`content/`](skills/docforge/_shared/content/) holds each document group's
contracts, writing-craft instructions, and output-scaffold templates.

[`runtime/cli/`](skills/docforge/_shared/runtime/cli/) holds the stable public
launchers split by language (`python/`, `js/`). Each launcher is a thin
re-export of its paired implementation under the subsystem folders in
[`runtime/`](skills/docforge/_shared/runtime/). The agent detects `python3` /
`python` / `node` / `bun` / `deno` once and locks one engine for the
session — there is no separate runtime-precheck CLI.
[`.claude-plugin/`](.claude-plugin/) packages the Claude Code marketplace
path; the marketplace entry installs this GitHub repo as the plugin (root
`skills/` + `agents/`). Agent Skills install discovers
[`skills/docforge/SKILL.md`](skills/docforge/SKILL.md) and
[`skills/docforge-revise/SKILL.md`](skills/docforge-revise/SKILL.md)
directly (no root `meta.json`).

## ▓▒░ SYSTEM REQUIREMENTS ░▒▓

- a compatible AI coding agent
- `git`
- a supported source of repository evidence
- **one** tool runtime: Python 3.10+ **or** a JS engine (Node.js 18+, Bun, or Deno)

The agent picks the session engine from what is installed. Core tools use only
the selected runtime's standard library or built-ins.

## ▓▒░ MULTIPLAYER ░▒▓

Found a bug or missing rule? [Open an issue](https://github.com/jonaskahn/docforge/issues) with the request, actual output, and expected output.

To contribute, edit the relevant workflow, reference, template, schema, and Python/Node pair together under `skills/` (and agent wrappers under `agents/`), then [open a pull request](https://github.com/jonaskahn/docforge/pulls).

## ▓▒░ CREDITS ░▒▓

SPDX-License-Identifier: MIT — [LICENSE](LICENSE)
