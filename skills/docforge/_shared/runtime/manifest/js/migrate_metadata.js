#!/usr/bin/env node
"use strict";
/* Migrate Docforge manifest metadata to 3.3 / provenance 2.0.
 *
 * Upgrades manifest 3.2 / provenance 2.0 (seeding each document's
 * catalog-owned `description` and the project's `provenance_storage`, then
 * moving inline frontmatter into `.docforge/provenance/` sidecars when
 * storage is `json`) and manifest 3.1 / provenance 2.0, plus manifest
 * 3.0 / provenance 1.0 (converting schema 1.0 and schema-less legacy
 * frontmatter, including pre-schema `doc` / `graph_snapshot` shapes, while
 * preserving section evidence), and re-registers any older legacy manifest —
 * 1.1 (`project_context` / `document_groups`), 2.0 (flat `documents` with
 * overlay profiles), or any other pre-3.0 shape — as 3.3: written documents
 * are adopted as `generated` with provenance 2.0, bodies preserved, and plan
 * entries kept. When a document cannot be converted to complete provenance
 * 2.0 (missing or unparseable frontmatter, conversion failure, or incomplete
 * result for a written document), write a best-effort scaffold, mark the
 * document `in_progress` for agent regeneration, and report `failed`.
 */

const fs = require("fs");
const path = require("path");
const { dumpJson, fail, loadManifest } = require("../../common/js/_util.js");
const pf = require("../../common/js/provenance_frontmatter.js");
const store = require("../../common/js/provenance_store.js");
const { SPECIAL_DOC_OUTPUTS } = require("../../common/js/special_files.js");
const queryCatalog = require("../../catalog/js/query_catalog.js");

const MANIFEST_CURRENT = "3.3";
const MANIFEST_IN_PLACE = ["3.3", "3.2", "3.1", "3.0"];
const MARKDOWN_EXCEPTIONS = SPECIAL_DOC_OUTPUTS;
const WRITTEN = new Set(["generated", "needs_review", "complete"]);
const SCALAR_FIELDS = ["doc_id", "path", "generated_at", "tier", "target_depth"];
const MANIFEST_LOAD = {
  allowedVersions: MANIFEST_IN_PLACE,
  unsupportedHint: "legacy manifests are re-registered by this command",
};
const LEGACY_TIER_MAP = { core: "spine", standard: "diligence", extended: "portfolio" };
const LEGACY_OVERLAY_MAP = {
  "business-analyst": ["audiences", "business-analysts"],
  "product-owner": ["audiences", "product-owners"],
  "agent-context": ["audiences", "coding-agents"],
  api: ["shapes", "api-service"],
  web: ["shapes", "web-app"],
  library: ["shapes", "library-sdk"],
  infrastructure: ["shapes", "infrastructure-platform"],
  "data-pipeline": ["shapes", "data-pipeline"],
};
const PROFILE_DIMENSIONS = ["shapes", "platforms", "frameworks", "concerns", "audiences"];
const STATUSES = ["planned", "in_progress", "generated", "needs_review", "complete", "skipped"];
const ORIGIN_KINDS = new Set([
  "tier", "shape", "platform", "framework", "concern", "audience", "condition", "dynamic", "ancestor",
]);

function needsProvenanceMigration(provenance) {
  if (!provenance || typeof provenance !== "object" || Array.isArray(provenance)) return false;
  if (!("schema" in provenance)) return false;
  if (
    pf.SUPPORTED_SCHEMA_VERSIONS.has(provenance.schema)
    && provenance.generator
    && !("tool_version" in provenance)
  ) {
    return false;
  }
  return true;
}

function bodyForRewrite(text) {
  const split = pf.splitFrontmatter(text);
  if (split.raw != null) return split.body;
  return text;
}

function migrationDefaults(doc, manifest) {
  const project = manifest.project && typeof manifest.project === "object" ? manifest.project : {};
  const embedded = doc.provenance && typeof doc.provenance === "object" ? doc.provenance : {};
  const graph = embedded.graph && typeof embedded.graph === "object" ? embedded.graph : {};
  return {
    doc_id: doc.id || embedded.doc_id || "<DOC_ID>",
    path: doc.path || embedded.path || embedded.doc || "<DOCUMENT_PATH>",
    tier: embedded.tier || project.tier || "<TIER>",
    target_depth: embedded.target_depth || doc.target_depth || "<TARGET_DEPTH>",
    provider: graph.provider || "<GRAPH_PROVIDER>",
    flow: graph.flow || "<FLOW_CAPABILITY>",
    generated_at: embedded.generated_at || "<GENERATED_AT>",
  };
}

