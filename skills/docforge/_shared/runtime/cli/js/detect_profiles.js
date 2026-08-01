#!/usr/bin/env node
"use strict";
/** Launcher: delegates to runtime/catalog/detect_profiles.js. */

module.exports = require("../../catalog/js/detect_profiles.js");

if (require.main === module) {
  process.exitCode = module.exports.main();
}
