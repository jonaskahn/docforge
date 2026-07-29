#!/usr/bin/env node
"use strict";
/** Check Docforge 2.0 section provenance using only JSON and Node built-ins. */

const crypto = require("crypto");
const fs = require("fs");
const path = require("path");
const WRITTEN = new Set(["generated", "needs_review", "complete"]);
const BLOB = /^[0-9a-f]{40}$/;

function fail(message, code = 2) {
  process.stderr.write(`error: ${message}\n`);
  return code;
}
function loadManifest(target) {
  if (!fs.existsSync(target) || !fs.statSync(target).isFile()) throw new Error(`manifest not found: ${target}`);
  const manifest = JSON.parse(fs.readFileSync(target, "utf8"));
  if (manifest.version !== "3.0") throw new Error(`manifest must use version 3.0: ${target}; manifest v2 is unsupported in Docforge 2.0`);
  return manifest;
}
function parseFrontmatter(target) {
  if (!fs.existsSync(target) || !fs.statSync(target).isFile() || path.extname(target).toLowerCase() !== ".md") return { state: "missing", provenance: null };
  const text = fs.readFileSync(target, "utf8");
  if (!text.startsWith("---\n")) return { state: "missing", provenance: null };
  const end = text.indexOf("\n---\n", 4);
  if (end < 0) return { state: "missing", provenance: null };
  try {
    const data = JSON.parse(text.slice(4, end));
    const provenance = data && data.docforge_provenance;
    if (!provenance || typeof provenance !== "object" || Array.isArray(provenance)) return { state: "missing", provenance: null };
    if (!("schema" in provenance)) return { state: "legacy", provenance };
    return { state: "ok", provenance };
  } catch {
    return { state: "unparseable", provenance: null };
  }
}
function gitBlob(target) {
  if (!fs.existsSync(target) || !fs.statSync(target).isFile()) return null;
  const content = fs.readFileSync(target);
  const header = Buffer.from(`blob ${content.length}\0`, "ascii");
  return crypto.createHash("sha1").update(header).update(content).digest("hex");
}
function syncProvenance(manifest, repo) {
  let updated = 0;
  const results = [];
  const failed = new Set();
  for (const doc of manifest.documents) {
    if (doc.provenance_mode === "manifest") continue;
    const parsed = parseFrontmatter(path.join(repo, ...doc.path.split("/")));
    if (parsed.state !== "ok") {
      failed.add(doc.path);
      if (parsed.state === "unparseable") results.push({ doc: doc.path, status: "UNPARSEABLE", detail: "invalid frontmatter JSON" });
      else results.push({ doc: doc.path, status: "UNTRACKED", detail: parsed.state === "legacy" ? "legacy provenance" : "missing provenance" });
      continue;
    }
    doc.provenance = parsed.provenance;
    updated++;
  }
  return { updated, results, failed };
}
function check(manifest, repo, sectionFilter, skipped = new Set()) {
  const results = [];
  let clean = true;
  for (const doc of manifest.documents) {
    if (!WRITTEN.has(doc.status)) continue;
    if (skipped.has(doc.path)) {
      clean = false;
      continue;
    }
    const provenance = doc.provenance;
    if (!provenance || typeof provenance !== "object" || Array.isArray(provenance) || !Object.keys(provenance).length) {
      results.push({ doc: doc.path, status: "UNTRACKED", detail: "missing provenance" });
      clean = false;
      continue;
    }
    if (!("schema" in provenance)) {
      results.push({ doc: doc.path, status: "UNTRACKED", detail: "legacy provenance" });
      clean = false;
      continue;
    }
    const sections = provenance.sections || [];
    const matching = sections.filter((section) => sectionFilter === undefined || section.id === sectionFilter);
    if (!sections.length) {
      results.push({ doc: doc.path, status: "UNTRACKED", detail: "missing provenance" });
      clean = false;
      continue;
    }
    if (sectionFilter !== undefined && !matching.length) continue;
    const stale = [];
    for (const section of matching) {
      for (const source of section.sources || []) {
        const sourcePath = source.path || "";
        if (typeof source.git_blob !== "string" || !BLOB.test(source.git_blob)) {
          stale.push({ doc: doc.path, status: "PARTIAL", section: section.id, file_status: "NO_BLOB", file: sourcePath });
          continue;
        }
        const current = gitBlob(path.join(repo, ...sourcePath.split("/")));
        if (current === null) {
          stale.push({ doc: doc.path, status: "PARTIAL", section: section.id, file_status: "MISSING", file: sourcePath });
        } else if (current !== source.git_blob) {
          stale.push({ doc: doc.path, status: "PARTIAL", section: section.id, file_status: "STALE", file: sourcePath });
        }
      }
    }
    if (stale.length) {
      results.push(...stale);
      clean = false;
    } else {
      results.push({ doc: doc.path, status: "FRESH" });
    }
  }
  return { results, clean };
}
function parseArgs(argv) {
  const result = {};
  const allowed = new Set(["manifest", "section", "json", "sync-provenance"]);
  for (let i = 0; i < argv.length; i++) {
    const token = argv[i];
    if (token === "-h" || token === "--help") return { help: true };
    if (!token.startsWith("--")) throw new Error(`unexpected argument: ${token}`);
    const raw = token.slice(2);
    if (!allowed.has(raw)) throw new Error(`unknown option: ${token}`);
    const key = raw.replace(/-/g, "_");
    if (raw === "json" || raw === "sync-provenance") result[key] = true;
    else {
      if (i + 1 >= argv.length || argv[i + 1].startsWith("--")) throw new Error(`option requires a value: ${token}`);
      result[key] = argv[++i];
    }
  }
  return result;
}
function usage() {
  console.log("usage: check_staleness.js --manifest <path> [--section <id>] [--json] [--sync-provenance]");
}
function main() {
  try {
    const args = parseArgs(process.argv.slice(2));
    if (args.help) { usage(); return 0; }
    if (!args.manifest) throw new Error("--manifest is required");
    const manifest = loadManifest(args.manifest);
    const repo = path.resolve((manifest.project && manifest.project.root) || path.resolve(path.dirname(args.manifest), ".."));
    let synchronized;
    let syncResults = [];
    let syncFailed = new Set();
    if (args.sync_provenance) {
      const sync = syncProvenance(manifest, repo);
      synchronized = sync.updated;
      syncResults = sync.results;
      syncFailed = sync.failed;
      fs.writeFileSync(args.manifest, JSON.stringify(manifest, null, 2) + "\n");
    }
    const outcome = check(manifest, repo, args.section, syncFailed);
    if (syncResults.length) {
      outcome.results.unshift(...syncResults);
      outcome.clean = false;
    }
    if (args.json) {
      const payload = synchronized === undefined ? outcome.results : { synchronized, results: outcome.results };
      console.log(JSON.stringify(payload, null, 2));
    } else {
      if (synchronized !== undefined) console.log(`Synchronized provenance for ${synchronized} documents.`);
      if (!outcome.results.length) console.log("no documents matched.");
      for (const result of outcome.results) {
        if (result.status === "FRESH") console.log(`FRESH      ${result.doc}`);
        else if (result.status === "UNTRACKED") console.log(`UNTRACKED  ${result.doc}  (${result.detail})`);
        else if (result.status === "UNPARSEABLE") console.log(`UNPARSEABLE  ${result.doc}  (${result.detail})`);
        else console.log(`PARTIAL    ${result.doc}  section=${result.section}  ${result.file_status}: ${result.file}`);
      }
    }
    return outcome.clean ? 0 : 1;
  } catch (error) {
    usage();
    return fail(error.message);
  }
}
process.exit(main());
