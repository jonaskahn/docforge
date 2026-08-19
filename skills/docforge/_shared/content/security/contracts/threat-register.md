# `threat-register`

**Reader question** — "For this specific interaction, what's the threat, how bad is it, and is it controlled?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | coverage-matrix |

Full coverage means one row per STRIDE category for every named DFD interaction the threat model scopes — generated only after a recorded high-criticality trigger and security-reviewer audience selection.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | One row per STRIDE category × named DFD interaction: stable ID, origin/destination, action plus protocol | the table | a row not traceable to a named DFD interaction |
| 2 | One declared score rubric applied throughout, or `unscored` where evidence cannot support a score | the table | mixed score systems in the same register |
| 3 | Disposition, control, and an owner named only when evidence establishes one | the table | a guessed owner |
| 4 | Residual uncertainty and evidence per row | the table | a duplicate narrative threat analysis instead of a scored row |

## Keep out

| Not here | Lives in |
|---|---|
| Credentials or exploit instructions | nowhere — not safe to publish |
| A guessed owner | nowhere — leave unowned rather than guess |
| The bounded DFD and narrative | `threat_model` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Scored threats, controls, owners | `threat_model` | the bounded DFD and narrative this register scores are owned there |
