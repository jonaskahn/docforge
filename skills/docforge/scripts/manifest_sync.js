#!/usr/bin/env node
"use strict";
/* Create and maintain the docforge tracking manifest at <repo>/.docforge/manifest.json.
 *
 * The manifest is the durable plan and fill-state of the documentation tree:
 * one entry per planned document, its group, path, template, and status.
 * Step 0 Gate 1 writes it with everything `planned`; the write loop advances
 * each document's status as it lands.
 *
 * Subcommands
 * -----------
 *   init     write a fresh .docforge/manifest.json for a tier (spine documents),
 *            every status "planned". Overlay and discovered-flow documents are
 *            added later with `add`.
 *   add      append one document to a group (a discovered flow, an overlay doc).
 *   set      change one document's status by id, recompute counts, stamp the time.
 *   status   print the plan as a table with a status summary.
 *
 * Statuses: planned -> in_progress -> generated -> needs_review -> complete (or skipped).
 * Paths mirror references/docs-tree.md and scripts/docs_scaffold.js exactly.
 *
 * Examples
 * --------
 *   node manifest_sync.js init   --repo ../my-service --tier 2 --name my-service
 *   node manifest_sync.js add    --repo ../my-service --group flows \
 *                                 --id flow_checkout --type flows \
 *                                 --path docs/flows/checkout.md --needs-dg
 *   node manifest_sync.js set    --repo ../my-service --id setup_guide --status complete
 *   node manifest_sync.js status --repo ../my-service
 *
 * Node.js built-ins only.
 */

const fs = require("fs");
const path = require("path");

const SKILL_ROOT = path.resolve(__dirname, "..");
const TEMPLATES_JSON = path.join(SKILL_ROOT, ".metadata", "document-templates.json");

const MANIFEST_REL = path.join(".docforge", "manifest.json");

const STATUSES = ["planned", "in_progress", "generated", "needs_review", "complete", "skipped"];
const GROUPS = [
  "architecture",
  "flows",
  "product",
  "engineering",
  "operations",
  "reference",
  "security",
  "contributing",
  "records",
  "agent-context",
];

// Spine plan: the documents a tier implies, keyed to the same paths
// docs_scaffold.js emits. `template` and `requires_*` are resolved from
// document-templates.json by type. [group, id, type, path, min_tier]
const SPINE_PLAN = [
  ["architecture", "arch_high_level", "architecture-high-level", "docs/architecture/high-level.md", 1],
  ["architecture", "arch_low_level", "architecture-low-level", "docs/architecture/low-level.md", 2],
  ["architecture", "dependencies", "dependencies-inventory", "docs/architecture/dependencies.md", 2],
  ["architecture", "tech_debt", "tech-debt-register", "docs/architecture/tech-debt.md", 2],
  ["architecture", "adr_index", "decision-records", "docs/architecture/decisions/README.md", 2],
  ["product", "product_overview", "product-overview", "docs/product/overview.md", 1],
  ["engineering", "setup_guide", "setup-guide", "docs/engineering/setup.md", 1],
  ["reference", "limitations", "limitations-register", "docs/reference/limitations.md", 1],
  ["security", "security_policy", "security-policy", "SECURITY.md", 2],
];

// Mirrors Python's datetime.now(timezone.utc).replace(microsecond=0).isoformat()
function nowIsoUtc() {
  const d = new Date();
  d.setUTCMilliseconds(0);
  return d.toISOString().replace(".000Z", "+00:00");
}

function loadTemplateIndex() {
  const data = JSON.parse(fs.readFileSync(TEMPLATES_JSON, "utf8"));
  const idx = {};
  for (const t of data.templates || []) {
    const req = t.requires || [];
    idx[t.type] = {
      template: t.instruction_file || null,
      needs_kg: req.includes("knowledge_graph"),
      needs_dg: req.includes("domain_graph"),
    };
  }
  return idx;
}

function makeDoc(id, type, docPath, template, needsKg, needsDg) {
  return {
    id,
    type,
    path: docPath,
    status: "planned",
    requires_domain_graph: needsDg,
    requires_knowledge_graph: needsKg,
    template,
    // Per-section provenance, filled as the document is written and stamped
    // (each entry: {id: <anchor>, sources: [{path, git_blob}]}).
    // check_provenance.js reads this to decide staleness; empty while planned.
    sections: [],
  };
}

