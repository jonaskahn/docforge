#!/usr/bin/env node
"use strict";
/** Launcher: delegates to runtime/graph/graph_source_codegraph.js. */

module.exports = require("../runtime/graph/graph_source_codegraph.js");

if (require.main === module) {
  process.exitCode = module.exports.main();
}
