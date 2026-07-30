#!/usr/bin/env node
"use strict";
/** Launcher: delegates to runtime/common/_util.js. */

module.exports = require("../../common/_util.js");

if (require.main === module) {
  process.stderr.write("error: _util.js is a shared module, not a CLI\n");
  process.exit(2);
}
