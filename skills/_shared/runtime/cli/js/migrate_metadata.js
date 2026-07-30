#!/usr/bin/env node
"use strict";
/** Launcher: delegates to runtime/manifest/migrate_metadata.js. */

module.exports = require("../../manifest/migrate_metadata.js");

if (require.main === module) {
  process.exitCode = module.exports.main(process.argv);
}