function isConvertibleLegacy(provenance) {
  if (!provenance || typeof provenance !== "object" || Array.isArray(provenance)) return false;
  if ("schema" in provenance) return false;
  if (Array.isArray(provenance.sections) && provenance.sections.length) return true;
  if (typeof provenance.doc === "string" && provenance.doc) return true;
  if (typeof provenance.path === "string" && provenance.path) return true;
  if (typeof provenance.generated_at === "string" && provenance.generated_at) return true;
  return false;
}

function isScaffoldValue(value) {
  return typeof value !== "string" || !value || pf.SCAFFOLD_TOKEN.test(value);
}

function provenanceGaps(provenance) {
  if (!provenance || typeof provenance !== "object" || Array.isArray(provenance)) {
    return ["provenance"];
  }
  const gaps = [];
  for (const key of SCALAR_FIELDS) {
    if (isScaffoldValue(provenance[key])) gaps.push(key);
  }
  const generator = provenance.generator;
  if (!generator || typeof generator !== "object" || Array.isArray(generator)) {
    gaps.push("generator");
  } else {
    for (const key of ["name", "version"]) {
      if (isScaffoldValue(generator[key])) gaps.push(`generator.${key}`);
    }
  }
  const graph = provenance.graph;
  if (!graph || typeof graph !== "object" || Array.isArray(graph)) {
    gaps.push("graph");
  } else {
    if (isScaffoldValue(graph.provider)) gaps.push("graph.provider");
    if (isScaffoldValue(graph.flow) || !pf.FLOW_VALUES.has(graph.flow)) gaps.push("graph.flow");
  }
  const sections = provenance.sections;
  if (!Array.isArray(sections) || !sections.length) {
    gaps.push("sections");
  } else if (!sections.some((section) => (
    section
    && typeof section === "object"
    && !Array.isArray(section)
    && Array.isArray(section.sources)
    && section.sources.length
  ))) {
    gaps.push("section sources");
  }
  return gaps;
}

function markForAgentRegen(doc) {
  if (!WRITTEN.has(doc.status)) return false;
  doc.status = "in_progress";
  doc.audit = null;
  return true;
}

function provenanceFromManifest(doc, manifest) {
  const defaults = migrationDefaults(doc, manifest);
  const embedded = doc.provenance && typeof doc.provenance === "object" ? doc.provenance : {};
  const generated = pf.scaffoldProvenance(
    String(defaults.doc_id),
    String(defaults.path),
    {
      tier: String(defaults.tier),
      target_depth: String(defaults.target_depth),
      provider: String(defaults.provider),
      flow: String(defaults.flow),
      generated_at: String(defaults.generated_at),
    },
  );
  if (Array.isArray(embedded.sections) && embedded.sections.length) {
    try {
      return pf.migrateV1ToV2(embedded, "", defaults);
    } catch {
      // fall through to scaffold
    }
  } else if (isConvertibleLegacy(embedded)) {
    try {
      return pf.migrateV1ToV2(embedded, "", defaults);
    } catch {
      // fall through to scaffold
    }
  }
  return generated;
}

function publicFor(text, doc) {
  const { state, data } = store.readInline(text);
  const publicMeta = {};
  if (state === "ok") {
    for (const key of ["id", "title", "description"]) {
      if (typeof data[key] === "string" && data[key]) publicMeta[key] = data[key];
    }
  }
  for (const key of ["id", "title", "description"]) {
    if (!publicMeta[key] && doc[key]) publicMeta[key] = doc[key];
  }
  if (!publicMeta.id) publicMeta.id = doc.id || "";
  if (!publicMeta.title) {
    publicMeta.title = (doc.id || "document").replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  }
  return publicMeta;
}

function writeOutput(repo, doc, text, provenance, dryRun, storage) {
  const body = bodyForRewrite(text);
  const filePath = path.join(repo, ...doc.path.split("/"));
  if (storage === store.STORAGE_JSON) {
    if (!dryRun) {
      const entry = publicFor(text, doc);
      entry.provenance = provenance;
      store.writeEntry(repo, doc.path, entry);
      fs.writeFileSync(filePath, body.replace(/^\n+/, ""), "utf8");
    }
  } else if (!dryRun) {
    fs.writeFileSync(filePath, pf.emitYaml(provenance) + body.replace(/^\n+/, ""), "utf8");
  }
}

function failDocument(repo, doc, manifest, dryRun, reason, options = {}) {
  const filePath = path.join(repo, ...doc.path.split("/"));
  const text = options.text != null ? options.text : fs.readFileSync(filePath, "utf8");
  const generated = options.provenance && typeof options.provenance === "object"
    ? options.provenance
    : provenanceFromManifest(doc, manifest);
  const demoted = markForAgentRegen(doc);
  let detail = `${reason}; agent must regenerate provenance`;
  if (demoted) detail += "; status -> in_progress";
  const result = { doc: doc.path, action: "failed", detail };
  writeOutput(repo, doc, text, generated, dryRun, store.storageFor(manifest));
  doc.provenance = generated;
  return result;
}

