#!/usr/bin/env node
"use strict";
/** Check Docforge 2.0 section provenance using only JSON and Node built-ins. */

const crypto = require("crypto");
const fs = require("fs");
const path = require("path");
const WRITTEN = new Set(["generated", "needs_review", "complete"]);

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
  if (!fs.existsSync(target) || !fs.statSync(target).isFile() || path.extname(target).toLowerCase() !== ".md") return null;
  const text = fs.readFileSync(target, "utf8");
  if (!text.startsWith("---\n")) return null;
  const end = text.indexOf("\n---\n", 4);
  if (end < 0) return null;
  try {
    const data = JSON.parse(text.slice(4, end));
    const sections = data && data.docforge_provenance && data.docforge_provenance.sections;
    return Array.isArray(sections) ? sections : null;
  } catch {
    return null;
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
  for (const doc of manifest.documents) {
    const sections = parseFrontmatter(path.join(repo, ...doc.path.split("/")));
    if (sections === null) continue;
    if (!doc.provenance) doc.provenance = {};
    doc.provenance.sections = sections;
    updated++;
  }
  return updated;
}
function check(manifest, repo, sectionFilter) {
  const results = [];
  let clean = true;
  for (const doc of manifest.documents) {
    if (!WRITTEN.has(doc.status)) continue;
    const sections = (doc.provenance && doc.provenance.sections) || [];
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
    if (args.sync_provenance) {
      synchronized = syncProvenance(manifest, repo);
      fs.writeFileSync(args.manifest, JSON.stringify(manifest, null, 2) + "\n");
    }
    const outcome = check(manifest, repo, args.section);
    if (args.json) {
      const payload = synchronized === undefined ? outcome.results : { synchronized, results: outcome.results };
      console.log(JSON.stringify(payload, null, 2));
    } else {
      if (synchronized !== undefined) console.log(`Synchronized provenance for ${synchronized} documents.`);
      if (!outcome.results.length) console.log("no documents matched.");
      for (const result of outcome.results) {
        if (result.status === "FRESH") console.log(`FRESH      ${result.doc}`);
        else if (result.status === "UNTRACKED") console.log(`UNTRACKED  ${result.doc}  (${result.detail})`);
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
