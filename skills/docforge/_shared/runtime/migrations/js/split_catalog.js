#!/usr/bin/env node
"use strict";
/* One-shot: split .metadata/catalog.json into catalog/index.json + types/ + profiles/.
 *
 * Applies Phase 0.10 infrastructure-platform signal widening and bumps version to 2.17.0.
 * Re-runnable: overwrites the split tree from the monolith when present, otherwise from
 * the already-split index + types (round-trip). Mirrors migrations/python/split_catalog.py.
 */

const fs = require("fs");
const path = require("path");

const DEFAULT_ROOT = path.resolve(__dirname, "..", "..", "..");
const TARGET_VERSION = "2.17.0";

const INFRA_EXTRA_SIGNALS = [
  { kind: "path", pattern: "ansible.cfg" },
  { kind: "path", pattern: "**/playbook*.yml", strength: "weak" },
  { kind: "path", pattern: "**/roles/**", strength: "weak" },
  { kind: "path", pattern: "**/kustomization.yaml" },
  {
    kind: "content",
    pattern: "**/*.{yaml,yml}",
    contains: "apiVersion:",
    strength: "weak",
  },
  {
    kind: "content",
    pattern: "**/*.{yaml,yml}",
    contains: "kind: Application",
    strength: "weak",
  },
  {
    kind: "content",
    pattern: "**/*.{yaml,yml}",
    contains: "kind: Kustomization",
    strength: "weak",
  },
  {
    kind: "content",
    pattern: "**/*.{yaml,yml}",
    contains: "kind: HelmRelease",
    strength: "weak",
  },
  {
    kind: "content",
    pattern: "**/*.{yaml,yml}",
    contains: "AWSTemplateFormatVersion",
    strength: "weak",
  },
];
const INFRA_EXTRA_ALIASES = ["deployment-config", "iac"];

function dump(value) {
  return `${JSON.stringify(value, null, 2)}\n`;
}

function layout(root) {
  const metadata = path.join(root, ".metadata");
  return {
    metadata,
    monolith: path.join(metadata, "catalog.json"),
    index: path.join(metadata, "catalog", "index.json"),
    types: path.join(metadata, "catalog", "types"),
    profiles: path.join(metadata, "catalog", "profiles"),
  };
}

function loadMonolith(root) {
  const L = layout(root);
  if (fs.existsSync(L.monolith)) {
    return JSON.parse(fs.readFileSync(L.monolith, "utf8"));
  }
  if (!fs.existsSync(L.index)) {
    throw new Error(`neither ${L.monolith} nor ${L.index} exists`);
  }
  // Reconstruct from split for re-apply of signal patches.
  const index = JSON.parse(fs.readFileSync(L.index, "utf8"));
  const profiles = {};
  for (const dimension of ["shapes", "platforms", "frameworks", "concerns", "audiences"]) {
    profiles[dimension] = JSON.parse(
      fs.readFileSync(path.join(L.profiles, `${dimension}.json`), "utf8"),
    );
  }
  const documents = [];
  for (const row of index.document_types) {
    documents.push(JSON.parse(fs.readFileSync(path.join(L.types, `${row.id}.json`), "utf8")));
  }
  const tiers = index.tiers && typeof index.tiers === "object" && !Array.isArray(index.tiers)
    ? Object.entries(index.tiers).map(([id, meta]) => ({ id, order: meta.order }))
    : (index.tiers || []);
  return {
    $schema: "catalog-schema.json",
    version: index.version,
    tiers,
    profiles,
    groups: index.groups || [],
    capabilities: index.capabilities || [],
    documents,
    cue_hints: index.cue_hints || [],
  };
}

function applyInfraWidening(catalog) {
  const infra = catalog.profiles.shapes.find((shape) => shape.id === "infrastructure-platform");
  const existing = new Set(
    infra.signals.map((signal) => `${signal.kind}\x00${signal.pattern || ""}\x00${signal.contains || ""}`),
  );
  for (const signal of INFRA_EXTRA_SIGNALS) {
    const key = `${signal.kind}\x00${signal.pattern || ""}\x00${signal.contains || ""}`;
    if (!existing.has(key)) {
      infra.signals.push(signal);
      existing.add(key);
    }
  }
  const aliases = [...(infra.aliases || [])];
  for (const alias of INFRA_EXTRA_ALIASES) {
    if (!aliases.includes(alias)) aliases.push(alias);
  }
  infra.aliases = aliases;
}

