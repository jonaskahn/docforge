# `root-readme`

**Reader question** — "What does this repository deliver, does it fit what I need, and how do I get a first result?"

| Mode | Depth | Shape |
|---|---|---|
| Orientation | orientation | answer-first |

The governing claim — what this delivers and whether it fits — comes before any setup detail; a runnable quick start makes that claim checkable.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | What this repository delivers and who it's for, as a decision a prospective reader can act on | L0 | a feature list with no stated audience |
| 2 | One runnable quick start, verified, before any environment or prerequisite detail | L1 | a quick start that requires reading setup first to run |
| 3 | Capabilities described as outcomes, and meaningful boundaries named honestly | L1 | a capability claimed with no evidence, or a limitation left unstated |
| 4 | A routing table sending each reader type to the document that owns their next question | L2 | the README trying to answer every question itself |
| 5 | Environment choices, prerequisites, and recovery, linked out rather than inlined | L3 | the quick start growing into a second setup guide |

## Keep out

| Not here | Lives in |
|---|---|
| Deep architecture | `arch_high_level` |
| Full setup procedure (environment choices, prerequisites, recovery) | `setup_guide` |
| An unverified status, owner, support channel, command, or link | nowhere — omit unknown operational metadata rather than presenting a placeholder as fact |
| The complete reader-question routing table | `docs_index` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Purpose, audience, verified quick start, routing | `quickstart` | the under-a-minute verified first result is owned there |
| — | `setup_guide` | linked when the quick start would need environment choices, prerequisites, or recovery |
| — | `docs_index` | the documentation index owns the complete reader-question routing table |
