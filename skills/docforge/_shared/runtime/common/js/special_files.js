#!/usr/bin/env node
"use strict";
/* Shared special markdown document definitions for Docforge. Not a public CLI. */

const SPECIAL_DOC_OUTPUTS = new Set(["AGENTS.md", "CLAUDE.md", "CLAUDE.local.md"]);
const SPECIAL_DOC_SOURCES = new Set(["agents-kernel.md", "claude-md.md", "claude-local-md.md"]);

module.exports = {
  SPECIAL_DOC_OUTPUTS,
  SPECIAL_DOC_SOURCES,
};
