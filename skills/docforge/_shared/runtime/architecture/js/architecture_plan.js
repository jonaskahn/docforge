"use strict";
/* Architecture plan ledger: prepare / import / decide / status / validate / audit.
 * Paired with runtime/architecture/python/plan.py. The architecture ledger
 * (.docforge/architecture-plan.json, schema 1.0) is the coordination record
 * for adaptive deep architecture generation. Both runtimes produce
 * byte-identical normalized JSON. */

const fs = require("fs");
const path = require("path");
const { fail, loadManifest } = require("../../common/js/_util.js");
const scale = require("../../common/js/scale.js");
const detectProfiles = require("../../catalog/js/detect_profiles.js");
const queryCatalog = require("../../catalog/js/query_catalog.js");

const PLAN_REL = ".docforge/architecture-plan.json";
const SCHEMA_VERSION = "1.0";
const EVIDENCE_WORKERS_BY_SCALE = { small: 3, medium: 6, large: 8 };
const PROPOSAL_AGENTS_BY_SCALE = { small: 2, medium: 3, large: 4 };
const RESEARCH_POLICIES = new Set(["official-primary", "official-only", "off"]);
const EXTERNAL_KINDS = new Set(["standard", "official-doc", "vendor-doc", "primary-research"]);
const EXTERNAL_RELATIONS = new Set(["primary-source", "supporting-source", "method", "terminology"]);
const DOCUMENT_STATES = new Set(["proposed", "selected", "declined"]);
const RFC3339 = /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?(Z|[+-]\d\d:\d\d)$/;
const URL = /^https?:\/\//;

function nowIso() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}

function dumpJson(value) {
  return JSON.stringify(value, null, 2) + "\n";
}

function planPath(repo) {
  return path.join(repo, PLAN_REL);
}

function readPlan(repo) {
  const target = planPath(repo);
  if (!fs.existsSync(target)) {
    throw new Error(`architecture plan not found: ${target}; run architecture_plan prepare first`);
  }
  let data;
  try {
    data = JSON.parse(fs.readFileSync(target, "utf8"));
  } catch (error) {
    throw new Error(`invalid architecture plan ${target}: ${error.message}`);
  }
  if (!data || typeof data !== "object" || data.schema !== SCHEMA_VERSION) {
    throw new Error(`architecture plan must use schema ${SCHEMA_VERSION}: ${target}`);
  }
  return data;
}

function writePlan(repo, plan) {
  plan.schema = SCHEMA_VERSION;
  plan.generated_at = nowIso();
  const target = planPath(repo);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, dumpJson(normalizePlan(plan)));
}

function normalizePlan(plan) {
  return JSON.parse(dumpJson(plan));
}

function scaleClass(repo) {
  const manifestPath = path.join(repo, ".docforge", "manifest.json");
  if (fs.existsSync(manifestPath)) {
    try {
      const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
      const scaleRec = (manifest.project || {}).scale;
      const klass = scaleRec && scaleRec.class;
      if (klass in EVIDENCE_WORKERS_BY_SCALE) return klass;
    } catch (_error) {
      /* fall through to detection */
    }
  }
  return scale.computeScale(repo).class;
}

function inventoryFiles(repo) {
  return detectProfiles.inventory(repo);
}

function detectLayoutTierProfiles(repo) {
  const manifestPath = path.join(repo, ".docforge", "manifest.json");
  let manifest = null;
  if (fs.existsSync(manifestPath)) {
    try {
      manifest = loadManifest(manifestPath);
    } catch (_error) {
      manifest = null;
    }
  }
  if (manifest) {
    const project = manifest.project || {};
    const scaleRec = project.scale || {};
    return {
      scale: scaleRec.class || scaleClass(repo),
      layout: scaleRec.layout || "standard",
      tier: project.tier || "diligence",
      profiles: project.profiles || {},
      graph_lock: manifest.graph && typeof manifest.graph === "object" ? manifest.graph : null,
    };
  }
  const klass = scaleClass(repo);
  const files = inventoryFiles(repo);
  const detections = detectProfiles.detect(repo, { persist: false, files });
  const profiles = { shapes: [], platforms: [], frameworks: [], concerns: [], audiences: [] };
  for (const item of detections) {
    if (item.confidence !== "confirmed") continue;
    if (item.dimension in profiles) profiles[item.dimension].push(item.id);
  }
  return {
    scale: klass,
    layout: scale.LAYOUT_BY_CLASS[klass] || "standard",
    tier: "diligence",
    profiles,
    graph_lock: null,
  };
}

