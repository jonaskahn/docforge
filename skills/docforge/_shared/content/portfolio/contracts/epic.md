# `epic`

**Reader question** — "What cross-repository initiative is this, and how does it actually move across the member repos?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | answer-first |

The initiative's outcome is the governing claim, stated before the member repos it spans.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | The initiative outcome | L0 | member repos listed before the outcome is stated |
| 2 | Member repos spanned, each with its owning flow/feature and component touched | L1 | a member's internal call graph restated instead of linked |
| 3 | The cross-repo sequence tying the repos together | L2 | an unproved sequence presented as confirmed instead of marked an open gap |
| 4 | Open gaps: missing owners, unresolved handoffs, undetermined sequencing | L3 | a gap silently omitted instead of marked `undetermined` |

## Keep out

| Not here | Lives in |
|---|---|
| Invented scope | nowhere — ground every claim in member documentation or history evidence |
| A member's internal call graph | that member's own `flow` document |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Outcome, member repos, owning flow/feature/component per repo, cross-repo sequence | each member repo's own `flow` document | the member's internal steps are owned there; this document only names which flow/feature each repo contributes |
| — | `portfolio_system_context` | system-context maps portfolio-wide boundaries; this document maps one initiative's path across them |
| An unresolved handoff or missing owner | `portfolio_diligence_index` | an open gap in the initiative is exactly the kind of claim diligence-index exists to track |
