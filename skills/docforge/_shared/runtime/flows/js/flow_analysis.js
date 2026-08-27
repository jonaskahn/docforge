#!/usr/bin/env node
"use strict";
/** Adaptive flow-analysis ledger. Paired with python/flow_analysis.py. */

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");
const { fail, loadManifest } = require("../../common/js/_util.js");
const scale = require("../../common/js/scale.js");

const ANALYSIS_REL = path.join(".docforge", "flow-analysis.json");
const INVESTIGATION_REL = path.join(".docforge", "flow-investigation.json");
const FLOW_EVIDENCE_REL = path.join(".docforge", "flow-evidence.json");
const SCHEMA_VERSION = 3;
const LEGACY_SCHEMA_VERSIONS = new Set([1, 2]);
const EVIDENCE_WORKERS_BY_SCALE = { small: 3, medium: 6, large: 8 };
const PROPOSAL_AGENTS_BY_SCALE = { small: 2, medium: 3, large: 4 };
const RESEARCH_POLICIES = new Set(["official-primary", "official-only", "off"]);
const FLOW_CHARACTERISTICS = new Set([
  "request-command", "event-message", "scheduled-batch",
  "lifecycle-stateful", "streaming-interactive", "fan-out-orchestration",
  "resource-lifecycle",
]);
const FLOW_STATES = new Set([
  "not-analyzed", "legacy-needs-analysis", "analyzing", "ready", "audited",
]);
const DECISIONS = new Set(["proposed", "selected", "declined"]);
const TRIGGER_KINDS = new Set(["http", "queue", "schedule", "cli", "ui", "internal"]);
const MODULES = new Set([
  "state", "transaction", "consistency", "idempotency", "ordering",
  "deduplication", "timing", "backpressure", "security", "observability",
  "recovery", "compensation", "residual-state",
]);
const FAILURE_CATEGORIES = new Set([
  "decision-rejected", "awaited-event-timeout", "timeout", "interruption", "cancellation",
]);
const DIAGRAM_FORMS = new Set(["sequenceDiagram", "flowchart", "stateDiagram-v2", "text"]);
const FLOW_ID = /^flow-[a-z0-9][a-z0-9-]*$/;
const STEP_REF_KEYS = new Set([
  "step", "step_order", "from_step", "to_step", "rejoin_step", "join_step",
]);

function nowIso() { return new Date().toISOString().replace(/\.\d{3}Z$/, "Z"); }
function dumpJson(value) { return JSON.stringify(value, null, 2) + "\n"; }
function analysisPath(repo) { return path.join(repo, ANALYSIS_REL); }
function normalizeAnalysis(data) { return JSON.parse(dumpJson(data)); }

function migrateLegacy(data, repo = null) {
  const source = data.source || (repo ? path.resolve(repo) : "legacy-analysis");
  const flows = [];
  (Array.isArray(data.flows) ? data.flows : []).forEach((old, index) => {
    if (!old || typeof old !== "object" || Array.isArray(old)) return;
    let id = String(old.id || old.flowId || `flow-legacy-${index + 1}`);
    if (!FLOW_ID.test(id)) {
      const slug = id.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || `legacy-${index + 1}`;
      id = `flow-${slug}`;
    }
    flows.push({
      id,
      name: String(old.name || old.title || id),
      analysis_state: "legacy-needs-analysis",
      decision: "proposed",
      parent_flow: null,
      legacy_evidence: old,
    });
  });
  const oldWorkers = data.workers && typeof data.workers === "object" ? data.workers : {};
  const oldAudit = data.audit && typeof data.audit === "object" ? data.audit : {};
  return {
    schemaVersion: SCHEMA_VERSION,
    source: String(source),
    generated_at: nowIso(),
    research_policy: data.research_policy === undefined ? null : data.research_policy,
    workers: { evidence: oldWorkers.evidence || 3, proposals: oldWorkers.proposals || 2 },
    audit: {
      status: oldAudit.status || "pending",
      verdict: oldAudit.verdict === undefined ? null : oldAudit.verdict,
      report: oldAudit.report === undefined ? null : oldAudit.report,
    },
    flows,
  };
}

