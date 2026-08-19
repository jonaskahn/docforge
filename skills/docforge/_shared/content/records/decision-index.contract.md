# `decision-index`

**Reader question** — "What decisions were recorded, and which one do I need?"

| Mode | Depth | Shape |
|---|---|---|
| Routing | router | router |

This index carries only routing metadata; the reasoning behind each decision lives in the record it links to, never here.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | What this log is, why decisions are recorded, and the status lifecycle (proposed → accepted → superseded) | L0 | rationale for any specific decision |
| 2 | A status legend: what each status value means | L1 | a status left unexplained the first time it appears |
| 3 | Entries grouped by topic area, ordered newest first within each group | L1 | one flat chronological list with no topic grouping |
| 4 | Per entry: ascending number, outcome-title link, status, date, optional topic | L2 | a title restated as the topic instead of the decided outcome |
| 5 | A superseding status shown inline (`superseded by NNNN`) so a reader never opens a stale record by mistake | L2 | a superseded record left indistinguishable from an active one |

## Keep out

| Not here | Lives in |
|---|---|
| Context, decision, consequences, or alternatives for any record | `adr` |
| Rationale for why a decision was reopened | the new record's context section |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Routing metadata only: number, outcome title, status, date, topic, grouping | every `adr` record it lists | the index routes; each record owns its own rationale |
