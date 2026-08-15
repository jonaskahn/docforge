#!/usr/bin/env node
"use strict";
/* Folder-mirrored JSON sidecar store for Docforge document metadata.
 * The public frontmatter identity (id, title, description) and
 * `docforge_provenance` live in one git-tracked JSON file per docs folder
 * under `.docforge/provenance/`; generated markdown carries no frontmatter at
 * all. Documents written before the sidecar store still carry inline
 * frontmatter — this module reads that layout so `migrate_metadata` can move
 * it, but nothing writes it. Mirrors common/python/provenance_store.py.
 */

const fs = require("fs");
const path = require("path");
const pf = require("./provenance_frontmatter.js");

const SIDECAR_SCHEMA = "1.0";
const STORAGE_JSON = "json";
const SIDECAR_DIRNAME = "provenance";
const PUBLIC_FIELDS = ["id", "title", "description"];

class SidecarError extends Error {
  constructor(message) {
    super(message);
    this.name = "SidecarError";
  }
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

// A schema-1.0-era document may carry JSON frontmatter rather than
// restricted YAML — provenance_frontmatter.js's parseFrontmatter already
// special-cases this; mirror it here so a document without a sidecar entry
// is classified the same way regardless of which reader resolves it.
function readInline(text) {
  const { raw } = pf.splitFrontmatter(text);
  if (raw == null) return { state: "missing", data: null };
  let data;
  const stripped = raw.replace(/^\s+/, "");
  if (stripped.startsWith("{")) {
    try {
      data = JSON.parse(raw);
    } catch {
      return { state: "unparseable", data: null };
    }
  } else {
    try {
      data = pf.parseYamlMapping(raw);
    } catch {
      return { state: "unparseable", data: null };
    }
  }
  if (!data || typeof data !== "object" || Array.isArray(data)) {
    return { state: "missing", data: null };
  }
  return { state: "ok", data };
}

function schemaState(provenance) {
  // Explicit classification of a provenance object's schema:
  // ok — current schema (2.0/2.1, no tool_version);
  // legacy — no schema key at all (pre-schema shape);
  // obsolete — schema 1.0, tool_version, or an unsupported schema;
  // missing — not a provenance object. Always on; no opt-in/opt-out.
  if (!provenance || typeof provenance !== "object" || Array.isArray(provenance) || !Object.keys(provenance).length) {
    return "missing";
  }
  if (!("schema" in provenance)) return "legacy";
  if (!pf.SUPPORTED_SCHEMA_VERSIONS.has(provenance.schema) || "tool_version" in provenance) {
    return "obsolete";
  }
  return "ok";
}

function readDocMetadata(repo, doc) {
  // Read one document's metadata, sidecar first. State is explicit: ok,
  // inline (current-schema frontmatter on a document not yet migrated),
  // legacy, obsolete, missing, unparseable. Old-schema metadata is never
  // folded into ok and is never silently moved.
  const docPath = (doc && doc.path) || "";
  const target = path.join(repo, docPath);
  const entry = entryFor(repo, docPath);
  if (entry && entry.provenance && typeof entry.provenance === "object") {
    return {
      state: schemaState(entry.provenance),
      public: publicOf(entry),
      provenance: entry.provenance,
      source: "sidecar",
    };
  }
  // No sidecar entry: the document may predate the store and still carry
  // frontmatter. Report that explicitly so migration can move it.
  if (fs.existsSync(target)) {
    const text = fs.readFileSync(target, "utf8");
    const { state, data } = readInline(text);
    if (state === "ok" && data.docforge_provenance && typeof data.docforge_provenance === "object") {
      const schema = schemaState(data.docforge_provenance);
      return {
        state: schema === "ok" ? "inline" : schema,
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

function moveInlineToSidecar(repo, doc) {
  // Move a document's inline frontmatter into the folder sidecar and strip
  // it from the markdown. Only current-schema provenance moves — old-schema
  // metadata is reported explicitly (legacy-schema / obsolete-schema) and
  // left untouched for migrate_metadata to convert first.
  const docPath = (doc && doc.path) || "";
  const target = path.join(repo, docPath);
  if (!fs.existsSync(target)) return "missing";
  const text = fs.readFileSync(target, "utf8");
  const { state, data } = readInline(text);
  if (state === "unparseable") return "unparseable";
  if (state === "missing" || !data.docforge_provenance || typeof data.docforge_provenance !== "object") {
    return "no-frontmatter";
  }
  const schema = schemaState(data.docforge_provenance);
  if (schema === "legacy") return "legacy-schema";
  if (schema === "obsolete") return "obsolete-schema";
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

module.exports = {
  SIDECAR_SCHEMA,
  STORAGE_JSON,
  SIDECAR_DIRNAME,
  PUBLIC_FIELDS,
  SidecarError,
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
  schemaState,
  readDocMetadata,
  publicOf,
  publicFromManifest,
  moveInlineToSidecar,
};
