#!/usr/bin/env node
"use strict";
/** Launcher: delegates to runtime/dashboard/dashboard.js. */

module.exports = require("../../dashboard/dashboard.js");

if (require.main === module) {
  module.exports.main().then((code) => process.exit(code));
}