function regeneratePlanned(repo, doc, manifest, dryRun, reason, text) {
  const generated = provenanceFromManifest(doc, manifest);
  const result = {
    doc: doc.path,
    action: "regenerate",
    detail: `${reason}; wrote provenance ${pf.SCHEMA_VERSION} scaffold from manifest`,
  };
  writeOutput(repo, doc, text, generated, dryRun, store.storageFor(manifest));
  doc.provenance = generated;
  return result;
}

function writeMigrated(repo, doc, manifest, text, migrated, dryRun, detail, requireComplete) {
  const gaps = requireComplete ? provenanceGaps(migrated) : [];
  if (gaps.length) {
    return failDocument(
      repo,
      doc,
      manifest,
      dryRun,
      `${detail}; incomplete after conversion (${gaps.join(", ")})`,
      { provenance: migrated, text },
    );
  }
  const result = { doc: doc.path, action: "migrate", detail };
  writeOutput(repo, doc, text, migrated, dryRun, store.storageFor(manifest));
  doc.provenance = migrated;
  return result;
}

function migrateDocumentFile(repo, doc, manifest, dryRun, requireComplete = null) {
  const result = { doc: doc.path, action: "skip", detail: "" };
  const storage = store.storageFor(manifest);
  if (doc.provenance_mode === "manifest" || MARKDOWN_EXCEPTIONS.has(path.basename(doc.path))) {
    result.detail = "manifest-only provenance";
    return result;
  }
  const filePath = path.join(repo, ...doc.path.split("/"));
  if (!fs.existsSync(filePath) || !fs.statSync(filePath).isFile() || !doc.path.endsWith(".md")) {
    result.action = "missing";
    result.detail = "file absent";
    return result;
  }
  const mustComplete = requireComplete == null ? WRITTEN.has(doc.status) : Boolean(requireComplete);
  if (storage === store.STORAGE_JSON) {
    const entry = store.entryFor(repo, doc.path);
    if (entry && entry.provenance && typeof entry.provenance === "object") {
      const defaults = migrationDefaults(doc, manifest);
      let provenance = entry.provenance;
      if (needsProvenanceMigration(provenance)) {
        try {
          provenance = pf.migrateV1ToV2(provenance, "", defaults);
        } catch {
          provenance = provenanceFromManifest(doc, manifest);
        }
        if (!dryRun) {
          const updated = { ...entry, provenance };
          store.writeEntry(repo, doc.path, updated);
        }
        doc.provenance = provenance;
        return { doc: doc.path, action: "migrate", detail: `sidecar schema -> ${pf.SCHEMA_VERSION}` };
      }
      if (mustComplete) {
        const gaps = provenanceGaps(provenance);
        if (gaps.length) {
          const demoted = markForAgentRegen(doc);
          let detail = `incomplete provenance 2.0 (${gaps.join(", ")}); agent must regenerate provenance`;
          if (demoted) detail += "; status -> in_progress";
          doc.provenance = provenance;
          return { doc: doc.path, action: "failed", detail };
        }
      }
      doc.provenance = provenance;
      result.detail = `already sidecar schema ${provenance.schema}`;
      return result;
    }
  }
  const text = fs.readFileSync(filePath, "utf8");
  const parsed = pf.parseFrontmatter(text);
  const defaults = migrationDefaults(doc, manifest);
  if (parsed.state === "missing" || parsed.state === "unparseable") {
    const reasons = {
      missing: "missing provenance",
      unparseable: "unparseable provenance",
    };
    if (mustComplete) {
      return failDocument(repo, doc, manifest, dryRun, reasons[parsed.state], { text });
    }
    return regeneratePlanned(repo, doc, manifest, dryRun, reasons[parsed.state], text);
  }
  if (parsed.state === "legacy" && parsed.provenance) {
    if (isConvertibleLegacy(parsed.provenance)) {
      const { body } = pf.splitFrontmatter(text);
      let migrated;
      try {
        migrated = pf.migrateV1ToV2(parsed.provenance, body, defaults);
      } catch (error) {
        return failDocument(
          repo,
          doc,
          manifest,
          dryRun,
          `legacy conversion failed: ${error.message}`,
          { text },
        );
      }
      return writeMigrated(
        repo,
        doc,
        manifest,
        text,
        migrated,
        dryRun,
        `legacy schema-less -> ${pf.SCHEMA_VERSION}`,
        mustComplete,
      );
    }
    if (mustComplete) {
      return failDocument(repo, doc, manifest, dryRun, "legacy provenance without schema", { text });
    }
    return regeneratePlanned(repo, doc, manifest, dryRun, "legacy provenance without schema", text);
  }
  if (parsed.state === "ok" && !needsProvenanceMigration(parsed.provenance)) {
    if (mustComplete) {
      const gaps = provenanceGaps(parsed.provenance);
      if (gaps.length) {
        return failDocument(
          repo,
          doc,
          manifest,
          dryRun,
          `incomplete provenance 2.0 (${gaps.join(", ")})`,
          { provenance: parsed.provenance, text },
        );
      }
    }
    doc.provenance = parsed.provenance;
    if (storage === store.STORAGE_JSON) {
      if (dryRun) {
        return { doc: doc.path, action: "migrate", detail: "inline -> sidecar" };
      }
      const action = store.moveInlineToSidecar(repo, doc, storage);
      return {
        doc: doc.path,
        action: action === "moved" ? "migrate" : "skip",
        detail: action === "moved" ? "inline -> sidecar" : action,
      };
    }
    result.detail = `already schema ${parsed.provenance.schema}`;
    return result;
  }
  if ((parsed.state !== "ok" && parsed.state !== "obsolete") || !parsed.provenance) {
    if (mustComplete) {
      return failDocument(repo, doc, manifest, dryRun, `unsupported state ${parsed.state}`, { text });
    }
    return regeneratePlanned(repo, doc, manifest, dryRun, `unsupported state ${parsed.state}`, text);
  }
  if (
    !pf.SUPPORTED_SCHEMA_VERSIONS.has(parsed.provenance.schema)
    && parsed.provenance.schema !== pf.LEGACY_SCHEMA
    && !("tool_version" in parsed.provenance)
  ) {
    const reason = `unsupported schema ${parsed.provenance.schema}`;
    if (mustComplete) return failDocument(repo, doc, manifest, dryRun, reason, { text });
    return regeneratePlanned(repo, doc, manifest, dryRun, reason, text);
  }
  const { body } = pf.splitFrontmatter(text);
  let migrated;
  try {
    migrated = pf.migrateV1ToV2(parsed.provenance, body, defaults);
  } catch (error) {
    return failDocument(
      repo,
      doc,
      manifest,
      dryRun,
      `conversion failed: ${error.message}`,
      { text },
    );
  }
  return writeMigrated(
    repo,
    doc,
    manifest,
    text,
    migrated,
    dryRun,
    `schema ${parsed.provenance.schema} -> ${pf.SCHEMA_VERSION}`,
    mustComplete,
  );
}