function readAnalysis(repo) {
  const target = analysisPath(repo);
  if (!fs.existsSync(target)) throw new Error(`flow analysis not found: ${target}; run flow_analysis prepare/import first`);
  let data;
  try { data = JSON.parse(fs.readFileSync(target, "utf8")); }
  catch (error) { throw new Error(`invalid flow analysis ${target}: ${error.message}`); }
  if (!data || typeof data !== "object" || Array.isArray(data)) throw new Error(`flow analysis must be a JSON object: ${target}`);
  const version = data.schemaVersion === undefined ? 1 : data.schemaVersion;
  if (LEGACY_SCHEMA_VERSIONS.has(version)) return migrateLegacy(data, repo);
  if (version !== SCHEMA_VERSION) throw new Error(`flow analysis must use schemaVersion 1, 2, or ${SCHEMA_VERSION}: ${target}`);
  return data;
}

function writeAnalysis(repo, data) {
  data.schemaVersion = SCHEMA_VERSION;
  data.generated_at = nowIso();
  const target = analysisPath(repo);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, dumpJson(normalizeAnalysis(data)), "utf8");
}

function manifestScale(manifest) {
  const record = manifest && manifest.project && manifest.project.scale;
  const value = record && typeof record === "object" ? record.class : null;
  return Object.prototype.hasOwnProperty.call(EVIDENCE_WORKERS_BY_SCALE, value) ? value : null;
}

function scaleClass(repo, manifestPath = null) {
  if (manifestPath) {
    const value = manifestScale(loadManifest(manifestPath));
    if (value) return value;
  }
  const local = path.join(repo, ".docforge", "manifest.json");
  if (fs.existsSync(local)) {
    try {
      const value = manifestScale(loadManifest(local));
      if (value) return value;
    } catch (_) { /* fall through to detection */ }
  }
  return scale.computeScale(repo).class;
}

function defaultAnalysis(repo, manifestPath = null) {
  const klass = scaleClass(repo, manifestPath);
  return {
    schemaVersion: SCHEMA_VERSION,
    // Python's Path.resolve() follows macOS's /private tmp symlink; use the
    // same canonical path so the schema-v3 stdout is actually paired.
    source: fs.realpathSync(repo),
    generated_at: nowIso(),
    research_policy: null,
    workers: {
      evidence: EVIDENCE_WORKERS_BY_SCALE[klass] || 3,
      proposals: PROPOSAL_AGENTS_BY_SCALE[klass] || 2,
    },
    audit: { status: "pending", verdict: null, report: null },
    flows: [],
  };
}

function validateStepReferences(flowId, patterns, orders) {
  const errors = [];
  if (!patterns || typeof patterns !== "object" || Array.isArray(patterns)) return [`flow ${flowId}: flow_patterns must be an object`];
  for (const [kind, records] of Object.entries(patterns)) {
    if (!Array.isArray(records)) { errors.push(`flow ${flowId}: flow_patterns.${kind} must be an array`); continue; }
    records.forEach((record, index) => {
      if (!record || typeof record !== "object" || Array.isArray(record)) {
        errors.push(`flow ${flowId}: flow_patterns.${kind}[${index + 1}] must be an object`);
        return;
      }
      for (const key of Object.keys(record).filter((key) => STEP_REF_KEYS.has(key))) {
        const refs = Array.isArray(record[key]) ? record[key] : [record[key]];
        for (const ref of refs) {
          if (Number.isInteger(ref) && !orders.has(ref)) {
            errors.push(`flow ${flowId}: flow_patterns.${kind}[${index + 1}].${key} references missing step ${ref}`);
          }
        }
      }
    });
  }
  return errors;
}

