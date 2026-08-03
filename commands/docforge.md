---
name: docforge
description: Writes new repository documentation from source-code evidence — catalog-driven, provenance-tracked, and independently audited.
---

If the invocation arguments contain `--help` (or the user asks what this
command does), print the `/docforge` section of
`${CLAUDE_PLUGIN_ROOT}/skills/docforge/_shared/help.md` — purpose and every
parameter with its meaning — and stop; do not load the skill or run a
workflow. Otherwise:

Load and follow the Docforge skill at
`${CLAUDE_PLUGIN_ROOT}/skills/docforge/SKILL.md` (including its load order into
`${CLAUDE_PLUGIN_ROOT}/skills/docforge/_shared/`). Treat this slash command as `/docforge`.
