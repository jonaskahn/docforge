#!/usr/bin/env node
"use strict";
// Public CLI: prepare | import | status | validate --repo --json --input
// --evidence --analysis (delegated to the normalized Python structural reader).
/* See python/flow_preflight.py for the normalized ledger implementation. */
const { spawnSync } = require("child_process");
const path = require("path");

function main(argv = process.argv.slice(2)) {
  // Use the Python launcher rather than the implementation module so its
  // runtime package path is initialized exactly as it is for direct Python
  // callers.
  const script = path.join(__dirname, "..", "..", "cli", "python", "flow_preflight.py");
  const result = spawnSync("python3", [script, ...argv], { encoding: "utf8" });
  if (result.error) {
    process.stderr.write(`error: could not run Python flow preflight: ${result.error.message}\n`);
    return 1;
  }
  if (result.stdout) process.stdout.write(result.stdout);
  if (result.stderr) process.stderr.write(result.stderr);
  return Number.isInteger(result.status) ? result.status : 1;
}

module.exports = { main };
if (require.main === module) process.exitCode = main();
