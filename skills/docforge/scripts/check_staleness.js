#!/usr/bin/env node
"use strict";
/* check_staleness.js — compare recorded git blob hashes against current
 * working-tree content to decide whether a docforge document (or one of its
 * sections) needs to be rewritten.
 *
 * Usage:
 *   node check_staleness.js --manifest .docforge/manifest.json
 *   node check_staleness.js --manifest .docforge/manifest.json --flow order-approval-threshold
 *   node check_staleness.js --manifest .docforge/manifest.json --json
 *   node check_staleness.js --rebuild-manifest --docs-dir docs --manifest .docforge/manifest.json
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

// Same group vocabulary manage_manifest.js uses, in the same order.
const GROUPS = ["architecture", "flows", "product", "engineering", "operations",
  "reference", "security", "contributing", "records"];

// Only documents that have actually been written carry provenance; a document
// still "planned"/"in_progress"/"skipped" is not checked for staleness.
const WRITTEN_STATUSES = new Set(["generated", "needs_review", "complete"]);

function inferGroup(rel) {
  const parts = rel.split("/");
  if (parts[0] === "docs" && parts.length > 1) {
    return GROUPS.includes(parts[1]) ? parts[1] : "records";
  }
  if (rel.toUpperCase().startsWith("SECURITY")) return "security";
  return "records";
}

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

// Reconstruct the manifest from every document's frontmatter, in the same
// document_groups envelope manage_manifest.js writes — so check() reads one shape
// whether the manifest was built by the plan or rebuilt from disk. Group and id
// are inferred from the path; type is "adopted" since frontmatter doesn't record it.
function rebuildManifest(docsDir, manifestPath) {
  const groups = {};
  let count = 0;
  for (const mdFile of walkMdFiles(docsDir).sort()) {
    let text;
    try {
      text = fs.readFileSync(mdFile, "utf8");
    } catch {
      continue;
    }
    const prov = extractFrontmatterProvenance(text);
    if (!prov) continue;
    const rel = path.relative(path.dirname(docsDir), mdFile).split(path.sep).join("/");
    const sections = prov.sections.map((section) => ({
      id: section.id,
      sources: section.sources.map((s) => ({ path: s.path, git_blob: s.git_blob })),
    }));
    const doc = {
      id: rel.replace(/[/.]/g, "_"),
      type: "adopted",
      path: rel,
      status: "generated",
      sections,
    };
    const g = inferGroup(rel);
    (groups[g] = groups[g] || []).push(doc);
    count++;
  }
  const ordered = GROUPS.filter((g) => g in groups);
  const manifest = {
    version: "1.1",
    generated_at: null,
    project_context: { repo_name: null, repo_path: null, tier: null, overlays: [] },
    document_groups: ordered.map((g) => ({ group: g, documents: groups[g] })),
    metadata: {},
  };
  fs.mkdirSync(path.dirname(manifestPath), { recursive: true });
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + "\n", "utf8");
  console.log(`rebuilt manifest: ${count} documents -> ${manifestPath}`);
}

function* iterDocuments(manifest) {
  for (const group of manifest.document_groups || []) {
    for (const doc of group.documents || []) yield doc;
  }
}

function check(manifest, repoRoot, flowFilter) {
  const results = [];
  let allFresh = true;
  for (const doc of iterDocuments(manifest)) {
    const status = doc.status;
    // Skip documents not yet written — they carry no provenance by design.
    if (status !== undefined && status !== null && !WRITTEN_STATUSES.has(status)) continue;
    const docPath = doc.path;
    const sections = doc.sections || [];
    if (!sections.length) {
      results.push({ doc: docPath, status: "STALE", detail: "no section granularity recorded" });
      allFresh = false;
      continue;
    }

    const sectionStatuses = [];
    for (const section of sections) {
      const sectionId = section.id;
      if (flowFilter && flowFilter !== sectionId) continue;
      const fileStatuses = [];
      for (const src of section.sources || []) {
        const currentHash = gitHashObject(src.path, repoRoot);
        if (currentHash === null) fileStatuses.push(["MISSING", src.path]);
        else if (currentHash !== src.git_blob) fileStatuses.push(["STALE", src.path]);
        else fileStatuses.push(["FRESH", src.path]);
      }
      const bad = fileStatuses.filter((f) => f[0] !== "FRESH");
      if (bad.length) sectionStatuses.push([sectionId, bad]);
    }

    if (!sectionStatuses.length) {
      if (!flowFilter) results.push({ doc: docPath, status: "FRESH" });
    } else {
      allFresh = false;
      for (const [sectionId, bad] of sectionStatuses) {
        for (const [fileStatus, filePath] of bad) {
          results.push({ doc: docPath, status: "PARTIAL", section: sectionId, file_status: fileStatus, file: filePath });
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
