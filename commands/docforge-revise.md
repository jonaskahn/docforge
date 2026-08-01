---
name: docforge-revise
description: Structural refresh of Docforge documentation — revise all, a docs area, or flows. Accepts --plan-only and --auto-accept. Shares the Docforge cartridge.
---

If the invocation arguments contain `--help` (or the user asks what this
command does), print the `/docforge-revise` section of
`${CLAUDE_PLUGIN_ROOT}/skills/docforge/_shared/help.md` — purpose and every
parameter with its meaning — and stop; do not load the skill or run a
workflow. Otherwise:

Load and follow the Docforge revise skill at
`${CLAUDE_PLUGIN_ROOT}/skills/docforge-revise/SKILL.md` (including its load
order into `${CLAUDE_PLUGIN_ROOT}/skills/docforge/_shared/`). Treat this slash command as
`/docforge-revise`.
