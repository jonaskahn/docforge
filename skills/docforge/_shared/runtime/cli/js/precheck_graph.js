#!/usr/bin/env node
"use strict";
/** Launcher: delegates to runtime/graph/precheck_graph.js. */

module.exports = require("../../graph/js/precheck_graph.js");

if (require.main === module) {
  process.exitCode = module.exports.main();
}
