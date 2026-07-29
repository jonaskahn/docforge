#!/usr/bin/env node
"use strict";
/* Migrate Docforge manifest 3.0 / provenance 1.0 metadata to 3.1 / 2.0 YAML.
 *
 * When a document cannot be converted (missing, unparseable, or legacy
 * frontmatter), regenerate a fresh provenance-2.0 YAML scaffold from the
 * manifest entry and keep the Markdown body.
 */

const fs = require("fs");
const path = require("path");
const pf = require("./provenance_frontmatter.js");

const MANIFEST_CURRENT = "3.1";
const MANIFEST_LEGACY = "3.0";
const MARKDOWN_EXCEPTIONS = new Set(["AGENTS.md", "CLAUDE.md", "CLAUDE.local.md"]);

function fail(message, code = 1) {
  console.error(`error: ${message}`);
  return code;
}

function loadManifest(target) {
  if (!fs.existsSync(target) || !fs.statSync(target).isFile()) {
    throw new Error(`manifest not found: ${target}`);
  }
  const data = JSON.parse(fs.readFileSync(target, "utf8"));
  if (data.version !== MANIFEST_CURRENT && data.version !== MANIFEST_LEGACY) {
    throw new Error(
      `manifest must use version ${MANIFEST_CURRENT} or ${MANIFEST_LEGACY}: ${target}; older manifests are unsupported`,
    );
  }
  return data;
}

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

function provenanceFromManifest(doc, manifest) {
  const project = manifest.project && typeof manifest.project === "object" ? manifest.project : {};
  const embedded = doc.provenance && typeof doc.provenance === "object" ? doc.provenance : {};
  const graph = embedded.graph && typeof embedded.graph === "object" ? embedded.graph : {};
  const generated = pf.scaffoldProvenance(
    doc.id || embedded.doc_id || "<DOC_ID>",
    doc.path || embedded.path || "<DOCUMENT_PATH>",
    {
      tier: String(embedded.tier || project.tier || "<TIER>"),
      target_depth: String(embedded.target_depth || doc.target_depth || "<TARGET_DEPTH>"),
      provider: String(graph.provider || "<GRAPH_PROVIDER>"),
      flow: String(graph.flow || "<FLOW_CAPABILITY>"),
      generated_at: String(embedded.generated_at || "<GENERATED_AT>"),
    },
  );
  if (
    Array.isArray(embedded.sections)
    && embedded.sections.length
    && (embedded.schema === pf.SCHEMA_VERSION
      || embedded.schema === pf.LEGACY_SCHEMA
      || "tool_version" in embedded)
  ) {
    try {
      return pf.migrateV1ToV2(embedded);
    } catch {
      // fall through to scaffold
    }
  }
  return generated;
}

function regenerateDocument(repo, doc, manifest, dryRun, reason) {
  const filePath = path.join(repo, ...doc.path.split("/"));
  const text = fs.readFileSync(filePath, "utf8");
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

function migrateDocumentFile(repo, doc, manifest, dryRun) {
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
  const text = fs.readFileSync(filePath, "utf8");
  const parsed = pf.parseFrontmatter(text);
  if (parsed.state === "missing" || parsed.state === "unparseable" || parsed.state === "legacy") {
    const reasons = {
      missing: "missing provenance",
      unparseable: "unparseable provenance",
      legacy: "legacy provenance without schema",
    };
    return regenerateDocument(repo, doc, manifest, dryRun, reasons[parsed.state]);
  }
  if (parsed.state === "ok" && !needsProvenanceMigration(parsed.provenance)) {
    result.detail = "already schema 2.0";
    return result;
  }
  if ((parsed.state !== "ok" && parsed.state !== "obsolete") || !parsed.provenance) {
    return regenerateDocument(repo, doc, manifest, dryRun, `unsupported state ${parsed.state}`);
  }
  if (
    parsed.provenance.schema !== pf.SCHEMA_VERSION
    && parsed.provenance.schema !== pf.LEGACY_SCHEMA
    && !("tool_version" in parsed.provenance)
  ) {
    return regenerateDocument(
      repo,
      doc,
      manifest,
      dryRun,
      `unsupported schema ${parsed.provenance.schema}`,
    );
  }
  const { body } = pf.splitFrontmatter(text);
  let migrated;
  try {
    migrated = pf.migrateV1ToV2(parsed.provenance, body);
  } catch (error) {
    return regenerateDocument(repo, doc, manifest, dryRun, `conversion failed: ${error.message}`);
  }
  result.action = "migrate";
  result.detail = `schema ${parsed.provenance.schema} -> ${pf.SCHEMA_VERSION}`;
  if (!dryRun) {
    fs.writeFileSync(filePath, pf.rewriteFrontmatter(text, migrated), "utf8");
  }
  doc.provenance = migrated;
  return result;
}

function migrateManifestObject(manifest) {
  let changed = false;
  if (manifest.version === MANIFEST_LEGACY) {
    manifest.version = MANIFEST_CURRENT;
    changed = true;
  }
  for (const doc of manifest.documents || []) {
    const provenance = doc.provenance;
    if (needsProvenanceMigration(provenance)) {
      try {
        doc.provenance = pf.migrateV1ToV2(provenance);
      } catch {
        doc.provenance = provenanceFromManifest(doc, manifest);
      }
      changed = true;
    } else if (!provenance || typeof provenance !== "object") {
      doc.provenance = provenanceFromManifest(doc, manifest);
      changed = true;
    }
  }
  return changed;
}

function migrate(repo, manifestPath, dryRun) {
  const manifest = loadManifest(manifestPath);
  const reports = [];
  const objectChanged = migrateManifestObject(manifest);
  reports.push({
    doc: manifestPath,
    action: objectChanged ? "migrate" : "skip",
    detail: objectChanged
      ? `manifest version -> ${MANIFEST_CURRENT}; provenance objects normalized`
      : `manifest already ${manifest.version}`,
  });
  for (const doc of manifest.documents || []) {
    reports.push(migrateDocumentFile(repo, doc, manifest, dryRun));
  }
  if (!dryRun) {
    migrateManifestObject(manifest);
    fs.writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
  }
  return {
    reports,
    changed: reports.some((item) => item.action === "migrate" || item.action === "regenerate"),
  };
}

function ensureMigrated(repo, manifestPath) {
  migrate(repo, manifestPath, false);
  return loadManifest(manifestPath);
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
    const missing = reports.filter((item) => item.action === "missing");
    if (args.report || args.dryRun) {
      console.log(JSON.stringify({ changed, results: reports }, null, 2));
    } else {
      console.log(`Migrated ${migrated} metadata targets; regenerated ${regenerated}.`);
      for (const item of missing) {
        console.log(`MISSING  ${item.doc}  (${item.detail})`);
      }
      for (const item of reports) {
        if (item.action === "regenerate") {
          console.log(`REGENERATED  ${item.doc}  (${item.detail})`);
        }
      }
    }
    return missing.length ? 1 : 0;
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
};
