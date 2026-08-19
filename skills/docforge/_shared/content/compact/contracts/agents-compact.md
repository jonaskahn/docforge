# `agents_compact`

**Reader question** — "What does a coding agent need to know about this repository, in one file it can read in one pass?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | deep-dive | merged-section-spine |

## What this file merges

| Member | At |
|---|---|
| `agents_architecture` | spine + coding-agents |
| `agents_patterns` | spine + coding-agents |
| `agents_testing` | spine + coding-agents |
| `agents_conventions` | spine + coding-agents (`conventions_source`) |
| `agents_tech_debt` | spine + coding-agents |
| `agents_flow` | spine + coding-agents |
| `agents_glossary` | spine + coding-agents |

Exactly the selected topics, in this order: architecture, patterns, testing, conditional conventions, tech debt, conditional flows, conditional terms. Omit conventions when no conventions source is evidenced; omit flows and terms when flow evidence is unavailable.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Concise purpose statement | lead | attribution language or narrative framing |
| 2 | Each selected topic as a self-contained answer to its own reader question, roughly 25 lines maximum | `## {{Topic}}` | a topic section that assumes another section's content |
| 3 | Direct facts, durable source/configuration paths, constraints, and verified commands per topic | `## {{Topic}}` | a volatile symbol dump instead of a durable fact |
| 4 | Repeated facts across topics where each topic's own question needs them | `## {{Topic}}` | a cross-reference between topics standing in for a repeated fact |

## Keep out

| Not here | Lives in |
|---|---|
| Markdown links, URLs, imports, or any documentation reference | nowhere — permanently isolated |
| Reader routing or attribution language | nowhere — this file is read, not browsed |
| A topic section not selected by evidence | nowhere — omit rather than pad the set |

## Isolation

No reference in either direction: this file, and each topic section within it, contains no Markdown link, URL, `@` import, or reference to any peer-agent or human-facing document. A generated non-agent document never links or mentions this file. Facts a topic needs are repeated within it rather than pointed at another section or another document — see [`document-composition.md`](../../references/document-composition.md).
