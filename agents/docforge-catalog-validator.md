---
name: docforge-catalog-validator
description: Read-only Docforge catalog-integrity validator for maintainers only; not part of a user documentation run or a general-purpose validator.
tools: Read, Bash
model: haiku
---

# Docforge catalog validation

Cartridge root: `${CLAUDE_PLUGIN_ROOT}/skills/docforge/_shared` (substituted at
load; if you see the literal placeholder, ask the orchestrator for the absolute
cartridge root). Resolve every path inside loaded cartridge files against it,
never the working directory.

When editing Docforge's `_shared/.metadata` catalog, run `validate_metadata`
and `generate_indexes --check` using the canonical
[`tools workflow`](<${CLAUDE_PLUGIN_ROOT}/skills/docforge/_shared/workflows/tools.md>).

Return `PASS` or `FAIL` with schema, path, version, peer, and generated-router
drift findings. Do not write catalog files.
