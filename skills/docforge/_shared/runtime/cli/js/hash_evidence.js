#!/usr/bin/env node
"use strict";
/** Launcher: delegates to runtime/manifest/hash_evidence.js. */

module.exports = require("../../manifest/js/hash_evidence.js");

if (require.main === module) {
  process.exitCode = module.exports.main();
}
