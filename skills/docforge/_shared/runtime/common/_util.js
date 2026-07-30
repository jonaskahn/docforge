#!/usr/bin/env node
"use strict";
/** Shared Node built-in helpers for Docforge scripts. Not a public CLI. */

const fs = require("fs");

function fail(message, code = 1) {
  process.stderr.write(`error: ${message}\n`);
  return code;
}

function readJson(target) {
  if (!fs.existsSync(target)) throw new Error(`file not found: ${target}`);
  let value;
  try {
    value = JSON.parse(fs.readFileSync(target, "utf8"));
  } catch (error) {
    throw new Error(`invalid JSON in ${target}: ${error.message}`);
  }
  if (!value || Array.isArray(value) || typeof value !== "object") {
    throw new Error(`expected a JSON object: ${target}`);
  }
  return value;
}

function dumpJson(value) {
  return JSON.stringify(value, null, 2) + "\n";
}

function loadManifest(target, options = {}) {
  const allowedVersions = options.allowedVersions || ["3.1"];
  const requireDocuments = Boolean(options.requireDocuments);
  const unsupportedHint =
    options.unsupportedHint || "run migrate_metadata.js for 3.0 manifests";
  if (!fs.existsSync(target) || !fs.statSync(target).isFile()) {
    throw new Error(`manifest not found: ${target}`);
  }
  const data = JSON.parse(fs.readFileSync(target, "utf8"));
  const versionsText = allowedVersions.join(" or ");
  if (
    !allowedVersions.includes(data.version) ||
    (requireDocuments && !Array.isArray(data.documents))
  ) {
    throw new Error(
      `manifest must use version ${versionsText}: ${target}; ${unsupportedHint}`,
    );
  }
  return data;
}

module.exports = {
  fail,
  readJson,
  dumpJson,
  loadManifest,
};

if (require.main === module) {
  process.stderr.write("error: _util.js is a shared module, not a CLI\n");
  process.exit(2);
}
