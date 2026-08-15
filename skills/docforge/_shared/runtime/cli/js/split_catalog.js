#!/usr/bin/env node
"use strict";
/** Launcher: delegates to runtime/migrations/split_catalog.js. */

module.exports = require("../../migrations/js/split_catalog.js");

if (require.main === module) {
  process.exitCode = module.exports.main(process.argv);
}
