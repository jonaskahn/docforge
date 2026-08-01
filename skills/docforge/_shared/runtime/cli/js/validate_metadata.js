#!/usr/bin/env node
"use strict";
/** Launcher: delegates to runtime/validation/validate_metadata.js. */

module.exports = require("../../validation/js/validate_metadata.js");

if (require.main === module) {
  process.exitCode = module.exports.main();
}
