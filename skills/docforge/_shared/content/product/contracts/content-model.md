# `content-model`

**Reader question** — "What content types exist, what state can they be in, and who can move them between states?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | entry-catalog |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | One section per content type: fields (name, type, required/optional) | per type | a field derived from a sample payload instead of schema evidence |
| 2 | Lifecycle states actually implemented (draft, review, published, archived, or whatever the system uses) and validation per transition | per type | an unsupported transition presented as available |
| 3 | The publishing boundary: what makes content visible to an end reader, and what stays staged | per type | the publishing boundary left implicit |
| 4 | Ownership per content type: who can create, edit, or publish it | per type | editorial strategy (tone, voice, calendar) presented as if it were ownership |

## Keep out

| Not here | Lives in |
|---|---|
| Editorial strategy unsupported by repository evidence | nowhere — out of this document set entirely |
| Wire representation of fields | `data_types` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Content types, fields, lifecycle, publishing boundary | `data_types` | wire representation of fields is owned there, linked not re-derived |
