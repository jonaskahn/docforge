# `flashing-recovery`

**Reader question** — "How do I flash this device, and what do I do if it fails mid-way?"

| Mode | Depth | Shape |
|---|---|---|
| How-to | deep-dive | ordered-narrative |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Prerequisites and required hardware/connection state | L0 | a prerequisite discovered mid-procedure |
| 2 | One verified path: connect, flash, verify, with the exact success signal | L1 | "wait for it to finish" instead of a checkable outcome |
| 3 | The mid-flash recovery path, given the same rigor as the happy path | L2 | a recovery path reduced to an afterthought |
| 4 | An explicit warning immediately before any irreversible or hardware-risking step | L2 | a general safety note at the top instead of inline before the specific step |

## Keep out

| Not here | Lives in |
|---|---|
| An unverified destructive command | nowhere — never present one as safe |
| Artifact provenance and channel discipline | `distribution` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| The verified flash path, recovery path, confirmation checkpoints | `distribution` | artifact provenance and channel discipline are owned there |
