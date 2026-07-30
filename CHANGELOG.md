# Changelog

## Unreleased — Whole-repo Claude plugin (no mirror)

- Keep a single tree for Agent Skills and Claude Code: marketplace
  `"source": "./"` with root [`skills/`](skills/) and [`agents/`](agents/).
- Dropped the experimental `docforge-plugin/` sync mirror to avoid duplicating
  the cartridge in git.

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
