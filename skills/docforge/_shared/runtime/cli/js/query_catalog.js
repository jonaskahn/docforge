#!/usr/bin/env node
"use strict";
/** Launcher: delegates to runtime/catalog/query_catalog.js. */

module.exports = require("../../catalog/js/query_catalog.js");

if (require.main === module) {
  process.exitCode = module.exports.main();
}
