---
name: docforge-dashboard
description: Previews the written docs as a local, browsable site — rebuilds only what changed, never touches the repo's package files.
---

If the invocation arguments contain `--help` (or the user asks what this
command does), print the `/docforge-dashboard` section of
`${CLAUDE_PLUGIN_ROOT}/skills/docforge/_shared/help.md` — purpose and every
parameter with its meaning — and stop; do not load the skill or run a
workflow. Otherwise:

Load and follow the Docforge dashboard skill at
`${CLAUDE_PLUGIN_ROOT}/skills/docforge-dashboard/SKILL.md` (including its load
order into `${CLAUDE_PLUGIN_ROOT}/skills/docforge/_shared/`). Treat this slash
command as `/docforge-dashboard`.
