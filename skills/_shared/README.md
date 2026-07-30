# Docforge shared cartridge

Not a skill. Hosts must not register this folder as an Agent Skill (no
`SKILL.md` frontmatter). Both `/docforge` and `/docforge-revise` load from
here.

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
| [`workflows/`](workflows/README.md) | Step-by-step procedure by invocation |
| [`references/`](references/README.md) | Owned policy prose |
| [`content/`](content/README.md) | Contracts, instructions, templates |
| [`runtime/cli/`](runtime/cli/README.md) | Public Python/Node launchers |
| [`runtime/`](runtime/README.md) | Implementation behind launchers |
| [`.metadata/`](.metadata/) | Catalog, schemas, profiles |

Tools run with this directory as the cartridge root. The agent locks one
session engine (see [`rules.md`](rules.md)), then invokes with **subcommand
before flags**:

```sh
# After locking python3:
python3 runtime/cli/python/query_catalog.py --route <document-id>

# After locking node:
node runtime/cli/js/query_catalog.js --route <document-id>
```

Entry skills: [`../docforge/SKILL.md`](../docforge/SKILL.md),
[`../docforge-revise/SKILL.md`](../docforge-revise/SKILL.md).
