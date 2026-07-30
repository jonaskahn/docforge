#!/usr/bin/env node
"use strict";
/** Launcher: delegates to runtime/documents/lint_document.js. */

module.exports = require("../runtime/documents/lint_document.js");

if (require.main === module) {
  process.exitCode = module.exports.main();
}