function seedDescriptions(docs, maps) {
  const seeded = [];
  for (const doc of docs || []) {
    if (doc.description) continue;
    const definition = matchDefinition(
      maps,
      String(doc.id || ""),
      doc.type,
      String(doc.path || ""),
    );
    const summary = (definition && definition.summary) || "";
    if (typeof summary === "string" && summary) {
      doc.description = summary;
      seeded.push(String(doc.id || ""));
    }
  }
  return seeded;
}

function migrateManifestObject(manifest, demoteIncomplete = false) {
  let changed = false;
  if (manifest.version === "3.2" || manifest.version === "3.1" || manifest.version === "3.0") {
    manifest.version = MANIFEST_CURRENT;
    changed = true;
  }
  if (manifest.project && typeof manifest.project === "object" && !manifest.project.provenance_storage) {
    manifest.project.provenance_storage = store.STORAGE_JSON;
    changed = true;
  }
  const docs = manifest.documents || [];
  if (docs.some((doc) => !doc.description)) {
    if (seedDescriptions(docs, loadCatalogMaps()).length) changed = true;
  }
  for (const doc of docs) {
    const provenance = doc.provenance;
    const defaults = migrationDefaults(doc, manifest);
    if (needsProvenanceMigration(provenance)) {
      try {
        doc.provenance = pf.migrateV1ToV2(provenance, "", defaults);
      } catch {
        doc.provenance = provenanceFromManifest(doc, manifest);
      }
      changed = true;
    } else if (isConvertibleLegacy(provenance)) {
      try {
        doc.provenance = pf.migrateV1ToV2(provenance, "", defaults);
      } catch {
        doc.provenance = provenanceFromManifest(doc, manifest);
      }
      changed = true;
    } else if (!provenance || typeof provenance !== "object") {
      doc.provenance = provenanceFromManifest(doc, manifest);
      changed = true;
    }
    if (demoteIncomplete && WRITTEN.has(doc.status) && provenanceGaps(doc.provenance).length) {
      if (markForAgentRegen(doc)) changed = true;
    }
  }
  return changed;
}

