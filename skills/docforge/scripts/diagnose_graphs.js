#!/usr/bin/env node
"use strict";
/** Launcher: delegates to runtime/graph/diagnose_graphs.js. */

module.exports = require("../runtime/graph/diagnose_graphs.js");

if (require.main === module) {
  process.exitCode = module.exports.main();
}