function defaultPlan(repo) {
  const project = detectLayoutTierProfiles(repo);
  const klass = project.scale;
  return {
    schema: SCHEMA_VERSION,
    project,
    system: {
      capability: "",
      drivers: [],
      actors: [],
      external_systems: [],
      deployable_blocks: [],
      subsystem_candidates: [],
      deployment_nodes: [],
      relationships: [],
      invariants: [],
      trust_boundaries: [],
      failure_domains: [],
      quality_constraints: [],
      conflicts: [],
    },
    documents: [],
    research: { policy: "off", authorized: false, questions: [], sources: [] },
    adjudication: { proposals: [], adjudicator: null, merged: [], omitted: [], expansions: [] },
    audit: { status: "pending", verdict: null, report: null },
    workers: {
      evidence: EVIDENCE_WORKERS_BY_SCALE[klass] || 3,
      proposals: PROPOSAL_AGENTS_BY_SCALE[klass] || 2,
    },
    research_policy: "off",
  };
}

function validatePlan(plan) {
  const errors = [];
  if (plan.schema !== SCHEMA_VERSION) errors.push(`plan schema must be ${SCHEMA_VERSION}`);
  const project = plan.project || {};
  if (!(project.scale in EVIDENCE_WORKERS_BY_SCALE)) {
    errors.push(`project.scale must be one of: ${Object.keys(EVIDENCE_WORKERS_BY_SCALE).sort().join(", ")}`);
  }
  if (project.layout !== "standard" && project.layout !== "compact") {
    errors.push("project.layout must be standard or compact");
  }
  const system = plan.system || {};
  const blocks = system.deployable_blocks || [];
  const blockIds = new Set(blocks.map((b) => b.id));
  if (blockIds.size !== blocks.length) errors.push("system.deployable_blocks: duplicate ids");
  for (const block of blocks) {
    if (block.parent && !blockIds.has(block.parent)) {
      errors.push(`system.deployable_blocks.${block.id}: parent ${block.parent} is not a block`);
    }
  }
  const actors = system.actors || [];
  const external = system.external_systems || [];
  for (const rel of system.relationships || []) {
    if (!blockIds.has(rel.origin) && !actors.includes(rel.origin)) {
      errors.push(`relationship origin ${rel.origin} is not a block or actor`);
    }
    if (!blockIds.has(rel.destination) && !external.includes(rel.destination)) {
      errors.push(`relationship destination ${rel.destination} is not a block or external system`);
    }
  }
  const subsystemIds = new Set((system.subsystem_candidates || []).map((c) => c.id));
  if (subsystemIds.size !== (system.subsystem_candidates || []).length) {
    errors.push("system.subsystem_candidates: duplicate ids");
  }
  const documents = plan.documents || [];
  const docIds = new Set();
  const batchIds = new Set();
  for (const doc of documents) {
    const docId = doc.id;
    if (docIds.has(docId)) errors.push(`documents: duplicate id ${docId}`);
    docIds.add(docId);
    if (!DOCUMENT_STATES.has(doc.state)) errors.push(`documents.${docId}: invalid state ${doc.state}`);
    for (const parent of doc.parent_blocks || []) {
      if (!blockIds.has(parent)) errors.push(`documents.${docId}: parent block ${parent} is not a block`);
    }
    for (const dependency of doc.dependencies || []) {
      if (!docIds.has(dependency) && !documents.some((d) => d.id === dependency)) {
        errors.push(`documents.${docId}: dependency ${dependency} is not a document`);
      }
    }
    if (typeof doc.batch === "number" && !batchIds.has(doc.batch)) batchIds.add(doc.batch);
  }
  const research = plan.research || {};
  if (!RESEARCH_POLICIES.has(research.policy)) {
    errors.push(`research.policy must be one of: ${[...RESEARCH_POLICIES].sort().join(", ")}`);
  }
  if (research.authorized && research.policy === "off") {
    errors.push("research.authorized is true but research.policy is off");
  }
  const sources = research.sources || [];
  const sourceIds = new Set(sources.map((s) => s.id));
  if (sourceIds.size !== sources.length) errors.push("research.sources: duplicate ids");
  for (const source of sources) {
    if (!URL.test(source.url || "")) errors.push(`research.sources.${source.id}: url must be http(s)`);
    if (!EXTERNAL_KINDS.has(source.kind)) errors.push(`research.sources.${source.id}: invalid kind`);
    if (!RFC3339.test(source.accessed_at || "")) {
      errors.push(`research.sources.${source.id}: accessed_at must be RFC3339`);
    }
  }
  for (const doc of documents) {
    for (const ref of doc.external_refs || []) {
      if (!sourceIds.has(ref.source_id)) {
        errors.push(`documents.${doc.id}: external_refs references unknown source ${ref.source_id}`);
      }
      if (!EXTERNAL_RELATIONS.has(ref.relation)) {
        errors.push(`documents.${doc.id}: invalid external_refs relation`);
      }
    }
  }
  const audit = plan.audit || {};
  if (!["pending", "passed", "failed"].includes(audit.status)) {
    errors.push("audit.status must be pending, passed, or failed");
  }
  if (![null, "PASS", "FAIL"].includes(audit.verdict)) {
    errors.push("audit.verdict must be PASS, FAIL, or null");
  }
  if (audit.verdict === "FAIL" && audit.status !== "failed") {
    errors.push("audit.verdict FAIL requires audit.status failed");
  }
  return errors;
}