function migrate(repo, manifestPath, dryRun) {
  const raw = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
    throw new Error(`manifest must be a JSON object: ${manifestPath}`);
  }
  if (!MANIFEST_IN_PLACE.includes(raw.version)) {
    return migrateLegacy(repo, manifestPath, raw, dryRun);
  }
  const manifest = loadManifest(manifestPath, MANIFEST_LOAD);
  const reports = [];
  const requireComplete = {};
  for (const doc of manifest.documents || []) {
    if (typeof doc.id === "string") requireComplete[doc.id] = WRITTEN.has(doc.status);
  }
  const objectChanged = migrateManifestObject(manifest, false);
  reports.push({
    doc: manifestPath,
    action: objectChanged ? "migrate" : "skip",
    detail: objectChanged
      ? `manifest version -> ${MANIFEST_CURRENT}; provenance objects normalized`
      : `manifest already ${manifest.version}`,
  });
  for (const doc of manifest.documents || []) {
    const mustComplete = Object.prototype.hasOwnProperty.call(requireComplete, doc.id)
      ? requireComplete[doc.id]
      : WRITTEN.has(doc.status);
    reports.push(migrateDocumentFile(repo, doc, manifest, dryRun, mustComplete));
  }
  if (!dryRun) {
    migrateManifestObject(manifest, true);
    fs.writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
  }
  return {
    reports,
    changed: reports.some((item) => (
      item.action === "migrate" || item.action === "regenerate" || item.action === "failed"
    )),
  };
}

function ensureMigrated(repo, manifestPath) {
  migrate(repo, manifestPath, false);
  return loadManifest(manifestPath, MANIFEST_LOAD);
}

// ---------------------------------------------------------------------------
// Legacy manifest re-registration (any pre-3.0 version)
// ---------------------------------------------------------------------------

function legacyProfiles(overlays) {
  const profiles = {};
  for (const dimension of PROFILE_DIMENSIONS) profiles[dimension] = [];
  for (const overlay of overlays) {
    const mapping = LEGACY_OVERLAY_MAP[overlay];
    if (mapping) {
      const [dimension, profileId] = mapping;
      if (!profiles[dimension].includes(profileId)) profiles[dimension].push(profileId);
    }
  }
  if (profiles.audiences.length === 0) profiles.audiences = ["engineers", "beginners"];
  return profiles;
}

function legacyProject(manifest, repo) {
  const ctx = manifest.project_context;
  const proj = manifest.project;
  const base = ctx && typeof ctx === "object" && !Array.isArray(ctx)
    ? ctx
    : proj && typeof proj === "object" && !Array.isArray(proj)
      ? proj
      : {};
  let tier = base.tier;
  if (LEGACY_TIER_MAP[tier]) tier = LEGACY_TIER_MAP[tier];
  if (!["spine", "diligence", "portfolio"].includes(tier)) tier = "spine";
  let overlays = base.overlays;
  if (!Array.isArray(overlays)) overlays = [];
  let profiles = legacyProfiles(overlays);
  if (proj && typeof proj === "object" && proj.profiles && typeof proj.profiles === "object") {
    const merged = {};
    for (const dimension of PROFILE_DIMENSIONS) {
      merged[dimension] = Array.isArray(proj.profiles[dimension])
        ? proj.profiles[dimension].map(String)
        : [];
    }
    if (merged.audiences.length === 0) merged.audiences = profiles.audiences;
    profiles = merged;
  }
  let name = ctx && typeof ctx === "object" ? ctx.repo_name || "" : "";
  name = name || (proj && typeof proj === "object" ? proj.name : null) || path.basename(repo);
  return { tier, profiles, name, root: repo };
}

function legacyDocuments(manifest) {
  const out = [];
  const groups = manifest.document_groups;
  if (Array.isArray(groups)) {
    for (const groupObj of groups) {
      const group = groupObj && typeof groupObj === "object" ? groupObj.group : null;
      const docs = groupObj && typeof groupObj === "object" ? groupObj.documents : null;
      for (const doc of docs || []) {
        if (doc && typeof doc === "object" && !Array.isArray(doc)) {
          out.push([doc, group || "reference"]);
        }
      }
    }
    return out;
  }
  const docs = manifest.documents;
  if (Array.isArray(docs)) {
    for (const doc of docs) {
      if (doc && typeof doc === "object" && !Array.isArray(doc)) {
        out.push([doc, doc.group || "reference"]);
      }
    }
  }
  return out;
}

function legacySections(doc) {
  if (Array.isArray(doc.sections)) return doc.sections;
  const provenance = doc.provenance;
  if (provenance && typeof provenance === "object" && !Array.isArray(provenance)) {
    if (Array.isArray(provenance.sections)) return provenance.sections;
  }
  return [];
}

function legacyEmbeddedProvenance(doc) {
  const provenance = doc.provenance;
  if (
    provenance && typeof provenance === "object" && !Array.isArray(provenance)
    && pf.SUPPORTED_SCHEMA_VERSIONS.has(provenance.schema) && typeof provenance.doc_id === "string"
  ) {
    return provenance;
  }
  return null;
}

function normalizeLegacyOrigins(origins) {
  const out = [];
  for (const origin of origins || []) {
    if (!origin || typeof origin !== "object" || Array.isArray(origin)) continue;
    const kind = origin.kind;
    const originId = origin.id;
    if (kind === "overlay") {
      const mapping = LEGACY_OVERLAY_MAP[originId];
      if (!mapping) continue;
      const [dimension, profileId] = mapping;
      out.push({ kind: dimension === "shapes" ? "shape" : "audience", id: profileId });
      continue;
    }
    if (ORIGIN_KINDS.has(kind) && typeof originId === "string") {
      out.push({ kind, id: originId });
    }
  }
  return out;
}

