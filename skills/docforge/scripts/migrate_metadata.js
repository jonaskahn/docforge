#!/usr/bin/env node
"use strict";
/* Migrate Docforge manifest 3.0 / provenance 1.0 metadata to 3.1 / 2.0 YAML.
 *
 * Converts schema 1.0 and schema-less legacy frontmatter (including pre-schema
 * `doc` / `graph_snapshot` shapes) while preserving section evidence. When a
 * document cannot be converted to complete provenance 2.0 (missing or
 * unparseable frontmatter, conversion failure, or incomplete result for a
 * written document), write a best-effort scaffold, mark the document
 * `in_progress` for agent regeneration, and report `failed`.
 */

const fs = require("fs");
const path = require("path");
const { fail, loadManifest } = require("./_util.js");
const pf = require("./provenance_frontmatter.js");

const MANIFEST_CURRENT = "3.1";
const MANIFEST_LEGACY = "3.0";
const MARKDOWN_EXCEPTIONS = new Set(["AGENTS.md", "CLAUDE.md", "CLAUDE.local.md"]);
const WRITTEN = new Set(["generated", "needs_review", "complete"]);
const SCALAR_FIELDS = ["doc_id", "path", "generated_at", "tier", "target_depth"];
const MANIFEST_LOAD = {
  allowedVersions: [MANIFEST_CURRENT, MANIFEST_LEGACY],
  unsupportedHint: "older manifests are unsupported",
};

function needsProvenanceMigration(provenance) {
  if (!provenance || typeof provenance !== "object" || Array.isArray(provenance)) return false;
  if (!("schema" in provenance)) return false;
  if (
    provenance.schema === pf.SCHEMA_VERSION
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

function failDocument(repo, doc, manifest, dryRun, reason, options = {}) {
  const filePath = path.join(repo, ...doc.path.split("/"));
  const text = options.text != null ? options.text : fs.readFileSync(filePath, "utf8");
  const body = bodyForRewrite(text);
  const generated = options.provenance && typeof options.provenance === "object"
    ? options.provenance
    : provenanceFromManifest(doc, manifest);
  const demoted = markForAgentRegen(doc);
  let detail = `${reason}; agent must regenerate provenance`;
  if (demoted) detail += "; status -> in_progress";
  const result = { doc: doc.path, action: "failed", detail };
  if (!dryRun) {
    fs.writeFileSync(filePath, pf.emitYaml(generated) + body.replace(/^\n+/, ""), "utf8");
  }
  doc.provenance = generated;
  return result;
}

function regeneratePlanned(repo, doc, manifest, dryRun, reason, text) {
  const filePath = path.join(repo, ...doc.path.split("/"));
  const body = bodyForRewrite(text);
  const generated = provenanceFromManifest(doc, manifest);
  const result = {
    doc: doc.path,
    action: "regenerate",
    detail: `${reason}; wrote provenance ${pf.SCHEMA_VERSION} scaffold from manifest`,
  };
  if (!dryRun) {
    fs.writeFileSync(filePath, pf.emitYaml(generated) + body.replace(/^\n+/, ""), "utf8");
  }
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
  const filePath = path.join(repo, ...doc.path.split("/"));
  const result = { doc: doc.path, action: "migrate", detail };
  if (!dryRun) {
    fs.writeFileSync(filePath, pf.rewriteFrontmatter(text, migrated), "utf8");
  }
  doc.provenance = migrated;
  return result;
}

function migrateDocumentFile(repo, doc, manifest, dryRun, requireComplete = null) {
  const result = { doc: doc.path, action: "skip", detail: "" };
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
    result.detail = "already schema 2.0";
    return result;
  }
  if ((parsed.state !== "ok" && parsed.state !== "obsolete") || !parsed.provenance) {
    if (mustComplete) {
      return failDocument(repo, doc, manifest, dryRun, `unsupported state ${parsed.state}`, { text });
    }
    return regeneratePlanned(repo, doc, manifest, dryRun, `unsupported state ${parsed.state}`, text);
  }
  if (
    parsed.provenance.schema !== pf.SCHEMA_VERSION
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

function migrateManifestObject(manifest, demoteIncomplete = false) {
  let changed = false;
  if (manifest.version === MANIFEST_LEGACY) {
    manifest.version = MANIFEST_CURRENT;
    changed = true;
  }
  for (const doc of manifest.documents || []) {
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
  migrate,
  ensureMigrated,
  loadManifest,
  needsProvenanceMigration,
  provenanceFromManifest,
  provenanceGaps,
  markForAgentRegen,
};