function runPrepare(repo, manifestPath) {
  let manifest = null;
  if (manifestPath) manifest = loadManifest(manifestPath);
  const plan = defaultPlan(repo);
  if (manifest) {
    const project = manifest.project || {};
    const scaleRec = project.scale || {};
    plan.project = {
      scale: scaleRec.class || plan.project.scale,
      layout: scaleRec.layout || plan.project.layout,
      tier: project.tier || plan.project.tier,
      profiles: project.profiles || plan.project.profiles,
      graph_lock: manifest.graph && typeof manifest.graph === "object" ? manifest.graph : null,
    };
  }
  const errors = validatePlan(plan);
  if (errors.length) {
    for (const error of errors) console.error(`error: ${error}`);
    return 1;
  }
  process.stdout.write(dumpJson(plan));
  return 0;
}

function runImport(repo, analysis) {
  let plan;
  try {
    plan = JSON.parse(fs.readFileSync(analysis, "utf8"));
  } catch (error) {
    return fail(`invalid analysis JSON: ${error.message}`, 1);
  }
  const errors = validatePlan(plan);
  if (errors.length) {
    for (const error of errors) console.error(`error: ${error}`);
    return 1;
  }
  writePlan(repo, plan);
  console.log(`Imported architecture plan to ${planPath(repo)}`);
  return 0;
}

function runDecide(repo, select, decline, researchPolicy) {
  const plan = readPlan(repo);
  if (!RESEARCH_POLICIES.has(researchPolicy)) {
    return fail(`research-policy must be one of: ${[...RESEARCH_POLICIES].sort().join(", ")}`, 2);
  }
  if ((plan.research || {}).policy !== "off") {
    return fail("research policy is already recorded; use --research-policy to change it", 1);
  }
  const docByIndex = {};
  for (const doc of plan.documents) docByIndex[doc.id] = doc;
  for (const docId of select) {
    if (!(docId in docByIndex)) return fail(`unknown document id: ${docId}`, 1);
    docByIndex[docId].state = "selected";
  }
  for (const docId of decline) {
    if (!(docId in docByIndex)) return fail(`unknown document id: ${docId}`, 1);
    docByIndex[docId].state = "declined";
  }
  for (const doc of plan.documents) {
    if (doc.state === "proposed") doc.state = "declined";
  }
  plan.research.policy = researchPolicy;
  plan.research.authorized = researchPolicy !== "off";
  writePlan(repo, plan);
  const selected = plan.documents.filter((doc) => doc.state === "selected");
  console.log(`Recorded ${selected.length} selected document(s); research policy: ${researchPolicy}.`);
  return 0;
}

