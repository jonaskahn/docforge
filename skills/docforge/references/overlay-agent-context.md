# Overlay: Agent Context

**Applies when:** the repo is, or will be, worked on by AI coding agents (Claude Code, Cursor, Copilot, Codex, Aider, Windsurf) — ask, or infer from an existing `.cursor/`, `.github/copilot-instructions.md`, or similar signal already in the repo.

This overlay is orthogonal to the repo-type overlays (api/web/library/data-pipeline/infrastructure) and to the BA/PO audience overlays — it can be layered onto any tier, any repo type, any combination of the others. Where those overlays add documents for a *human* reader, this one adds documents for the AI agent itself, at the moment it opens the repo cold.

## The governing rule: less work, not more

Everything under `docs/agents/` exists to orient an agent inside a limited context window — not to re-document the system. Wherever a human-facing document already owns a fact (tech-debt, glossary, testing strategy, architecture rationale, flow steps), the agent-facing file is a **brief stub**: a couple of lines of framing plus a link to the human document's read path. It is never a second full treatment of the same subject, and it is never a compressed *rewrite* of the human document either — it points, it doesn't paraphrase at length.

The one exception is `docs/agents/patterns.md`: complexity hotspots and function exemplars have no other home anywhere in the human tree, so that file carries real content by necessity, not by choice.

This is a deliberate, stated departure from how this capability works elsewhere: independently re-deriving glossary/tech-debt/testing content on every run duplicates a fact docforge's own non-negotiable ("state each fact once, link everywhere") forbids. Treat every `docs/agents/*` file as a pointer first; only let it carry real prose when the catalog entry below says so.

## Root files

### `AGENTS.md`

The kernel — the one file an agent reads before touching anything else. **Hard cap: 100 lines.** Sui generis: not on the L0–L3 depth ladder, no YAML frontmatter (see the provenance exception in `provenance-tracking.md`), checked by its own mechanical linter (`scripts/check_agents_kernel.{py,js}`), not the general document checklist.

Seven numbered `## ` sections, each opening with a bold one-line tagline and (except Boundaries and Absolute Rules) closing with a `The test: …` sentence that lets a reader verify the section actually holds:

1. **Commands** — the one way to install/dev/test/lint/build, derived from the manifests actually present (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, …). One fenced code block, no alternates.
2. **Boundaries** — Always / Ask first / Never, as short imperative lines. Distilled from `CONVENTIONS.md` if one exists; otherwise the safe defaults every repo shares (no force-push to main, no editing applied migrations, no destructive commands without approval).
3. **Module Map** — one bullet per architectural layer (name, size, one-line responsibility), from the knowledge graph. Not a restatement of `architecture/high-level.md`'s prose — a compressed index into it.
4. **Architectural Altitude** — the two or three entry points a cold reader needs first, from the graph's guided tour.
5. **Non-Obvious Conventions** — topology-derived surprises (import-graph anomalies, naming deviators) that genuinely have no other home. Omit the whole section if there's nothing surprising to report — an empty "nothing found" section is worse than no section.
6. **Absolute Rules** — the static Safety / While-coding rules every repo gets, plus a `### Project-specific` block only for directives from `CONVENTIONS.md` not already covered above.
7. **Deeper Context** — one bullet per `docs/agents/*` file actually produced, `@`-prefixed (Claude Code's import syntax), each with a five-word gist. This is the file's only legitimate "go deeper" surface — nothing else in AGENTS.md should need a link out.

Closing line, verbatim style: `Working if: agents stop asking "where does X live?", hook denials are respected, and PRs match the conventions above without being told.`

### `CLAUDE.md`

Exactly one line: `@AGENTS.md`. Nothing else — this is the purest possible thin pointer, not a document to write.

### `CLAUDE.local.md`

A three-line, gitignored stub for personal preferences. Never put anything here a teammate would need — that belongs in `AGENTS.md`.

### `.claude/settings.json`

Machine config, not documentation: a `permissions.deny` array of destructive-command patterns, and a `hooks.Stop` entry running lint/test if the manifests expose those commands (omit the `hooks` block entirely if neither exists). **This file is merged on every re-run, never overwritten** — union the deny lists by exact string match, add a Stop hook only if none exists, never remove an existing entry. This is the one document type in the whole tree that is explicitly not "regenerate in place."

## `docs/agents/` — on-demand depth, linked from AGENTS.md §7

### `architecture.md` — brief stub
A handful of bullets (stack, quick-start commands, layer names) plus a link to `../architecture/high-level.md` and `../architecture/low-level.md` for the actual map and rationale. Enough on-page context that the common case doesn't require following the link; nothing more.

### `patterns.md` — the one file with real content
Complexity hotspots, function exemplars per layer, a recurring-imports table — genuinely owned here because no human document tracks this.

### `glossary.md` — brief stub
A linking view only: `{{term}} → ../reference/glossary.md#{{anchor}}` per term an agent is likely to hit while editing. Never redefines a term — that would violate the glossary's status as the single spine for domain vocabulary.

### `testing.md` — brief stub
Runner command, one-line layout note, single-test command, and a mock-stance line (the one place a typed placeholder is expected, not a defect, if the mock convention genuinely isn't inferable). Link to `../engineering/testing.md` for strategy and rationale.

### `tech-debt.md` — brief stub
One line plus a link to `../architecture/tech-debt.md`. Real content only for a gap that is genuinely agent-specific (a footgun an agent, not a human, is likely to hit) and absent from the human register.

### `flow.md` — brief stub
Entry points and triggers per business domain, as a short list, each linking to `../flows/<flow>.md` for the actual steps. Sourced from `/understand-domain` — same hard gate as `docs/flows/` (see "Gating" below). Never a rewritten Explanation+how-to treatment; that depth already exists at the link target.

### `conventions.md` — conditional
Only produced if a `CONVENTIONS.md` already exists in the repo. A distilled, AI-targeted directive list — never a verbatim copy of the source file.

## Cross-vendor mirrors — hand-pulled, not scaffolded

`GEMINI.md`, `.cursor/rules/agents.mdc`, `.github/copilot-instructions.md`, `.codex/instructions.md`, `.windsurf/rules/agents.md`, `.aider.conf.yml` are mechanical derivations of the finished `AGENTS.md` — the same fact at N tool-conventional paths, sanctioned because each is read by a different *tool*, not a different *human reader* (see the R2 exception in `document-composition.md`).

**Build a vendor mirror only when that vendor's own signal is already present in the repo** — an existing `.cursor/` folder, a Copilot-referencing CI step, a `.windsurf/` directory. Never speculatively generate all six for every repo; that's the same "unrequested audience file" anti-pattern `audience-matrix.md` already warns against, applied to tools instead of readers. There is no scaffold template for these — derive each at the moment `AGENTS.md` is finalized: strip the H1, wrap in the vendor's required frontmatter/format, add a provenance comment, done.

## Gating

`AGENTS.md`'s module map, `docs/agents/architecture.md`, `patterns.md`, `testing.md`, `tech-debt.md` need only the knowledge graph — check with `scripts/check_preconditions.py --need graph`. `docs/agents/flow.md` and the full (non-stub) `glossary.md` variant need the domain graph too — `--need domain`, the identical hard gate already governing `docs/flows/` and product content. No fallback to hand-typed flows for this overlay either.

## Non-negotiable specific to this overlay

Never let `AGENTS.md` exceed its 100-line cap by restating content a linked document already carries. A kernel that duplicates `architecture/high-level.md`'s prose to avoid a link is a **duplicated-truth** defect, made worse by blowing the budget that makes the kernel usable in the first place — run `scripts/check_agents_kernel.{py,js}` before presenting it.