function manifestPath(repo) {
  return path.join(repo, MANIFEST_REL);
}

function loadManifest(repo) {
  const p = manifestPath(repo);
  if (!fs.existsSync(p)) {
    console.error(`No manifest at ${p}. Run \`init\` first.`);
    process.exit(1);
  }
  return JSON.parse(fs.readFileSync(p, "utf8"));
}

function recount(man) {
  const docs = man.document_groups.flatMap((g) => g.documents);
  man.metadata = man.metadata || {};
  Object.assign(man.metadata, {
    total_documents: docs.length,
    completed: docs.filter((d) => d.status === "complete").length,
    in_progress: docs.filter((d) => d.status === "in_progress").length,
    requires_review: docs.filter((d) => d.status === "needs_review").length,
    last_updated: nowIsoUtc(),
  });
}

function saveManifest(repo, man) {
  recount(man);
  const p = manifestPath(repo);
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, JSON.stringify(man, null, 2) + "\n", "utf8");
}

// ---------------------------------------------------------------------------
// Commands
// ---------------------------------------------------------------------------

function cmdInit(args) {
  const p = manifestPath(args.repo);
  if (fs.existsSync(p) && !args.force) {
    console.error(`${p} exists. Pass --force to overwrite.`);
    process.exit(1);
  }

  if (!args.noAgentContext && !args.overlay.includes("agent-context")) {
    args.overlay.push("agent-context");
  }

  const tidx = loadTemplateIndex();
  const groups = {};
  for (const [group, id, type, docPath, minTier] of SPINE_PLAN) {
    if (minTier > args.tier) continue;
    const meta = tidx[type] || {};
    const doc = makeDoc(id, type, docPath, meta.template || null, meta.needs_kg || false, meta.needs_dg || false);
    (groups[group] = groups[group] || []).push(doc);
  }

  // flows is always present but discovered later via `add`
  groups.flows = groups.flows || [];

  const ordered = GROUPS.filter((g) => g in groups);
  const man = {
    version: "1.1",
    generated_at: nowIsoUtc(),
    project_context: {
      repo_name: args.name,
      repo_path: path.resolve(args.repo),
      tier: { 1: "core", 2: "standard", 3: "extended" }[args.tier],
      overlays: args.overlay,
    },
    document_groups: ordered.map((g) => ({ group: g, documents: groups[g] })),
    metadata: {},
  };
  saveManifest(args.repo, man);
  const n = Object.values(groups).reduce((a, v) => a + v.length, 0);
  console.log(`Wrote ${manifestPath(args.repo)} — tier ${args.tier}, ${n} spine documents planned.`);
  console.log("Add discovered flows and overlay documents with `add`; advance status with `set`.");
  return 0;
}

function cmdAdd(args) {
  const man = loadManifest(args.repo);
  if (!GROUPS.includes(args.group)) {
    console.error(`Unknown group '${args.group}'. One of: ${GROUPS.join(", ")}`);
    process.exit(1);
  }

  const allIds = new Set(man.document_groups.flatMap((g) => g.documents.map((d) => d.id)));
  if (allIds.has(args.id)) {
    console.error(`Document id '${args.id}' already in manifest.`);
    process.exit(1);
  }

  const tidx = loadTemplateIndex();
  const meta = tidx[args.type] || {};
  const template = args.template || meta.template || null;
  const needsKg = args.needsKg || meta.needs_kg || false;
  const needsDg = args.needsDg || meta.needs_dg || false;
  const doc = makeDoc(args.id, args.type, args.path, template, needsKg, needsDg);

  // Rebuild document_groups with new doc added to target group
  const groupsMap = {};
  for (const g of man.document_groups) {
    groupsMap[g.group] = g.documents;
  }
  if (!(args.group in groupsMap)) {
    groupsMap[args.group] = [];
  }
  groupsMap[args.group].push(doc);

  // Reconstruct document_groups in canonical order
  man.document_groups = GROUPS.filter((g) => g in groupsMap).map((g) => ({
    group: g,
    documents: groupsMap[g],
  }));

  saveManifest(args.repo, man);
  console.log(`Added ${args.id} (${args.path}) to group '${args.group}', status planned.`);
  return 0;
}

