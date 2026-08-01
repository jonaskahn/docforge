#!/usr/bin/env node
"use strict";
/** Launcher: delegates to runtime/documents/lint_agents_kernel.js. */

module.exports = require("../../documents/js/lint_agents_kernel.js");

if (require.main === module) {
  process.exitCode = module.exports.main();
}
