#!/usr/bin/env node
"use strict";
/**
 * Docforge dashboard runtime (JS peer of dashboard.py).
 *
 * Backs the dashboard capability of the `docforge` skill (the optional
 * `/docforge-dashboard` skill is only a thin entrypoint into this cartridge).
 * Builds and serves a local Fumadocs application under `<repo>/.docforge/dashboard/`
 * from the Docforge manifest and the repository's `docs/` Markdown. The
 * dashboard directory is self-contained: its own package.json, lockfile, and
 * node_modules; it never touches the repository's package files.
 *
 * Subcommands: start, status, stop. Python and JS peers are equivalent.
 */

const { execFileSync, spawn, spawnSync } = require("child_process");
const crypto = require("crypto");
const fs = require("fs");
const net = require("net");
const path = require("path");

const { dumpJson, ensureDocforgeGitignore, fail, loadManifest, readJson } = require("../../common/js/_util.js");
const pf = require("../../common/js/provenance_frontmatter.js");

const TOOL_VERSION = "2.11.0";
const TEMPLATE_VERSION = "1";
const STATE_SCHEMA = 1;
const STATE_FILE = ".docforge-dashboard.json";
const BASE_URL = "/docs";
const DOC_PREFIX = "docs/";
const WRITTEN = new Set(["generated", "needs_review", "complete"]);
const ASSET_EXTS = [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".avif", ".ico", ".bmp"];
const ASSET_MAX_BYTES = 10 * 1024 * 1024;
const SCHEMES = ["http://", "https://", "mailto:", "tel:", "//"];
const ENTITY = { "<": "&lt;", ">": "&gt;", "{": "&#123;", "}": "&#125;" };

const LINK_RE = /(!?\[[^\]]*\])(\(([^)\s]+)(?:\s+["'][^"']*["'])?\))/g;
const HEADING_RE = /^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$/;
const CUSTOM_ANCHOR_RE = /\[#([^\]]+)\]$/;
const INLINE_LINK_RE = /\]\(([^)]+)\)/g;
const SKIP_LINK_RE = /^(#|http:\/\/|https:\/\/|mailto:|tel:|\/\/)/;

function nowIso() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}

function sha256Bytes(data) {
  return crypto.createHash("sha256").update(data).digest("hex");
}

