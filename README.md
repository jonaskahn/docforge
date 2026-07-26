<div align="center">
  <img src="logo.png" alt="docforge" width="200" />
  <h1>docforge</h1>
</div>

An AI agent skill for designing and generating a repository's documentation set — `docs/` tree, README and ARCHITECTURE, decision records (ADRs), a known-limitations register, a third-party dependency inventory, security policy, API error catalogs, data contracts, and runbooks. Grounds every document in a knowledge-graph analysis of the actual source before writing, so nothing is invented. Host-neutral — works on any git host and never hardcodes one forge's paths.

[![MIT License](https://img.shields.io/badge/license-MIT-10b981?style=flat-square)](LICENSE)
[![Claude Code](https://img.shields.io/badge/works_with-Claude_Code-10b981?style=flat-square)](https://docs.claude.com/claude-code/skills)
[![agentskills](https://img.shields.io/badge/format-Agent_Skill-10b981?style=flat-square)](https://agentskills.io)

---

## Installation

Install with [npx skills](https://skills.sh):

```sh
npx skills add jonaskahn/docforge
```

Install globally so it's available in every project:

```sh
npx skills add jonaskahn/docforge -g -y
```

After installing, Claude Code and compatible agents automatically load the skill when you're working on documentation for a repository.

---

## How to Use

The skill activates automatically when context suggests repository documentation work. You can also invoke it directly:

```sh
/docforge
```

Or describe what you need — the agent loads only the reference files relevant to your task:

> "Document this repo from scratch — it's a Python API service with a Postgres backend"

> "Audit this repo for diligence — the design partner wants to see our docs before signing"

> "Generate ADRs from the git history of this service"

> "Scaffold a Tier 1 docs tree for this fresh side project"

> "Add the API service overlay on top of our existing docs/ folder"

> "Run the quality-bar review on the documentation we already have"

The skill loads lazily — only reference files relevant to your current work are pulled into context. This keeps the agent fast and focused.

---

## What's Included

Reference | Covers
---|---
`SKILL.md` | Entry point — non-negotiables, source analysis, tier selection, overlay selection, workflow, root vs `docs/`, anti-patterns
`references/source-analysis.md` | How to build and query the knowledge graph, and which command answers which document
`references/docs-tree.md` | Canonical taxonomy, folder naming rules, full tree, per-folder and per-file specification
`references/host-neutrality.md` | Language rules so generated docs outlive any one forge
`references/decision-records.md` | ADR format, front matter, numbering, backfilling from history
`references/risk-docs.md` | Limitations register, dependency inventory, security policy
`references/quality-bar.md` | Review checklist and rubric for finished documentation
`references/diligence.md` | Multi-repo portfolio layer for audits, acquisitions, vendor review
`references/overlay-api-service.md` | API service overlay — routes, data contracts, error catalog
`references/overlay-data-pipeline.md` | Data pipeline overlay — stages, schedules, lineage, ops runbooks
`references/overlay-web-app.md` | Web application overlay — routing, state, browser entry, asset pipeline
`references/overlay-library.md` | Library / SDK overlay — public surface, versioning, examples
`references/overlay-infrastructure.md` | Infrastructure overlay — Terraform, Pulumi, Helm, Ansible, clusters

Templates in `assets/templates/` provide starting scaffolds for every spine file. Scripts in `scripts/` scaffold a new tree and audit an existing one.

---

## How to Improve

### Edit an existing reference

Each file in `skills/docforge/references/` covers one topic. To fix, extend, or update:

1. Fork this repo
2. Edit the relevant `.md` file
3. Keep content dense and practical — this is consumed by an AI agent, not a human reader
4. Open a pull request

### Add a new reference file

1. Create `skills/docforge/references/<topic>.md`
2. Add an entry under "Loading Files" / "Reference map" in `skills/docforge/SKILL.md`
3. Add a one-line description under "Available Guidance" / the README's "What's Included" table

### Content style guide

- Start with the most common pattern, not the simplest case
- Include at least one complete, runnable example per concept
- Note gotchas inline — don't separate them into a warnings section
- No introductory sentences, no marketing language — just the technical substance

### Reporting issues

If the skill gives wrong, outdated, or missing guidance, open an issue describing:

- What you asked the agent to do
- What the skill produced
- What the correct answer should be

---

## License

MIT
