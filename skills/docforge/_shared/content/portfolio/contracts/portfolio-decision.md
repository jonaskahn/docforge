# `portfolio-decision`

**Reader question** — "Why does this cross-repository arrangement exist, and which member repos does it bind?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | deep-dive | fixed-frame |

External authority: the MADR/Nygard decision-record shape, applied at portfolio scope — title, status, context, decision, consequences, with member ADR links standing in for a single repo's local evidence.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | An outcome title stated as the cross-repository decision, not the topic | title | a repository-local ADR duplicated instead of linked |
| 2 | Status and date | status/date | a decision presented as portfolio-wide when it is really one member's local choice |
| 3 | Cross-repository decision evidence: the member ADRs that establish it | context | member local rationale rewritten as a new shared fact |
| 4 | The decision and its consequences across the member set | decision/consequences | a consequence stated for one member only, with no cross-repo framing |

## Keep out

| Not here | Lives in |
|---|---|
| Repository-local ADR duplication | the member repo's own `adr` |
| Rewritten member rationale | nowhere — link the member ADR, never restate its argument |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| The cross-repository decision, its consequences, and which members it binds | each member ADR it draws on | a portfolio decision links the member ADRs that establish it and must not rewrite their local rationale |