function titleFor(doc) {
  return doc.title || doc.id.replace(/[-_]/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function gitRemoteUrl(repo) {
  const result = spawnSync("git", ["-C", repo, "config", "--get", "remote.origin.url"], { encoding: "utf8", timeout: 10000 });
  const value = result.status === 0 ? result.stdout.trim() : "";
  if (!value) return null;
  let out = value.endsWith(".git") ? value.slice(0, -4) : value;
  if (out.startsWith("git@")) {
    out = out.replace(":", "/", 1).replace("git@", "https://", 1);
  }
  if (out.startsWith("http://") || out.startsWith("https://")) return out;
  return null;
}

function rootDocHasProvenance(repo, rel) {
  const { raw } = splitFrontmatterRaw(fs.readFileSync(path.join(repo, rel), "utf8"));
  if (!raw) return false;
  let data;
  try {
    data = pf.parseYamlMapping(raw);
  } catch {
    return false;
  }
  const provenance = data.docforge_provenance;
  return !!(provenance && typeof provenance === "object" && provenance.schema === pf.SCHEMA_VERSION);
}

function manifestProvenance(doc) {
  if (doc.provenance_mode !== "manifest") return false;
  return !!(doc.provenance && typeof doc.provenance === "object" && doc.provenance.schema === pf.SCHEMA_VERSION);
}

function includedDocuments(repo, manifest) {
  const out = [];
  for (const doc of manifest.documents || []) {
    if (!WRITTEN.has(doc.status)) continue;
    const p = doc.path || "";
    if (!(p.endsWith(".md") || p.endsWith(".mdx"))) continue;
    if (!p.startsWith(DOC_PREFIX) && p.includes("/")) continue;
    if (!fs.existsSync(path.join(repo, p))) continue;
    if (!p.startsWith(DOC_PREFIX) && !rootDocHasProvenance(repo, p) && !manifestProvenance(doc)) continue;
    out.push(doc);
  }
  return out.sort((a, b) => (a.path === b.path ? (a.id < b.id ? -1 : a.id > b.id ? 1 : 0) : a.path < b.path ? -1 : 1));
}

function routeForDoc(doc) {
  const p = doc.path || "";
  if (p.startsWith(DOC_PREFIX)) {
    const rel = p.slice(DOC_PREFIX.length);
    if (rel === "README.md") return ["index.mdx", BASE_URL];
    if (rel.endsWith("/README.md")) {
      const directory = rel.slice(0, -"/README.md".length);
      return [`${directory}/index.mdx`, `${BASE_URL}/${directory}`];
    }
    const stem = rel.endsWith(".md") ? rel.slice(0, -3) : rel.slice(0, -4);
    return [`${stem}.mdx`, `${BASE_URL}/${stem}`];
  }
  const stem = p.endsWith(".md") ? p.slice(0, -3) : p.slice(0, -4);
  const slug = stem.toLowerCase();
  return [`root/${slug}.mdx`, `${BASE_URL}/root/${slug}`];
}

function buildLedger(docs) {
  const ledger = { pages: [], by_path: {}, by_url: {} };
  for (const doc of docs) {
    const [output, url] = routeForDoc(doc);
    const page = {
      id: doc.id,
      doc_id: doc.id,
      doc,
      title: titleFor(doc),
      source_path: doc.path,
      output_path: output,
      url,
      write_order: doc.write_order || 0,
    };
    ledger.pages.push(page);
    ledger.by_path[doc.path] = page;
    ledger.by_url[url] = page;
  }
  return ledger;
}

function treeFiles(repo) {
  const root = path.join(repo, "docs");
  if (!fs.existsSync(root) || !fs.statSync(root).isDirectory()) return [];
  const out = [];
  const walk = (dir) => {
    for (const entry of fs.readdirSync(dir)) {
      const full = path.join(dir, entry);
      const stat = fs.statSync(full);
      if (stat.isFile()) out.push(path.relative(repo, full).split(path.sep).join("/"));
      else if (stat.isDirectory()) walk(full);
    }
  };
  walk(root);
  return out.sort();
}

function sortedTemplateFiles(templateDir) {
  const out = [];
  const walk = (dir) => {
    for (const entry of fs.readdirSync(dir)) {
      const full = path.join(dir, entry);
      const stat = fs.statSync(full);
      if (stat.isFile()) out.push(full);
      else if (stat.isDirectory()) walk(full);
    }
  };
  walk(templateDir);
  return out.sort((a, b) => (path.relative(templateDir, a) < path.relative(templateDir, b) ? -1 : 1));
}

function manifestProjection(manifest) {
  return (manifest.documents || [])
    .slice()
    .sort((a, b) => ((a.path || "") < (b.path || "") ? -1 : 1))
    .map((doc) => ({
      id: doc.id || "",
      path: doc.path || "",
      status: doc.status || "",
      title: titleFor(doc),
      write_order: doc.write_order || 0,
    }));
}

function renderSignature(repo, manifest) {
  const records = [];
  for (const doc of manifestProjection(manifest)) {
    records.push(`doc\x00${JSON.stringify(doc)}`);
  }
  for (const rel of treeFiles(repo)) {
    records.push(`file\x00${rel}\x00${sha256Bytes(fs.readFileSync(path.join(repo, rel)))}`);
  }
  for (const doc of manifestProjection(manifest)) {
    const rel = doc.path;
    if (!rel || rel.includes("/") || !(rel.endsWith(".md") || rel.endsWith(".mdx"))) continue;
    const target = path.join(repo, rel);
    if (fs.existsSync(target)) records.push(`root\x00${rel}\x00${sha256Bytes(fs.readFileSync(target))}`);
  }
  const settings = {
    base_url: BASE_URL,
    generator: TOOL_VERSION,
    include: "docs/**, root/*.md",
  };
  records.push(`settings\x00${JSON.stringify(settings)}`);
  return sha256Bytes(Buffer.from(records.join("\n")));
}

function shellSignature(templateDir, repo, manifest) {
  const records = [];
  for (const full of sortedTemplateFiles(templateDir)) {
    const rel = path.relative(templateDir, full).split(path.sep).join("/");
    records.push(`template\x00${rel}\x00${sha256Bytes(fs.readFileSync(full))}`);
  }
  const project = {
    git_url: gitRemoteUrl(repo) || "",
    name: (manifest.project && manifest.project.name) || path.basename(repo),
  };
  records.push(`project\x00${JSON.stringify(project)}`);
  records.push(`template_version\x00${TEMPLATE_VERSION}`);
  return sha256Bytes(Buffer.from(records.join("\n")));
}

function statePath(dashboard) {
  return path.join(dashboard, STATE_FILE);
}

function loadState(dashboard) {
  const target = statePath(dashboard);
  if (fs.existsSync(target)) {
    try {
      const value = readJson(target);
      if (value && typeof value === "object" && !Array.isArray(value)) return value;
    } catch {
      /* fall through */
    }
  }
  return {};
}

function saveState(dashboard, state) {
  fs.mkdirSync(dashboard, { recursive: true });
  fs.writeFileSync(statePath(dashboard), dumpJson(state), "utf8");
}

function publicFrontmatter(doc, provenance) {
  return pf.emitDocumentFrontmatter(doc.id, titleFor(doc), provenance);
}

function splitFrontmatterRaw(text) {
  const split = pf.splitFrontmatter(text);
  return { raw: split.raw, body: split.body };
}

function reconcileMetadata(repo, manifest, dryRun = false) {
  const report = { reconciled: [], unchanged: [], skipped: [], errors: [] };
  for (const doc of manifest.documents || []) {
    if (doc.status === "skipped") continue;
    const p = doc.path || "";
    if (!p.startsWith(DOC_PREFIX) || !p.endsWith(".md")) continue;
    const target = path.join(repo, p);
    if (!fs.existsSync(target)) continue;
    const text = fs.readFileSync(target, "utf8");
    const { raw, body } = splitFrontmatterRaw(text);
    if (raw == null) {
      report.skipped.push({ doc: doc.id, detail: "no frontmatter" });
      continue;
    }
    let data;
    try {
      data = pf.parseYamlMapping(raw);
    } catch (error) {
      report.errors.push({ doc: doc.id, detail: `unparseable frontmatter: ${error.message}` });
      continue;
    }
    const provenance = data.docforge_provenance;
    if (!provenance || typeof provenance !== "object" || provenance.schema !== pf.SCHEMA_VERSION) {
      report.skipped.push({ doc: doc.id, detail: "provenance is not schema 2.0" });
      continue;
    }
    const wantId = doc.id;
    const wantTitle = titleFor(doc);
    const problems = [];
    if (data.id !== wantId) problems.push("id");
    if (data.title !== wantTitle) problems.push("title");
    if (provenance.doc_id !== wantId) problems.push("provenance.doc_id");
    if (provenance.path !== p) problems.push("provenance.path");
    if (problems.length === 0) {
      report.unchanged.push({ doc: doc.id });
      continue;
    }
    report.reconciled.push({ doc: doc.id, path: p, fixed: problems });
    if (!dryRun) {
      if (problems.includes("provenance.doc_id")) provenance.doc_id = wantId;
      if (problems.includes("provenance.path")) provenance.path = p;
      fs.writeFileSync(target, publicFrontmatter(doc, provenance) + body, "utf8");
    }
  }
  report.counts = {
    reconciled: report.reconciled.length,
    unchanged: report.unchanged.length,
    errors: report.errors.length,
  };
  return report;
}

function escapeMdxText(line) {
  let out = "";
  let inCode = false;
  for (const char of line) {
    if (char === "`") {
      inCode = !inCode;
      out += char;
    } else if (inCode) {
      out += char;
    } else {
      out += ENTITY[char] || char;
    }
  }
  return out;
}

function stripHtmlComments(body) {
  let out = "";
  let inFence = false;
  let inComment = false;
  for (const line of body.split(/(?<=\n)/)) {
    if (line.trimStart().startsWith("```")) {
      inFence = !inFence;
      out += line;
      continue;
    }
    if (inFence) {
      out += line;
      continue;
    }
    let lineOut = "";
    let inCode = false;
    let i = 0;
    while (i < line.length) {
      const char = line[i];
      if (inComment) {
        const end = line.indexOf("-->", i);
        if (end < 0) {
          i = line.length;
          continue;
        }
        inComment = false;
        i = end + 3;
        continue;
      }
      if (char === "`") {
        inCode = !inCode;
        lineOut += char;
        i += 1;
        continue;
      }
      if (!inCode && line.startsWith("<!--", i)) {
        const end = line.indexOf("-->", i + 4);
        if (end < 0) {
          inComment = true;
          i = line.length;
          continue;
        }
        i = end + 3;
        continue;
      }
      lineOut += char;
      i += 1;
    }
    out += lineOut;
  }
  return out;
}

function resolveLink(target, sourcePath, ledger, assetsNeeded) {
  const index = target.indexOf("#");
  const fragment = index >= 0 ? target.slice(index) : "";
  const clean = index >= 0 ? target.slice(0, index) : target;
  if (!clean) return target;
  if (clean.startsWith("#")) return null;
  if (SCHEMES.some((scheme) => clean.startsWith(scheme))) return null;
  const base = path.posix.dirname(sourcePath);
  const repoRel = clean.startsWith("/") ? clean.replace(/^\/+/, "") : path.posix.normalize(path.posix.join(base, clean));
  const normalized = repoRel.replace(/\/+$/, "");
  let page = ledger.by_path[normalized];
  if (!page && !normalized.endsWith(".md")) {
    page = ledger.by_path[`${normalized}/README.md`];
  }
  if (page) return page.url + fragment;
  if (ledger.assets && ledger.assets.has(normalized)) {
    assetsNeeded.add(normalized);
    return `/docs-assets/${normalized}` + fragment;
  }
  return null;
}

function convertBody(body, sourcePath, ledger, assetsNeeded) {
  const unresolved = [];
  body = stripHtmlComments(body);
  let inFence = false;
  let lines = [];
  for (const line of body.split(/(?<=\n)/)) {
    const stripped = line.trimStart();
    if (stripped.startsWith("```")) {
      inFence = !inFence;
      lines.push(line);
      continue;
    }
    lines.push(inFence ? line : escapeMdxText(line));
  }
  let converted = lines.join("");

  converted = converted.replace(LINK_RE, (whole, label, __, inner) => {
    const rewritten = resolveLink(inner, sourcePath, ledger, assetsNeeded);
    if (rewritten == null || rewritten === inner) return whole;
    return `${label}(${rewritten})`;
  });
  return [converted, unresolved];
}

function firstH1Title(body) {
  for (const line of body.split(/\r?\n/)) {
    const match = HEADING_RE.exec(line);
    if (!match || match[1] !== "#") continue;
    let text = match[2];
    text = text.replace(/(\s*\[(?:[!#]|toc)[^\]]*\])+\s*$/, "");
    text = text.replace(/\[([^\]]+)\]\([^)]*\)/g, "$1");
    text = text.replace(/[*_`]/g, "");
    text = text.replace(/\s+/g, " ").trim();
    if (text) return text;
  }
  return null;
}

function headingAnchors(text) {
  const anchors = [];
  for (const line of text.split(/\r?\n/)) {
    const match = HEADING_RE.exec(line);
    if (!match) continue;
    const content = match[2].trim();
    const custom = CUSTOM_ANCHOR_RE.exec(content);
    if (custom) {
      anchors.push(custom[1]);
      continue;
    }
    const slug = content.replace(/[^\w\s-]/g, "").toLowerCase().replace(/\s+/g, "-").replace(/^-+|-+$/g, "");
    anchors.push(slug);
  }
  return anchors;
}

function collectAssetMap(repo) {
  const result = new Set();
  for (const rel of treeFiles(repo)) {
    if (ASSET_EXTS.some((ext) => rel.endsWith(ext))) result.add(rel);
  }
  return result;
}

function blobSha1(content) {
  return crypto.createHash("sha1")
    .update(Buffer.from(`blob ${content.length}\0`))
    .update(content)
    .digest("hex");
}

function scan(repo, manifest) {
  const problems = [];
  const report = reconcileMetadata(repo, manifest, true);
  for (const entry of report.errors) problems.push({ kind: "metadata", doc: entry.doc, detail: entry.detail });
  for (const entry of report.skipped) problems.push({ kind: "metadata", doc: entry.doc, detail: entry.detail });
  for (const doc of manifest.documents || []) {
    const p = doc.path || "";
    if (!(p.endsWith(".md") || p.endsWith(".mdx"))) continue;
    if (!WRITTEN.has(doc.status)) {
      problems.push({ kind: "incomplete", doc: doc.id || "", detail: `status ${doc.status}` });
      continue;
    }
    if (!fs.existsSync(path.join(repo, p))) {
      problems.push({ kind: "missing_file", doc: doc.id || "", detail: p });
    }
  }
  for (const doc of manifest.documents || []) {
    const prov = doc.provenance;
    if (!prov || typeof prov !== "object" || prov.schema !== pf.SCHEMA_VERSION) continue;
    for (const section of prov.sections || []) {
      for (const source of section.sources || []) {
        const sourcePath = source.path;
        const want = source.git_blob;
        if (!sourcePath) continue;
        const target = path.join(repo, sourcePath);
        if (!fs.existsSync(target)) {
          problems.push({ kind: "drift", doc: doc.id || "", detail: `${sourcePath} missing` });
          continue;
        }
        if (want && blobSha1(fs.readFileSync(target)) !== want) {
          problems.push({ kind: "drift", doc: doc.id || "", detail: `${sourcePath} changed since provenance` });
        }
      }
    }
  }
  const docs = includedDocuments(repo, manifest);
  const ledger = buildLedger(docs);
  ledger.assets = collectAssetMap(repo);
  const tracked = new Set((manifest.documents || []).map((d) => d.path).filter(Boolean));
  for (const rel of treeFiles(repo)) {
    if ((rel.endsWith(".md") || rel.endsWith(".mdx")) && !tracked.has(rel)) {
      problems.push({ kind: "untracked", doc: "", detail: rel });
    }
  }
  for (const doc of docs) {
    const text = fs.readFileSync(path.join(repo, doc.path), "utf8");
    const { raw, body } = splitFrontmatterRaw(text);
    const scanBody = raw == null ? text : body;
    for (const match of scanBody.matchAll(LINK_RE)) {
      const inner = match[3];
      if (resolveLink(inner, doc.path, ledger, new Set()) != null) continue;
      const clean = inner.split("#")[0];
      if (!clean || clean.startsWith("#") || SCHEMES.some((scheme) => clean.startsWith(scheme))) continue;
      const repoRel = clean.startsWith("/")
        ? clean.replace(/^\/+/, "")
        : path.posix.normalize(path.posix.join(path.posix.dirname(doc.path), clean));
      const normalized = repoRel.replace(/\/+$/, "");
      if (/\.mdx?(?:#|$)/.test(normalized) && (normalized.startsWith(DOC_PREFIX) || !normalized.includes("/"))) {
        problems.push({ kind: "broken_link", doc: doc.id, detail: `${doc.path}: ${inner}` });
      }
    }
  }
  const kinds = ["metadata", "incomplete", "missing_file", "drift", "untracked", "broken_link"];
  const counts = {};
  for (const kind of kinds) counts[kind] = problems.filter((p) => p.kind === kind).length;
  return { problems, counts };
}

function plan(repo, manifest) {
  const docs = includedDocuments(repo, manifest);
  const ledger = buildLedger(docs);
  const problems = [];
  const folded = {};
  for (const page of ledger.pages) {
    const key = page.url.toLowerCase();
    if (key in folded) {
      problems.push(`duplicate url: ${page.url} (docs ${folded[key]} and ${page.source_path})`);
    } else {
      folded[key] = page.source_path;
    }
  }
  const byDir = {};
  for (const page of ledger.pages) {
    const dir = dirOf(page.output_path);
    byDir[dir] = byDir[dir] || [];
    byDir[dir].push(page);
  }
  if (!ledger.pages.some((page) => page.url === BASE_URL)) {
    problems.push("no docs index: docs/README.md is not a written document");
  }
  return {
    base_url: BASE_URL,
    pages: ledger.pages,
    folder_count: Object.keys(byDir).length,
    problems,
  };
}

function stemOf(name) {
  const ext = path.posix.extname(name);
  return ext ? name.slice(0, -ext.length) : name;
}

function dirOf(outputPath) {
  const dir = path.posix.dirname(outputPath);
  return dir === "." ? "" : dir;
}

function metaTitle(folder, ledger, manifest) {
  for (const page of ledger.pages) {
    if (page.output_path === (folder ? `${folder}/index.mdx` : "index.mdx")) return page.title;
  }
  if (folder === "") {
    for (const doc of manifest.documents || []) {
      if (doc.id === "docs_index") return titleFor(doc);
    }
  }
  if (folder === "root") return "Others";
  const name = path.posix.basename(folder);
  return name.replace(/[-_]/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function metaPlans(ledger, manifest) {
  const folders = {};
  for (const page of ledger.pages) {
    const folder = dirOf(page.output_path);
    folders[folder] = folders[folder] || { index: null, files: [], write_order: {} };
    if (path.posix.basename(page.output_path) === "index.mdx") {
      folders[folder].index = page;
    } else {
      folders[folder].files.push(page);
    }
    folders[folder].write_order[page.doc_id] = page.write_order;
  }
  for (const folder of Object.keys(folders)) {
    folders[folder].files.sort((a, b) => a.write_order - b.write_order || (a.source_path < b.source_path ? -1 : 1));
  }
  const folderOrder = (folder) => {
    // The `root` folder (repository-root files such as README.md and
    // CHANGELOG.md) always sorts last in the sidebar.
    if (folder === "root") return [Number.MAX_SAFE_INTEGER, folder];
    const info = folders[folder];
    if (!info) return [Number.MAX_SAFE_INTEGER, folder];
    if (info.index) return [info.index.write_order, folder];
    const min = info.files.length ? Math.min(...info.files.map((p) => p.write_order)) : Number.MAX_SAFE_INTEGER;
    return [min, folder];
  };

  const plans = {};
  for (const [folder, info] of Object.entries(folders)) {
    const names = new Set(
      Object.keys(folders)
        .filter((other) => other !== folder && (folder === "" || other.startsWith(folder + "/")))
        .map((other) => path.posix.relative(folder, other).split("/")[0]),
    );
    const entries = [];
    for (const name of names) {
      const [order] = folderOrder(folder ? `${folder}/${name}` : name);
      entries.push([[order, name], name]);
    }
    for (const page of info.files) {
      const stem = stemOf(path.posix.basename(page.output_path));
      entries.push([[page.write_order, stem], stem]);
    }
    entries.sort((a, b) => {
      const [oa, na] = a[0];
      const [ob, nb] = b[0];
      return oa - ob || (na < nb ? -1 : na > nb ? 1 : 0);
    });
    const pages = [];
    if (info.index) pages.push("index");
    pages.push(...entries.map((entry) => entry[1]));
    plans[folder] = {
      path: folder ? `${folder}/meta.json` : "meta.json",
      title: metaTitle(folder, ledger, manifest),
      pages,
    };
  }
  return plans;
}

function convertDocuments(repo, manifest, ledger, stageDocs) {
  const assetsNeeded = new Set();
  const anchors = {};
  const converted = [];
  for (const doc of ledger.pages) {
    const source = path.join(repo, doc.source_path);
    const text = fs.readFileSync(source, "utf8");
    const { raw, body } = splitFrontmatterRaw(text);
    let provenance;
    if (raw == null) {
      const manifestDoc = doc.doc || {};
      provenance = manifestDoc.provenance;
      if (
        manifestDoc.provenance_mode !== "manifest" ||
        !provenance || typeof provenance !== "object" || provenance.schema !== pf.SCHEMA_VERSION
      ) {
        throw new Error(`document has no frontmatter: ${doc.source_path}`);
      }
    } else {
      let data;
      try {
        data = pf.parseYamlMapping(raw);
      } catch (error) {
        throw new Error(`unparseable frontmatter: ${doc.source_path}: ${error.message}`);
      }
      provenance = data.docforge_provenance;
      if (!provenance || typeof provenance !== "object" || provenance.schema !== pf.SCHEMA_VERSION) {
        throw new Error(`provenance is not schema 2.0: ${doc.source_path}`);
      }
    }
    const [mdxBody] = convertBody(body, doc.source_path, ledger, assetsNeeded);
    const h1Title = firstH1Title(body);
    if (h1Title) doc.title = h1Title;
    const content = publicFrontmatter(doc, provenance) + mdxBody;
    const target = path.join(stageDocs, doc.output_path);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.writeFileSync(target, content, "utf8");
    anchors[doc.url] = headingAnchors(mdxBody);
    converted.push({ doc: doc.doc_id, url: doc.url, output: doc.output_path });
  }
  return { converted, assets_needed: [...assetsNeeded].sort(), anchors };
}

function copyAssets(repo, targetAssetsDir, assets) {
  const copied = [];
  for (const rel of assets) {
    const source = path.join(repo, rel);
    if (!fs.existsSync(source) || !ASSET_EXTS.some((ext) => rel.endsWith(ext))) continue;
    if (fs.statSync(source).size > ASSET_MAX_BYTES) continue;
    const target = path.join(targetAssetsDir, rel);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.copyFileSync(source, target);
    copied.push(rel);
  }
  return copied;
}

function swapStage(dashboard, stageDocs, stageAssets) {
  const contentTarget = path.join(dashboard, "content", "docs");
  fs.rmSync(contentTarget, { recursive: true, force: true });
  fs.renameSync(stageDocs, contentTarget);
  const assetsTarget = path.join(dashboard, "public", "docs-assets");
  fs.rmSync(assetsTarget, { recursive: true, force: true });
  if (fs.existsSync(stageAssets)) {
    fs.mkdirSync(path.dirname(assetsTarget), { recursive: true });
    fs.renameSync(stageAssets, assetsTarget);
  }
}

function validateBuild(repo, manifest, contentDir, assetsDir) {
  const docs = includedDocuments(repo, manifest);
  const ledger = buildLedger(docs);
  const errors = [];
  const warnings = [];
  const folded = {};
  for (const page of ledger.pages) {
    const key = page.url.toLowerCase();
    if (key in folded) {
      errors.push(`duplicate url: ${page.url} (${folded[key]}, ${page.source_path})`);
    } else {
      folded[key] = page.source_path;
    }
    if (!fs.existsSync(path.join(contentDir, page.output_path))) {
      errors.push(`missing output: ${page.output_path} (${page.url})`);
    }
  }
  if (!fs.existsSync(path.join(contentDir, "index.mdx"))) {
    errors.push("missing docs index: content/docs/index.mdx");
  }
  const urlToPage = {};
  for (const page of ledger.pages) urlToPage[page.url] = page;
  const anchors = {};
  for (const page of ledger.pages) {
    const output = path.join(contentDir, page.output_path);
    if (fs.existsSync(output)) {
      anchors[page.url] = new Set(headingAnchors(fs.readFileSync(output, "utf8")));
    }
  }
  for (const page of ledger.pages) {
    const output = path.join(contentDir, page.output_path);
    if (!fs.existsSync(output)) continue;
    const text = fs.readFileSync(output, "utf8");
    for (const match of text.matchAll(INLINE_LINK_RE)) {
      const target = match[1].trim();
      if (SKIP_LINK_RE.test(target)) continue;
      if (target.startsWith(`${BASE_URL}/`) || target === BASE_URL || target.startsWith(`${BASE_URL}#`)) {
        const hashIndex = target.indexOf("#");
        const url = hashIndex >= 0 ? target.slice(0, hashIndex) : target;
        const fragment = hashIndex >= 0 ? target.slice(hashIndex) : "";
        if (!urlToPage[url]) {
          errors.push(`broken link in ${page.output_path}: ${target}`);
          continue;
        }
        if (fragment && !anchors[url].has(fragment.slice(1))) {
          errors.push(`broken anchor in ${page.output_path}: ${target}`);
        }
      } else if (target.startsWith("/docs-assets/")) {
        const asset = target.slice("/docs-assets/".length).split("#")[0];
        if (!fs.existsSync(path.join(assetsDir, asset))) {
          errors.push(`missing asset in ${page.output_path}: ${target}`);
        }
      } else {
        const targetPath = target.split("#")[0];
        const normalized = path.posix.normalize(
          path.posix.join(DOC_PREFIX, path.posix.dirname(page.output_path), targetPath),
        );
        if (/\.mdx?(?:#|$)/.test(normalized) && (normalized.startsWith(DOC_PREFIX) || !normalized.includes("/"))) {
          errors.push(`unresolved internal link in ${page.output_path}: ${target}`);
        } else {
          warnings.push(`unresolved target in ${page.output_path}: ${target}`);
        }
      }
    }
  }
  let metaPaths = [];
  const rootMeta = path.join(contentDir, "meta.json");
  if (fs.existsSync(rootMeta)) {
    const walk = (dir) => {
      for (const entry of fs.readdirSync(dir)) {
        const full = path.join(dir, entry);
        const stat = fs.statSync(full);
        if (stat.isFile() && entry === "meta.json") metaPaths.push(full);
        else if (stat.isDirectory()) walk(full);
      }
    };
    walk(contentDir);
  }
  metaPaths.sort();
  for (const metaFile of metaPaths) {
    const folder = path.relative(contentDir, path.dirname(metaFile)).split(path.sep).join("/");
    let data;
    try {
      data = readJson(metaFile);
    } catch {
      errors.push(`invalid meta.json: ${metaFile}`);
      continue;
    }
    const expected = new Set();
    for (const page of ledger.pages) {
      if (dirOf(page.output_path) === folder) {
        expected.add(stemOf(path.posix.basename(page.output_path)));
      }
    }
    for (const entry of fs.readdirSync(path.dirname(metaFile))) {
      const full = path.join(path.dirname(metaFile), entry);
      if (fs.statSync(full).isDirectory() && fs.existsSync(path.join(full, "meta.json"))) {
        expected.add(entry);
      }
    }
    const actual = new Set(data.pages || []);
    for (const missing of [...expected].sort()) {
      if (!actual.has(missing)) errors.push(`meta coverage missing in ${path.relative(dashboard, metaFile)}: ${missing}`);
    }
    for (const extra of [...actual].sort()) {
      if (!expected.has(extra)) errors.push(`meta coverage extra in ${path.relative(dashboard, metaFile)}: ${extra}`);
    }
  }
  return {
    ok: errors.length === 0,
    errors,
    warnings,
    counts: { pages: ledger.pages.length, meta_files: metaPaths.length },
  };
}

function ensureDashboardIgnored(dashboard) {
  ensureDocforgeGitignore(path.dirname(dashboard));
  const gitignore = path.join(path.dirname(dashboard), ".gitignore");
  const lines = fs.readFileSync(gitignore, "utf8").split(/\r?\n/);
  if (!lines.includes("dashboard/")) {
    let text = fs.readFileSync(gitignore, "utf8");
    const suffix = !text || text.endsWith("\n") ? "" : "\n";
    fs.writeFileSync(gitignore, text + suffix + "dashboard/\n", "utf8");
  }
}

function scaffoldApp(dashboard, templateDir, repo, manifest, force = false) {
  const current = loadState(dashboard);
  const sha = shellSignature(templateDir, repo, manifest);
  if (!force && current.shell_sig === sha && fs.existsSync(path.join(dashboard, "lib", "shared.ts"))) {
    return false;
  }
  for (const name of ["app", "components", "lib", "next.config.mjs", "tsconfig.json", "postcss.config.mjs", "package.json", ".gitignore", "README.md"]) {
    const source = path.join(templateDir, name);
    const target = path.join(dashboard, name);
    if (fs.existsSync(source) && fs.statSync(source).isDirectory()) {
      fs.rmSync(target, { recursive: true, force: true });
      fs.cpSync(source, target, { recursive: true });
    } else if (fs.existsSync(source)) {
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.copyFileSync(source, target);
    }
  }
  const projectName = (manifest.project && manifest.project.name) || path.basename(repo);
  const gitUrl = gitRemoteUrl(repo) || "";
  const tpl = fs.readFileSync(path.join(templateDir, "lib", "shared.ts.tpl"), "utf8");
  fs.writeFileSync(
    path.join(dashboard, "lib", "shared.ts"),
    tpl.replaceAll("{{APP_NAME}}", projectName).replaceAll("{{GITHUB_URL}}", gitUrl),
    "utf8",
  );
  ensureDashboardIgnored(dashboard);
  return true;
}

function nodeMajor() {
  try {
    const version = execFileSync("node", ["--version"], { encoding: "utf8", timeout: 10000 }).trim().replace(/^v/, "");
    return parseInt(version.split(".")[0], 10) || 0;
  } catch {
    return 0;
  }
}

function ensureDependencies(dashboard, repo) {
  if (nodeMajor() < 22) {
    throw new Error("dashboard requires Node.js 22 or newer; install it before running /docforge-dashboard");
  }
  const rootGuards = {};
  for (const name of ["package.json", "package-lock.json"]) {
    const rootFile = path.join(repo, name);
    if (fs.existsSync(rootFile)) rootGuards[name] = sha256Bytes(fs.readFileSync(rootFile));
  }
  const nodeModules = path.join(dashboard, "node_modules");
  const lockfile = path.join(dashboard, "package-lock.json");
  const command = !fs.existsSync(nodeModules) || !fs.existsSync(lockfile)
    ? ["npm", "--prefix", dashboard, "install"]
    : ["npm", "--prefix", dashboard, "ci"];
  const result = spawnSync(command[0], command.slice(1), {
    cwd: dashboard,
    encoding: "utf8",
    timeout: 900000,
    env: { ...process.env, NEXT_TELEMETRY_DISABLED: "1" },
  });
  if (result.error || result.status !== 0) {
    throw new Error(`npm install failed; see the dashboard directory for logs (${result.error ? result.error.message : `exit ${result.status}`})`);
  }
  for (const [name, before] of Object.entries(rootGuards)) {
    const after = fs.existsSync(path.join(repo, name)) ? sha256Bytes(fs.readFileSync(path.join(repo, name))) : null;
    if (after !== before) {
      throw new Error(`dashboard touched the repository's ${name}; refusing to continue`);
    }
  }
}

function freePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.listen(0, "127.0.0.1", () => {
      const port = server.address().port;
      server.close(() => resolve(port));
    });
    server.on("error", reject);
  });
}

function pidAlive(pid) {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

async function serverUp(port) {
  try {
    await fetch(`http://127.0.0.1:${port}${BASE_URL}`, { signal: AbortSignal.timeout(2000) });
    return true;
  } catch {
    return false;
  }
}

const delay = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

async function waitForServer(port, logPath, timeout = 180) {
  const deadline = Date.now() + timeout * 1000;
  while (Date.now() < deadline) {
    if (await serverUp(port)) return;
    await delay(250);
  }
  let tail = "";
  if (fs.existsSync(logPath)) {
    const lines = fs.readFileSync(logPath, "utf8").split(/\r?\n/);
    tail = lines.slice(-40).join("\n");
  }
  throw new Error(`dashboard server did not start within ${timeout}s; last log lines:\n${tail}`);
}

async function ensureServer(dashboard, requestedPort) {
  const state = loadState(dashboard);
  const logPath = path.join(dashboard, "dev.log");
  if (state.pid && state.dashboard === path.resolve(dashboard)) {
    if (typeof state.pid === "number" && pidAlive(state.pid) && typeof state.port === "number") {
      if (await serverUp(state.port)) {
        return { pid: state.pid, port: state.port, reused: true, url: `http://127.0.0.1:${state.port}${BASE_URL}` };
      }
    }
  }
  const port = typeof requestedPort === "number" && requestedPort > 0 ? requestedPort : await freePort();
  fs.mkdirSync(path.dirname(logPath), { recursive: true });
  const log = fs.openSync(logPath, "a");
  const proc = spawn(
    "npm",
    ["--prefix", dashboard, "run", "dev", "--", "-H", "127.0.0.1", "-p", String(port)],
    {
      cwd: dashboard,
      stdio: ["ignore", log, log],
      detached: true,
      env: { ...process.env, NEXT_TELEMETRY_DISABLED: "1" },
    },
  );
  proc.unref();
  const newState = {
    ...state,
    schema: STATE_SCHEMA,
    dashboard: path.resolve(dashboard),
    pid: proc.pid,
    port,
    url: `http://127.0.0.1:${port}${BASE_URL}`,
    started_at: nowIso(),
  };
  saveState(dashboard, newState);
  try {
    await waitForServer(port, logPath);
  } catch (error) {
    await stopServer(dashboard);
    throw error;
  }
  return { pid: proc.pid, port, reused: false, url: newState.url };
}

function processGroupAlive(pid) {
  try {
    process.kill(-pid, 0);
    return true;
  } catch {
    return pidAlive(pid);
  }
}

function signalProcessGroup(pid, signal) {
  try {
    process.kill(-pid, signal);
    return true;
  } catch {
    try {
      process.kill(pid, signal);
      return true;
    } catch {
      return false;
    }
  }
}

async function stopServer(dashboard) {
  const state = loadState(dashboard);
  const pid = state.pid;
  const stopped = typeof pid === "number" && pid > 0;
  let forced = false;
  if (stopped && processGroupAlive(pid)) {
    signalProcessGroup(pid, "SIGTERM");
    const deadline = Date.now() + 3000;
    while (processGroupAlive(pid) && Date.now() < deadline) {
      await delay(50);
    }
    if (processGroupAlive(pid)) {
      forced = signalProcessGroup(pid, "SIGKILL");
    }
  }
  delete state.pid;
  delete state.port;
  delete state.url;
  saveState(dashboard, state);
  return { stopped, forced };
}

function openBrowser(url) {
  let command = process.platform === "darwin" ? "open" : "xdg-open";
  if (process.platform === "win32") {
    command = "start";
    const proc = spawn("cmd", ["/c", "start", "", url], { detached: true, stdio: "ignore" });
    proc.unref();
    return;
  }
  try {
    const proc = spawn(command, [url], { detached: true, stdio: "ignore" });
    proc.unref();
  } catch {
    /* browser opening must never fail the run */
  }
}

function stageBuild(dashboard, repo, manifest, templateDir, force) {
  const state = loadState(dashboard);
  const shellSig = shellSignature(templateDir, repo, manifest);
  scaffoldApp(dashboard, templateDir, repo, manifest, force || state.shell_sig !== shellSig);
  const routePlan = plan(repo, manifest);
  if (routePlan.problems.length) {
    for (const problem of routePlan.problems) console.log(`problem: ${problem}`);
    console.log("route plan has errors; fix the manifest or document tree before starting");
    throw new Error("route plan has errors");
  }
  const contentDir = path.join(dashboard, "content");
  const staging = path.join(contentDir, ".staging");
  const stageDocs = path.join(staging, "docs");
  const stageAssets = path.join(staging, "public", "docs-assets");
  fs.rmSync(staging, { recursive: true, force: true });
  fs.mkdirSync(stageDocs, { recursive: true });
  try {
    const ledger = buildLedger(includedDocuments(repo, manifest));
    ledger.assets = collectAssetMap(repo);
    const converted = convertDocuments(repo, manifest, ledger, stageDocs);
    const meta = metaPlans(ledger, manifest);
    for (const [folder, item] of Object.entries(meta)) {
      const metaPath = path.join(stageDocs, item.path);
      fs.mkdirSync(path.dirname(metaPath), { recursive: true });
      fs.writeFileSync(metaPath, dumpJson({ title: item.title, pages: item.pages }), "utf8");
    }
    const copied = copyAssets(repo, stageAssets, converted.assets_needed);
    const validation = validateBuild(repo, manifest, stageDocs, stageAssets);
    for (const warning of validation.warnings) console.log(`  warning: ${warning}`);
    if (!validation.ok) {
      for (const error of validation.errors) console.log(`  error: ${error}`);
      throw new Error("dashboard validation failed; previous dashboard left in place");
    }
    swapStage(dashboard, stageDocs, stageAssets);
    fs.rmSync(staging, { recursive: true, force: true });
    return { converted: converted.converted, copied, validation };
  } catch (error) {
    fs.rmSync(staging, { recursive: true, force: true });
    console.log("dashboard was NOT opened: the documentation failed the dashboard build; run /docforge-revise to fix it, then `dashboard start` again");
    throw error;
  }
}

async function cmdStart(args, dashboard, manifest, templateDir) {
  const shellSig = shellSignature(templateDir, args.repo, manifest);
  let renderSig = renderSignature(args.repo, manifest);
  if (args.plan_only) {
    const metadataReport = reconcileMetadata(args.repo, manifest, true);
    const routePlan = plan(args.repo, manifest);
    console.log(`metadata (dry-run): ${metadataReport.counts.reconciled} to reconcile, ${metadataReport.counts.unchanged} unchanged, ${metadataReport.counts.errors} errors`);
    for (const page of routePlan.pages) {
      console.log(`  ${page.doc_id.padEnd(32)} ${page.source_path.padEnd(48)} -> ${page.url}`);
    }
    console.log(`${routePlan.pages.length} pages in ${routePlan.folder_count} folders; ${routePlan.problems.length} problems`);
    for (const problem of routePlan.problems) console.log(`  problem: ${problem}`);
    console.log(`render_sig: ${renderSig}`);
    console.log(`shell_sig: ${shellSig}`);
    const ok = routePlan.problems.length === 0 && metadataReport.counts.errors === 0;
    return ok ? 0 : 1;
  }

  const metadataReport = reconcileMetadata(args.repo, manifest);
  console.log(`metadata: ${metadataReport.counts.reconciled} reconciled, ${metadataReport.counts.unchanged} unchanged`);
  const scanResult = scan(args.repo, manifest);
  if (scanResult.problems.length) {
    console.log(`scan: ${scanResult.problems.length} problems found:`);
    for (const problem of scanResult.problems) {
      const who = problem.doc ? `${problem.doc}: ` : "";
      console.log(`  [${problem.kind}] ${who}${problem.detail}`);
    }
    console.log("you should revise again: run /docforge-revise to fix the documentation before relying on this dashboard");
  } else {
    console.log("scan: 0 problems");
  }
  // Reconcile rewrites frontmatter, so the render signature must be computed
  // after it: the stored signature must describe the exact bytes a rebuild
  // would consume.
  renderSig = renderSignature(args.repo, manifest);

  const state = loadState(dashboard);
  const built = fs.existsSync(path.join(dashboard, "content", "docs", "index.mdx"));
  const needsRender = args.force || state.render_sig !== renderSig || !built;
  if (needsRender) {
    const result = stageBuild(dashboard, args.repo, manifest, templateDir, args.force);
    const newState = {
      ...state,
      schema: STATE_SCHEMA,
      dashboard: path.resolve(dashboard),
      render_sig: renderSig,
      shell_sig: shellSig,
      built_at: nowIso(),
    };
    saveState(dashboard, newState);
    console.log(`converted ${result.converted.length} documents; copied ${result.copied.length} assets`);
  } else {
    console.log("signature unchanged: dashboard is up to date");
  }

  if (!args.skip_install && !fs.existsSync(path.join(dashboard, "node_modules"))) {
    ensureDependencies(dashboard, args.repo);
  }

  const server = await ensureServer(dashboard, args.port);
  console.log(`dashboard: ${server.url} (reused=${server.reused})`);
  if (!args.no_open) openBrowser(server.url);
  console.log("dashboard server running in the background; stop it with `dashboard stop`");
  return 0;
}

async function cmdScan(args, manifest) {
  const result = scan(args.repo, manifest);
  if (args.json) {
    console.log(dumpJson(result));
    return result.problems.length ? 1 : 0;
  }
  if (result.problems.length === 0) {
    console.log("scan: 0 problems; the documentation is ready to render");
    return 0;
  }
  console.log(`scan: ${result.problems.length} problems found:`);
  for (const problem of result.problems) {
    const who = problem.doc ? `${problem.doc}: ` : "";
    console.log(`  [${problem.kind}] ${who}${problem.detail}`);
  }
  console.log("you should revise again: run /docforge-revise to fix the documentation, then `dashboard start` again");
  return 1;
}

async function cmdStatus(args, dashboard, manifest, templateDir) {
  const docs = includedDocuments(args.repo, manifest);
  const state = loadState(dashboard);
  const renderSig = renderSignature(args.repo, manifest);
  const running = Boolean(
    state.pid && typeof state.port === "number" && pidAlive(state.pid) && (await serverUp(state.port)),
  );
  const result = {
    dashboard,
    exists: fs.existsSync(dashboard),
    render_sig: {
      current: renderSig,
      stored: state.render_sig || null,
      match: state.render_sig === renderSig,
    },
    server: {
      running,
      port: running ? state.port : null,
      url: running ? state.url : null,
    },
    counts: { included_docs: docs.length },
    built_at: state.built_at || null,
  };
  if (args.json) console.log(dumpJson(result));
  else {
    console.log(`dashboard: ${result.dashboard}`);
    console.log(`exists: ${result.exists}  render signature match: ${result.render_sig.match}`);
    console.log(`server: ${result.server.running ? `running on ${result.server.url}` : "not running"}`);
    console.log(`included documents: ${result.counts.included_docs}`);
  }
  return 0;
}

async function cmdStop(args, dashboard) {
  const result = await stopServer(dashboard);
  console.log(`stopped: ${result.stopped ? "True" : "False"}`);
  return 0;
}

function parseArgs(argv) {
  const args = {
    repo: ".",
    manifest: null,
    dashboard: null,
    json: false,
    command: null,
    force: false,
    plan_only: false,
    no_open: false,
    skip_install: false,
    port: 0,
  };
  const positional = [];
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--repo") args.repo = argv[++i];
    else if (arg === "--manifest") args.manifest = argv[++i];
    else if (arg === "--dashboard") args.dashboard = argv[++i];
    else if (arg === "--json") args.json = true;
    else if (arg === "--force") args.force = true;
    else if (arg === "--plan-only") args.plan_only = true;
    else if (arg === "--no-open") args.no_open = true;
    else if (arg === "--skip-install") args.skip_install = true;
    else if (arg === "--port") args.port = parseInt(argv[++i], 10) || 0;
    else if (arg.startsWith("-")) throw new Error(`unknown flag: ${arg}`);
    else positional.push(arg);
  }
  if (positional.length !== 1) throw new Error("expected exactly one subcommand: start, status, stop");
  args.command = positional[0];
  return args;
}

async function main() {
  let args;
  try {
    args = parseArgs(process.argv.slice(2));
  } catch (error) {
    process.stderr.write(`error: ${error.message}\n`);
    return 2;
  }
  const repo = path.resolve(args.repo);
  const manifestPath = args.manifest ? path.resolve(args.manifest) : path.join(repo, ".docforge", "manifest.json");
  const dashboard = args.dashboard ? path.resolve(args.dashboard) : path.join(repo, ".docforge", "dashboard");
  args.repo = repo;
  args.manifest = manifestPath;
  args.dashboard = dashboard;
  const templateDir = path.join(fs.realpathSync(__dirname), "..", "template");
  let manifest = {};
  if (args.command === "start" || args.command === "status" || args.command === "scan") {
    try {
      manifest = loadManifest(manifestPath);
    } catch (error) {
      return fail(error.message);
    }
  }
  try {
    switch (args.command) {
      case "scan":
        return await cmdScan(args, manifest);
      case "start":
        return await cmdStart(args, dashboard, manifest, templateDir);
      case "status":
        return await cmdStatus(args, dashboard, manifest, templateDir);
      case "stop":
        return await cmdStop(args, dashboard);
      default:
        return 2;
    }
  } catch (error) {
    return fail(error.message);
  }
}

module.exports = {
  main,
  renderSignature,
  shellSignature,
  plan,
  includedDocuments,
  buildLedger,
  convertBody,
  headingAnchors,
  metaPlans,
  reconcileMetadata,
  validateBuild,
  treeFiles,
  gitRemoteUrl,
  titleFor,
  sha256Bytes,
};

if (require.main === module) {
  main().then((code) => process.exit(code));
}