function validateAnalysis(data, repo = null, allowEmpty = false) {
  const errors = [];
  if (data.schemaVersion !== SCHEMA_VERSION) errors.push(`schemaVersion must be ${SCHEMA_VERSION}`);
  if (!String(data.source || "").trim()) errors.push("source must be a non-empty string");
  if (data.research_policy !== null && !RESEARCH_POLICIES.has(data.research_policy)) {
    errors.push("research_policy must be official-primary, official-only, off, or null");
  }
  const workers = data.workers;
  if (!workers || typeof workers !== "object" || !["evidence", "proposals"].every((key) => Number.isInteger(workers[key]) && workers[key] > 0)) {
    errors.push("workers must contain positive evidence and proposals counts");
  }
  const audit = data.audit;
  if (!audit || typeof audit !== "object" || Array.isArray(audit)) errors.push("audit must be an object");
  else {
    if (!["pending", "passed", "failed"].includes(audit.status)) errors.push("audit.status must be pending, passed, or failed");
    if (![null, "PASS", "FAIL"].includes(audit.verdict)) errors.push("audit.verdict must be PASS, FAIL, or null");
    if (audit.verdict === "PASS" && audit.status !== "passed") errors.push("audit.verdict PASS requires audit.status passed");
    if (audit.verdict === "FAIL" && audit.status !== "failed") errors.push("audit.verdict FAIL requires audit.status failed");
  }
  const flows = data.flows;
  if (!Array.isArray(flows)) { errors.push("flows must be an array"); return errors; }
  if (!flows.length && !allowEmpty) errors.push("flows must contain at least one analyzed flow");
  const evidenceEntries = new Map();
  const evidenceIds = new Set();
  if (repo && fs.existsSync(path.join(repo, FLOW_EVIDENCE_REL))) {
    try {
      const topology = JSON.parse(fs.readFileSync(path.join(repo, FLOW_EVIDENCE_REL), "utf8"));
      for (const item of topology.evidence || []) if (item && typeof item === "object" && item.id) evidenceIds.add(String(item.id));
      for (const entry of topology.entry_points || []) {
        if (!entry || typeof entry !== "object") continue;
        for (const ref of entry.evidence_refs || []) evidenceEntries.set(String(ref), entry);
      }
    } catch { errors.push("flow evidence is not valid JSON"); }
  }
  const flowIds = new Set();
  const proposalIds = new Set();
  const childIds = new Set();
  flows.forEach((flow, position) => {
    if (!flow || typeof flow !== "object" || Array.isArray(flow)) { errors.push(`flows[${position + 1}] must be an object`); return; }
    const id = String(flow.id || "");
    if (!FLOW_ID.test(id)) errors.push(`flow ${id || position + 1}: invalid id`);
    if (flowIds.has(id)) errors.push(`duplicate flow id: ${id}`);
    flowIds.add(id);
    if (!String(flow.name || "").trim()) errors.push(`flow ${id}: name is required`);
    if (!FLOW_STATES.has(flow.analysis_state)) errors.push(`flow ${id}: invalid analysis_state ${JSON.stringify(flow.analysis_state)}`);
    if (!DECISIONS.has(flow.decision || "proposed")) errors.push(`flow ${id}: invalid decision ${JSON.stringify(flow.decision)}`);
    if (flow.analysis_state === "legacy-needs-analysis") {
      if (!flow.legacy_evidence || typeof flow.legacy_evidence !== "object") errors.push(`flow ${id}: legacy_evidence is required for legacy migration`);
      return;
    }
    const refs = flow.evidence_refs === undefined ? [] : flow.evidence_refs;
    if (!Array.isArray(refs) || refs.some((ref) => typeof ref !== "string")) {
      errors.push(`flow ${id}: evidence_refs must be an array of strings`);
    } else if (evidenceIds.size) {
      for (const ref of refs) {
        if (!evidenceIds.has(ref)) errors.push(`flow ${id}: dangling evidence_ref ${ref}`);
        const entry = evidenceEntries.get(ref);
        if (["ready", "audited"].includes(flow.analysis_state) && entry && !entry.analysis_ready) {
          errors.push(`flow ${id}: referenced topology is not analysis-ready`);
        }
      }
    }
    for (const key of ["reader_question", "characteristics", "trigger", "guarantee", "terminal_outcomes", "actors", "steps", "document_design"]) {
      if (!(key in flow)) errors.push(`flow ${id}: missing required field '${key}'`);
    }
    if (!Array.isArray(flow.characteristics) || !flow.characteristics.length) errors.push(`flow ${id}: characteristics must be a non-empty array`);
    else {
      const unknown = [...new Set(flow.characteristics.filter((value) => !FLOW_CHARACTERISTICS.has(value)))].sort();
      if (unknown.length) errors.push(`flow ${id}: unknown characteristics: ${unknown.join(", ")}`);
    }
    if (!flow.trigger || typeof flow.trigger !== "object" || !TRIGGER_KINDS.has(flow.trigger.kind) || !String(flow.trigger.signature || "").trim()) errors.push(`flow ${id}: trigger requires kind and signature`);
    if (!String(flow.guarantee || "").trim()) errors.push(`flow ${id}: guarantee is required`);
    if (!Array.isArray(flow.terminal_outcomes) || !flow.terminal_outcomes.length) errors.push(`flow ${id}: terminal_outcomes must be non-empty`);
    if (!flow.actors || typeof flow.actors !== "object" || !["initiator", "visible", "hidden"].every((key) => key in flow.actors)) errors.push(`flow ${id}: actors requires initiator, visible, and hidden`);
    const orders = new Set();
    if (!Array.isArray(flow.steps) || !flow.steps.length) errors.push(`flow ${id}: steps must be non-empty`);
    else flow.steps.forEach((step) => {
      if (!step || typeof step !== "object" || Array.isArray(step)) { errors.push(`flow ${id}: each step must be an object`); return; }
      const order = step.order;
      if (!Number.isInteger(order) || order < 1 || orders.has(order)) errors.push(`flow ${id}: step order ${JSON.stringify(order)} is invalid or duplicate`);
      else orders.add(order);
      for (const key of ["name", "actor", "file", "evidence"]) if (!String(step[key] || "").trim()) errors.push(`flow ${id}: step ${order} missing ${key}`);
      const evidencePath = step.file && path.isAbsolute(step.file) ? step.file : path.join(repo || "", step.file || "");
      if (repo && step.file && !fs.existsSync(evidencePath)) errors.push(`flow ${id}: step ${order} references missing file ${step.file}`);
    });
    if (orders.size) {
      const max = Math.max(...orders);
      if (orders.size !== max || !Array.from({ length: max }, (_, i) => i + 1).every((order) => orders.has(order))) errors.push(`flow ${id}: step order must be contiguous from 1`);
    }
    errors.push(...validateStepReferences(id, flow.flow_patterns || {}, orders));
    for (const module of flow.modules || []) {
      if (!module || typeof module !== "object" || !MODULES.has(module.name) || !String(module.evidence || "").trim()) errors.push(`flow ${id}: each module requires a supported name and evidence`);
    }
    for (const failure of flow.failures || []) {
      if (!failure || typeof failure !== "object" || !FAILURE_CATEGORIES.has(failure.category)) { errors.push(`flow ${id}: each failure requires a supported category`); continue; }
      const failureFile = String(failure.file || "");
      const failurePath = failureFile && path.isAbsolute(failureFile) ? failureFile : path.join(repo || "", failureFile);
      if (!failureFile) errors.push(`flow ${id}: failure file is required`);
      else if (repo && !fs.existsSync(failurePath)) errors.push(`flow ${id}: failure references missing file ${failureFile}`);
    }
    const design = flow.document_design;
    if (!design || typeof design !== "object" || !Array.isArray(design.section_order) || !design.section_order.length) errors.push(`flow ${id}: document_design.section_order must be non-empty`);
    else if (new Set(design.section_order).size !== design.section_order.length) errors.push(`flow ${id}: document_design.section_order contains duplicates`);
    const diagrams = design && design.diagrams;
    if (!Array.isArray(diagrams)) errors.push(`flow ${id}: document_design.diagrams must be an array`);
    else {
      const sections = new Set(design.section_order || []);
      for (const diagram of diagrams) if (!diagram || typeof diagram !== "object" || !DIAGRAM_FORMS.has(diagram.form) || !sections.has(diagram.section) || !String(diagram.question || "").trim()) errors.push(`flow ${id}: diagram references a section outside section_order`);
    }
    for (const proposal of (flow.decomposition_proposals || [])) {
      if (!proposal || typeof proposal !== "object" || Array.isArray(proposal)) { errors.push(`flow ${id}: decomposition proposal must be an object`); continue; }
      const proposalId = String(proposal.id || "");
      if (!proposalId || proposalIds.has(proposalId)) errors.push(`flow ${id}: duplicate or empty decomposition proposal id ${JSON.stringify(proposalId)}`);
      proposalIds.add(proposalId);
      const proposed = Array.isArray(proposal.proposed_flows) ? proposal.proposed_flows : [];
      if (proposal.approved && !proposed.length) errors.push(`flow ${id}: approved proposal ${proposalId} has no proposed_flows`);
      for (const child of proposed) {
        const childId = child && typeof child === "object" ? String(child.id || "") : "";
        if (!FLOW_ID.test(childId) || childId === id || childIds.has(childId)) errors.push(`flow ${id}: invalid or duplicate proposed child id ${JSON.stringify(childId)}`);
        childIds.add(childId);
      }
    }
  });
  const parents = new Map(flows.filter((flow) => flow && typeof flow === "object").map((flow) => [flow.id, flow.parent_flow]));
  for (const [id, parent] of parents.entries()) {
    if (parent !== null && parent !== undefined && !flowIds.has(parent)) errors.push(`flow ${id}: parent_flow ${JSON.stringify(parent)} does not exist`);
    const seen = new Set([id]);
    let cursor = parent;
    while (cursor !== null && cursor !== undefined) {
      if (seen.has(cursor)) { errors.push(`flow ${id}: decomposition cycle detected`); break; }
      seen.add(cursor); cursor = parents.get(cursor);
    }
  }
  return errors;
}

