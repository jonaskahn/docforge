# Coding-agent audience profile

Select the `coding-agents` audience when coding agents need a concise,
repository-local operating context. Every generated output is permanently
self-contained and independently useful for its own reader question. The
profile may repeat evidence-backed facts across outputs to preserve that
property.

## Generated structure

Standard layout:

```text
AGENTS.md
CLAUDE.md
CLAUDE.local.md
.claude/settings.json
docs/agents/
|-- architecture.md
|-- patterns.md
|-- testing.md
|-- conventions.md   # conditional on an evidenced conventions source
|-- tech-debt.md
|-- flow.md
`-- glossary.md
```

Compact layout combines the seven topic views into one file. The
tooling-owned root and local configuration outputs never fold:

```text
AGENTS.md
CLAUDE.md
CLAUDE.local.md
.claude/settings.json
docs/agents.md       # architecture, patterns, testing, conventions,
                     # tech debt, flows, terms
```

`CLAUDE.local.md` is added to the target repository's ignore rules.
`.claude/settings.json` is deep-merged so existing configuration survives.
`AGENTS.md` and `CLAUDE.md` resolve the same kernel contract, instruction,
template, target depth, and audit profile; each materializes the full concise
kernel.

Architecture, patterns, and both kernels use `code_graph`; testing and both
kernels use manifests. Conventions is selected only when a conventions source
exists. Flow and glossary require `flow_graph`. A missing required capability
marks only the affected output `skipped`; `requires` gates evidence, not
selection.

## Permanent isolation

Every agent-context output directly states the facts needed to answer its own
question. It contains none of the following:

- Markdown links or URLs;
- `@` imports;
- references to another agent output or a human-facing document;
- bare paths naming generated documentation;
- directions to open, read, or consult another document.

Plain source and configuration paths and verified commands are allowed.
Generated non-agent documentation never links, mentions, or exposes an
agent-context output. Agent-context outputs therefore do not participate in
the generated documentation navigation graph.

## Content contracts

### Root kernels

Both root kernels are full concise duplicates. Each directly states the
project purpose and stack, verified commands, durable repository map and
entry points, precedence, hard boundaries, non-obvious evidenced conventions,
and validation expectations. Neither includes a deeper-context section. Both
pass the `agents-kernel` size and content rubric.

### Local preferences and settings

The local-preferences output states its uncommitted, developer-specific
scope, keeps shared project behavior out, and warns against secrets. Settings
contain only safe portable denials and optional hooks backed by verified
commands; merge preserves existing user keys.

### Topic views

- `architecture.md`: stack, durable component and entry-point source paths,
  responsibilities, dependency direction, data boundaries, and material
  constraints.
- `patterns.md`: repeated implementation shapes, representative source paths,
  complexity hotspots, safe edit constraints, and applicable checks.
- `testing.md`: exact commands, suite layout and naming, test selection,
  fixtures and isolation, required validation matrix, and success signals.
- `conventions.md`: evidenced safety, naming, structural, and workflow
  directives with practical consequences; omitted when its condition is false.
- `tech-debt.md`: observed limitations, affected source paths, editing risks,
  safe handling, and tempting incidental fixes that need separate scope.
- `flow.md`: evidence-backed triggers, entry source paths, durable component
  sequences, terminal effects, and material failure behavior.
- `glossary.md`: concise evidence-backed definitions, code context,
  distinctions, aliases, and material state constraints.

The compact form presents those same seven topics in that order. Each
selected section remains independently useful, contains no documentation
reference, and is budgeted to roughly 25 lines. Omit Conventions when its
condition is false; omit Flows and Terms when flow evidence is unavailable.
Never emit an empty conditional section.

## Evidence recipe

Retrieve the smallest sufficient structural context from the selected code
graph. Use flow data only for flow and glossary. Convert raw nodes into
durable source/configuration paths, responsibilities, commands, constraints,
stable sequences, and direct definitions. Never paste raw graph schemas,
volatile line numbers, or inferred intent.

Commands must be verified against manifests, task definitions, CI, or direct
execution evidence. A convention needs repository policy, enforcement, or a
repeated structural signal. A limitation or flow step must be observed, not
plausible. When evidence cannot establish a required fact, state the bounded
uncertainty or skip the affected output instead of filling the gap.

### Non-obvious conventions

The kernel's optional Conventions section exists only for surprises the graph
actually surfaced. Mine topology rather than names. Strong signals include:

- rare cross-layer import anomalies;
- naming deviators inside an otherwise consistent layer;
- layer and source-path disagreements;
- dependency edges against the dominant direction;
- repeated non-generic return-shape or naming behavior.

Trace every candidate to real evidence, verify it across more than one signal
when possible, rank by rarity and editing impact, and keep only the few that
fit the kernel budget. Omit the entire section when nothing qualifies.
