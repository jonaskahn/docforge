# `backlog-traceability`

**Reader question** — "Which ticket produced this feature, and what's its current status?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | coverage-matrix |

This dynamic document exists only when discovery finds ticket evidence; full coverage means every evidenced item has a row, and the document is omitted entirely rather than left as an empty seed table.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Per evidenced item: immutable ticket identifier, feature, relevant flow/change, verification, status | the table | a guessed mapping inferred from a commit message |
| 2 | Tracker wording preserved, with a source link where permitted | the table | invented backlog status |

## Keep out

| Not here | Lives in |
|---|---|
| A guessed ticket mapping | nowhere — omit the row rather than guess |
| An empty seed table | nowhere — omit the whole document when evidence disappears |
| Flow-level verification detail | the relevant `flow` document |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Ticket → feature/flow → verification → status mappings | `po_features` | the feature a ticket maps to is owned there |
| Flow-level verification evidence | the relevant `flow` document | owned there, linked not duplicated per ticket |