function printErrors(errors) { for (const error of errors) console.error(`error: ${error}`); }
function refreshPreflight(repo) {
  let locked = null;
  const manifest = path.join(repo, ".docforge", "manifest.json");
  try {
    const data = JSON.parse(fs.readFileSync(manifest, "utf8"));
    locked = data.graph && data.graph.provider ? String(data.graph.provider) : null;
  } catch { /* preflight falls back to on-disk provider */ }
  const provider = ["codegraph", "gitnexus"].includes(locked) ? locked
    : (fs.existsSync(path.join(repo, ".docforge", "tmp", "gitnexus-flows.json")) ? "gitnexus"
      : (fs.existsSync(path.join(repo, ".codegraph", "codegraph.db")) ? "codegraph" : null));
  const source = provider === "gitnexus" ? path.join(repo, ".docforge", "tmp", "gitnexus-flows.json")
    : (provider === "codegraph" ? path.join(repo, ".codegraph", "codegraph.db") : null);
  if (!provider || !source || !fs.existsSync(source)) return null;
  const script = path.join(__dirname, "..", "..", "cli", "python", "flow_preflight.py");
  const result = spawnSync("python3", [script, "prepare", "--repo", repo], { encoding: "utf8" });
  return result.error || result.status !== 0 ? (result.stderr || (result.error && result.error.message) || "preflight command failed").trim() : null;
}
function runPrepare(repo, manifestPath) {
  const preflightError = refreshPreflight(repo);
  const data = defaultAnalysis(repo, manifestPath);
  const errors = validateAnalysis(data, null, true);
  if (errors.length) { printErrors(errors); return 1; }
  // stdout stays the v3 scaffold. The branch-preserving structural companion
  // is persisted for the investigator rather than flattened into a card.
  const evidencePath = path.join(repo, FLOW_EVIDENCE_REL);
  const investigation = { schemaVersion: "1.0", generated_at: nowIso(), source: evidencePath, entries: [], unresolved_gaps: [] };
  if (fs.existsSync(evidencePath)) {
    try {
      const ledger = JSON.parse(fs.readFileSync(evidencePath, "utf8"));
      const variants = (ledger.path_variants || []).filter((item) => item && typeof item === "object");
      const gaps = (ledger.evidence_gaps || []).filter((item) => item && typeof item === "object");
      for (const entry of ledger.entry_points || []) {
        if (!entry || typeof entry !== "object") continue;
        const trigger = entry.trigger && typeof entry.trigger === "object" ? entry.trigger : {};
        const subtype = trigger.subtype || "unresolved";
        investigation.entries.push({
          entry_ref: entry.id, surface_ref: entry.surface_ref, evidence_refs: entry.evidence_refs || [],
          topology_variants: variants.filter((item) => item.entry_ref === entry.id).map((item) => item.id),
          analysis_ready: Boolean(entry.analysis_ready),
          questions: [
            `What guards and rejection branches apply to this ${subtype} entry?`,
            "Which verified state changes occur on each retained path?",
            "What terminal outcomes, failures, and recovery behavior are evidenced?",
          ],
          unresolved_gaps: gaps.filter((item) => item.entry_ref === entry.id).map((item) => item.id),
        });
      }
      investigation.unresolved_gaps = gaps;
    } catch { investigation.unresolved_gaps = [{ type: "invalid-ledger", message: "flow-evidence.json could not be read" }]; }
  } else if (preflightError) {
    investigation.unresolved_gaps = [{ type: "preflight-refresh-failed", message: preflightError }];
  }
  fs.mkdirSync(path.dirname(path.join(repo, INVESTIGATION_REL)), { recursive: true });
  fs.writeFileSync(path.join(repo, INVESTIGATION_REL), dumpJson(investigation), "utf8");
  process.stdout.write(dumpJson(data)); return 0;
}
function runImport(repo, sourcePath) {
  if (!fs.existsSync(sourcePath)) return fail(`analysis file not found: ${sourcePath}`, 1);
  let data;
  try { data = JSON.parse(fs.readFileSync(sourcePath, "utf8")); }
  catch (error) { return fail(`invalid analysis JSON: ${error.message}`, 1); }
  if (!data || typeof data !== "object" || Array.isArray(data)) return fail("analysis must be a JSON object", 1);
  if (LEGACY_SCHEMA_VERSIONS.has(data.schemaVersion === undefined ? 1 : data.schemaVersion)) data = migrateLegacy(data, repo);
  const errors = validateAnalysis(data, repo, false);
  if (errors.length) { printErrors(errors); return 1; }
  writeAnalysis(repo, data); console.log(`Imported flow analysis to ${analysisPath(repo)}`); return 0;
}
function runDecide(repo, select, decline, approveDecomposition, researchPolicy) {
  const data = readAnalysis(repo);
  const byId = new Map((data.flows || []).map((flow) => [flow.id, flow]));
  const overlap = [...new Set(select.filter((id) => decline.includes(id)))].sort();
  if (overlap.length) return fail(`flow ids cannot be both selected and declined: ${overlap.join(", ")}`, 1);
  for (const id of [...select, ...decline]) if (!byId.has(id)) return fail(`unknown flow id: ${id}`, 1);
  const proposals = new Map();
  for (const flow of data.flows || []) for (const proposal of flow.decomposition_proposals || []) proposals.set(proposal.id, proposal);
  for (const id of approveDecomposition) if (!proposals.has(id)) return fail(`unknown decomposition proposal id: ${id}`, 1);
  for (const flow of data.flows || []) flow.decision = select.includes(flow.id) ? "selected" : "declined";
  for (const proposal of proposals.values()) proposal.approved = approveDecomposition.includes(proposal.id);
  data.research_policy = researchPolicy;
  writeAnalysis(repo, data);
  console.log(`Recorded ${select.length} selected flow(s), ${approveDecomposition.length} approved decomposition(s); research policy: ${researchPolicy}.`);
  return 0;
}
function runStatus(repo, asJson) {
  const data = readAnalysis(repo);
  const selected = (data.flows || []).filter((flow) => flow.decision === "selected");
  const declined = (data.flows || []).filter((flow) => flow.decision === "declined");
  const unresolved = [];
  for (const flow of data.flows || []) for (const gap of flow.evidence_gaps || []) unresolved.push({ flow_id: flow.id, gap });
  if (asJson) process.stdout.write(dumpJson({ schemaVersion: SCHEMA_VERSION, generated_at: data.generated_at, selected_flows: selected, declined_flows: declined, unresolved_gaps: unresolved, research_policy: data.research_policy, audit: data.audit }));
  else {
    console.log(`Flow analysis: ${analysisPath(repo)}`);
    console.log(`Selected flows: ${selected.length}; declined: ${declined.length}; unresolved gaps: ${unresolved.length}`);
    console.log(`Research policy: ${data.research_policy}`);
    console.log(`Pack audit: ${data.audit.status} (${data.audit.verdict || "pending"})`);
  }
  return 0;
}
function runValidate(repo) {
  const errors = validateAnalysis(readAnalysis(repo), repo, false);
  if (errors.length) { printErrors(errors); return 1; }
  console.log("flow analysis ok"); return 0;
}
function runAudit(repo, verdict, report) {
  const data = readAnalysis(repo);
  if (!fs.existsSync(report) || !fs.readFileSync(report, "utf8").trim()) return fail(`audit report must be a non-empty file: ${report}`, 1);
  const errors = validateAnalysis(data, repo, false);
  if (verdict === "PASS") {
    const selected = (data.flows || []).filter((flow) => flow.decision === "selected");
    if (!selected.length) return fail("cannot pass flow-pack audit without selected flows", 1);
    const unready = selected.filter((flow) => !["ready", "audited"].includes(flow.analysis_state)).map((flow) => flow.id);
    if (unready.length) return fail(`cannot pass flow-pack audit; analysis is not ready: ${unready.join(", ")}`, 1);
    if (errors.length) return fail("cannot pass flow-pack audit while analysis validation fails", 1);
    for (const flow of selected) flow.analysis_state = "audited";
  }
  data.audit = { status: verdict === "PASS" ? "passed" : "failed", verdict, report: String(report) };
  writeAnalysis(repo, data); console.log(`Recorded flow-pack audit ${verdict}.`); return 0;
}

