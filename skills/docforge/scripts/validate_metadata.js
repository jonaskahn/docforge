#!/usr/bin/env node
"use strict";
/** Validate the Docforge catalog, schemas, templates, peers, and release metadata. */

const fs = require("fs");
const path = require("path");
const SKILL_ROOT = path.resolve(__dirname, "..");
const REPO_ROOT = path.resolve(SKILL_ROOT, "..", "..");
const REQUIRED = new Set(["id", "type", "path", "group", "selection", "scaffold_template", "requires", "target_depth", "write_order", "provenance_mode", "audit_profile"]);
const EXCEPTIONS = new Set(["agents-kernel.md", "claude-md.md", "claude-local-md.md"]);
const PUBLIC_CONTRACTS = {
  manage_manifest: ["init", "add", "set", "status", "audit", "--repo", "--tier", "--overlay", "--type", "--id", "--path", "--status", "--mode", "--verdict", "--report"],
  scaffold_docs: ["--repo", "--manifest", "--dry-run", "--document", "--audit"],
  precheck_graph: ["--repo", "--need", "code", "flow"],
  check_staleness: ["--manifest", "--section", "--json", "--sync-provenance"],
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
  if (catalog.version !== "1.0.0") errors.push("catalog version must be 1.0.0");
  if ((((catalogSchema.properties || {}).version || {}).const) !== "1.0.0") errors.push("catalog schema version disagrees with catalog");
  if ((((manifestSchema.properties || {}).version || {}).const) !== "2.0") errors.push("manifest schema must require version 2.0");
  const tiers = new Set(catalog.tiers.map((item) => item.id));
  const overlays = new Set(catalog.overlays.map((item) => item.id));
  const groups = new Set(catalog.groups);
  const capabilities = new Set(catalog.capabilities);
  const staticIds = new Set();
  const staticPaths = new Set();
  const dynamicTypes = new Set();
  for (let index = 0; index < catalog.documents.length; index++) {
    const doc = catalog.documents[index];
    const label = doc.id || `document[${index}]`;
    const missing = [...REQUIRED].filter((field) => !(field in doc)).sort();
    if (missing.length) {
      errors.push(`${label}: missing fields: ${missing.join(", ")}`);
      continue;
    }
    const selection = doc.selection || {};
    if (!groups.has(doc.group)) errors.push(`${label}: unknown group ${doc.group}`);
    if (!tiers.has(selection.min_tier)) errors.push(`${label}: unknown tier ${selection.min_tier}`);
    for (const overlay of selection.overlays || []) if (!overlays.has(overlay)) errors.push(`${label}: unknown overlay ${overlay}`);
    for (const overlay of selection.include_if_overlay || []) if (!overlays.has(overlay)) errors.push(`${label}: unknown include_if_overlay ${overlay}`);
    for (const requirement of doc.requires || []) if (!capabilities.has(requirement)) errors.push(`${label}: unknown requirement ${requirement}`);
    if (!Number.isInteger(doc.write_order)) errors.push(`${label}: write_order must be an integer`);
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
    if (!text.startsWith("---\n{")) {
      errors.push(`${name}: provenance frontmatter must start at byte one`);
      continue;
    }
    const end = text.indexOf("\n---\n", 4);
    let frontmatter = null;
    try { frontmatter = end >= 0 ? JSON.parse(text.slice(4, end)) : null; } catch {}
    if (!frontmatter || typeof frontmatter !== "object" || !("docforge_provenance" in frontmatter)) {
      errors.push(`${name}: provenance frontmatter is not valid JSON`);
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
  if (versions.size !== 1 || !versions.has("1.0.0")) errors.push(`release versions disagree: ${[...versions].map(String).sort().join(", ")}`);
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
