# `configuration`

**Reader question** — "What setting controls this behavior, what's its default, and why did changing it have no effect?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | lookup |

The precedence rule is the L0 obligation this shape's stop test enforces: a settings row read without it is wrong, not merely incomplete — so the read-rule comes before the table, not after.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Sources and precedence: which source wins when two disagree | lead | the precedence rule stated after the settings table, or not at all |
| 2 | Every read setting: name, default, scope, sensitivity, validation | the table | an aspirational setting the code doesn't actually read |
| 3 | Settings ordered by how often a reader tunes them, not alphabetically | the table | the setting everyone changes in local dev buried below one nobody has touched since launch |

## Keep out

| Not here | Lives in |
|---|---|
| A secret value | nowhere — show the variable name, note where the value lives |
| An aspirational setting | nowhere — only settings the code actually reads |
| Per-environment values | `infra_environments` |
| First-run walkthrough | `setup_guide` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Every read setting: name, default, scope, sensitivity | `infra_environments` | which environment differs and how is owned there, referenced not re-derived |
| — | `setup_guide` | the verified path to a running instance consumes these settings; the guide links here rather than restating them |
