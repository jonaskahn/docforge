# `adr`

**Reader question** — "Why does this exist the way it does, and can the reasoning still change?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | reference | fixed-frame |

External authority: the MADR/Nygard architecture-decision-record shape (title, status, context, decision, consequences). This document does not reorder those sections to put a governing claim first — conformance to the record shape is the point.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | An outcome title stated as the decision, not the topic | title | "Database choice" instead of "Use Postgres for session storage" |
| 2 | Status and date, and — for a decision this one supersedes or is superseded by — the link in both directions | status/date | editing a superseded record instead of preserving it and cross-linking |
| 3 | Context: past-tense constraints that forced the decision | context | present-tense narration that reads as still-open |
| 4 | The active decision, in present-tense commitments | decision | a decision buried inside the context prose |
| 5 | Evidenced alternatives and drivers, one parallel line each, when recoverable | decision | an alternative with no comparable tradeoff line |
| 6 | Consequences split into positive, negative, and follow-up | consequences | only the benefit stated, the real cost omitted |
| 7 | A revisit condition: what would reopen this decision | consequences | no stated condition, leaving the decision permanently unquestioned |
| 8 | A source citation or an explicit `Reconstructed` notice naming the history used and what may be incomplete | context | a later commit's implementation promoted into contemporaneous rationale |

## Keep out

| Not here | Lives in |
|---|---|
| Rewritten or invented history | nowhere — reconstruct honestly or say so |
| Index routing metadata (number, status, date across all records) | `decision-index` |
| The resulting architectural fact this decision produced | the document that fact belongs to (e.g. `arch_high_level`) |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Title, status, context, decision, consequences for this one decision | the architecture or domain document the decision shaped | the record owns rationale; the shaped document owns the resulting fact, linked not restated |
| A decision this one supersedes | the superseded record, both directions | preserves history — old and new records must reference each other explicitly |
