#!/usr/bin/env node
"use strict";
/** Validate the Docforge catalog, schemas, templates, peers, and release metadata. */

const fs = require("fs");
const path = require("path");
const pf = require("./provenance_frontmatter.js");
const SKILL_ROOT = path.resolve(__dirname, "..");
const REPO_ROOT = path.resolve(SKILL_ROOT, "..", "..");
const REQUIRED = new Set(["id", "type", "path", "group", "selection", "scaffold_template", "requires", "target_depth", "write_order", "provenance_mode", "audit_profile"]);
const EXCEPTIONS = new Set(["agents-kernel.md", "claude-md.md", "claude-local-md.md"]);
const PUBLIC_CONTRACTS = {
  manage_manifest: ["init", "add", "set", "status", "audit", "--repo", "--tier", "--shape", "--platform", "--framework", "--concern", "--audience", "--type", "--id", "--path", "--status", "--mode", "--verdict", "--report"],
  detect_profiles: ["--repo", "--json", "--emit-gate-pack", "confirmed", "candidate"],
  scaffold_docs: ["--repo", "--manifest", "--dry-run", "--document", "--audit"],
  precheck_graph: ["--repo", "--need", "code", "flow"],
  check_staleness: ["--manifest", "--section", "--json", "--sync-provenance"],
  flow_index: ["harvest", "revise", "render", "organize", "emit", "apply", "--repo", "--gitnexus-export", "--main-limit", "--output", "--organization"],
  migrate_metadata: ["--repo", "--manifest", "--dry-run", "--report"],
};