function parseArgs(argv) {
  const result = { _: [] };
  const allowed = new Set(["repo", "manifest", "json", "analysis", "select", "decline", "approve-decomposition", "research-policy", "verdict", "report", "help"]);
  for (let i = 0; i < argv.length; i++) {
    const token = argv[i];
    if (token === "-h" || token === "--help") return { help: true };
    if (!token.startsWith("--")) { result._.push(token); continue; }
    const raw = token.slice(2);
    if (!allowed.has(raw)) throw new Error(`unknown option: ${token}`);
    const key = raw.replace(/-/g, "_");
    if (raw === "json" || raw === "help") result[key] = true;
    else if (["select", "decline", "approve-decomposition"].includes(raw)) {
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
  console.log("usage: flow_analysis.js <prepare|import|decide|status|validate|audit> --repo <repo> [--manifest <path>] [--json] [--analysis <path>] [--select <id>...] [--decline <id>...] [--approve-decomposition <id>...] [--research-policy <mode>] [--verdict PASS|FAIL] [--report <path>]");
}
function main(argv) {
  try {
    const args = parseArgs(argv);
    if (args.help) { usage(); return 0; }
    const command = args._[0];
    if (!command) throw new Error("a command is required");
    if (!args.repo) throw new Error("--repo is required");
    if (command === "prepare") return runPrepare(args.repo, args.manifest);
    if (command === "import") { if (!args.analysis) throw new Error("--analysis is required for import"); return runImport(args.repo, args.analysis); }
    if (command === "decide") {
      if (!args.research_policy || !RESEARCH_POLICIES.has(args.research_policy)) throw new Error("--research-policy is required for decide");
      return runDecide(args.repo, args.select || [], args.decline || [], args.approve_decomposition || [], args.research_policy);
    }
    if (command === "status") return runStatus(args.repo, args.json);
    if (command === "validate") return runValidate(args.repo);
    if (command === "audit") {
      if (!["PASS", "FAIL"].includes(args.verdict)) throw new Error("--verdict PASS|FAIL is required for audit");
      if (!args.report) throw new Error("--report is required for audit");
      return runAudit(args.repo, args.verdict, args.report);
    }
    throw new Error(`unknown command: ${command}`);
  } catch (error) { usage(); return fail(error.message, 2); }
}

module.exports = {
  SCHEMA_VERSION, EVIDENCE_WORKERS_BY_SCALE, PROPOSAL_AGENTS_BY_SCALE,
  RESEARCH_POLICIES, defaultAnalysis, validateAnalysis, normalizeAnalysis,
  migrateLegacy, main,
};

if (require.main === module) process.exitCode = main(process.argv.slice(2));
