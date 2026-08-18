#!/usr/bin/env node
"use strict";
/** Launcher: delegates to runtime/documents/harvest_candidates.js. */

module.exports = require("../../documents/js/harvest_candidates.js");

if (require.main === module) {
  process.exitCode = module.exports.main();
}
