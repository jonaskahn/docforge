# `contributing-router`

**Reader question** — "What do I need to do before my change is accepted?"

| Mode | Depth | Shape |
|---|---|---|
| Orientation | router | router |

A router hands the contributor to the document that owns each step; it never restates a setup, testing, or convention detail its own children already own.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | The verified path from clone to an accepted change, as an ordered link list | L0 | a path that has not actually been run |
| 2 | Which checks are required before a change is accepted (build, tests, lint, review) | L1 | a check listed but not linked to where it is run |
| 3 | Links to the conventions and setup documents that own each step's detail | L1 | conventions or setup content restated here |
| 4 | Links to ownership: who reviews what, and the escalation path when a reviewer is unavailable | L2 | an invented reviewer or team not evidenced in the repository |
| 5 | Where to route a question that isn't answered by a linked document | L3 | leaving a contributor with no next step |

## Keep out

| Not here | Lives in |
|---|---|
| The setup or testing procedure itself | `setup_guide`, `testing_guide` |
| Coding conventions | `conventions` |
| Named owners and their boundaries | `ownership` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| The ordered contribution path and which checks gate it | `setup_guide`, `testing_guide`, `conventions`, `ownership` | each linked document owns its own step in full; this page only orders them |
