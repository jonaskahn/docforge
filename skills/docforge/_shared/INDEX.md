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

`agents/` at the plugin root contains Claude-plugin-native, thin dispatch
wrappers. Canonical procedure remains in `_shared`; non-Claude hosts use the
inline fallback in each workflow.

| Path | Owns |
|---|---|
| [`workflows/`](workflows/INDEX.md) | Step-by-step procedure by invocation |
| [`references/`](references/INDEX.md) | Owned policy prose |
| [`content/`](content/INDEX.md) | Contracts, instructions, templates |
| [`runtime/cli/`](runtime/cli/INDEX.md) | Public Python/Node launchers |
| [`runtime/`](runtime/INDEX.md) | Implementation behind launchers |
| [`.metadata/`](.metadata/) | Catalog, schemas, profiles |

Tools run with this directory as the cartridge root. The agent locks one
session engine; see [`rules.md`](rules.md) and [`workflows/tools.md`](workflows/tools.md).

Entry skills: [`../SKILL.md`](../SKILL.md),
[`../../docforge-revise/SKILL.md`](../../docforge-revise/SKILL.md).
