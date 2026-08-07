#!/usr/bin/env node
"use strict";
/** Check Docforge section provenance using only JSON and Node built-ins. */

const fs = require("fs");
const path = require("path");
const { fail, loadManifest } = require("../../common/js/_util.js");
const { ensureMigrated } = require("./migrate_metadata.js");
const pf = require("../../common/js/provenance_frontmatter.js");
const { classifySource, gitBlobForPath } = require("../../common/js/evidence_hash.js");

const WRITTEN = new Set(["generated", "needs_review", "complete"]);

function gitBlob(target) {
  return gitBlobForPath(fs, target);
}

function matchesDocument(doc, documentFilter) {
  if (documentFilter === undefined || documentFilter === null) return true;
  return doc.id === documentFilter || doc.path === documentFilter;
}

function syncProvenance(manifest, repo, documentFilter) {
  let updated = 0;
  const results = [];
  const failed = new Set();
  for (const doc of manifest.documents) {
    if (!matchesDocument(doc, documentFilter)) continue;
    if (doc.provenance_mode === "manifest") continue;
    const filePath = path.join(repo, ...doc.path.split("/"));
    let parsed;
    if (!fs.existsSync(filePath) || !fs.statSync(filePath).isFile() || path.extname(filePath).toLowerCase() !== ".md") {
      parsed = { state: "missing", provenance: null };
    } else {
      const codec = pf.parseFrontmatter(fs.readFileSync(filePath, "utf8"));
      parsed = { state: codec.state, provenance: codec.provenance };
    }
    if (parsed.state === "obsolete" && parsed.provenance) {
      const text = fs.readFileSync(filePath, "utf8");
      const { body } = pf.splitFrontmatter(text);
      const migrated = pf.migrateV1ToV2(parsed.provenance, body);
      fs.writeFileSync(filePath, pf.rewriteFrontmatter(text, migrated), "utf8");
      doc.provenance = migrated;
      updated += 1;
      continue;
    }
    if (parsed.state !== "ok") {
      failed.add(doc.path);
      if (parsed.state === "unparseable") {
        results.push({ doc: doc.path, status: "UNPARSEABLE", detail: "invalid frontmatter" });
      } else if (parsed.state === "obsolete") {
        results.push({ doc: doc.path, status: "UNTRACKED", detail: "obsolete schema" });
      } else {
        results.push({
          doc: doc.path,
          status: "UNTRACKED",
          detail: parsed.state === "legacy" ? "legacy provenance" : "missing provenance",
        });
      }
      continue;
    }
    doc.provenance = parsed.provenance;
    updated += 1;
  }
  return { updated, results, failed };
}

function check(manifest, repo, sectionFilter, skipped = new Set(), documentFilter) {
  const results = [];
  let clean = true;
  for (const doc of manifest.documents) {
    if (!matchesDocument(doc, documentFilter)) continue;
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
    if (!pf.SUPPORTED_SCHEMA_VERSIONS.has(provenance.schema) || "tool_version" in provenance) {
      results.push({ doc: doc.path, status: "UNTRACKED", detail: "obsolete schema" });
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
    const findings = [];
    let hasBlocking = false;
    const statusMap = { missing: "MISSING", cosmetic: "COSMETIC", stale: "STALE" };
    for (const section of matching) {
      for (const source of section.sources || []) {
        const sourcePath = source.path || "";
        if (typeof source.git_blob !== "string" || !pf.BLOB.test(source.git_blob)) {
          findings.push({ doc: doc.path, status: "PARTIAL", section: section.id, file_status: "NO_BLOB", file: sourcePath });
          hasBlocking = true;
          continue;
        }
        const target = path.join(repo, ...sourcePath.split("/"));
        const currentBytes = (fs.existsSync(target) && fs.statSync(target).isFile()) ? fs.readFileSync(target) : null;
        const outcome = classifySource(source, currentBytes);
        if (outcome === "fresh") continue;
        findings.push({ doc: doc.path, status: "PARTIAL", section: section.id, file_status: statusMap[outcome], file: sourcePath });
        if (outcome !== "cosmetic") hasBlocking = true;
      }
    }
    if (findings.length) {
      results.push(...findings);
      if (hasBlocking) clean = false;
    } else {
      results.push({ doc: doc.path, status: "FRESH" });
    }
  }
  return { results, clean };
}

function parseArgs(argv) {
  const result = {};
  const allowed = new Set(["manifest", "document", "section", "json", "sync-provenance"]);
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
  console.log("usage: check_staleness.js --manifest <path> [--document <id|path>] [--section <id>] [--json] [--sync-provenance]");
}

function main() {
  try {
    const args = parseArgs(process.argv.slice(2));
    if (args.help) { usage(); return 0; }
    if (!args.manifest) throw new Error("--manifest is required");
    const manifestPath = path.resolve(args.manifest);
    const raw = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
    const repo = path.resolve((raw.project && raw.project.root) || path.resolve(path.dirname(manifestPath), ".."));
    let manifest;
    if (args.sync_provenance) {
      manifest = ensureMigrated(repo, manifestPath);
    } else {
      manifest = loadManifest(manifestPath);
    }
    let synchronized;
    let syncResults = [];
    let syncFailed = new Set();
    if (args.sync_provenance) {
      const sync = syncProvenance(manifest, repo, args.document);
      synchronized = sync.updated;
      syncResults = sync.results;
      syncFailed = sync.failed;
      fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + "\n");
    }
    const outcome = check(manifest, repo, args.section, syncFailed, args.document);
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
    return fail(error.message, 2);
  }
}
process.exit(main());
