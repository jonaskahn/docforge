#!/usr/bin/env node
"use strict";
/** Launcher: delegates to runtime/graph/graph_source_gitnexus.js. */

module.exports = require("../runtime/graph/graph_source_gitnexus.js");

if (require.main === module) {
  process.exitCode = module.exports.main();
}