function loadCatalogMaps() {
  const byId = {};
  const byType = {};
  const byPath = {};
  for (const row of queryCatalog.loadIndex().document_types) {
    const detail = queryCatalog.loadType(row.id);
    byId[detail.id] = detail;
    (byType[detail.type] = byType[detail.type] || []).push(detail);
    if (detail.path) byPath[detail.path] = detail;
  }
  return { byId, byType, byPath };
}

function matchDefinition(maps, docId, legacyType, docPath) {
  if (maps.byId[docId]) return maps.byId[docId];
  const candidates = maps.byType[legacyType] || [];
  if (candidates.length === 1) return candidates[0];
  return maps.byPath[docPath] || null;
}

function probeCodeGraph(repo) {
  if (fs.existsSync(path.join(repo, ".ua")) && fs.statSync(path.join(repo, ".ua")).isDirectory()) {
    return { provider: "understand-anything", flow: "native" };
  }
  if (fs.existsSync(path.join(repo, ".gitnexus")) && fs.statSync(path.join(repo, ".gitnexus")).isDirectory()) {
    return { provider: "gitnexus", flow: "native" };
  }
  if (fs.existsSync(path.join(repo, ".codegraph")) && fs.statSync(path.join(repo, ".codegraph")).isDirectory()) {
    return { provider: "codegraph", flow: "none" };
  }
  return { provider: "none", flow: "none" };
}

function provenanceFromLegacySections(sections, docId, docPath, generatedAt, tier, graph, targetDepth, version) {
  const normalized = pf.normalizeSections(
    sections
      .filter((section) => section && typeof section === "object" && !Array.isArray(section))
      .map((section) => ({ id: section.id, sources: section.sources })),
  );
  return {
    schema: pf.SCHEMA_VERSION,
    doc_id: docId,
    path: docPath,
    generated_at: generatedAt,
    generator: { name: pf.GENERATOR_NAME, version },
    tier,
    target_depth: targetDepth,
    graph: { provider: graph.provider, flow: graph.flow },
    sections: normalized,
  };
}

function normalizeEmbedded(embedded) {
  return { ...embedded, sections: pf.normalizeSections(embedded.sections) };
}

function provenanceForLegacyFile(repo, docId, docPath, sections, graph, generatedAt, tier, targetDepth, version, embedded) {
  const target = path.join(repo, docPath);
  const text = fs.readFileSync(target, "utf8");
  const parsed = pf.parseFrontmatter(text);
  const defaults = { doc_id: docId, path: docPath, generated_at: generatedAt, tier, target_depth: targetDepth };
  if (parsed.state === "ok" && parsed.provenance && typeof parsed.provenance === "object") {
    return { provenance: parsed.provenance, detail: `already schema ${parsed.provenance.schema}`, needsRewrite: false };
  }
  if ((parsed.state === "legacy" || parsed.state === "obsolete") && parsed.provenance) {
    try {
      const migrated = pf.migrateV1ToV2(parsed.provenance, bodyForRewrite(text), defaults);
      return { provenance: migrated, detail: `frontmatter migrated to schema ${pf.SCHEMA_VERSION}`, needsRewrite: true };
    } catch (error) {
      return {
        provenance: embedded ? normalizeEmbedded(embedded) : provenanceFromLegacySections(
          sections, docId, docPath, generatedAt, tier, graph, targetDepth, version,
        ),
        detail: `frontmatter conversion failed (${error.message}); provenance from manifest`,
        needsRewrite: true,
      };
    }
  }
  if (parsed.state === "unparseable") {
    return {
      provenance: embedded ? normalizeEmbedded(embedded) : provenanceFromLegacySections(
        sections, docId, docPath, generatedAt, tier, graph, targetDepth, version,
      ),
      detail: "frontmatter unparseable; provenance from manifest",
      needsRewrite: true,
    };
  }
  if (embedded) {
    return { provenance: normalizeEmbedded(embedded), detail: "provenance 2.0 carried from manifest", needsRewrite: true };
  }
  if (Array.isArray(sections) && sections.length) {
    return {
      provenance: provenanceFromLegacySections(sections, docId, docPath, generatedAt, tier, graph, targetDepth, version),
      detail: "provenance from manifest sections",
      needsRewrite: true,
    };
  }
  return {
    provenance: pf.scaffoldProvenance(docId, docPath, {
      tier,
      target_depth: targetDepth,
      provider: graph.provider,
      flow: graph.flow,
      generated_at: generatedAt,
    }),
    detail: "no provenance evidence; scaffolded",
    needsRewrite: true,
  };
}

