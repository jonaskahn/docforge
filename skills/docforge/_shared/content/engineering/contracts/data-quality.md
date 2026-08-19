# `data-quality`

**Reader question** — "What's actually checked about this data, where does the check run, and what happens when it fails?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | entry-catalog |

_Aliased with: `data-flow`, `data-types` (same content contract)._

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Organized by quality dimension (accuracy, completeness, timeliness, validity, uniqueness, consistency) | lead | dimensions omitted or merged into one generic "quality" bucket |
| 2 | Per dimension: what is checked and where (ingestion, transformation, scheduled audit) | the table | a check described with no stated enforcement point |
| 3 | What happens on failure: reject, quarantine, alert-only, or auto-correct | the table | a scoped guarantee (sample-only) read as universal |
| 4 | An evidenced durable relationship only, when a diagram is used | optional erDiagram | inferred lineage or cardinality drawn with no evidence |

## Keep out

| Not here | Lives in |
|---|---|
| Unevidenced lineage or a sample-only guarantee stated as universal | nowhere — say so plainly instead |
| A dataset's identity and lineage contract | `dataset` |
| Per-handoff movement guarantees | `data_flow` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Quality dimensions, checks, enforcement points, failure actions | `dataset` | each dataset's identity and lineage contract is owned there |
| — | `data_flow` | per-handoff guarantees are owned there |
| A failed check's recovery handoff | the relevant `runbook` | recovery procedure is owned there, linked not restated |
