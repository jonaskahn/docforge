#!/usr/bin/env node
"use strict";
/** Shared Node built-in helpers for Docforge scripts. Not a public CLI. */

const fs = require("fs");
const path = require("path");

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

const DOCFORGE_GITIGNORE_RULES = [
  "# Ephemeral run state and scratch space for Docforge",
  "tmp/",
  "audits/",
  "scratch/",
  "backups/",
  "cache/",
  "obsolete/",
  "*.tmp",
  "*.log",
];

function ensureDocforgeGitignore(docforgeDir) {
  fs.mkdirSync(docforgeDir, { recursive: true });
  const gitignore = path.join(docforgeDir, ".gitignore");
  if (!fs.existsSync(gitignore)) {
    fs.writeFileSync(gitignore, DOCFORGE_GITIGNORE_RULES.join("\n") + "\n", "utf-8");
  } else {
    const existing = fs.readFileSync(gitignore, "utf8").split(/\r?\n/);
    const missing = DOCFORGE_GITIGNORE_RULES.filter(
      (rule) => !rule.startsWith("#") && !existing.includes(rule),
    );
    if (missing.length > 0) {
      let content = fs.readFileSync(gitignore, "utf8");
      const suffix = !content || content.endsWith("\n") ? "" : "\n";
      fs.writeFileSync(gitignore, content + suffix + missing.join("\n") + "\n", "utf-8");
    }
  }
  return gitignore;
}

function finishDocforge(docforgeDir, options = {}) {
  const cleanTmp = options.cleanTmp !== false;
  ensureDocforgeGitignore(docforgeDir);
  const cleaned = [];
  if (cleanTmp) {
    for (const folderName of ["tmp", "scratch"]) {
      const folder = path.join(docforgeDir, folderName);
      if (fs.existsSync(folder) && fs.statSync(folder).isDirectory()) {
        const entries = fs.readdirSync(folder);
        for (const entry of entries) {
          if (entry === ".gitignore") continue;
          const fullPath = path.join(folder, entry);
          fs.rmSync(fullPath, { recursive: true, force: true });
        }
        cleaned.push(folderName);
      }
    }
  }
  return {
    docforge_dir: docforgeDir,
    gitignore_ensured: true,
    cleaned_dirs: cleaned,
  };
}

// Create dirPath if needed and drop a .gitignore containing '*' inside it so
// its contents are never committed, in whichever repo Docforge is
// documenting. Idempotent.
function ensureGitignoredDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
  if (
    ["tmp", "audits", "scratch", "obsolete"].includes(path.basename(dirPath)) &&
    path.basename(path.dirname(dirPath)) === ".docforge"
  ) {
    ensureDocforgeGitignore(path.dirname(dirPath));
  }
  const gitignore = path.join(dirPath, ".gitignore");
  if (!fs.existsSync(gitignore)) fs.writeFileSync(gitignore, "*\n", "utf-8");
  return gitignore;
}

function loadManifest(target, options = {}) {
  const allowedVersions = options.allowedVersions || ["3.9", "3.8", "3.7", "3.6", "3.5", "3.4", "3.3", "3.2", "3.1"];
  const requireDocuments = Boolean(options.requireDocuments);
  const unsupportedHint =
    options.unsupportedHint || "run migrate_metadata.js to re-register legacy manifests";
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

// Paths the user decided to keep self-managed: never tracked by Docforge,
// never re-asked, updatable in place without ownership. Reads
// `project.unmanaged_docs` (`[{path, decided_at}]`).
function unmanagedPaths(manifest) {
  const project = manifest && manifest.project;
  if (!project || typeof project !== "object" || !Array.isArray(project.unmanaged_docs)) {
    return new Set();
  }
  return new Set(
    project.unmanaged_docs
      .filter((entry) => entry && typeof entry.path === "string" && entry.path)
      .map((entry) => entry.path),
  );
}

module.exports = {
  fail,
  readJson,
  dumpJson,
  loadManifest,
  unmanagedPaths,
  ensureGitignoredDir,
  ensureDocforgeGitignore,
  finishDocforge,
  DOCFORGE_GITIGNORE_RULES,
};

if (require.main === module) {
  process.stderr.write("error: _util.js is a shared module, not a CLI\n");
  process.exit(2);
}
