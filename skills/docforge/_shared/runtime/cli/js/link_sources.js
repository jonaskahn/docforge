#!/usr/bin/env node
"use strict";
/** Launcher: delegates to runtime/documents/link_sources.js. */

module.exports = require("../../documents/js/link_sources.js");

if (require.main === module) {
  process.exitCode = module.exports.main();
}
