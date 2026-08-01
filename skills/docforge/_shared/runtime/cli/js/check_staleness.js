#!/usr/bin/env node
"use strict";
/** Launcher: delegates to runtime/manifest/check_staleness.js. */

module.exports = require("../../manifest/js/check_staleness.js");

if (require.main === module) {
  process.exitCode = module.exports.main();
}
