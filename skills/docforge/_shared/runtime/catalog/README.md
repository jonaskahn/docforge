# Catalog runtime

Catalog reading, repository-profile detection, and the discovery-gate judgment
pipeline. Public launchers live in
[`runtime/cli/`](../cli/README.md); run the launcher, never these
implementation files directly.

## Load this when

- Reading catalog records, tiers, profiles, routes, or a legacy catalog → `query_catalog`.
- Detecting a repository's shape/platform/framework/concern signals at intake → `detect_profiles`.
- Validating or applying an agent's bounded judgment on ambiguous profile evidence → `discovery_gate` (library only).

## Scripts

| Script | js/py | Kind | Purpose |
|---|---|---|---|
| `query_catalog` | both | CLI + library | Canonical read access to the split catalog; never open catalog JSON by hand |
| `detect_profiles` | both | CLI + library | Shape/platform/framework/concern detection with evidence, cues, confidence |
| `discovery_gate` | both | library only | Validate/apply a discovery-gate judgment JSON; offline, fail-open, no CLI |

## Details

### `query_catalog`

Canonical catalog interface. Use before selecting documents, resolving a
writing route, reading profile definitions, or validating catalog metadata.

```sh
python3 runtime/cli/python/query_catalog.py <mode>   # node runtime/cli/js/query_catalog.js <mode>
```

Exactly one mode: `--tier`, `--id`, `--ids`, `--profile`, `--applicable`,
`--legacy`, `--validate`, `--category`, `--route` (with repeatable
`--audience`), `--groups`. `--applicable` also takes repeatable `--group`,
which restricts selection to those catalog groups (aliases accepted, e.g.
`agents` for `agent-context`); omit it for every group. `--groups` lists every
group with its aliases and the audiences that unlock it. Read-only. Exit `0` success, `1` catalog validation defects,
`2` invocation error. The Python module also exposes `load_index`,
`load_profile(s)`, `applicable`, `category`, `groups`, `group_audiences`,
`normalize_groups`, `route`, `resolve_presentation`, `validate`; JS exports camelCase peers.

For a compact document id, `--route` composes the contract at route time: the
group's header contract plus each `compact_members` member contract as a named
`##` section, in member order, with the member list mirrored under `compact`.
Standard routes keep `contract` as a plain file path.

Agent-context records have one stable route with no content variants. Every
record fixes `presentation.related_docs` to `none`; the two root-kernel records
resolve the same contract, instruction, template, and audit profile. The compact
agent record composes only the seven topic members.

### `detect_profiles`

Read-only recommendations of shape/platform/framework/concern candidates from
repository signals (capped inventory, dependency manifests, selected text
files).

```sh
python3 runtime/cli/python/detect_profiles.py --repo <path> [--json] [--emit-gate-pack]
```

**Not fully read-only:** even plain detection writes
`.docforge/scratch/manifest-deps.json` in the target repository.
`--emit-gate-pack` additionally emits strong/weak detections, cues, excerpts,
`needs_gate` for the discovery-gate step, and `scale` — the three-way project
scale (`small` | `medium` | `large`), its `suggested_layout`
(`compact` | `standard`), and its measurement `signals` (`tracked_files`,
`source_files`, `confirmed_profiles`, `declared_dependencies`,
`flow_candidates`). Classification lives in `common/scale`; the pack reuses
its own walk, so nothing is re-traversed. See
[`../common/README.md`](../common/README.md) for the thresholds.

### `discovery_gate`

Offline library for the gate step after `detect_profiles --emit-gate-pack`:
`needs_gate(detections)`, `validate_judgment(judgment, pack)`,
`apply_judgment(detections, judgment)`, `load_schema()`. No CLI parser; direct
execution errors. Invalid judgments fail open (original detections preserved).

## Where invoked

| Script | Documented callers | Programmatic callers |
|---|---|---|
| `query_catalog` | [`workflows/planning.md`](../../workflows/planning.md), [`workflows/writing.md`](../../workflows/writing.md), [`workflows/revision.md`](../../workflows/revision.md), [`workflows/tools.md`](../../workflows/tools.md), [`retrieval.md`](../../retrieval.md), [`references/docs-tree.md`](../../references/docs-tree.md) | `validation/generate_indexes`, `validation/validate_metadata`, `manifest/manage_manifest`, `manifest/migrate_metadata`, `catalog/detect_profiles` |
| `detect_profiles` | [`workflows/intake.md`](../../workflows/intake.md), [`workflows/tools.md`](../../workflows/tools.md), [`references/source-analysis.md`](../../references/source-analysis.md), [`references/discovery-gate.md`](../../references/discovery-gate.md) | `manifest/manage_manifest` (`init`, `reconcile`) |
| `discovery_gate` | [`workflows/intake.md`](../../workflows/intake.md), [`references/discovery-gate.md`](../../references/discovery-gate.md) | `catalog/detect_profiles --emit-gate-pack` (produces its input); no CLI, no other callers |

## Boundaries

Reads catalog data beneath `_shared/.metadata/catalog`. `query_catalog` and
`detect_profiles` are imported by other subsystems; nothing here imports from
`cli/`.
