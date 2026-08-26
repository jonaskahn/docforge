# `agents-layer-rule`

**Reader question** — "What conventions apply specifically to files in this layer, that the kernel does not already cover?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | deep-dive | lookup |

Inherits [topic-view-commons.md](../references/topic-view-commons.md).

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Layer name, path glob, and one-line layer description | lead | a glob that does not match the layer's files |
| 2 | Up to five evidenced non-obvious conventions with their required shape | L2 | a convention inferred from a single occurrence |
| 3 | Up to three complexity hotspots with safe-edit constraints | L2 | an invented hotspot with no repository evidence |
| 4 | One verified validation command for the changed area | last | an invented command never actually run |

## Keep out

| Not here | Lives in |
|---|---|
| Kernel facts (commands, precedence, boundaries) | `AGENTS.md` |
| Any documentation reference | nowhere — permanently isolated |
| Inferred intent or speculative debt | nowhere — state the observed fact |

## Isolation

No reference in either direction: this file contains no Markdown link, URL,
`@` import, or reference to any peer-agent or human-facing document. Facts
this output's own question needs are repeated here rather than pointed
elsewhere.
