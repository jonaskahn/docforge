# `decisions_compact`

**Reader question** — "What decisions were recorded, and what does each one say?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | orientation | merged-section-spine |

## What this file merges

| Member | At |
|---|---|
| `decisions_index` | diligence |
| `adr` (one section per recorded decision) | diligence |

The register comes first, holding every recorded decision whether or not it earned a written-up section; the section budget bounds how many decisions are expanded here, never how many are known.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Section introduction: what this log is and how the status lifecycle works | lead | rationale for any specific decision |
| 2 | The decision register: identifier, title, status, date, superseded-by, for every recorded decision | `## Decision register` | dropping a decision from the register because it lacks a section |
| 3 | Links to every unmerged document in this section's folder | `## Decision register` | a promised link to an unmaterialized path |
| 4 | One `##` section per folded decision, carrying every field of the `adr` contract — outcome title, status/date, context, decision, consequences, revisit condition — condensed, never summarized | `## {{Decision title}}` | a folded decision missing its consequences or revisit condition |

## Keep out

| Not here | Lives in |
|---|---|
| Implementation detail owned by an architecture section | `arch_low_level` |
| Retroactive justification the repository does not evidence | nowhere — mark `Reconstructed` instead |
| Direct source-file navigation | provenance |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| The register and section ordering | each unmerged document in `docs/decisions/` | the fold covers folded decisions only; the rest keep their own paths |
| Nothing a folded decision owns | `decisions.md#<slug>` anchors | a folded decision has no file of its own; the `adr` contract's own links resolve inside this file |
