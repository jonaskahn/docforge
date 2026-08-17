# {{TITLE}}

_Last reviewed: {{YYYY-MM-DD}}_

{{Two or three sentences introducing the compact coding-agent section: what
these retrieval views cover, why they exist separately from the human
documentation, and how an agent should budget its reading. A coding agent
with no prior project knowledge should be able to pick the right section in
one pass.}}

## At a glance

| View | Answers | Read when |
|---|---|---|
| {{Section name}} | {{the question this view answers}} | {{the situation that sends an agent here}} |

{{One row per `##` section below. Keep the table short enough to read before
committing tokens to a section.}}

## Scope and boundaries

{{What these views cover, and what they deliberately do not: design rationale,
business context, and operational procedure have no document in this repository
and must not be invented here. Say so plainly rather than implying coverage.
Link `AGENTS.md` as the kernel — entry points, verified commands, and precedence
live there and are never restated here. Link every selected document under
`docs/agents/` that this file does not merge, plus `CLAUDE.md`,
`CLAUDE.local.md`, and `.claude/settings.json` when selected.}}

{{Budget each `##` section below to roughly 25 lines.}}

## Architecture

{{Durable component paths and the constraints that bind them, grounded in the
code graph. Paths only — no volatile symbol dumps.}}

## Patterns

{{The repeated shapes an agent should follow, each with the verified command
that exercises it and a link to the human document that owns the rationale.}}

## Testing

{{How to run and extend the suite — verified commands only, grounded in
repository manifests and scripts.}}

## Conventions

_Only when a conventions source exists — omit this section entirely
otherwise._

**Convention:** {{stated plainly}} · **Evidence:** {{lint rule, CI check, or
repeated pattern recorded in provenance}} · **If not followed:**
{{consequence}}

{{Repeat per convention. Drop any dimension the repository doesn't evidence.}}

## Tech debt

{{Known rough edges an agent will hit, and what not to "fix" incidentally.
Each entry names the durable path and the reason the shape is the way it
is.}}

## Flows

_Only when a flow graph is available — omit this section entirely
otherwise._

{{Compact flow lookup grounded in declared flow evidence: flow name, entry
point, and the owning flow document.}}

## Terms

_Only when a flow graph is available — omit this section entirely
otherwise._

{{Term lookup. Each term links the human document that owns its definition;
never restate a definition owned elsewhere.}}
