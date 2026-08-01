# Changelog

## Enforced coding-agents kernel lint

- Wired the orphaned `lint_agents_kernel` into the completion gate: the
  `docforge-audit` mechanical gate now runs it in place of `lint_document` for
  AGENTS.md-shaped outputs, documented end to end in `docforge-audit`,
  `document-audit`, `ownership`, the coding-agents audience profile, and
  `writing.md`; fixed shims remain literal and unlinted by design.
- Strengthened `lint_agents_kernel` (Python/Node parity) with hard rubric
  defects `title-shape` (1–4 words, Title Case, no trailing `?`) and
  `tagline-length` (5–12 words), plus advisory warnings `weak-tagline`,
  `low-negation-ratio`, and `bullet-length` scoped to guidance sections
  2/5/6 — the shipped kernel template stays clean.
- Added a topology-derived "Non-obvious conventions" evidence recipe to the
  coding-agents audience profile (§5 no longer a vibe: every bullet traces to
  a graph edge, linked instead of restated when a human doc owns it).
- Added `tests/test_agents_kernel.py` (clean golden fixture + per-check dirty
  fixtures, Python/Node parity asserted).

## Two-mode fluency and de-duplication pass

- Standardized mode terminology to canonical "fresh start" for `/docforge` vs "revise" for `/docforge-revise`.
- Harmonized the interactive question pack across `intake.md`, `revision.md`, and `docforge-revise/SKILL.md` to identical order, profile dimensions (`shape / platform / framework / concern`), and gate sentence (`never proceed on silent defaults`).
- Smoothed prose in `intake.md` and `docforge-revise/SKILL.md`, aligned flag table descriptions with `flags.md`, and mirrored cross-references between the two skills for symmetry.

## 2.7.0 - Model-native depth ladders

- Added model-depth routing, evidence locators, illustration budgets, deterministic PROV core projection, and the conditional STRIDE interaction register.
- Normalized target depths and added body-preserving metadata reconciliation prerequisites.

## 2.6.1 — Trusted sources and root README policy

- Plan reporting names only READY graph providers; Understand Anything,
  GitNexus, and CodeGraph are equally trusted for `code_graph`. Native
  `flow_graph` remains UA/GitNexus only; CodeGraph-only runs schedule
  Docforge-derived flows.
- Existing root `README.md` requires explicit migrate / skip / rewrite —
  no silent overwrite with the `root_readme` template.
- Keep a single tree for Agent Skills and Claude Code: root [`skills/`](skills/)
  and [`agents/`](agents/). Marketplace entry uses an HTTPS git URL plugin
  source (`https://github.com/jonaskahn/docforge.git`) so installs do not
  require SSH host keys; `"source": "./"` failed to register in Claude Code.
- Dropped the experimental `docforge-plugin/` sync mirror to avoid duplicating
  the cartridge in git.
- Register both skills explicitly and add [`commands/`](commands/) wrappers so
  Claude Code exposes `/docforge` and `/docforge-revise` (plugin skills alone
  appear as `/docforge:docforge` and `/docforge:docforge-revise`).

## 2.6.0 — Claude-native Docforge agents

- Added six read-only, Claude-plugin-native `docforge-*` agents: audit,
  tree-review, graph-precheck, catalog-validator, flow, and ground.
- Agents are thin advisory wrappers over `_shared`; workflows retain inline
  fallbacks so non-Claude hosts follow the same canonical procedure.

## 2.5.0 — Context-bounded repository refactor

Internal reorganization for agent retrieval efficiency. No behavior change
for existing users; see "Stable public interfaces" below for what did not
move.

### Internal path changes

- **Catalog records** moved from one flat `.metadata/catalog/types/*.json`
  directory into `.metadata/catalog/documents/<group>/*.json` (large groups)
  or `.metadata/catalog/documents/*.json` (small groups: root, contributing,
  flows, records). Every record gained `summary`, `contract_file`, and
  `template_file` (renamed from `scaffold_template`); `record` paths are now
  explicit in `index.json` rather than derived by convention.
- **Content artifacts** (contracts, writing-craft instructions, output
  templates) moved from three flat directories
  (`references/catalog-contracts/`, `instructions/`, `assets/templates/`)
  into `content/<group>/` per document group, with a `content/shared/` for
  artifacts used by more than one group. Groups with six or more files of one
  kind get a `contracts/`, `instructions/`, or `templates/` subfolder;
  smaller collections stay flat with a `.contract.md`/`.instruction.md`/
  `.template.md` suffix to disambiguate same-named files.
- **`SKILL.md`** shrank from ~525 lines to under 180 by moving its detailed
  procedure into `workflows/{intake,planning,writing,revision,validation,
  tools}.md`. `SKILL.md` now holds only what must always be loaded: what
  Docforge does, the code-graph precondition, provider sufficiency, safety
  boundaries, invocation routing, and the retrieval protocol.
- **References** reorganized: graph-provider docs into `references/graph/`,
  audience/shape guides into `references/profiles/`; both gained routers.
- **Runtime implementations** moved from a single flat `scripts/` directory
  into `runtime/<subsystem>/` (`common`, `catalog`, `graph`, `flows`,
  `manifest`, `documents`, `portfolio`, `validation`, `migrations`).
  `scripts/*.py`/`*.js` are now thin launchers that import and delegate to
  the runtime implementation — never business logic.
- Generated routers (`.metadata/catalog/README.md`,
  `documents/README.md`, and category `index.json`/`README.md` pairs) are
  produced deterministically by the new `scripts/generate_indexes.py`/`.js`.

### Stable public interfaces (unchanged)

- Every existing `scripts/*.py`/`*.js` entrypoint, its flags, and its exit
  codes.
- `query_catalog`'s existing modes (`--tier`, `--id`, `--ids`, `--profile`,
  `--applicable`, `--legacy`, `--validate`) — serialized output is
  byte-identical to 2.4.0, including for the now-renamed `template_file`
  field, which still prints as `scaffold_template` in these modes.
- Manifest schema `3.1` and provenance schema `2.0` — unchanged.
- Document IDs, type IDs, profile IDs, group IDs, tier names, and capability
  names — unchanged.
- Generated documentation paths in downstream repositories — unchanged.

### New

- `query_catalog --category <group>` and `query_catalog --route <id>` —
  resolve a document's contract/instruction/template/workflow in one call.
- `generate_indexes.py`/`.js --write`/`--check` — regenerate or verify
  catalog routers deterministically.
