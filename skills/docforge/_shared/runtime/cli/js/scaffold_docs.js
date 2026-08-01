#!/usr/bin/env node
"use strict";
/** Launcher: delegates to runtime/documents/scaffold_docs.js. */

module.exports = require("../../documents/js/scaffold_docs.js");

if (require.main === module) {
  process.exitCode = module.exports.main();
}
