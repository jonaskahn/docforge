#!/usr/bin/env node
"use strict";
/* Folder-mirrored JSON sidecar store for Docforge document metadata.
 * With `project.provenance_storage: json` (default) the public frontmatter
 * identity (id, title, description) and `docforge_provenance` live in one
 * git-tracked JSON file per docs folder under `.docforge/provenance/`; the
 * markdown files carry no frontmatter. With `markdown` storage the legacy
 * inline layout is kept. Mirrors common/python/provenance_store.py.
 */

const fs = require("fs");
const path = require("path");
const pf = require("./provenance_frontmatter.js");

const SIDECAR_SCHEMA = "1.0";
const STORAGE_JSON = "json";
const STORAGE_MARKDOWN = "markdown";
const SIDECAR_DIRNAME = "provenance";
const PUBLIC_FIELDS = ["id", "title", "description"];

class SidecarError extends Error {
  constructor(message) {
    super(message);
    this.name = "SidecarError";
  }
}

function storageFor(manifest) {
  const value = (manifest && manifest.project && manifest.project.provenance_storage) || null;
  return value === STORAGE_JSON || value === STORAGE_MARKDOWN ? value : STORAGE_JSON;
}

function sidecarRoot(repo) {
  return path.join(repo, ".docforge", SIDECAR_DIRNAME);
}

function folderOf(docPath) {
  const normalized = String(docPath).replace(/\\/g, "/");
  const parent = normalized.includes("/") ? normalized.slice(0, normalized.lastIndexOf("/")) : "";
  return parent === "." ? "" : parent;
}

function sidecarPath(repo, folder) {
  const name = folder ? `${folder}.json` : "root.json";
  return path.join(sidecarRoot(repo), name);
}

function readSidecar(repo, folder) {
  const target = sidecarPath(repo, folder);
  if (!fs.existsSync(target)) return null;
  let data;
  try {
    data = JSON.parse(fs.readFileSync(target, "utf8"));
  } catch (error) {
    throw new SidecarError(`invalid sidecar ${path.relative(repo, target)}: ${error.message}`);
  }
  if (!data || typeof data !== "object" || Array.isArray(data)
    || !data.files || typeof data.files !== "object" || Array.isArray(data.files)) {
    throw new SidecarError(`invalid sidecar shape: ${path.relative(repo, target)}`);
  }
  return data;
}

function writeSidecar(repo, folder, data) {
  const target = sidecarPath(repo, folder);
  const files = data && typeof data === "object" ? data.files : null;
  if (!files || typeof files !== "object" || Array.isArray(files) || Object.keys(files).length === 0) {
    if (fs.existsSync(target)) fs.unlinkSync(target);
    return;
  }
  fs.mkdirSync(path.dirname(target), { recursive: true });
  const payload = { schema: SIDECAR_SCHEMA, folder, files };
  fs.writeFileSync(target, JSON.stringify(payload, null, 2) + "\n", "utf8");
}

function fileNameOf(docPath) {
  const normalized = String(docPath).replace(/\\/g, "/");
  return normalized.includes("/") ? normalized.slice(normalized.lastIndexOf("/") + 1) : normalized;
}

function entryFor(repo, docPath) {
  const data = readSidecar(repo, folderOf(docPath));
  if (!data) return null;
  const entry = data.files[fileNameOf(docPath)];
  return entry && typeof entry === "object" && !Array.isArray(entry) ? entry : null;
}

function writeEntry(repo, docPath, entry) {
  const folder = folderOf(docPath);
  const name = fileNameOf(docPath);
  const data = readSidecar(repo, folder);
  const files = data ? { ...data.files } : {};
  files[name] = entry;
  writeSidecar(repo, folder, { files });
}

function removeEntry(repo, docPath) {
  const folder = folderOf(docPath);
  const name = fileNameOf(docPath);
  const data = readSidecar(repo, folder);
  if (!data || !(name in data.files)) return;
  const files = { ...data.files };
  delete files[name];
  writeSidecar(repo, folder, { files });
}

function readInline(text) {
  const { raw } = pf.splitFrontmatter(text);
  if (raw == null) return { state: "missing", data: null };
  let data;
  try {
    data = pf.parseYamlMapping(raw);
  } catch {
    return { state: "unparseable", data: null };
  }
  if (!data || typeof data !== "object" || Array.isArray(data)) {
    return { state: "missing", data: null };
  }
  return { state: "ok", data };
}

