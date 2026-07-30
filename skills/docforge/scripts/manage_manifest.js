#!/usr/bin/env node
"use strict";
/** Launcher: delegates to runtime/manifest/manage_manifest.js. */

module.exports = require("../runtime/manifest/manage_manifest.js");

if (require.main === module) {
  process.exitCode = module.exports.main();
}
