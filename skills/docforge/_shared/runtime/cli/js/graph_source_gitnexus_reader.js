#!/usr/bin/env node
"use strict";
/** Launcher: delegates to runtime/graph/graph_source_gitnexus_reader.js. */

module.exports = require("../../graph/graph_source_gitnexus_reader.js");

if (require.main === module) {
  process.exitCode = module.exports.main();
}
