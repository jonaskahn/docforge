#!/usr/bin/env node
"use strict";
/** Validate the Docforge catalog, schemas, templates, peers, and release metadata. */

const fs = require("fs");
const path = require("path");
const { readJson } = require("../common/_util.js");
const pf = require("../common/provenance_frontmatter.js");
const { SPECIAL_DOC_SOURCES } = require("../common/special_files.js");
const queryCatalog = require("../catalog/query_catalog.js");
const generateIndexes = require("./generate_indexes.js");

const SKILL_ROOT = path.resolve(__dirname, "..", "..");
const REPO_ROOT = path.resolve(SKILL_ROOT, "..", "..", "..");
const EXCEPTIONS = SPECIAL_DOC_SOURCES;
const CATALOG_VERSION = "2.8.0";
const PUBLIC_CONTRACTS = {
  manage_manifest: ["init", "add", "set", "status", "audit", "reconcile", "--repo", "--tier", "--shape", "--platform", "--framework", "--concern", "--audience", "--type", "--id", "--path", "--evidence", "--status", "--mode", "--verdict", "--report"],
  detect_profiles: ["--repo", "--json", "--emit-gate-pack", "confirmed", "candidate"],
  scaffold_docs: ["--repo", "--manifest", "--dry-run", "--document", "--audit", "--revise"],
  precheck_graph: ["--repo", "--need", "code", "flow"],
  check_staleness: ["--manifest", "--document", "--section", "--json", "--sync-provenance"],
  flow_index: ["harvest", "revise", "render", "organize", "emit", "apply", "--repo", "--gitnexus-export", "--main-limit", "--output", "--organization"],
  migrate_metadata: ["--repo", "--manifest", "--dry-run", "--report"],
  query_catalog: ["--tier", "--id", "--ids", "--profile", "--applicable", "--validate", "--category", "--route"],
  generate_indexes: ["--write", "--check"],
};

