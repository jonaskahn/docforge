# `output-exit-contract`

**Reader question** — "Can I script against this command's output, and what exit code means what?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | lookup |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | The exit-code table first: code, meaning, scripting stability | lead | usage prose standing in for the exit-code table |
| 2 | Which stream owns which content, and the output format's stability guarantee | L2 | a format's stability guarantee left unstated |
| 3 | One real, captured output example per format, whitespace and field order intact | L2 | a hand-typed approximation instead of a captured example |

## Keep out

| Not here | Lives in |
|---|---|
| Command-specific side effects or usage prose | `cli_commands` |
| A prose-only example with no verified output | nowhere — capture it or omit it |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Exit codes, stream ownership, format stability, captured examples | `cli_commands` | per-command usage and side effects are owned there, linked not restated |
