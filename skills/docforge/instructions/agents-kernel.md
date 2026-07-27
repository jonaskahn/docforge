# Agent Context Kernel — Instruction Template

Craft guidance for writing `AGENTS.md` and its `docs/agents/` family (agent-context overlay).
Content contract (must-present, keep-out, per file): `references/document-catalog.md` → "Agent-context overlay documents".
Full overlay reference, including the brief-stub rule and cross-vendor derivation: `references/overlay-agent-context.md`.

## Purpose

Give an AI coding agent a token-budgeted orientation kernel derived from the actual graph and
manifests — never a second full documentation set. Budget-first: cut before you elaborate.

## Data Requirements

- Knowledge graph — layers, tour, module map for `AGENTS.md` §3–4 and `docs/agents/architecture.md`, `patterns.md`
- Domain graph — `docs/agents/flow.md` and the non-stub `glossary.md` variant (hard-gated, same as `docs/flows/`)
- Manifests (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, …) — install/dev/test/lint/build commands
- Existing `CONVENTIONS.md`, if present — feeds Boundaries, Absolute Rules, and `docs/agents/conventions.md`

## Template Structure

- `AGENTS.md`: the 7 numbered `## ` sections in fixed order (Commands, Boundaries, Module Map,
  Architectural Altitude, Non-Obvious Conventions, Absolute Rules, Deeper Context), each with a
  bold tagline first line and — except Boundaries and Absolute Rules — a closing `The test: …`
  sentence. Omit §5 entirely if there's nothing non-obvious to report. If the file runs over
  100 lines, cut in this order before touching anything else: §5 (Non-Obvious Conventions) →
  §4 (Architectural Altitude) → §7 (trim gists to three words). Never cut §1, §2, or §6.
- `docs/agents/*`: brief-stub shape for every file except `patterns.md` — a couple of lines of
  framing, then a link to the human document that owns the subject. See the per-file list in
  `overlay-agent-context.md`.
- Cross-vendor mirrors: not templated. Derive from the finished `AGENTS.md` at the moment it's
  finalized, only for a vendor whose own signal is already in the repo.

## Provenance Requirements

- `AGENTS.md`/`CLAUDE.md`/`CLAUDE.local.md` use the HTML-comment exception in
  `provenance-tracking.md`, not YAML frontmatter — one `kernel` section in the manifest.
- Every other `docs/agents/*.md` file uses standard frontmatter like any other document.

## Notes

- Never let a `docs/agents/*` file restate a fact `architecture/`, `reference/`, or
  `engineering/` already owns — link instead. `patterns.md` is the sole exception.
- Run `scripts/check_agents_kernel.{py,js}` on `AGENTS.md` before presenting it; a clean pass
  is necessary, not sufficient — the independent audit (`document-audit.md`) still judges depth
  and duplication.
- `.claude/settings.json` is merged on re-runs, never overwritten — union `permissions.deny`,
  add a `Stop` hook only if none exists.
