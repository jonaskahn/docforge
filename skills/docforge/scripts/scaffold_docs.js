#!/usr/bin/env node
"use strict";
/** Preview, materialize, or audit the exact tree in a Docforge 2.0 manifest. */

const fs = require("fs");
const path = require("path");
const TEMPLATES = path.resolve(__dirname, "..", "assets", "templates");
const PLACEHOLDER = /\{\{[^}]+\}\}|TODO\([^)]*\)/g;
const TOKEN = /<[A-Z][A-Z0-9_]{2,}>/g;
const LINK = /\[[^\]]*\]\(([^)]+)\)/g;
const FORGE = /\b(github|gitlab|bitbucket|gitea|forgejo|sourcehut|azure devops|github actions|gitlab ci|codeowners)\b/gi;
const MARKDOWN_EXCEPTIONS = new Set(["AGENTS.md", "CLAUDE.md", "CLAUDE.local.md"]);

function fail(message, code = 1) {
  process.stderr.write(`error: ${message}\n`);
  return code;
}
function resolveManifest(value, repo) {
  if (path.isAbsolute(value)) return value;
  const direct = path.resolve(value);
  const repoRelative = path.resolve(repo, value);
  return fs.existsSync(direct) ? direct : repoRelative;
}
function loadManifest(target) {
  if (!fs.existsSync(target) || !fs.statSync(target).isFile()) throw new Error(`manifest not found: ${target}`);
  const manifest = JSON.parse(fs.readFileSync(target, "utf8"));
  if (manifest.version !== "2.0" || !Array.isArray(manifest.documents)) throw new Error(`manifest must use version 2.0: ${target}`);
  return manifest;
}
function activeDocuments(manifest) {
  return manifest.documents.filter((doc) => doc.status !== "skipped");
}
function preview(manifest) {
  const docs = activeDocuments(manifest);
  for (const doc of docs) console.log(`${String(doc.write_order).padStart(3, "0")}  ${doc.id.padEnd(28)}  ${doc.path}`);
  console.log(`\n${docs.length} manifest documents.`);
  return 0;
}
function posixDirname(value) {
  return path.posix.dirname(value);
}
function titleFor(doc) {
  return path.posix.basename(doc.path, path.posix.extname(doc.path)).replace(/[-_]/g, " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
}
function isDirectChild(directory, candidate) {
  const relative = path.posix.relative(directory, candidate.path);
  const parts = relative.split("/");
  return !relative.startsWith("..") && (parts.length === 1 || (parts.length === 2 && parts[1] === "README.md"));
}
function indexBody(doc, manifest) {
  const directory = posixDirname(doc.path);
  const children = activeDocuments(manifest)
    .filter((candidate) => candidate.id !== doc.id && isDirectChild(directory, candidate))
    .sort((a, b) => a.write_order - b.write_order || a.path.localeCompare(b.path));
  const lines = [
    "---",
    '{"docforge_provenance":{"sections":[]}}',
    "---",
    `# ${titleFor(doc)}`,
    "",
    "_Last reviewed: {{YYYY-MM-DD}}_",
    "",
    "| Document | Purpose |",
    "|---|---|",
  ];
  for (const child of children) {
    const relative = path.posix.relative(directory, child.path);
    lines.push(`| [${titleFor(child)}](${relative}) | {{Describe ${child.id} from repository evidence.}} |`);
  }
  if (!children.length) lines.push("| {{document}} | {{purpose}} |");
  return lines.join("\n") + "\n";
}
function scaffoldBody(doc, manifest) {
  const indexes = new Set(["folder-index", "docs-index", "portfolio-index", "decision-index", "portfolio-decisions-index", "ba-index", "po-index"]);
  if (indexes.has(doc.type)) return indexBody(doc, manifest);
  const template = path.join(TEMPLATES, doc.scaffold_template);
  if (!fs.existsSync(template)) throw new Error(`template not found for ${doc.id}: ${doc.scaffold_template}`);
  return fs.readFileSync(template, "utf8");
}
function deepMerge(existing, defaults) {
  if (Array.isArray(existing) && Array.isArray(defaults)) return existing.concat(defaults.filter((item) => !existing.some((old) => JSON.stringify(old) === JSON.stringify(item))));
  if (existing && defaults && typeof existing === "object" && typeof defaults === "object" && !Array.isArray(existing) && !Array.isArray(defaults)) {
    const result = { ...existing };
    for (const [key, value] of Object.entries(defaults)) result[key] = key in result ? deepMerge(result[key], value) : value;
    return result;
  }
  return existing;
}
function ensureLocalIgnore(repo) {
  const target = path.join(repo, ".gitignore");
  const text = fs.existsSync(target) ? fs.readFileSync(target, "utf8") : "";
  if (!text.split(/\r?\n/).includes("CLAUDE.local.md")) {
    const suffix = !text || text.endsWith("\n") ? "" : "\n";
    fs.writeFileSync(target, text + suffix + "CLAUDE.local.md\n");
  }
}
function writeDocument(repo, doc, manifest) {
  const target = path.join(repo, ...doc.path.split("/"));
  const body = scaffoldBody(doc, manifest);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  let action;
  if (doc.type === "machine-config" && fs.existsSync(target)) {
    const existing = JSON.parse(fs.readFileSync(target, "utf8"));
    const defaults = JSON.parse(body);
    fs.writeFileSync(target, JSON.stringify(deepMerge(existing, defaults), null, 2) + "\n");
    action = "merge";
  } else if (fs.existsSync(target)) {
    action = "exists";
  } else {
    fs.writeFileSync(target, body);
    action = "create";
  }
  if (doc.path === "CLAUDE.local.md") ensureLocalIgnore(repo);
  console.log(`${action}  ${doc.path}`);
}
function requiredIndexes(doc, manifest) {
  const ancestors = [];
  let parent = posixDirname(doc.path);
  while (parent && parent !== ".") {
    ancestors.push(`${parent}/README.md`);
    parent = posixDirname(parent);
  }
  const byPath = Object.fromEntries(activeDocuments(manifest).map((item) => [item.path, item]));
  return ancestors.reverse().filter((item) => item !== doc.path && byPath[item]).map((item) => byPath[item]);
}
function materialize(repo, manifest, docId) {
  const doc = activeDocuments(manifest).find((item) => item.id === docId);
  if (!doc) return fail(`document id not found or skipped: ${docId}`, 2);
  try {
    for (const index of requiredIndexes(doc, manifest)) {
      if (!fs.existsSync(path.join(repo, ...index.path.split("/")))) writeDocument(repo, index, manifest);
    }
    writeDocument(repo, doc, manifest);
    return 0;
  } catch (error) {
    return fail(error.message, 2);
  }
}
function parseFrontmatter(text) {
  if (!text.startsWith("---\n")) return null;
  const end = text.indexOf("\n---\n", 4);
  if (end < 0) return null;
  const line = text.slice(4, end);
  if (line.includes("\n")) return null;
  try {
    const value = JSON.parse(line);
    return value && typeof value === "object" && !Array.isArray(value) ? value : null;
  } catch {
    return null;
  }
}
function audit(repo, manifest) {
  const findings = {
    missing: [],
    "unfilled scaffold": [],
    "invalid provenance": [],
    "broken links": [],
    "invalid json": [],
    "folder-only promotion": [],
    "forge leakage": [],
    unexpected: [],
  };
  const tokens = [];
  const docs = activeDocuments(manifest);
  const expected = new Set(docs.map((doc) => doc.path));
  for (const rootName of ["docs", "docs-portfolio"]) {
    const root = path.join(repo, rootName);
    if (!fs.existsSync(root) || !fs.statSync(root).isDirectory()) continue;
    const stack = [root];
    while (stack.length) {
      const current = stack.pop();
      for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
        const target = path.join(current, entry.name);
        if (entry.isDirectory()) {
          if (entry.name !== "_archive") stack.push(target);
        } else if (entry.isFile() && entry.name.endsWith(".md")) {
          const rel = path.relative(repo, target).split(path.sep).join("/");
          if (!expected.has(rel)) findings.unexpected.push(rel);
        }
      }
    }
  }
  for (const doc of docs) {
    const target = path.join(repo, ...doc.path.split("/"));
    if (!fs.existsSync(target) || !fs.statSync(target).isFile()) {
      findings.missing.push(doc.path);
      continue;
    }
    const text = fs.readFileSync(target, "utf8");
    if (doc.type === "machine-config") {
      try { JSON.parse(text); } catch { findings["invalid json"].push(doc.path); }
      continue;
    }
    const placeholders = text.match(PLACEHOLDER) || [];
    if (placeholders.length) findings["unfilled scaffold"].push(`${doc.path} (${placeholders.length})`);
    const foundTokens = [...new Set(text.match(TOKEN) || [])].sort();
    if (foundTokens.length) tokens.push(`${doc.path}: ${foundTokens.join(", ")}`);
    const forgeHits = [...new Set((text.match(FORGE) || []).map((item) => item.toLowerCase()))].sort();
    if (forgeHits.length) findings["forge leakage"].push(`${doc.path}: ${forgeHits.join(", ")}`);
    if (doc.provenance_mode === "sections" && !MARKDOWN_EXCEPTIONS.has(doc.path)) {
      const frontmatter = parseFrontmatter(text);
      if (!frontmatter || !("docforge_provenance" in frontmatter)) findings["invalid provenance"].push(doc.path);
    }
    for (const match of text.matchAll(LINK)) {
      const link = match[1];
      const clean = link.split("#", 1)[0];
      if (!clean || /^(https?:\/\/|mailto:)/.test(clean)) continue;
      if (/\{\{[^}]+\}\}|<[A-Z][A-Z0-9_]{2,}>/.test(clean)) continue;
      if (!fs.existsSync(path.resolve(path.dirname(target), clean))) findings["broken links"].push(`${doc.path} -> ${link}`);
    }
  }
  for (const prefix of ["docs/flows/", "docs/architecture/concepts/"]) {
    const folders = new Set([...expected].filter((value) => value.startsWith(prefix)).map(posixDirname));
    for (const folder of [...folders].sort()) {
      if (folder === prefix.replace(/\/$/, "")) continue;
      if (expected.has(`${folder}/README.md`)) {
        const children = [...expected].filter((value) => posixDirname(value) === folder && !value.endsWith("/README.md"));
        if (!children.length) findings["folder-only promotion"].push(folder);
      }
    }
  }
  const total = Object.values(findings).reduce((sum, items) => sum + items.length, 0);
  for (const [label, items] of Object.entries(findings)) {
    items.sort();
    if (items.length) {
      console.log(`${label.toUpperCase()} (${items.length})`);
      for (const item of items) console.log(`  ${item}`);
      console.log();
    }
  }
  if (tokens.length) {
    console.log(`EXTERNAL TOKENS (${tokens.length})`);
    for (const item of tokens) console.log(`  ${item}`);
    console.log();
  }
  console.log(`${docs.length} manifest documents checked, ${total} defects.`);
  return total ? 1 : 0;
}
function parseArgs(argv) {
  const result = {};
  const allowed = new Set(["repo", "manifest", "dry-run", "document", "audit"]);
  for (let i = 0; i < argv.length; i++) {
    const token = argv[i];
    if (token === "-h" || token === "--help") return { help: true };
    if (!token.startsWith("--")) throw new Error(`unexpected argument: ${token}`);
    const raw = token.slice(2);
    if (!allowed.has(raw)) throw new Error(`unknown option: ${token}`);
    const key = raw.replace(/-/g, "_");
    if (raw === "dry-run" || raw === "audit") result[key] = true;
    else {
      if (i + 1 >= argv.length || argv[i + 1].startsWith("--")) throw new Error(`option requires a value: ${token}`);
      result[key] = argv[++i];
    }
  }
  return result;
}
function usage() {
  console.log("usage: scaffold_docs.js --repo <path> --manifest <path> (--dry-run | --document <id> | --audit)");
}
function main() {
  let args;
  try {
    args = parseArgs(process.argv.slice(2));
    if (args.help) { usage(); return 0; }
    if (!args.repo || !args.manifest) throw new Error("--repo and --manifest are required");
    const modes = [Boolean(args.dry_run), Boolean(args.document), Boolean(args.audit)].filter(Boolean).length;
    if (modes !== 1) throw new Error("choose exactly one of --dry-run, --document, or --audit");
    if (!fs.existsSync(args.repo) || !fs.statSync(args.repo).isDirectory()) return fail(`not a directory: ${args.repo}`, 2);
    const manifest = loadManifest(resolveManifest(args.manifest, args.repo));
    if (args.dry_run) return preview(manifest);
    if (args.document) return materialize(args.repo, manifest, args.document);
    return audit(args.repo, manifest);
  } catch (error) {
    usage();
    return fail(error.message, 2);
  }
}
process.exit(main());
