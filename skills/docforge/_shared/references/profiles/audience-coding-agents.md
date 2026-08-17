# Coding-agent audience profile

Select the `coding-agents` audience when AI coding agents need a compact, repository-local
operating map. It writes last because it links to completed human-facing
documentation and compresses facts rather than creating another source of
truth.

## Generated structure

Standard layout:

```text
AGENTS.md
CLAUDE.md
CLAUDE.local.md
.claude/settings.json
docs/agents/
├── README.md
├── architecture.md
├── patterns.md
├── testing.md
├── tech-debt.md
├── conventions.md   # conditional on an existing conventions source
├── flow.md
└── glossary.md
```

Compact layout — the eight `docs/agents/*` views fold into one merged file, one
`##` per view. The four host-contract paths are tooling-owned locations and
never fold:

```text
AGENTS.md
CLAUDE.md
CLAUDE.local.md
.claude/settings.json
docs/agents.md       # at a glance, architecture, patterns, testing,
                     # conventions, tech debt, flows, terms
```

`CLAUDE.local.md` is added to the target repository’s ignore rules.
`.claude/settings.json` is deep-merged so existing configuration survives.
Cross-vendor mirrors beyond the fixed shims are generated only when requested
or when existing target configuration makes them applicable. `AGENTS.md` and
architecture/pattern views use `code_graph`; testing uses manifests; `conventions.md` is
selected only when a conventions source exists; only `flow.md` and flow-derived `glossary.md`
require `flow_graph`. A missing flow graph delays two views, not the whole profile.

`requires` gates **evidence, not selection**: a view whose capability is absent
is still selected into the manifest and is then marked `skipped`, rather than
never appearing. Only `selection.min_tier`, `selection.selectors`, and
`selection.condition` decide membership.

## One-way references

Agent-context documents may link any human-facing document. **No human-facing
document may link, mention, or `@`-reference an agent-context output** —
`docs/agents/`, `docs/agents.md`, `AGENTS.md`, `CLAUDE.md`, `CLAUDE.local.md`,
or `.claude/settings.json`. The agent overlay knows the whole tree; the tree
reads exactly as it would if this audience had never been confirmed. That is
why these views are routed from `AGENTS.md` and appear in no human-facing
index, and why the reachability rule in
[`../quality-bar.md`](../quality-bar.md) exempts them from `docs/README.md`.
The mechanical gate is the `agent-context leak` finding in
`scaffold_docs --audit`.

## Content ownership

### `AGENTS.md`

Keep a small root kernel: repository map, verified commands, validation rules,
critical constraints, and links to deeper context. It is exempt from
frontmatter, records provenance in the manifest, and must pass the dedicated
`lint_agents_kernel.{py,js}` size/content rubric (see
[`../../runtime/documents/README.md`](../../runtime/documents/README.md)).

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

These are token-budgeted retrieval views in both modes. What changes is who
owns the facts:

| Mode | When | These views |
|---|---|---|
| `linked` (default) | human-facing documentation exists | link to the human document that owns each fact, and include agent-specific exemplars only when no human-facing document owns that guidance |
| `standalone` | the agent-context group is all this run writes | own their facts, because there is no human document to link. The depth ceiling is unchanged: durable paths, boundaries, entry points, verified commands, and observable hazards — never design rationale, business context, or operational procedure |

`standalone` is agent-sufficient, not a replacement human documentation set.
A later run that adds human-facing documentation asks whether to convert these
views into linked stubs or keep them self-contained; see
[`../../workflows/revision.md`](../../workflows/revision.md).

## Evidence recipe

Follow the evidence loop in [`source-analysis.md`](../source-analysis.md).
Retrieve the smallest structural context from the code graph, and use flow data only for
`flow.md` and `glossary.md` (see [`graph-sources.md`](../graph/graph-sources.md)). Convert
raw graph nodes into durable paths, responsibilities, commands, constraints, and links; never
paste raw graph schemas or volatile line numbers.

### Non-obvious conventions

§5 of the kernel exists only for surprises the graph actually surfaced — omit the
section (heading included) when nothing qualifies. Mine the *topology*, not the
names: every bullet must trace to a real graph edge, and each claim is checked
against the graph before it is written.

Signals to look for, in order of evidence strength:

- **Cross-layer import anomalies** — edges that occur once or twice between
  layers that otherwise never talk;
- **Naming deviators within a layer** — files whose names do not match the
  layer's modal suffix or pattern;
- **Layer/path disagreements** — a file's location contradicts its graph
  classification (e.g. a source file parked under `tests/`);
- **Dependency-direction violations** — upward imports against the layer
  precedence the module map states;
- **Recurring return-shape / naming signals** — patterns repeated across
  non-generic function summaries (e.g. every factory returns a tuple in the
  same order).

Rank candidates by rarity and traceability, keep only the top few, and cap the
bullet count to fit the kernel's `lint_agents_kernel.{py,js}` line budget.
Never
restate a convention a human architecture document already owns — link instead.
