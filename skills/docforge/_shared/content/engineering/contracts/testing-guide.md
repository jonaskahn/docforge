# `testing-guide`

**Reader question** — "How do I run this project's tests, and what does a flaky-looking failure usually mean?"

| Mode | Depth | Shape |
|---|---|---|
| How-to | deep-dive | entry-catalog |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Organized by test layer (unit, integration, end-to-end), fast-and-narrow first | lead | layers presented in random order with no pyramid shape |
| 2 | Per layer: run command, what it covers, what it deliberately doesn't, isolation model (real database, container, or mock) | per layer | an isolation model left unstated |
| 3 | Failure diagnosis per layer: what a flaky-looking failure usually means, and the first thing to check | per layer | generic testing philosophy instead of "my tests are red" diagnosis |
| 4 | Unsupported environments retained as explicit limitations | lead or L3 | an unsupported environment silently dropped |

## Keep out

| Not here | Lives in |
|---|---|
| Generic testing advice with no repository grounding | nowhere |
| Testing conventions and their enforcement | `conventions` |
| Which checks gate a release | `release_guide` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Test layers, run commands, isolation models, failure diagnosis | `conventions` | testing conventions and their enforcement are owned there |
| — | `release_guide` | the release procedure owns its own gates |
