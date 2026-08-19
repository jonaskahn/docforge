# `machine-config`

**Reader question** — "What permissions and hooks does this machine's local Claude Code configuration carry?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | n/a — JSON artifact, not a Markdown document |

This is a JSON settings file, not prose; the shape vocabulary in [`document-shapes.md`](../../references/document-shapes.md) applies only to Markdown templates and does not cover it.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Valid, portable safety denials | top-level | a destructive allowance |
| 2 | Only verified optional hooks | top-level | an invented hook not evidenced in the repository |
| 3 | Merge that preserves every existing user key | merge behavior | an existing user key silently discarded |

## Keep out

| Not here | Lives in |
|---|---|
| Any documentation reference | nowhere — this is a settings file, not a document |
| An invented command | nowhere — verify before adding it |
| Destructive allowances | nowhere — portable safety denials only |
| Host-specific configuration | nowhere — portable settings only |

## Isolation

No reference in either direction: this file contains no Markdown link, URL, `@` import, or reference to any peer-agent or human-facing document. A generated non-agent document never links or mentions this file.