function validate() {
  const errors = [];
  const metadata = path.join(SKILL_ROOT, ".metadata");
  errors.push(...queryCatalog.validate());
  try {
    for (const target of generateIndexes.staleTargets()) {
      errors.push(`generated router is stale: ${path.relative(SKILL_ROOT, target)} (run generate_indexes --write)`);
    }
  } catch (error) {
    errors.push(`generate_indexes --check failed: ${error.message}`);
  }
  let catalog;
  try {
    catalog = queryCatalog.asLegacyCatalog();
  } catch (error) {
    errors.push(error.message);
    catalog = { version: null, documents: [], profiles: {}, tiers: [] };
  }
  const catalogSchema = readJson(path.join(metadata, "catalog-schema.json"));
  const manifestSchema = readJson(path.join(metadata, "manifest-schema.json"));
  const flowIndexSchema = readJson(path.join(metadata, "flow-index-schema.json"));
  const provenanceSchemaPath = path.join(metadata, "provenance-schema.json");
  if (!fs.existsSync(provenanceSchemaPath)) {
    errors.push("provenance-schema.json is missing");
  } else {
    const provenanceSchema = readJson(provenanceSchemaPath);
    if ((((provenanceSchema.properties || {}).schema || {}).const) !== pf.SCHEMA_VERSION) {
      errors.push("provenance schema must require schema 2.0");
    }
  }
  if (catalog.version !== CATALOG_VERSION) errors.push(`catalog version must be ${CATALOG_VERSION}`);
  if ((((catalogSchema.properties || {}).version || {}).const) !== CATALOG_VERSION) {
    errors.push("catalog schema version disagrees with catalog");
  }
  if (!fs.existsSync(path.join(metadata, "catalog", "index.json"))) {
    errors.push("split catalog index.json is missing");
  }
  if (fs.existsSync(path.join(metadata, "catalog.json"))) {
    errors.push("obsolete monolith catalog.json remains; use .metadata/catalog/");
  }
  if ((((manifestSchema.properties || {}).version || {}).const) !== "3.1") {
    errors.push("manifest schema must require version 3.1");
  }
  if ((((flowIndexSchema.properties || {}).version || {}).const) !== "1.1") {
    errors.push("flow index schema must require version 1.1");
  }
  const flowItem = ((((flowIndexSchema.properties || {}).flows || {}).items || {}).properties) || {};
  for (const field of ["display_name", "family", "doc_role", "composed_into", "doc_path"]) {
    if (!(field in flowItem)) errors.push(`flow index schema must define flow.${field}`);
  }
  const docRoles = ((flowItem.doc_role || {}).enum) || [];
  if (docRoles.length !== 3 || !["standalone", "member", "index_only"].every((item) => docRoles.includes(item))) {
    errors.push("flow index schema doc_role must be standalone|member|index_only");
  }
  const dimensions = ["shapes", "platforms", "frameworks", "concerns", "audiences"];
  const schemaProfileRequired = new Set(((((catalogSchema.properties || {}).profiles || {}).required) || []));
  const manifestProfileRequired = new Set(((((((manifestSchema.properties || {}).project || {}).properties || {}).profiles || {}).required) || []));
  if (schemaProfileRequired.size !== dimensions.length || dimensions.some((item) => !schemaProfileRequired.has(item))) {
    errors.push("catalog schema profile dimensions disagree with catalog");
  }
  if (manifestProfileRequired.size !== dimensions.length || dimensions.some((item) => !manifestProfileRequired.has(item))) {
    errors.push("manifest schema profile dimensions disagree with catalog");
  }
  for (const dimension of dimensions) {
    const definitions = (catalog.profiles || {})[dimension] || [];
    if (!definitions.length) errors.push(`${dimension}: profile registry must not be empty`);
    const orders = definitions.map((item) => item.order);
    if (new Set(orders).size !== orders.length || orders.some((item) => !Number.isInteger(item))) {
      errors.push(`${dimension}: profile order values must be unique integers`);
    }
    for (const item of definitions) {
      for (const signal of item.signals || []) {
        if (!["path", "content", "dependency"].includes(signal.kind)) {
          errors.push(`${dimension}/${item.id}: invalid signal kind`);
        }
        if (["path", "content"].includes(signal.kind) && (typeof signal.pattern !== "string" || !signal.pattern)) {
          errors.push(`${dimension}/${item.id}: signal needs a pattern`);
        }
        if (signal.kind === "content" && !signal.contains) {
          errors.push(`${dimension}/${item.id}: content signal needs contains`);
        }
        if (signal.kind === "dependency" && (!signal.ecosystem || !signal.name)) {
          errors.push(`${dimension}/${item.id}: dependency signal needs ecosystem and name`);
        }
        if (signal.strength != null && !["strong", "weak"].includes(signal.strength)) {
          errors.push(`${dimension}/${item.id}: signal strength must be strong|weak`);
        }
        if (signal.weight != null && (typeof signal.weight !== "number" || signal.weight <= 0 || signal.weight > 1)) {
          errors.push(`${dimension}/${item.id}: signal weight must be in (0, 1]`);
        }
      }
    }
  }
  const crossAliases = new Map();
  for (const dimension of dimensions) {
    for (const item of (catalog.profiles || {})[dimension] || []) {
      for (const name of [item.id, ...(item.aliases || [])]) {
        if (typeof name !== "string") continue;
        if (!crossAliases.has(name)) crossAliases.set(name, []);
        crossAliases.get(name).push(`${dimension}:${item.id}`);
      }
    }
  }
  for (const name of [...crossAliases.keys()].sort()) {
    const owners = crossAliases.get(name);
    if (owners.length > 1) errors.push(`cross-dimension profile name collision ${name}: ${owners.join(", ")}`);
  }
  for (const hint of catalog.cue_hints || []) {
    if (!hint || typeof hint !== "object" || !hint.cue || !hint.note) {
      errors.push("cue_hints entries require cue and note");
    }
  }
  const gateSchemaPath = path.join(metadata, "discovery-gate-schema.json");
  if (!fs.existsSync(gateSchemaPath)) errors.push("discovery-gate-schema.json is missing");
  else {
    const gateSchema = readJson(gateSchemaPath);
    if (!(((gateSchema.definitions || {}).judgment))) errors.push("discovery-gate-schema.json must define judgment");
    if (!(((gateSchema.definitions || {}).pack))) errors.push("discovery-gate-schema.json must define pack");
  }
  for (let index = 0; index < (catalog.documents || []).length; index++) {
    const doc = catalog.documents[index];
    const label = doc.id || `document[${index}]`;
    const selection = doc.selection || {};
    const obsolete = ["overlays", "include_if_overlay"].filter((field) => field in selection).sort();
    if (obsolete.length) errors.push(`${label}: obsolete selection fields: ${obsolete.join(", ")}`);
  }
  // Drive the template scan from the catalog itself (template_file paths
  // now vary by group/kind under content/) plus the two shared templates
  // with no catalog reference (audit-report, audience-deepdive).
  const templatePaths = new Set(
    queryCatalog
      .loadAllTypes()
      .map((detail) => detail.template_file)
      .filter((rel) => rel.endsWith(".md"))
      .map((rel) => path.join(SKILL_ROOT, rel)),
  );
  for (const name of ["audit-report.template.md", "audience-deepdive.template.md"]) {
    templatePaths.add(path.join(SKILL_ROOT, "content", "shared", name));
  }
  for (const templatePath of [...templatePaths].sort()) {
    const name = path.basename(templatePath);
    if (EXCEPTIONS.has(name)) continue;
    const text = fs.readFileSync(templatePath, "utf8");
    if (!text.startsWith("---\ndocforge_provenance:\n")) {
      errors.push(`${name}: provenance frontmatter must be YAML docforge_provenance at byte one`);
      continue;
    }
    const parsed = pf.parseFrontmatter(text);
    if (parsed.state !== "ok") {
      errors.push(`${name}: provenance frontmatter state is ${parsed.state}`);
      continue;
    }
    const provenance = parsed.provenance;
    if (!provenance || typeof provenance !== "object" || Array.isArray(provenance)) {
      errors.push(`${name}: provenance frontmatter is not valid YAML`);
      continue;
    }
    const missing = [...pf.PROVENANCE_FIELDS].filter((key) => !(key in provenance));
    const graph = provenance.graph;
    const generator = provenance.generator;
    if (missing.length || !graph || typeof graph !== "object" || !("provider" in graph) || !("flow" in graph)) {
      errors.push(`${name}: provenance frontmatter is missing required fields`);
    }
    if (!generator || typeof generator !== "object" || !("name" in generator) || !("version" in generator)) {
      errors.push(`${name}: provenance frontmatter is missing generator`);
    }
    if (provenance.schema !== pf.SCHEMA_VERSION || "graph_snapshot" in provenance) {
      errors.push(`${name}: provenance frontmatter must use schema 2.0`);
    }
  }
  const cliPy = path.join(SKILL_ROOT, "runtime", "cli", "python");
  const cliJs = path.join(SKILL_ROOT, "runtime", "cli", "js");
  const peerless = new Set(["split_catalog", "split_document_catalog"]);
  const py = new Set(
    fs.readdirSync(cliPy)
      .filter((name) => name.endsWith(".py"))
      .map((name) => path.basename(name, ".py"))
      .filter((name) => !peerless.has(name)),
  );
  const js = new Set(
    fs.readdirSync(cliJs)
      .filter((name) => name.endsWith(".js"))
      .map((name) => path.basename(name, ".js"))
      .filter((name) => !peerless.has(name)),
  );
  for (const name of [...py].filter((name) => !js.has(name)).sort()) errors.push(`missing Node peer for ${name}.py`);
  for (const name of [...js].filter((name) => !py.has(name)).sort()) errors.push(`missing Python peer for ${name}.js`);
  const runtimeRoot = path.join(SKILL_ROOT, "runtime");
  function findImpl(dir, filename, relativeParts = []) {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        if (entry.name === "cli" && relativeParts.length === 0) continue;
        const found = findImpl(full, filename, relativeParts.concat(entry.name));
        if (found) return found;
      } else if (entry.name === filename) {
        return full;
      }
    }
    return null;
  }
  for (const [name, tokens] of Object.entries(PUBLIC_CONTRACTS)) {
    for (const suffix of ["py", "js"]) {
      // CLI flags live in the runtime implementation; the cli/ launcher
      // is a thin re-export with no flag text.
      const fallback = path.join(suffix === "py" ? cliPy : cliJs, `${name}.${suffix}`);
      const source = findImpl(runtimeRoot, `${name}.${suffix}`) || fallback;
      const text = fs.readFileSync(source, "utf8");
      const missing = tokens.filter((token) => !text.includes(token));
      if (missing.length) errors.push(`${name}.${suffix}: missing CLI contract tokens: ${missing.join(", ")}`);
    }
  }
  const plugin = readJson(path.join(REPO_ROOT, ".claude-plugin", "plugin.json"));
  const market = readJson(path.join(REPO_ROOT, ".claude-plugin", "marketplace.json")).plugins[0];
  const versions = new Set([plugin.version, market.version, catalog.version]);
  if (versions.size !== 1 || !versions.has(CATALOG_VERSION)) {
    errors.push(`release versions disagree: ${[...versions].map(String).sort().join(", ")}`);
  }
  const skillText = fs.readFileSync(path.join(REPO_ROOT, "skills", "docforge", "SKILL.md"), "utf8");
  const skillMatch = skillText.match(/^description: (.+)$/m);
  const reviseText = fs.readFileSync(path.join(REPO_ROOT, "skills", "docforge-revise", "SKILL.md"), "utf8");
  const reviseMatch = reviseText.match(/^description: (.+)$/m);
  if (!skillMatch) errors.push("skills/docforge/SKILL.md missing description frontmatter");
  if (!reviseMatch) errors.push("skills/docforge-revise/SKILL.md missing description frontmatter");
  if (new Set([plugin.description, market.description, skillMatch ? skillMatch[1] : null]).size !== 1) {
    errors.push("package descriptions disagree (plugin, marketplace, docforge SKILL.md)");
  }
  if (fs.existsSync(path.join(REPO_ROOT, "meta.json"))) {
    errors.push("obsolete meta.json remains; Agent Skills install uses SKILL.md only");
  }
  const IGNORED_DIRS = new Set([".git", ".pytest_cache", "__pycache__", ".venv", "venv", "node_modules"]);
  function collectReadmes(dir, out) {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory() && !IGNORED_DIRS.has(entry.name)) collectReadmes(full, out);
      else if (entry.isFile() && entry.name === "README.md" && full !== path.join(REPO_ROOT, "README.md")) {
        out.push(path.relative(REPO_ROOT, full).split(path.sep).join("/"));
      }
    }
  }
  const readmes = []; collectReadmes(REPO_ROOT, readmes);
  if (readmes.length) errors.push(`nested README.md files are obsolete; use README.md: ${readmes.sort().join(", ")}`);
  const forbidden = new Set(["document" + "-templates.json", "generation" + "-status.json", "status" + "-schema.json", "template" + "-schema.json"]);
  const present = fs.readdirSync(metadata).filter((name) => forbidden.has(name)).sort();
  if (present.length) errors.push(`obsolete metadata files remain: ${present.join(", ")}`);
  const legacyConstants = ["SP" + "INE", "SPINE_" + "PLAN", "OVER" + "LAYS"];
  const duplicate = new RegExp(`\\b(${legacyConstants.join("|")})\\s*=`);
  function collectSourceFiles(dir, out, relativeParts = []) {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        if (entry.name === "cli" && relativeParts.length === 0) {
          collectSourceFiles(path.join(full, "python"), out, relativeParts.concat("cli", "python"));
          collectSourceFiles(path.join(full, "js"), out, relativeParts.concat("cli", "js"));
          continue;
        }
        collectSourceFiles(full, out, relativeParts.concat(entry.name));
      } else if (/\.(py|js)$/.test(entry.name)) {
        out.push(full);
      }
    }
  }
  const scannable = [];
  collectSourceFiles(runtimeRoot, scannable);
  for (const source of scannable.sort()) {
    if (duplicate.test(fs.readFileSync(source, "utf8"))) {
      errors.push(`${path.basename(source)}: duplicated registry constant`);
    }
  }
  return errors;
}

function main() {
  const args = process.argv.slice(2);
  if (args.some((arg) => !["-h", "--help"].includes(arg))) {
    console.error(`error: unknown option: ${args.find((arg) => !["-h", "--help"].includes(arg))}`);
    return 2;
  }
  if (args.length) {
    console.log("usage: validate_metadata.js");
    return 0;
  }
  const errors = validate();
  if (errors.length) {
    for (const error of errors) console.log(`ERROR  ${error}`);
    console.log(`\n${errors.length} metadata errors.`);
    return 1;
  }
  console.log("OK  catalog, schemas, templates, runtime peers, and package metadata agree.");
  return 0;
}

process.exit(main());
