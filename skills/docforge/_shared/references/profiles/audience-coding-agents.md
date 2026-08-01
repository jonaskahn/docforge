# Coding-agent audience profile

Select the `coding-agents` audience when AI coding agents need a compact, repository-local
operating map. It writes last because it links to completed human-facing
documentation and compresses facts rather than creating another source of
truth.

## Generated structure

```text
AGENTS.md
CLAUDE.md
CLAUDE.local.md
.claude/settings.json
docs/agents/
├── INDEX.md
├── architecture.md
├── patterns.md
├── testing.md
├── tech-debt.md
├── conventions.md   # conditional on an existing conventions source
├── flow.md
└── glossary.md
```

`CLAUDE.local.md` is added to the target repository’s ignore rules.
`.claude/settings.json` is deep-merged so existing configuration survives.
Cross-vendor mirrors beyond the fixed shims are generated only when requested
or when existing target configuration makes them applicable. `AGENTS.md` and
architecture/pattern views use `code_graph`; testing uses manifests; `conventions.md` is
selected only when a conventions source exists; only `flow.md` and flow-derived `glossary.md`
require `flow_graph`. A missing flow graph delays two views, not the whole profile.

## Content ownership

### `AGENTS.md`

Keep a small root kernel: repository map, verified commands, validation rules,
critical constraints, and links to deeper context. It is exempt from
frontmatter, records provenance in the manifest, and must pass the dedicated
size/content lint.

### Fixed shims and settings

`CLAUDE.md` points to the canonical root kernel. `CLAUDE.local.md` is a local
extension point. Settings contain only safe, portable defaults and are merged
without discarding user values.

### `docs/agents/`

- `architecture.md`: short layer/entry-point map linked to the owning
  architecture documents;
- `patterns.md`: representative paths, recurring conventions, and complexity
  hotspots useful before editing;
- `testing.md`: exact commands, test locations, and the minimum validation
  matrix;
- `tech-debt.md`: editing hazards linked to the authoritative debt/limitation
  entries;
- `conventions.md`: evidenced local conventions, generated only when the
  source condition is satisfied;
- `flow.md`: triggers and entry points linked to canonical flow documents;
- `glossary.md`: flow/domain terms linked to their owning glossary or flow.

These are token-budgeted retrieval views. They link to the human document that
owns each fact and include agent-specific exemplars only when no human-facing
document owns that guidance.

## Evidence recipe

Follow the evidence loop in [`source-analysis.md`](../source-analysis.md).
Retrieve the smallest structural context from the code graph, and use flow data only for
`flow.md` and `glossary.md` (see [`graph-sources.md`](../graph/graph-sources.md)). Convert
raw graph nodes into durable paths, responsibilities, commands, constraints, and links; never
paste raw graph schemas or volatile line numbers.
