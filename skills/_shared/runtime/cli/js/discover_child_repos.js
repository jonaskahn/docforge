#!/usr/bin/env node
"use strict";
/** Launcher: delegates to runtime/portfolio/discover_child_repos.js. */

module.exports = require("../../portfolio/discover_child_repos.js");

if (require.main === module) {
  process.exitCode = module.exports.main();
}
