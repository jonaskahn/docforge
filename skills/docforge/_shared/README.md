# Docforge shared cartridge

Not a skill. Hosts must not register this folder as an Agent Skill (no
`SKILL.md` frontmatter). Lives under `skills/docforge/_shared/` so Agent
Skills install (`npx skills add`) copies it with the `docforge` skill —
a top-level `skills/_shared/` sibling is skipped by that installer and
also collides with unrelated hub `_shared/` folders. Both `/docforge` and
`/docforge-revise` load from here (`docforge-revise` resolves
`../docforge/_shared/`).

## Always-load policy

| File | Owns |
|---|---|
| [`rules.md`](rules.md) | Safety boundaries, code-graph precondition, provider sufficiency, completion |
| [`retrieval.md`](retrieval.md) | Agent retrieval protocol |
| [`flags.md`](flags.md) | Shared skill flags (`--plan-only`, `--auto-accept`) |
| [`ownership.md`](ownership.md) | Canonical ownership of policy and content |

## Cartridge layout

Every workflow executes its canonical procedure inline from this cartridge, so
plugin and Agent Skills installs follow the same path.

| Path | Owns |
|---|---|
| [`workflows/`](workflows/README.md) | Step-by-step procedure by invocation (incl. [`workflows/dashboard.md`](workflows/dashboard.md)) |
| [`references/`](references/README.md) | Owned policy prose |
| [`content/`](content/README.md) | Contracts, instructions, templates |
| [`runtime/cli/`](runtime/cli/README.md) | Public Python/Node launchers |
| [`runtime/`](runtime/README.md) | Implementation behind launchers (incl. [`runtime/dashboard/`](runtime/dashboard/README.md) — the dashboard build/serve runtime and its Fumadocs template) |
| [`.metadata/`](.metadata/) | Catalog, schemas, profiles |
| [`help.md`](help.md) | Canonical `--help` reference per entrypoint (purpose + every parameter) |

Tools run with this directory as the cartridge root. The agent locks one
session engine; see [`rules.md`](rules.md) and [`workflows/tools.md`](workflows/tools.md).

### Linking contract

Every entrypoint that hands out this cartridge resolves it to an **absolute
path at load time**, never a working-directory-relative one:

- Skill content (`skills/*/SKILL.md`) uses `${CLAUDE_SKILL_DIR}/_shared/…`
  (`docforge`) or `${CLAUDE_SKILL_DIR}/../docforge/_shared/…` (the thin
  entrypoints) — the absolute skill dir, for both plugin and Agent Skills
  installs.
- `rules.md`'s always-loaded path-anchoring rule makes every `./`/`../`
  reference inside cartridge files resolve against the given absolute root.

All entrypoints carry the fallback: if the literal `${CLAUDE_SKILL_DIR}`
placeholder survives (older host), ask the user for the absolute cartridge
root before following any cartridge link. Tests in `tests/test_structure.py`
enforce the contract (placeholder targets resolve and no CWD-relative
cartridge links appear in `skills/*/SKILL.md`).

Entry skills: [`../SKILL.md`](../SKILL.md),
[`../../docforge-revise/SKILL.md`](../../docforge-revise/SKILL.md),
[`../../docforge-dashboard/SKILL.md`](../../docforge-dashboard/SKILL.md).
