<div align="center">
  <img src="logo.png" alt="Docforge" width="160" />

  <h1>DOCFORGE</h1>

  <p><strong>INSERT REPOSITORY. GENERATE DOCUMENTATION. NO INVENTED LORE.</strong></p>

  [![Version](https://img.shields.io/badge/version-2.19.0-10b981?style=flat-square)](.claude-plugin/plugin.json)
  [![Agent Skill](https://img.shields.io/badge/format-Agent_Skill-10b981?style=flat-square)](https://agentskills.io)
  [![MIT License](https://img.shields.io/badge/license-MIT-10b981?style=flat-square)](LICENSE)

  <p><code>► PRESS START</code></p>
</div>

---

An Agent Skill cartridge for AI coding agents: designs, writes, audits, and
maintains documentation **grounded in the actual source** — code graphs,
manifests, git history, repository evidence. Every claim carries a blob-stamped
provenance, every document passes an independent audit before it counts.

```text
PRECHECK → ANALYZE → PLAN → WRITE → AUDIT → TRACK
```

Docforge reads the repository's own size and shape before deciding how big
the docs should be: a small repo gets **compact layout** — the same subjects,
folded into fewer, denser files — while a large one gets the full standard
tree; either way you can override the suggestion. Documents that fall out of
scope on a later run (tier downgrade, dropped profile, layout switch) are
**retired**, not deleted out from under you — moved to a git-ignored
`.docforge/obsolete/<year>/` (or removed, if you say so explicitly) with the
history kept in the manifest.

## ██▓▒░ INSERT COIN ░▒▓██

```sh
# Agent Skills — insert in the current project
npx skills add jonaskahn/docforge

# or globally
npx skills add jonaskahn/docforge -g -y
```

Claude Code native marketplace:

```text
/plugin marketplace add jonaskahn/docforge
/plugin install docforge@docforge
```

Both paths load [`skills/docforge`](skills/docforge/SKILL.md) — the required
core bundle. `docforge-revise` and `docforge-dashboard` are thin optional
entrypoints on top of it.

## ██▓▒░ HOW TO PLAY ░▒▓██

Invocation order is always **command → scope args → flags**. Plain language
works across compatible agents:

```text
Document this repository from scratch.
Create diligence documentation for this service.
Generate ADRs from the repository history.
Check which generated docs have drifted from source.
```

### /docforge — fresh start

Intake, plan, or write a tree from scratch. On intake it performs only
read-only discovery, then asks its scope questions in two turns: first your
goal and the documentation layout, then tier, repository profiles, audience,
graph source, and execution mode. It finally summarizes the complete scope and
asks you to confirm, edit, or cancel before writing anything.

| Command | Use |
|---|---|
| `/docforge` | Fresh start: intake, plan, or write |
| `/docforge --plan-only` | Plan / dry-run tree only |

### /docforge-revise — keep it current

Re-ground what drifted; a bare run only syncs manifest metadata.

| Command | Use |
|---|---|
| `/docforge-revise` | Migrate/upgrade manifest metadata only — no questions, no writing |
| `/docforge-revise all` | Full-tree structural refresh |
| `/docforge-revise <area>` | Scoped revise (architecture, flows, operations, …) |
| `/docforge-revise flow` | Flow harvest → organize → derive → write |
| `/docforge-revise flow --plan-only` | Flow analysis only (no body writes) |

### /docforge-dashboard — liquid docs

Render the written docs as a local Fumadocs site (Liquid Glass theme).

| Command | Use |
|---|---|
| `/docforge-dashboard` | `dashboard start`: reconcile → rebuild when changed → serve → open |
| `/docforge-dashboard --plan-only` | Preflight, metadata dry-run, signatures, route plan |
| `/docforge-dashboard export` | Static export (`next build` → `<dashboard>/out/`) for GitHub Pages / S3 |
| `/docforge-dashboard status` | Read-only: signature match, server state, document count |
| `/docforge-dashboard stop` | Stop the detached dev server |

### CHEAT CODES

`--plan-only` — analyze / dry-run tree only.
`--auto-accept` — skip routine pauses after the scope confirm.
`--no-dashboard` — skip the automatic dashboard build/serve at completion.
`--help` — per-command reference (canonical text in
[`help.md`](skills/docforge/_shared/help.md)).

## ██▓▒░ DEMO ░▒▓██

The cabinet's attract mode after a run:

<p align="center">
  <img src="assests/demo-01.png" alt="Docforge dashboard preview (dark mode)" width="400" />
  <img src="assests/demo-02.png" alt="Docforge dashboard preview (light mode)" width="400" />
</p>

## ██▓▒░ SYSTEM REQUIREMENTS ░▒▓██

- a compatible AI coding agent
- `git`
- one tool runtime: Python 3.10+ **or** Node.js 22+ / Bun / Deno
- Node.js 22+ and `npm` only for the dashboard install/serve steps

Full procedure and policy: [workflows](skills/docforge/_shared/workflows/README.md),
[document contracts](skills/docforge/_shared/content/README.md),
[provenance model](skills/docforge/_shared/references/provenance-tracking.md).

## ██▓▒░ CREDITS ░▒▓██

Created by [Jonas Kahn](https://github.com/jonaskahn). SPDX-License-Identifier:
MIT — [LICENSE](LICENSE). Bugs: [issues](https://github.com/jonaskahn/docforge/issues).
Contributions: [pull requests](https://github.com/jonaskahn/docforge/pulls).

<code>GAME OVER? NO. CONTINUE. →</code>
