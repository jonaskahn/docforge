#!/usr/bin/env node
"use strict";
/* check_provenance.js — compare recorded git blob hashes against current
 * working-tree content to decide whether a docforge document (or one of its
 * sections) needs to be rewritten.
 *
 * Usage:
 *   node check_provenance.js --manifest .docforge/manifest.json
 *   node check_provenance.js --manifest .docforge/manifest.json --flow order-approval-threshold
 *   node check_provenance.js --manifest .docforge/manifest.json --json
 *   node check_provenance.js --rebuild-manifest --docs-dir docs --manifest .docforge/manifest.json
 *
 * Exit code is 0 if everything is FRESH, 1 if anything is PARTIAL/STALE/MISSING,
 * 2 on a usage or IO error — so this can gate a CI job.
 *
 * Node.js built-ins only.
 */

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const FRONTMATTER_RE = /^---\n([\s\S]*?)\n---\n/;

function gitHashObject(relPath, repoRoot) {
  const full = path.join(repoRoot, relPath);
  if (!fs.existsSync(full)) return null;
  const res = spawnSync("git", ["hash-object", full], { cwd: repoRoot, encoding: "utf8" });
  if (res.status !== 0 || res.error) return null;
  return res.stdout.trim();
}

function loadManifest(manifestPath) {
  if (!fs.existsSync(manifestPath)) {
    console.error(`error: manifest not found at ${manifestPath}`);
    process.exit(2);
  }
  return JSON.parse(fs.readFileSync(manifestPath, "utf8"));
}

// Minimal parser for the fixed docforge_provenance frontmatter shape (see
// references/provenance-tracking.md). Avoids a hard dependency on a YAML
// library — this skill's frontmatter is machine-written in one exact shape,
// so a general YAML parser is unneeded. Falls back to null ("no frontmatter
// recorded") on anything that doesn't match.
function extractFrontmatterProvenance(text) {
  const m = FRONTMATTER_RE.exec(text);
  if (!m) return null;
  const block = m[1];
  if (!block.includes("docforge_provenance")) return null;

  const lines = block.split("\n");
  let i = lines.findIndex((l) => l.trim() === "docforge_provenance:");
  if (i === -1) return null;
  i++;

  const prov = { sections: [] };
  let currentSection = null;
  let currentSource = null;

  for (; i < lines.length; i++) {
    const line = lines[i];
    if (line.length && !/^\s/.test(line)) break; // dedented past the block

    const sectionsMatch = line.match(/^\s{2}sections:\s*$/);
    if (sectionsMatch) continue;

    const idMatch = line.match(/^\s{4}-\s*id:\s*(.+?)\s*$/);
    if (idMatch) {
      currentSection = { id: idMatch[1], sources: [] };
      prov.sections.push(currentSection);
      currentSource = null;
      continue;
    }

    const sourcesMatch = line.match(/^\s{6}sources:\s*$/);
    if (sourcesMatch) continue;

    const pathMatch = line.match(/^\s{8}-\s*path:\s*(.+?)\s*$/);
    if (pathMatch && currentSection) {
      currentSource = { path: pathMatch[1], git_blob: null };
      currentSection.sources.push(currentSource);
      continue;
    }

    const blobMatch = line.match(/^\s{10}git_blob:\s*(.+?)\s*$/);
    if (blobMatch && currentSource) {
      currentSource.git_blob = blobMatch[1];
      continue;
    }
    // top-level scalar fields (doc, generated_at, graph_snapshot) are ignored —
    // only sections/sources are consumed downstream.
  }

  return prov.sections.length ? prov : null;
}

function walkMdFiles(dir) {
  const out = [];
  function walk(cur) {
    let entries;
    try {
      entries = fs.readdirSync(cur, { withFileTypes: true });
    } catch {
      return;
    }
    for (const entry of entries) {
      const full = path.join(cur, entry.name);
      if (entry.isDirectory()) walk(full);
      else if (entry.isFile() && entry.name.endsWith(".md")) out.push(full);
    }
  }
  walk(dir);
  return out;
}

