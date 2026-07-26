# Overlay: Business Analyst

**Applies when:** the codebase encodes business rules, eligibility logic, approval workflows, or process steps that a non-engineer needs to consult reliably without reading source.

Adds four files under `docs/product/business-analyst/`.

## `README.md`

Index only — one line per file below, plus a single closing sentence: "If Product Owner documentation is also needed, see `../product-owner/`."

## `business-rules.md`

The BA's primary artifact. One entry per rule, sourced from the knowledge graph and verified against the actual conditional logic — never inferred from a variable or function name.

```markdown
### Rule: <plain-language name>
**Statement:** <the rule, in one sentence a business stakeholder would recognize>
**Enforced in:** `src/<module>::<function>` (symbol name, not a line-number link — links rot on refactor)
**Applies to:** <which flow, which entity>
**Exceptions:** <any override conditions — usually the part a BA most needs and the code most obscures>
**Source:** verified via `/understand-chat "what conditions gate <rule>"` against `<flow-name>`, <date>
```

Build the rule set by asking the graph narrow questions per flow — list flows with `/understand-domain`, then ask `/understand-chat "what business rules gate <flow>"` per flow. Do not derive rules from architecture prose; that describes structure, not business logic.

**Anti-pattern:** restating code in English ("if status equals 'approved' then...") — a BA wants the business meaning of a condition, not a transliteration of the branch that implements it.

## `process-flows.md`

The business process as actually executed by the system — business-language steps a domain expert recognizes, each annotated with where it's enforced, not the technical call graph.

```markdown
### Flow: <business name, e.g. "Order approval">
1. <step, business language> — enforced by `<symbol>`
2. <step> — enforced by `<symbol>`
...
**Decision points:** <where the flow branches, on what business condition — link to the relevant entry in business-rules.md rather than restating it>
```

Source steps from `/understand-domain`. Cross-check against `git log` only when the *why* of a branch is in question — that reasoning belongs in an ADR (`docs/architecture/decisions/`); link to it, don't duplicate it here.

## `requirements-traceability.md`

Maps requirement → implementation → verification — the file a BA opens when a stakeholder asks "did we actually build what was asked for."

| Requirement (stakeholder's own wording, if available) | Business rule(s) implementing it | Code location | Test coverage | Status |
|---|---|---|---|---|
| | link to `business-rules.md#rule` | `symbol` | test file/name, or "none — flag" | implemented / partial / not started |

If the original requirement wording isn't recoverable from any connected source (no ticket system, no discussion history), do not invent stakeholder language — write the requirement as inferred from the code and mark the row `> TODO(owner): confirm original requirement wording`.

## Non-negotiable specific to this overlay

Never state a business rule's condition more precisely than the code actually enforces it. If the code's edge-case handling is genuinely ambiguous, record that ambiguity in the rule entry rather than resolving it in the reader's favor — a documented ambiguity is a bug report waiting to be filed; a silently resolved one is a future incident.