function readDocMetadata(repo, doc, storage) {
  const docPath = (doc && doc.path) || "";
  const target = path.join(repo, docPath);
  if (storage === STORAGE_JSON) {
    const entry = entryFor(repo, docPath);
    if (entry && entry.provenance && typeof entry.provenance === "object") {
      return {
        state: "ok",
        public: publicOf(entry),
        provenance: entry.provenance,
        source: "sidecar",
      };
    }
    if (fs.existsSync(target)) {
      const text = fs.readFileSync(target, "utf8");
      const { state, data } = readInline(text);
      if (state === "ok" && data.docforge_provenance && typeof data.docforge_provenance === "object") {
        return {
          state: "inline",
          public: publicOf(data),
          provenance: data.docforge_provenance,
          source: "markdown",
        };
      }
      if (state === "unparseable") {
        return { state: "unparseable", public: null, provenance: null, source: "markdown" };
      }
    }
    return { state: "missing", public: null, provenance: null, source: "sidecar" };
  }
  if (!fs.existsSync(target)) {
    return { state: "missing", public: null, provenance: null, source: "markdown" };
  }
  const text = fs.readFileSync(target, "utf8");
  const { state, data } = readInline(text);
  if (state === "unparseable") {
    return { state: "unparseable", public: null, provenance: null, source: "markdown" };
  }
  if (state === "ok" && data.docforge_provenance && typeof data.docforge_provenance === "object") {
    return {
      state: "ok",
      public: publicOf(data),
      provenance: data.docforge_provenance,
      source: "markdown",
    };
  }
  return { state: "missing", public: null, provenance: null, source: "markdown" };
}

function publicOf(data) {
  const publicMeta = {};
  for (const key of PUBLIC_FIELDS) {
    if (data && data[key]) publicMeta[key] = data[key];
  }
  return publicMeta;
}

function publicFromManifest(doc) {
  const title = doc.title || doc.id.replace(/-/g, " ").replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  const publicMeta = { id: doc.id, title };
  if (doc.description) publicMeta.description = doc.description;
  return publicMeta;
}

function moveInlineToSidecar(repo, doc, storage) {
  if (storage !== STORAGE_JSON) return "skip";
  const docPath = (doc && doc.path) || "";
  const target = path.join(repo, docPath);
  if (!fs.existsSync(target)) return "missing";
  const text = fs.readFileSync(target, "utf8");
  const { state, data } = readInline(text);
  if (state === "unparseable") return "unparseable";
  if (state === "missing" || !data.docforge_provenance || typeof data.docforge_provenance !== "object") {
    return "no-frontmatter";
  }
  const publicMeta = publicOf(data);
  if (!publicMeta.id) publicMeta.id = doc.id || "";
  if (!publicMeta.title) {
    publicMeta.title = doc.title || (doc.id || "document").replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  }
  if (!publicMeta.description && doc.description) publicMeta.description = doc.description;
  const entry = { ...publicMeta, provenance: data.docforge_provenance };
  writeEntry(repo, docPath, entry);
  const { body } = pf.splitFrontmatter(text);
  fs.writeFileSync(target, body.replace(/^\n+/, ""), "utf8");
  return "moved";
}

function moveSidecarToInline(repo, doc) {
  const docPath = (doc && doc.path) || "";
  const entry = entryFor(repo, docPath);
  if (!entry) return "no-sidecar";
  const publicMeta = publicOf(entry);
  const title = publicMeta.title || doc.title || doc.id || "document";
  const docId = publicMeta.id || doc.id || "";
  const frontmatter = pf.emitDocumentFrontmatter(docId, title, entry.provenance, publicMeta.description || null);
  const target = path.join(repo, docPath);
  let content = frontmatter;
  if (fs.existsSync(target)) {
    const text = fs.readFileSync(target, "utf8");
    const { body } = pf.splitFrontmatter(text);
    content = frontmatter + body.replace(/^\n+/, "");
  }
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, content, "utf8");
  removeEntry(repo, docPath);
  return "moved";
}

module.exports = {
  SIDECAR_SCHEMA,
  STORAGE_JSON,
  STORAGE_MARKDOWN,
  SIDECAR_DIRNAME,
  PUBLIC_FIELDS,
  SidecarError,
  storageFor,
  sidecarRoot,
  folderOf,
  sidecarPath,
  readSidecar,
  writeSidecar,
  fileNameOf,
  entryFor,
  writeEntry,
  removeEntry,
  readInline,
  readDocMetadata,
  publicOf,
  publicFromManifest,
  moveInlineToSidecar,
  moveSidecarToInline,
};