function readJson(target) {
  return JSON.parse(fs.readFileSync(target, "utf8"));
}
function validate() {
  const errors = [];
  const metadata = path.join(SKILL_ROOT, ".metadata");
  const catalog = readJson(path.join(metadata, "catalog.json"));
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
  if (catalog.version !== "2.2.0") errors.push("catalog version must be 2.2.0");
  if ((((catalogSchema.properties || {}).version || {}).const) !== "2.2.0") errors.push("catalog schema version disagrees with catalog");
  if ((((manifestSchema.properties || {}).version || {}).const) !== "3.1") errors.push("manifest schema must require version 3.1");
  if ((((flowIndexSchema.properties || {}).version || {}).const) !== "1.1") errors.push("flow index schema must require version 1.1");
  const flowItem = ((((flowIndexSchema.properties || {}).flows || {}).items || {}).properties) || {};
  for (const field of ["display_name", "family", "doc_role", "composed_into", "doc_path"]) {
    if (!(field in flowItem)) errors.push(`flow index schema must define flow.${field}`);
  }
  const docRoles = ((flowItem.doc_role || {}).enum) || [];
  if (docRoles.length !== 3 || !["standalone", "member", "index_only"].every((item) => docRoles.includes(item))) {
    errors.push("flow index schema doc_role must be standalone|member|index_only");
  }
  const tiers = new Set(catalog.tiers.map((item) => item.id));
  const dimensions = ["shapes", "platforms", "frameworks", "concerns", "audiences"];
  const schemaProfileRequired = new Set(((((catalogSchema.properties || {}).profiles || {}).required) || []));
  const manifestProfileRequired = new Set(((((((manifestSchema.properties || {}).project || {}).properties || {}).profiles || {}).required) || []));
  if (schemaProfileRequired.size !== dimensions.length || dimensions.some((item) => !schemaProfileRequired.has(item))) errors.push("catalog schema profile dimensions disagree with catalog");
  if (manifestProfileRequired.size !== dimensions.length || dimensions.some((item) => !manifestProfileRequired.has(item))) errors.push("manifest schema profile dimensions disagree with catalog");
  const profileIds = {};
  for (const dimension of dimensions) {
    const definitions = (catalog.profiles || {})[dimension] || [];
    if (!definitions.length) errors.push(`${dimension}: profile registry must not be empty`);
    profileIds[dimension] = new Set(definitions.map((item) => item.id));
    if (profileIds[dimension].size !== definitions.length) errors.push(`${dimension}: duplicate profile id`);
    const orders = definitions.map((item) => item.order);
    if (new Set(orders).size !== orders.length || orders.some((item) => !Number.isInteger(item))) errors.push(`${dimension}: profile order values must be unique integers`);
    const names = new Map();
    for (const item of definitions) {
      for (const name of [item.id, ...(item.aliases || [])]) {
        if (typeof name !== "string" || !/^[a-z0-9][a-z0-9-]*$/.test(name)) errors.push(`${dimension}: invalid profile name ${name}`);
        else {
          if (names.has(name)) errors.push(`${dimension}: profile name collision ${name} between ${names.get(name)} and ${item.id}`);
          names.set(name, item.id);
        }
      }
      for (const signal of item.signals || []) {
        if (!["path", "content", "dependency"].includes(signal.kind)) errors.push(`${dimension}/${item.id}: invalid signal kind`);
        if (["path", "content"].includes(signal.kind) && (typeof signal.pattern !== "string" || !signal.pattern)) errors.push(`${dimension}/${item.id}: signal needs a pattern`);
        if (signal.kind === "content" && !signal.contains) errors.push(`${dimension}/${item.id}: content signal needs contains`);
        if (signal.kind === "dependency" && (!signal.ecosystem || !signal.name)) errors.push(`${dimension}/${item.id}: dependency signal needs ecosystem and name`);
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
  const groups = new Set(catalog.groups);
  const capabilities = new Set(catalog.capabilities);
  const staticIds = new Set();
  const staticPaths = new Set();
  const dynamicTypes = new Set();
  const catalogContract = fs.readFileSync(path.join(SKILL_ROOT, "references", "document-catalog.md"), "utf8");
  for (let index = 0; index < catalog.documents.length; index++) {
    const doc = catalog.documents[index];
    const label = doc.id || `document[${index}]`;
    const missing = [...REQUIRED].filter((field) => !(field in doc)).sort();
    if (missing.length) {
      errors.push(`${label}: missing fields: ${missing.join(", ")}`);
      continue;
    }
    const selection = doc.selection || {};
    const obsolete = ["overlays", "include_if_overlay"].filter((field) => field in selection).sort();
    if (obsolete.length) errors.push(`${label}: obsolete selection fields: ${obsolete.join(", ")}`);
    if (!groups.has(doc.group)) errors.push(`${label}: unknown group ${doc.group}`);
    if (!tiers.has(selection.min_tier)) errors.push(`${label}: unknown tier ${selection.min_tier}`);
    for (const [dimension, values] of Object.entries(selection.selectors || {})) {
      if (!profileIds[dimension]) errors.push(`${label}: unknown selector dimension ${dimension}`);
      else for (const value of values) if (!profileIds[dimension].has(value)) errors.push(`${label}: unknown ${dimension} selector ${value}`);
    }
    if ((((selection.selectors || {}).frameworks) || []).length) errors.push(`${label}: frameworks may tailor evidence but must not select documents`);
    for (const requirement of doc.requires || []) if (!capabilities.has(requirement)) errors.push(`${label}: unknown requirement ${requirement}`);
    if (!Number.isInteger(doc.write_order)) errors.push(`${label}: write_order must be an integer`);
    if (!catalogContract.includes(doc.type)) errors.push(`${label}: document type is missing from document-catalog.md`);
    if (!fs.existsSync(path.join(SKILL_ROOT, "assets", "templates", doc.scaffold_template))) errors.push(`${label}: missing template ${doc.scaffold_template}`);
    if (doc.instruction_file && !fs.existsSync(path.join(SKILL_ROOT, "instructions", doc.instruction_file))) errors.push(`${label}: missing instruction ${doc.instruction_file}`);
    if (selection.mode === "static") {
      if (staticIds.has(doc.id)) errors.push(`duplicate static id: ${doc.id}`);
      if (staticPaths.has(doc.path)) errors.push(`duplicate static path: ${doc.path}`);
      staticIds.add(doc.id);
      staticPaths.add(doc.path);
    } else if (selection.mode === "dynamic") {
      if (dynamicTypes.has(doc.type)) errors.push(`duplicate dynamic type: ${doc.type}`);
      dynamicTypes.add(doc.type);
    } else errors.push(`${label}: selection.mode must be static or dynamic`);
  }
  const templates = path.join(SKILL_ROOT, "assets", "templates");
  for (const name of fs.readdirSync(templates).filter((name) => name.endsWith(".md")).sort()) {
    if (EXCEPTIONS.has(name)) continue;
    const text = fs.readFileSync(path.join(templates, name), "utf8");
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
  const scripts = path.join(SKILL_ROOT, "scripts");
  const names = fs.readdirSync(scripts);
  const py = new Set(names.filter((name) => name.endsWith(".py")).map((name) => path.basename(name, ".py")));
  const js = new Set(names.filter((name) => name.endsWith(".js")).map((name) => path.basename(name, ".js")));
  for (const name of [...py].filter((name) => !js.has(name)).sort()) errors.push(`missing Node peer for ${name}.py`);
  for (const name of [...js].filter((name) => !py.has(name)).sort()) errors.push(`missing Python peer for ${name}.js`);
  for (const [name, tokens] of Object.entries(PUBLIC_CONTRACTS)) {
    for (const suffix of ["py", "js"]) {
      const text = fs.readFileSync(path.join(scripts, `${name}.${suffix}`), "utf8");
      const missing = tokens.filter((token) => !text.includes(token));
      if (missing.length) errors.push(`${name}.${suffix}: missing CLI contract tokens: ${missing.join(", ")}`);
    }
  }
  const meta = readJson(path.join(REPO_ROOT, "meta.json"));
  const plugin = readJson(path.join(REPO_ROOT, ".claude-plugin", "plugin.json"));
  const market = readJson(path.join(REPO_ROOT, ".claude-plugin", "marketplace.json")).plugins[0];
  const versions = new Set([meta.version, plugin.version, market.version, catalog.version]);
  if (versions.size !== 1 || !versions.has("2.2.0")) errors.push(`release versions disagree: ${[...versions].map(String).sort().join(", ")}`);
  const skillText = fs.readFileSync(path.join(SKILL_ROOT, "SKILL.md"), "utf8");
  const skillMatch = skillText.match(/^description: (.+)$/m);
  const entryDescription = (((meta.skills || {}).entries || [{}])[0] || {}).description;
  if (new Set([meta.description, plugin.description, market.description, entryDescription, skillMatch ? skillMatch[1] : null]).size !== 1) errors.push("package descriptions disagree");
  const forbidden = new Set(["document" + "-templates.json", "generation" + "-status.json", "status" + "-schema.json", "template" + "-schema.json"]);
  const present = fs.readdirSync(metadata).filter((name) => forbidden.has(name)).sort();
  if (present.length) errors.push(`obsolete metadata files remain: ${present.join(", ")}`);
  const legacyConstants = ["SP" + "INE", "SPINE_" + "PLAN", "OVER" + "LAYS"];
  const duplicate = new RegExp(`\\b(${legacyConstants.join("|")})\\s*=`);
  for (const name of names.filter((name) => /\.(py|js)$/.test(name)).sort()) {
    if (duplicate.test(fs.readFileSync(path.join(scripts, name), "utf8"))) errors.push(`${name}: duplicated registry constant`);
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
