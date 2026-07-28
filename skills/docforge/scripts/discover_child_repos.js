#!/usr/bin/env node
"use strict";
/* discover_repos.js — assemble the full repo collection for a docforge
 * diligence job: the parent, every declared git submodule, and every nested
 * repo detected on disk that ISN'T declared in .gitmodules (vendored copies,
 * git-subtree merges, manually cloned submodules).
 *
 * For each repo found, reports whether it already has a docforge baseline
 * (docs/architecture/high-level.md) and/or a docforge provenance manifest
 * (.docforge/manifest.json), so the caller knows which repos need
 * generation before a diligence portfolio layer is built on top of them.
 *
 * Usage:
 *   node discover_repos.js --root <parent-repo-path>
 *   node discover_repos.js --root <parent-repo-path> --json
 *   node discover_repos.js --root <parent-repo-path> --exclude node_modules --exclude vendor/cache
 *
 * Node.js built-ins only.
 */

const fs = require("fs");
const path = require("path");

const DEFAULT_EXCLUDES = new Set([".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"]);

function isDir(p) {
  try {
    return fs.statSync(p).isDirectory();
  } catch {
    return false;
  }
}

function exists(p) {
  return fs.existsSync(p);
}

// Minimal INI parser for .gitmodules — enough for [submodule "name"] sections
// with path/url keys, the only shape git itself writes.
function parseGitmodules(root) {
  const gmPath = path.join(root, ".gitmodules");
  if (!exists(gmPath)) return {};
  const text = fs.readFileSync(gmPath, "utf8");
  const declared = {};
  let currentName = null;
  let currentPath = null;
  let currentUrl = null;

  function flush() {
    if (currentPath) {
      declared[path.posix.normalize(currentPath)] = { name: currentName, url: currentUrl };
    }
  }

  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#") || line.startsWith(";")) continue;
    const sectionMatch = line.match(/^\[submodule\s+"([^"]*)"\]$/);
    if (sectionMatch) {
      flush();
      currentName = sectionMatch[1];
      currentPath = null;
      currentUrl = null;
      continue;
    }
    const kv = line.match(/^(\w+)\s*=\s*(.*)$/);
    if (kv && currentName !== null) {
      const [, key, value] = kv;
      if (key === "path") currentPath = value.trim();
      else if (key === "url") currentUrl = value.trim();
    }
  }
  flush();
  return declared;
}

// True if `path` is itself a git repo (a .git dir, or a .git file pointing
// elsewhere — the shape submodule worktrees and some worktree checkouts use).
function hasOwnGit(p) {
  const marker = path.join(p, ".git");
  try {
    const stat = fs.statSync(marker);
    return stat.isDirectory() || stat.isFile();
  } catch {
    return false;
  }
}

// Walk the tree under root (excluding root itself) for any directory that is
// its own git repo.
function findNestedRepos(root, excludes) {
  const found = [];
  function walk(dir) {
    let entries;
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
      return;
    }
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      if (excludes.has(entry.name)) continue;
      const full = path.join(dir, entry.name);
      if (hasOwnGit(full)) found.push(full);
      walk(full);
    }
  }
  walk(root);
  return found;
}

function docforgeStatus(repoPath) {
  const arch = path.join(repoPath, "docs", "architecture");
  const hasOverview = exists(path.join(arch, "high-level.md")) || exists(path.join(arch, "overview.md"));
  const hasManifest = exists(path.join(repoPath, ".docforge", "manifest.json"));
  if (hasManifest) return "docforge baseline + provenance";
  if (hasOverview) return "docforge baseline present (no provenance manifest yet)";
  return "none — needs generation";
}

function parseArgs(argv) {
  const args = { exclude: [], json: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--root") args.root = argv[++i];
    else if (a === "--exclude") args.exclude.push(argv[++i]);
    else if (a === "--json") args.json = true;
  }
  return args;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.root) {
    console.error("usage: discover_repos.js --root <path> [--exclude <name>]... [--json]");
    return 2;
  }
  const root = path.resolve(args.root);
  if (!isDir(root)) {
    console.error(`Not a directory: ${root}`);
    return 2;
  }
  const excludes = new Set([...DEFAULT_EXCLUDES, ...args.exclude]);

  const declared = parseGitmodules(root);
  const nested = findNestedRepos(root, excludes);

  const declaredPaths = new Set(Object.keys(declared).map((p) => path.join(root, p)));
  const detected = nested.filter((p) => !declaredPaths.has(p));

  const collection = [
    { path: root, membership: "parent", status: docforgeStatus(root) },
  ];

  for (const [relPath, meta] of Object.entries(declared)) {
    const full = path.join(root, relPath);
    collection.push({
      path: full,
      membership: "declared (submodule)",
      submodule_name: meta.name,
      submodule_url: meta.url,
      status: exists(full) ? docforgeStatus(full) : "not checked out locally",
    });
  }

  for (const full of detected) {
    collection.push({
      path: full,
      membership: "detected — NOT in .gitmodules",
      status: docforgeStatus(full),
    });
  }

  const needsGeneration = collection.filter((c) => c.status.startsWith("none"));

  if (args.json) {
    console.log(
      JSON.stringify(
        {
          root,
          collection,
          needs_generation: needsGeneration.map((c) => c.path),
        },
        null,
        2
      )
    );
    return 0;
  }

  console.log(`Repo collection under ${root}\n`);
  for (const c of collection) {
    const flag = c.status.startsWith("none") ? "  <-- needs docforge generation before diligence" : "";
    console.log(`[${c.membership}] ${c.path}\n    status: ${c.status}${flag}\n`);
  }

  if (collection.some((c) => c.membership.startsWith("detected"))) {
    console.log("NOTE: one or more detected child repos are not declared in .gitmodules.");
    console.log("      Confirm with the repo owner whether each is in scope before proceeding.\n");
  }

  if (needsGeneration.length) {
    console.log(`${needsGeneration.length} repo(s) need a docforge baseline before the portfolio layer is built:`);
    for (const c of needsGeneration) {
      console.log(`  - ${c.path}`);
    }
  }
  return 0;
}

process.exit(main());
