# `command-reference`

**Reader question** — "What does this command do, what flags does it take, and can I copy-paste an example?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | entry-catalog |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Subcommands grouped under their parent | L1 | subcommands flattened alphabetically |
| 2 | Every short flag paired with its long-named equivalent, documented together | L2 | `-v` and `--verbose` listed as separate entries |
| 3 | One runnable, copy-pasteable example per command, needing no edits after paste | L2 | a plausible invocation presented as runnable but never tested |
| 4 | Side effects stated plainly as part of the command's own entry | L2 | a side effect buried in prose elsewhere |

## Keep out

| Not here | Lives in |
|---|---|
| An implementation call graph | nowhere — a reader needs the interface, not the internals |
| A call graph or internal function name | nowhere |
| Machine-output stream/exit-code semantics | `cli_output` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Flags, subcommands, runnable examples, side effects | `cli_output` | machine-output semantics — exit codes, streams, format stability — are owned there |