function buildLegacyEntry(definition, legacyDoc, docPath, group, status, provenance, generatedAt, tier, writeOrder, version) {
  const id = String(legacyDoc.id || "");
  let provenanceMode = legacyDoc.provenance_mode;
  if (provenanceMode !== "sections" && provenanceMode !== "manifest") {
    provenanceMode = MARKDOWN_EXCEPTIONS.has(path.basename(docPath)) ? "manifest" : "sections";
  }
  const targetDepth = legacyDoc.target_depth || (definition && definition.target_depth) || "orientation";
  let selection = legacyDoc.selection;
  if (!selection || typeof selection !== "object" || Array.isArray(selection)) selection = {};
  let origins = normalizeLegacyOrigins(selection.origins);
  if (origins.length === 0) origins = [{ kind: "dynamic", id: `legacy-v${version}` }];
  const evidence = Array.isArray(selection.evidence) ? selection.evidence : [];
  let requires = legacyDoc.requires;
  if (!Array.isArray(requires)) requires = [...((definition && definition.requires) || [])];
  let writeOrderValue = legacyDoc.write_order;
  if (typeof writeOrderValue !== "number") {
    writeOrderValue = (definition && definition.write_order) || writeOrder;
  }
  const base = {
    id,
    title: legacyDoc.title || (definition && definition.title)
      || id.replace(/[-_]/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
    path: docPath,
    group,
    selection: { origins, evidence },
    status,
    requires,
    scaffold_template: legacyDoc.scaffold_template || legacyDoc.template
      || (definition && definition.template_file) || "generic.md",
    instruction_file: Object.prototype.hasOwnProperty.call(legacyDoc, "instruction_file")
      ? legacyDoc.instruction_file
      : (definition && definition.instruction_file) || null,
    target_depth: targetDepth,
    write_order: writeOrderValue,
    provenance_mode: provenanceMode,
    audit_profile: legacyDoc.audit_profile || (definition && definition.audit_profile) || "standard",
    provenance: provenance || pf.scaffoldProvenance(id, docPath, {
      tier,
      target_depth: targetDepth,
      generated_at: generatedAt,
    }),
    audit: null,
  };
  if (legacyDoc.type) {
    base.type = legacyDoc.type;
  } else if (definition) {
    base.type = definition.type || "generic";
  } else {
    base.type = "generic";
  }
  const contractRevision = legacyDoc.contract_revision || (definition && definition.contract_revision);
  if (contractRevision) base.contract_revision = contractRevision;
  return base;
}

function migrateLegacy(repo, manifestPath, manifest, dryRun) {
  const version = String(manifest.version || "unknown");
  const reports = [];
  const maps = loadCatalogMaps();
  const project = legacyProject(manifest, repo);
  const generatedAt = manifest.generated_at || new Date().toISOString();
  const graph = probeCodeGraph(repo);
  const newManifest = {
    version: MANIFEST_CURRENT,
    generated_at: generatedAt,
    project: {
      name: project.name,
      root: project.root,
      tier: project.tier,
      profiles: project.profiles,
      provenance_storage: store.STORAGE_JSON,
    },
    discovery: [],
    discovery_gate: null,
    documents: [],
    metadata: {},
  };
  let adopted = 0;
  let keptPlanned = 0;
  let skipped = 0;
  let failed = 0;
  let fallback = 0;
  let writeOrder = 1000;
  for (const [legacyDoc, group] of legacyDocuments(manifest)) {
    const docId = String(legacyDoc.id || "");
    const docPath = String(legacyDoc.path || "");
    let legacyStatus = legacyDoc.status || "planned";
    if (!STATUSES.includes(legacyStatus)) legacyStatus = "planned";
    const sections = legacySections(legacyDoc);
    const embedded = legacyEmbeddedProvenance(legacyDoc);
    const definition = matchDefinition(maps, docId, legacyDoc.type, docPath);
    writeOrder += 1;
    if (legacyStatus === "skipped") {
      newManifest.documents.push(
        buildLegacyEntry(definition, legacyDoc, docPath, group, "skipped", null, generatedAt, project.tier, writeOrder, version),
      );
      skipped += 1;
      reports.push({ doc: docPath, action: "skip", detail: "kept skipped" });
      continue;
    }
    if (!docPath || !fs.existsSync(path.join(repo, docPath)) || !fs.statSync(path.join(repo, docPath)).isFile()) {
      if (WRITTEN.has(legacyStatus)) {
        failed += 1;
        reports.push({ doc: docPath, action: "failed", detail: "file absent; agent must regenerate" });
      }
      newManifest.documents.push(
        buildLegacyEntry(definition, legacyDoc, docPath, group, "planned", null, generatedAt, project.tier, writeOrder, version),
      );
      keptPlanned += 1;
      continue;
    }
    if (!WRITTEN.has(legacyStatus)) {
      newManifest.documents.push(
        buildLegacyEntry(definition, legacyDoc, docPath, group, legacyStatus, null, generatedAt, project.tier, writeOrder, version),
      );
      keptPlanned += 1;
      reports.push({ doc: docPath, action: "migrate", detail: `kept ${legacyStatus}` });
      continue;
    }
    const targetDepth = legacyDoc.target_depth || (definition && definition.target_depth) || "orientation";
    const { provenance, detail, needsRewrite } = provenanceForLegacyFile(
      repo, docId, docPath, sections, graph, generatedAt, project.tier, targetDepth, version, embedded,
    );
    let status = legacyStatus === "complete" ? "generated" : legacyStatus;
    if (!WRITTEN.has(status)) status = "generated";
    if (!definition) fallback += 1;
    newManifest.documents.push(
      buildLegacyEntry(definition, legacyDoc, docPath, group, status, provenance, generatedAt, project.tier, writeOrder, version),
    );
    adopted += 1;
    const entryDetail = definition
      ? `adopted as ${status} (${detail})`
      : `adopted as ${status} without catalog match (${detail})`;
    reports.push({ doc: docPath, action: "migrate", detail: entryDetail });
    if (needsRewrite && WRITTEN.has(status) && docPath.endsWith(".md") && !MARKDOWN_EXCEPTIONS.has(path.basename(docPath)) && !dryRun) {
      const target = path.join(repo, docPath);
      const text = fs.readFileSync(target, "utf8");
      writeOutput(repo, legacyDoc, text, provenance, dryRun, store.STORAGE_JSON);
    }
  }
  if (!dryRun) {
    fs.writeFileSync(manifestPath, dumpJson(newManifest), "utf8");
  }
  let manifestLabel;
  try {
    manifestLabel = path.relative(repo, manifestPath);
  } catch {
    manifestLabel = manifestPath;
  }
  reports.unshift({
    doc: manifestLabel,
    action: "migrate",
    detail: `manifest version -> ${MANIFEST_CURRENT}; re-registered from ${version} ` +
      `(${adopted} adopted, ${keptPlanned} planned/in-progress, ${skipped} skipped, ${failed} failed, ${fallback} generic)`,
  });
  return { reports, changed: Boolean(adopted || keptPlanned || failed) };
}

function main(argv) {
  const args = { repo: null, manifest: null, dryRun: false, report: false };
  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--repo") args.repo = argv[++i];
    else if (arg === "--manifest") args.manifest = argv[++i];
    else if (arg === "--dry-run") args.dryRun = true;
    else if (arg === "--report") args.report = true;
    else if (arg === "--help" || arg === "-h") {
      console.log("Usage: node migrate_metadata.js --repo <repo> [--manifest <path>] [--dry-run] [--report]");
      return 0;
    } else {
      return fail(`unknown argument: ${arg}`, 2);
    }
  }
  if (!args.repo) return fail("--repo is required", 2);
  const repo = path.resolve(args.repo);
  if (!fs.existsSync(repo) || !fs.statSync(repo).isDirectory()) {
    return fail(`not a directory: ${args.repo}`, 2);
  }
  let manifestPath = args.manifest
    ? path.resolve(repo, args.manifest)
    : path.join(repo, ".docforge", "manifest.json");
  if (args.manifest && !fs.existsSync(manifestPath) && path.isAbsolute(args.manifest)) {
    manifestPath = args.manifest;
  }
  try {
    const { reports, changed } = migrate(repo, manifestPath, args.dryRun);
    const migrated = reports.filter((item) => item.action === "migrate").length;
    const regenerated = reports.filter((item) => item.action === "regenerate").length;
    const failed = reports.filter((item) => item.action === "failed");
    const missing = reports.filter((item) => item.action === "missing");
    if (args.report || args.dryRun) {
      console.log(JSON.stringify({ changed, results: reports }, null, 2));
    } else {
      console.log(
        `Migrated ${migrated} metadata targets; regenerated ${regenerated}; failed ${failed.length}.`,
      );
      for (const item of missing) {
        console.log(`MISSING  ${item.doc}  (${item.detail})`);
      }
      for (const item of reports) {
        if (item.action === "regenerate") {
          console.log(`REGENERATED  ${item.doc}  (${item.detail})`);
        } else if (item.action === "failed") {
          console.log(`FAILED  ${item.doc}  (${item.detail})`);
        }
      }
    }
    return (missing.length || failed.length) ? 1 : 0;
  } catch (error) {
    return fail(error.message, 2);
  }
}

if (require.main === module) {
  process.exit(main(process.argv));
}

module.exports = {
  main,
  migrate,
  ensureMigrated,
  loadManifest,
  needsProvenanceMigration,
  provenanceFromManifest,
  provenanceGaps,
  markForAgentRegen,
  MANIFEST_CURRENT,
};
