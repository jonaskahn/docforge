#!/usr/bin/env node
"use strict";
/** Launcher: delegates to runtime/flows/derive_flow_graph.js. */

module.exports = require("../runtime/flows/derive_flow_graph.js");

if (require.main === module) {
  process.exitCode = module.exports.main();
}
