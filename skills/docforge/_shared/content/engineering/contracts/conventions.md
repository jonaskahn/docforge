# `conventions`

**Reader question** — "What conventions does this codebase actually enforce, and what breaks if I ignore one?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | deep-dive | lookup |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Conventions grouped by dimension (code structure, error handling, testing, review) | lead | generic style advice with no repository evidence |
| 2 | Each convention cited to the lint rule, CI check, or repeated pattern that enforces or demonstrates it | the table | "we use dependency injection" asserted with no constructor pattern shown |
| 3 | The consequence of not following it (a failing lint rule, a rejected review), where one exists | the table | a real enforcement consequence left unstated, reading as a suggestion instead of a rule |
| 4 | Ordered by how often a contributor collides with it | the table | ordering by adoption date instead |

## Keep out

| Not here | Lives in |
|---|---|
| Generic language advice ("write clean code") | nowhere — omit unless evidenced |
| How conventions are exercised by the test suite | `testing_guide` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Evidenced conventions, their artifacts, enforcement consequences | `testing_guide` | how conventions are exercised by the suite is owned there |