function cmdSet(args) {
  if (!STATUSES.includes(args.status)) {
    console.error(`Invalid status '${args.status}'. One of: ${STATUSES.join(", ")}`);
    process.exit(1);
  }
  const man = loadManifest(args.repo);
  for (const g of man.document_groups) {
    for (const d of g.documents) {
      if (d.id === args.id) {
        const old = d.status;
        d.status = args.status;
        saveManifest(args.repo, man);
        console.log(`${args.id}: ${old} -> ${args.status}`);
        return 0;
      }
    }
  }
  console.error(`No document with id '${args.id}' in manifest.`);
  process.exit(1);
}

function cmdStatus(args) {
  const man = loadManifest(args.repo);
  const ctx = man.project_context || {};
  console.log(
    `repo: ${ctx.repo_name}  tier: ${ctx.tier}  overlays: ${(ctx.overlays || []).join(", ") || "none"}`
  );
  console.log(`updated: ${(man.metadata || {}).last_updated}\n`);

  const rows = [];
  for (const g of man.document_groups) {
    for (const d of g.documents) {
      rows.push([g.group, d.status, d.id, d.path]);
    }
  }
  if (!rows.length) {
    console.log("(no documents planned)");
    return 0;
  }
  const wGrp = Math.max(...rows.map((r) => r[0].length));
  const wSt = Math.max(...rows.map((r) => r[1].length));
  const wId = Math.max(...rows.map((r) => r[2].length));
  for (const [grp, st, id, docPath] of rows) {
    console.log(`  ${grp.padEnd(wGrp)}  ${st.padEnd(wSt)}  ${id.padEnd(wId)}  ${docPath}`);
  }

  const counts = {};
  for (const [, st] of rows) counts[st] = (counts[st] || 0) + 1;
  const summary = Object.keys(counts)
    .sort()
    .map((k) => `${k}=${counts[k]}`)
    .join("  ");
  console.log(`\n${rows.length} documents:  ${summary}`);
  return 0;
}

function parseArgs(argv) {
  const cmd = argv[0];
  const rest = argv.slice(1);
  const args = { cmd, overlay: [] };
  for (let i = 0; i < rest.length; i++) {
    const a = rest[i];
    if (a === "--repo") args.repo = rest[++i];
    else if (a === "--tier") args.tier = parseInt(rest[++i], 10);
    else if (a === "--name") args.name = rest[++i];
    else if (a === "--overlay") args.overlay.push(rest[++i]);
    else if (a === "--no-agent-context") args.noAgentContext = true;
    else if (a === "--force") args.force = true;
    else if (a === "--group") args.group = rest[++i];
    else if (a === "--id") args.id = rest[++i];
    else if (a === "--type") args.type = rest[++i];
    else if (a === "--path") args.path = rest[++i];
    else if (a === "--template") args.template = rest[++i];
    else if (a === "--needs-kg") args.needsKg = true;
    else if (a === "--needs-dg") args.needsDg = true;
    else if (a === "--status") args.status = rest[++i];
  }
  if (args.tier === undefined) args.tier = 2;
  return args;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const validCmds = ["init", "add", "set", "status"];
  if (!validCmds.includes(args.cmd)) {
    console.error(`usage: manifest_sync.js <${validCmds.join("|")}> --repo <path> [options]`);
    return 1;
  }
  if (!args.repo) {
    console.error("--repo is required");
    return 1;
  }
  if (!fs.existsSync(args.repo) || !fs.statSync(args.repo).isDirectory()) {
    console.error(`Not a directory: ${args.repo}`);
    return 1;
  }
  if (args.cmd === "init") {
    if (![1, 2, 3].includes(args.tier)) {
      console.error(`--tier must be 1, 2 or 3, got ${args.tier}`);
      return 1;
    }
    return cmdInit(args);
  }
  if (args.cmd === "add") return cmdAdd(args);
  if (args.cmd === "set") return cmdSet(args);
  if (args.cmd === "status") return cmdStatus(args);
  return 1;
}

process.exit(main());
