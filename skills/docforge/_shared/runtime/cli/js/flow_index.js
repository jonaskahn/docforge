#!/usr/bin/env node
"use strict";
/** Launcher: delegates to runtime/flows/flow_index.js. */

module.exports = require("../../flows/js/flow_index.js");

if (require.main === module) {
  process.exitCode = module.exports.main();
}
