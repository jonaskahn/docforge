# Workflows

Step-by-step procedure, split by invocation type.
[`../rules.md`](../rules.md) and siblings hold the rules that must always be
loaded; every procedural detail lives here.

## Load this when

- Bare `/docforge`, no task or flags → [intake.md](intake.md)
- A task with tier/profile/flags already given, or continuing after intake
  confirmation → [planning.md](planning.md)
- Materializing the next document in `write_order`, or continuing an incomplete
  run → [writing.md](writing.md)
- `/docforge-revise` (`all` \| `<area>` \| `flow`), or update/refresh a named
  document → [revision.md](revision.md)
- Staleness, migration, the whole-tree gate, or completion criteria →
  [validation.md](validation.md)
- Looking up a script's exact flags, invocation form, or exit codes →
  [tools.md](tools.md)

`/docforge` and `/docforge-revise` share flags: see
[`../flags.md`](../flags.md) (`--plan-only`, `--auto-accept`).
There is no `--resume` or `--status` skill flag — continue via intake/plain
language; status via plain language or `manage_manifest status`.

## Contents

- [intake.md](intake.md) — bare `/docforge` invocation, discovery gate, discovery brief, scope questions, confirmation gate, graph-provider choice.
- [planning.md](planning.md) — inspection, tier/profile selection, dynamic discovery, manifest init, dry-run tree, plan checkpoint.
- [writing.md](writing.md) — per-document execution card, evidence, scaffolding, provenance, status transitions, independent audit; continue incomplete runs.
- [revision.md](revision.md) — `/docforge-revise` (incl. shared flags), single-document update/refresh, flow-index organization.
- [validation.md](validation.md) — staleness, migration, whole-tree audit, cross-document quality gate.
- [tools.md](tools.md) — every public script's Python/Node invocation, inputs, outputs, exit codes.

## Boundaries

Procedure only. Policy that a procedure depends on (graph provider detail,
audience/shape guidance, quality bar, provenance format) is owned in
`../references/` and linked from here, not restated.
