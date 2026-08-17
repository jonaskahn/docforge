# Workflows

Step-by-step procedure, split by invocation type.
[`../rules.md`](../rules.md) and siblings hold the rules that must always be
loaded; every procedural detail lives here.

## Load this when

Canonical workflow responsibility is owned by [`../ownership.md`](../ownership.md).

- Bare `/docforge`, no task or flags → [intake.md](intake.md) — discovery
  gate, brief, **two-turn scope questions**, confirmation gate, graph provider
  choice.
- A task with tier/profile/flags already given, or continuing after intake
  confirmation → [planning.md](planning.md) — inspection, tier/profile
  selection, dynamic discovery, manifest init, dry-run tree, plan checkpoint.
- Materializing the next document in `write_order`, or continuing an
  incomplete run → [writing.md](writing.md) — execution card, evidence,
  scaffolding, provenance, status transitions, independent audit.
- `/docforge-revise` (`all` \| `<area>` \| `flow`), or update/refresh a named
  document → [revision.md](revision.md) — incl. shared flags, single-document
  update/refresh, flow-index organization.
- Staleness, migration, the whole-tree gate, or completion criteria →
  [validation.md](validation.md).
- The local dashboard (`dashboard.{py,js} start` / `status` / `stop`, see
  [`../runtime/dashboard/README.md`](../runtime/dashboard/README.md)) →
  [dashboard.md](dashboard.md) — metadata reconcile, signatures,
  build-if-changed, serve, open.
- Looking up a script's exact flags, invocation form, or exit codes →
  [tools.md](tools.md).

`/docforge` and `/docforge-revise` share flags: see
[`../flags.md`](../flags.md) (`--plan-only`, `--auto-accept`,
`--no-dashboard`).
There is no `--resume` or `--status` skill flag — see [`../flags.md`](../flags.md).

## Boundaries

Procedure only. Policy that a procedure depends on is owned in
`../references/` and canonical file ownership in [`../ownership.md`](../ownership.md); linked from here, not restated.
