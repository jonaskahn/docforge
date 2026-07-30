#!/usr/bin/env node
"use strict";
/** Launcher: delegates to runtime/validation/generate_indexes.js. */

module.exports = require("../../validation/generate_indexes.js");

if (require.main === module) {
  process.exitCode = module.exports.main();
}
