# `ownership`

**Reader question** — "Who owns this area, and who do I escalate to if they're unavailable?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | lookup |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | One row per owned area (a directory, service, or domain — not "everything") | the table | an area with no stated responsibility boundary, reading as "owns everything here" |
| 2 | The responsibility boundary: what owning it means (review authority, on-call, or both) | the table | an invented owner with no CODEOWNERS file or team declaration |
| 3 | An escalation token: a team name or channel, never an individual's name that will go stale | the table | an individual's name used as the escalation token |
| 4 | Rows ordered by how often a contributor needs to find that owner | the table | alphabetical ordering |

## Keep out

| Not here | Lives in |
|---|---|
| An invented person or team | nowhere — state the area unowned or undetermined instead |
| Frequent authorship treated as proof of ownership | nowhere — use CODEOWNERS or team declarations as primary evidence |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Owned areas, responsibility boundaries, escalation tokens | `contributing_root` | the contribution journey links here to name who must approve |