function runStatus(repo, asJson) {
  const plan = readPlan(repo);
  const selected = plan.documents.filter((doc) => doc.state === "selected");
  if (asJson) {
    const payload = {
      schema: SCHEMA_VERSION,
      generated_at: plan.generated_at,
      selected_documents: selected,
      unresolved_gaps: (plan.research.questions || []).filter((q) => !q.resolved),
      research_policy: plan.research.policy,
      audit: plan.audit,
    };
    process.stdout.write(dumpJson(payload));
  } else {
    console.log(`Architecture plan: ${planPath(repo)}`);
    console.log(`Selected documents (${selected.length}):`);
    for (const doc of selected) console.log(`  ${doc.id}  ${doc.path}`);
    console.log(`Research policy: ${plan.research.policy}`);
    console.log(`Pack audit: ${plan.audit.status} (${plan.audit.verdict || "pending"})`);
  }
  return 0;
}

function runValidate(repo) {
  const plan = readPlan(repo);
  const errors = validatePlan(plan);
  if (errors.length) {
    for (const error of errors) console.error(`error: ${error}`);
    return 1;
  }
  console.log("architecture plan ok");
  return 0;
}

function runAudit(repo, verdict, report) {
  const plan = readPlan(repo);
  if (verdict !== "PASS" && verdict !== "FAIL") return fail("--verdict must be PASS or FAIL", 2);
  plan.audit.verdict = verdict;
  plan.audit.report = report || null;
  plan.audit.status = verdict === "PASS" ? "passed" : "failed";
  writePlan(repo, plan);
  console.log(`Recorded pack audit ${verdict}.`);
  return 0;
}

function parseArgs(argv) {
  const result = { _: [] };
  const allowed = new Set(["repo", "manifest", "json", "analysis", "select", "decline", "research-policy", "verdict", "report", "help"]);
  for (let i = 0; i < argv.length; i++) {
    const token = argv[i];
    if (token === "-h" || token === "--help") return { help: true };
    if (!token.startsWith("--")) {
      result._.push(token);
      continue;
    }
    const raw = token.slice(2);
    if (!allowed.has(raw)) throw new Error(`unknown option: ${token}`);
    const key = raw.replace(/-/g, "_");
    if (raw === "json" || raw === "help") result[key] = true;
    else if (raw === "select" || raw === "decline") {
      const values = [];
      while (i + 1 < argv.length && !argv[i + 1].startsWith("--")) values.push(argv[++i]);
      result[key] = values;
    } else {
      if (i + 1 >= argv.length || argv[i + 1].startsWith("--")) throw new Error(`option requires a value: ${token}`);
      result[key] = argv[++i];
    }
  }
  return result;
}

function usage() {
  console.log(
    "usage: architecture_plan.js <prepare|import|decide|status|validate|audit> --repo <repo> " +
    "[--manifest <path>] [--json] [--analysis <path>] [--select <id>...] [--decline <id>...] " +
    "[--research-policy <mode>] [--verdict PASS|FAIL] [--report <path>]",
  );
}

function main(argv) {
  try {
    const args = parseArgs(argv);
    if (args.help) { usage(); return 0; }
    const command = args._[0];
    if (!command) throw new Error("a command is required");
    if (!args.repo) throw new Error("--repo is required");
    if (command === "prepare") return runPrepare(args.repo, args.manifest);
    if (command === "import") {
      if (!args.analysis) throw new Error("--analysis is required for import");
      return runImport(args.repo, args.analysis);
    }
    if (command === "decide") {
      if (!args.research_policy) throw new Error("--research-policy is required for decide");
      return runDecide(args.repo, args.select || [], args.decline || [], args.research_policy);
    }
    if (command === "status") return runStatus(args.repo, args.json);
    if (command === "validate") return runValidate(args.repo);
    if (command === "audit") {
      if (!args.verdict) throw new Error("--verdict is required for audit");
      return runAudit(args.repo, args.verdict, args.report);
    }
    throw new Error(`unknown command: ${command}`);
  } catch (error) {
    usage();
    return fail(error.message, 2);
  }
}

module.exports = {
  SCHEMA_VERSION,
  EVIDENCE_WORKERS_BY_SCALE,
  PROPOSAL_AGENTS_BY_SCALE,
  RESEARCH_POLICIES,
  defaultPlan,
  validatePlan,
  normalizePlan,
  main,
};
