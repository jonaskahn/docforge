#!/usr/bin/env node
"use strict";
/** Launcher: delegates to runtime/graph/read_graph.js. */

module.exports = require("../../graph/js/read_graph.js");

if (require.main === module) {
  process.exitCode = module.exports.main();
}