function normalizeTiers(tiers) {
  if (tiers && typeof tiers === "object" && !Array.isArray(tiers)) return tiers;
  return Object.fromEntries(tiers.map((item) => [item.id, { order: item.order }]));
}

function emit(catalog, dryRun, root) {
  const L = layout(root);
  const copy = JSON.parse(JSON.stringify(catalog)); // deep copy
  applyInfraWidening(copy);
  copy.version = TARGET_VERSION;

  const tiers = normalizeTiers(copy.tiers);
  const documentTypes = copy.documents.map((doc) => ({
    id: doc.id,
    tier: doc.selection.min_tier,
    path: doc.path,
  }));
  const index = {
    $schema: "catalog-index-schema.json",
    version: TARGET_VERSION,
    tiers,
    groups: copy.groups,
    capabilities: copy.capabilities,
    cue_hints: copy.cue_hints || [],
    document_types: documentTypes,
  };

  const typeFiles = Object.fromEntries(copy.documents.map((doc) => [doc.id, doc]));
  const profileFiles = Object.fromEntries(
    ["shapes", "platforms", "frameworks", "concerns", "audiences"]
      .map((dimension) => [dimension, copy.profiles[dimension]]),
  );

  const infra = profileFiles.shapes.find((shape) => shape.id === "infrastructure-platform");
  const summary = {
    version: TARGET_VERSION,
    document_types: Object.keys(typeFiles).length,
    profiles: Object.fromEntries(
      Object.entries(profileFiles).map(([dimension, definitions]) => [dimension, definitions.length]),
    ),
    infra_signals: infra.signals.length,
    infra_aliases: infra.aliases,
  };

  if (dryRun) {
    console.log(JSON.stringify(summary, null, 2));
    return summary;
  }

  fs.mkdirSync(L.types, { recursive: true });
  fs.mkdirSync(L.profiles, { recursive: true });
  fs.writeFileSync(L.index, dump(index), "utf8");
  for (const [docId, detail] of Object.entries(typeFiles)) {
    fs.writeFileSync(path.join(L.types, `${docId}.json`), dump(detail), "utf8");
  }
  for (const [dimension, definitions] of Object.entries(profileFiles)) {
    fs.writeFileSync(path.join(L.profiles, `${dimension}.json`), dump(definitions), "utf8");
  }

  // Round-trip check: reconstruct monolith shape and compare documents field-for-field.
  const originalDocs = Object.fromEntries(copy.documents.map((doc) => [doc.id, doc]));
  for (const row of index.document_types) {
    const reconstructed = JSON.parse(
      fs.readFileSync(path.join(L.types, `${row.id}.json`), "utf8"),
    );
    if (JSON.stringify(reconstructed) !== JSON.stringify(originalDocs[row.id])) {
      throw new Error(`round-trip mismatch for document ${row.id}`);
    }
  }

  console.log(
    `Wrote ${path.relative(root, L.index)} + ${Object.keys(typeFiles).length} types + `
    + `${Object.keys(profileFiles).length} profile files (version ${TARGET_VERSION}).`,
  );
  console.log(JSON.stringify(summary, null, 2));
  return summary;
}

function main(argv) {
  const args = { dryRun: false, root: null };
  for (let i = 2; i < argv.length; i += 1) {
    const token = argv[i];
    if (token === "--dry-run") args.dryRun = true;
    else if (token === "--root") args.root = argv[++i];
    else if (token === "--help" || token === "-h") {
      console.log("usage: split_catalog.js [--dry-run] [--root <path>]");
      return 0;
    } else {
      process.stderr.write(`error: unknown argument: ${token}\n`);
      return 2;
    }
  }
  const root = args.root ? path.resolve(args.root) : DEFAULT_ROOT;
  let catalog;
  try {
    catalog = loadMonolith(root);
  } catch (error) {
    process.stderr.write(`error: ${error.message}\n`);
    return 1;
  }
  emit(catalog, args.dryRun, root);
  return 0;
}

module.exports = { main, loadMonolith, emit, layout, TARGET_VERSION };

if (require.main === module) {
  process.exitCode = main(process.argv);
}
