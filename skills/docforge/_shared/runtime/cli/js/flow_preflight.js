#!/usr/bin/env node
"use strict";
// Public CLI: prepare | import | status | validate --repo --json --input
// --evidence --analysis. The implementation owns parsing; these tokens keep
// the generated-command contract discoverable beside the launcher.
/**
 * Node launcher for the surface-aware preflight ledger.
 *
 * The ledger format is deliberately byte-normalized by the Python structural
 * reader today: it is the runtime that can open CodeGraph's SQLite index on
 * all supported Node versions.  Keeping this launcher thin makes `node` and
 * `python` emit the exact same normalized evidence while the public command
 * remains paired.  The rest of the flow pipeline remains native in both
 * runtimes.
 */
module.exports = require("../../flows/js/flow_preflight.js");
if (require.main === module) process.exitCode = module.exports.main();