function rebuildManifest(docsDir, manifestPath) {
  const documents = {};
  for (const mdFile of walkMdFiles(docsDir)) {
    let text;
    try {
      text = fs.readFileSync(mdFile, "utf8");
    } catch {
      continue;
    }
    const prov = extractFrontmatterProvenance(text);
    if (!prov) continue;
    const rel = path.relative(path.dirname(docsDir), mdFile).split(path.sep).join("/");
    const sections = {};
    for (const section of prov.sections) {
      const sources = {};
      for (const s of section.sources) sources[s.path] = s.git_blob;
      sections[section.id] = { sources };
    }
    documents[rel] = { sections };
  }
  fs.mkdirSync(path.dirname(manifestPath), { recursive: true });
  fs.writeFileSync(manifestPath, JSON.stringify({ generated_at: null, documents }, null, 2) + "\n", "utf8");
  console.log(`rebuilt manifest: ${Object.keys(documents).length} documents -> ${manifestPath}`);
}

function check(manifest, repoRoot, flowFilter) {
  const results = [];
  let allFresh = true;
  for (const [docPath, docData] of Object.entries(manifest.documents || {})) {
    const sections = docData.sections || {};
    if (!Object.keys(sections).length) {
      results.push({ doc: docPath, status: "STALE", detail: "no section granularity recorded" });
      allFresh = false;
      continue;
    }

    const sectionStatuses = [];
    for (const [sectionId, sectionData] of Object.entries(sections)) {
      if (flowFilter && flowFilter !== sectionId) continue;
      const fileStatuses = [];
      for (const [srcPath, recordedHash] of Object.entries(sectionData.sources || {})) {
        const currentHash = gitHashObject(srcPath, repoRoot);
        if (currentHash === null) fileStatuses.push(["MISSING", srcPath]);
        else if (currentHash !== recordedHash) fileStatuses.push(["STALE", srcPath]);
        else fileStatuses.push(["FRESH", srcPath]);
      }
      const bad = fileStatuses.filter((f) => f[0] !== "FRESH");
      if (bad.length) sectionStatuses.push([sectionId, bad]);
    }

    if (!sectionStatuses.length) {
      if (!flowFilter) results.push({ doc: docPath, status: "FRESH" });
    } else {
      allFresh = false;
      for (const [sectionId, bad] of sectionStatuses) {
        for (const [status, filePath] of bad) {
          results.push({ doc: docPath, status: "PARTIAL", section: sectionId, file_status: status, file: filePath });
        }
      }
    }
  }
  return [results, allFresh];
}

function parseArgs(argv) {
  const args = { manifest: path.join(".docforge", "manifest.json"), repoRoot: ".", docsDir: "docs" };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--manifest") args.manifest = argv[++i];
    else if (a === "--repo-root") args.repoRoot = argv[++i];
    else if (a === "--flow") args.flow = argv[++i];
    else if (a === "--json") args.json = true;
    else if (a === "--rebuild-manifest") args.rebuildManifest = true;
    else if (a === "--docs-dir") args.docsDir = argv[++i];
  }
  return args;
}

function main() {
  const args = parseArgs(process.argv.slice(2));

  if (args.rebuildManifest) {
    rebuildManifest(args.docsDir, args.manifest);
    return 0;
  }

  const manifest = loadManifest(args.manifest);
  const [results, allFresh] = check(manifest, args.repoRoot, args.flow || null);

  if (args.json) {
    console.log(JSON.stringify(results, null, 2));
  } else {
    if (!results.length) console.log("no documents matched.");
    for (const r of results) {
      if (r.status === "FRESH") console.log(`FRESH    ${r.doc}`);
      else if (r.status === "PARTIAL") console.log(`PARTIAL  ${r.doc}  section=${r.section}  ${r.file_status}: ${r.file}`);
      else console.log(`STALE    ${r.doc}  (${r.detail || ""})`);
    }
  }

  return allFresh ? 0 : 1;
}

process.exit(main());
