#!/usr/bin/env node
"use strict";
/** Launcher: delegates to runtime/architecture/plan.js. */

module.exports = require("../../architecture/js/architecture_plan.js");

if (require.main === module) {
  process.exitCode = module.exports.main(process.argv.slice(2));
}
