<div align="center">
  <img src="logo.png" alt="docforge" width="200" />
  <h1>docforge</h1>
  <p>An AI agent skill that designs and writes a repository's whole documentation set — grounded in the actual source, not invented.</p>

  [![MIT License](https://img.shields.io/badge/license-MIT-10b981?style=flat-square)](LICENSE)
  [![Claude Code](https://img.shields.io/badge/works_with-Claude_Code-10b981?style=flat-square)](https://docs.claude.com/claude-code/skills)
  [![agentskills](https://img.shields.io/badge/format-Agent_Skill-10b981?style=flat-square)](https://agentskills.io)
</div>

---

## What it does

Point it at a repo and it produces the documentation that survives: a `docs/` tree, README and ARCHITECTURE, decision records (ADRs), a known-limitations register, a dependency inventory, security policy, API error catalogs, data contracts, and runbooks — plus **Business Analyst and Product Owner audience overlays** when a specific reader is asked for.

Three things make the output trustworthy:

- **Grounded in source.** It reads the codebase through a knowledge graph before writing a word, so every claim is verifiable — no invention, no drift.
- **Provenance-tracked.** Each document records the exact source files it draws from by git blob hash, so "has this drifted?" is answered by comparison, not a re-read and a guess — and only the stale section gets rewritten.
- **Host-neutral.** Works on any git host; never hardcodes one forge's paths. For multi-repo diligence it discovers the full collection first — declared submodules and undeclared nested/vendored repos alike.

## Install

```sh
npx skills add jonaskahn/docforge        # this project
npx skills add jonaskahn/docforge -g -y  # every project
```

Claude Code and compatible agents load the skill automatically once installed.

> **Note:** PromptScript does not support global skill installs, so it is skipped during `-g` installation (`Failed to install 1`). This is expected and does not affect any other agent. To use docforge with PromptScript, install per-project (omit `-g`).

## Use

It activates on its own when you're documenting a repo. Or invoke it directly with `/docforge`, or just describe the job:

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

Only the reference files relevant to your task load into context, so the agent stays fast and focused.

## What's inside

| Path | Purpose |
|---|---|
| `SKILL.md` | Entry point — non-negotiables, source analysis, tier + overlay selection, workflow, anti-patterns |
| `references/source-analysis.md` | Build and query the knowledge graph; which command answers which document |
| `references/docs-tree.md` | Canonical taxonomy — folder rules, full tree, per-file spec |
| `references/provenance-tracking.md` | Frontmatter schema, manifest format, staleness algorithm, partial rewrites |
| `references/host-neutrality.md` | Language rules so docs outlive any one forge |
| `references/decision-records.md` | ADR format, numbering, backfilling from history |
| `references/risk-docs.md` | Limitations register, dependency inventory, security policy |
| `references/quality-bar.md` | Review checklist and rubric for finished docs |
| `references/document-composition.md` | One topic, many readers — the document-as-folder pattern, no-loss/notice invariants, durability rules (no code, no duplication) |
| `references/depth-and-audience.md` | The depth ladder (L0–L3), which reader reads which depth, and which understand-anything command feeds each |
| `references/audience-matrix.md` | The three document classes (aligned / audience-specific / shared-fact spine), the BA/PO split, and which folder owns which fact |
| `references/diligence.md` | Multi-repo portfolio layer for audits, acquisitions, vendor review |
| `references/diligence-collection.md` | Discover the repo collection and gap-check every member first |
| `references/overlay-*.md` | Type overlays (API service, data pipeline, web app, library, infrastructure) and audience overlays (business-analyst, product-owner) |

Plus `assets/templates/` (scaffolds for every spine and overlay file) and `scripts/` (scaffold a tree, audit it, check provenance, discover child repos).

## Contributing

References live in `skills/docforge/references/`, one topic per file. To change one: fork, edit the `.md`, open a PR.

To add a reference: create `references/<topic>.md`, then register it in `SKILL.md` and the table above.

Content is read by an agent, not a human — keep it dense:

- Lead with the common pattern, not the simplest case
- One complete, runnable example per concept
- Gotchas inline, no separate warnings section
- No intros, no marketing — just the technical substance

Wrong or missing guidance? Open an issue with what you asked, what the skill produced, and what it should have said.

## License

MIT
