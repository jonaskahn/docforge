#!/usr/bin/env node
"use strict";
/** Launcher: delegates to runtime/flows/js/flow_analysis.js. */

module.exports = require("../../flows/js/flow_analysis.js");

if (require.main === module) {
  process.exitCode = module.exports.main(process.argv.slice(2));
}
