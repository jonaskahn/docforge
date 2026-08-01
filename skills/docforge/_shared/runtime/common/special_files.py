#!/usr/bin/env python3
"""Shared special markdown document definitions for Docforge. Not a public CLI."""

from __future__ import annotations

# Output materialized doc filenames that bypass standard linting/scaffolding constraints.
SPECIAL_DOC_OUTPUTS: set[str] = {"AGENTS.md", "CLAUDE.md", "CLAUDE.local.md"}

# Source template filenames in content/ corresponding to special markdown outputs.
SPECIAL_DOC_SOURCES: set[str] = {"agents-kernel.md", "claude-md.md", "claude-local-md.md"}

if __name__ == "__main__":
    raise SystemExit("error: special_files.py is a shared module, not a CLI")
