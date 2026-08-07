#!/usr/bin/env node
"use strict";
/** Stamp git_blob / git_blob_normalized / range_blob for one provenance source.
 *
 * The writing agent uses this to hash a cited file (and optionally a specific
 * line range) exactly the way `check_staleness.js` will later recompute it --
 * `git_blob` matches `git hash-object`; `git_blob_normalized` and `range_blob`
 * have no standard-tool equivalent, so both sides must share one implementation.
 */

const fs = require("fs");
const path = require("path");
const { fail } = require("../../common/js/_util.js");
const { normalizedBlobHash, rangeBlobHash, rawBlobHash } = require("../../common/js/evidence_hash.js");

function parseRange(value) {
  const match = /^([0-9]+)-([0-9]+)$/.exec(value);
  if (!match) throw new Error(`invalid --range: ${value} (expected <start>-<end>)`);
  const start = Number(match[1]);
  const end = Number(match[2]);
  if (start < 1 || end < start) throw new Error(`invalid --range: ${value} (expected 1 <= start <= end)`);
  return [start, end];
}

function hashEvidence(repo, relPath, span) {
  if (path.isAbsolute(relPath) || relPath.split(/[\\/]/).includes("..")) {
    throw new Error(`path escapes repo: ${relPath}`);
  }
  const target = path.resolve(repo, relPath);
  if (target !== repo && !target.startsWith(`${repo}${path.sep}`)) {
    throw new Error(`path escapes repo: ${relPath}`);
  }
  if (!fs.existsSync(target) || !fs.statSync(target).isFile()) {
    throw new Error(`file not found: ${relPath}`);
  }
  const content = fs.readFileSync(target);
  const result = { git_blob: rawBlobHash(content) };
  const normalized = normalizedBlobHash(content);
  if (normalized !== null) result.git_blob_normalized = normalized;
  if (span) {
    const [start, end] = span;
    const scoped = rangeBlobHash(content, start, end);
    if (scoped === null) {
      throw new Error(`cannot hash range ${start}-${end} of ${relPath} (out of bounds or not valid UTF-8 text)`);
    }
    result.evidence_range = { start: String(start), end: String(end) };
    result.range_blob = scoped;
  }
  return result;
}

function parseArgs(argv) {
  const result = {};
  const allowed = new Set(["repo", "path", "range", "json"]);
  for (let i = 0; i < argv.length; i++) {
    const token = argv[i];
    if (token === "-h" || token === "--help") return { help: true };
    if (!token.startsWith("--")) throw new Error(`unexpected argument: ${token}`);
    const raw = token.slice(2);
    if (!allowed.has(raw)) throw new Error(`unknown option: ${token}`);
    if (raw === "json") result[raw] = true;
    else {
      if (i + 1 >= argv.length || argv[i + 1].startsWith("--")) throw new Error(`option requires a value: ${token}`);
      result[raw] = argv[++i];
    }
  }
  return result;
}

function usage() {
  console.log("usage: hash_evidence.js --repo <repo> --path <repo-relative-path> [--range <start>-<end>] [--json]");
}

function main() {
  try {
    const args = parseArgs(process.argv.slice(2));
    if (args.help) { usage(); return 0; }
    if (!args.repo) throw new Error("--repo is required");
    if (!args.path) throw new Error("--path is required");
    const repo = path.resolve(args.repo);
    if (!fs.existsSync(repo) || !fs.statSync(repo).isDirectory()) {
      return fail(`not a directory: ${args.repo}`, 2);
    }
    let span = null;
    let result;
    try {
      span = args.range ? parseRange(args.range) : null;
      result = hashEvidence(repo, args.path, span);
    } catch (error) {
      return fail(error.message, 2);
    }
    if (args.json) {
      console.log(JSON.stringify(result, null, 2));
    } else {
      console.log(`git_blob: ${result.git_blob}`);
      if ("git_blob_normalized" in result) console.log(`git_blob_normalized: ${result.git_blob_normalized}`);
      if ("evidence_range" in result) {
        console.log(`evidence_range: ${result.evidence_range.start}-${result.evidence_range.end}`);
        console.log(`range_blob: ${result.range_blob}`);
      }
    }
    return 0;
  } catch (error) {
    usage();
    return fail(error.message, 2);
  }
}
process.exit(main());
