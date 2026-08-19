# `business-rules`

**Reader question** — "What's the exact rule here, and how do I know it's actually enforced?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | deep-dive | entry-catalog |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | One entry per rule: stable id, plain-language statement | per entry | a method, field, or branch name promoted into a rule with no proven condition |
| 2 | Trigger, outcome, exceptions, owning process | per entry | rules that share a code path but differ in trigger or outcome, merged into one entry |
| 3 | Source-enforced condition and executable verification, when one exists | per entry | precedence between conflicting rules left unstated |

## Keep out

| Not here | Lives in |
|---|---|
| A rule inferred only from a name | nowhere — prove the condition and effect |
| The process's ordered steps, duplicated | `ba_process_flows` |
| Test implementation, duplicated | the owning test suite, linked |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Rule identity, trigger, outcome, exceptions, enforcement evidence | `ba_process_flows` | the business narrative that applies rules is owned there |
| The chain from requirement to owning rule | `ba_requirements` | owned there, linked not rebuilt here |
