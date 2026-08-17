"use strict";
/** Deterministic generation-plan rendering shared by init, preview, and revise.
 *  Plans each manifest document (and each main-priority flow from the flow
 *  index) with a per-document action so a fresh start or revise run shows
 *  exactly which documents will be added, updated, rewritten, or left
 *  unchanged before anything is written. Node mirrors plan.py byte-for-byte.
 */

const fs = require("fs");
const path = require("path");
const pf = require("./provenance_frontmatter.js");
const store = require("./provenance_store.js");

const WRITTEN = new Set(["generated", "needs_review", "complete"]);

function flowIsMainPriority(row) {
  if (row.priority === "main") return true;
  if (row.priority === "deferred") return false;
  if (row.status === "main" || row.status === "documented") return true;
  if (row.status === "placeholder" && row.priority === "main") return true;
  return false;
}

function documentAction(repo, doc, revise) {
  const status = doc.status || "planned";
  if (status === "skipped") return ["skip", "explicitly skipped"];
  if (status === "retired") return ["retired", "out of scope; content moved by retire; entry preserved"];
  const target = path.join(repo, ...doc.path.split("/"));
  if (!fs.existsSync(target) || !fs.statSync(target).isFile()) {
    if (WRITTEN.has(status)) return ["add", `file missing despite ${status}`];
    return ["add", "planned; will be scaffolded"];
  }
  let state;
  let provenance;
  const meta = store.readDocMetadata(repo, doc);
  if (meta.state === "ok") {
    state = "ok";
    provenance = meta.provenance;
  } else if (meta.state === "inline") {
    return ["update", "inline provenance pending sidecar migration"];
  } else if (meta.state === "legacy") {
    return ["rewrite", "legacy provenance pending migration"];
  } else if (meta.state === "obsolete") {
    return ["rewrite", "obsolete provenance schema; run migrate_metadata"];
  } else {
    return ["rewrite", "provenance missing or unparseable"];
  }
  if (state !== "ok" || !provenance || typeof provenance !== "object") {
    return ["rewrite", "provenance missing or unparseable"];
  }
  if (status === "in_progress" || status === "needs_review") {
    return ["rewrite", "status requires re-grounding"];
  }
  if (status === "planned") return ["update", "adopts existing file into the plan"];
  if (status === "generated") return ["update", "will re-ground changed sections"];
  if (revise) return ["unchanged", "fresh; re-check on structural change"];
  return ["unchanged", "already complete"];
}

// `groups` narrows which documents this run works on -- the transient `<area>`
// filter. It never touches `project.groups`, the persistent scope, because
// narrowing that would make every out-of-area written document a retire
// candidate.
function planEntries(repo, manifest, flowIndexPath, revise, groups = null) {
  const scoped = new Set(groups || []);
  const entries = [];
  for (const doc of manifest.documents || []) {
    if (scoped.size && !scoped.has(doc.group)) continue;
    const [action, reason] = documentAction(repo, doc, revise);
    entries.push({
      id: doc.id,
      path: doc.path,
      action,
      reason,
      flow_id: null,
      flow_name: null,
      is_flow: false,
    });
  }
  if (flowIndexPath && fs.existsSync(flowIndexPath)) {
    let index = {};
    try {
      index = JSON.parse(fs.readFileSync(flowIndexPath, "utf8"));
    } catch {
      index = {};
    }
    for (const row of index.flows || []) {
      if (!flowIsMainPriority(row)) continue;
      const flowId = String(row.id || "");
      const slug = String(row.slug || flowId);
      const flowPath = String(row.doc_path || `docs/flows/${slug}.md`);
      const doc = (manifest.documents || []).find(
        (entry) => entry.type === "flow" && entry.path === flowPath,
      );
      let action;
      let reason;
      if (!doc) {
        action = "add";
        reason = `flow ${flowId}: not yet planned`;
      } else {
        [action, reason] = documentAction(repo, doc, revise);
      }
      entries.push({
        id: flowId,
        path: flowPath,
        action,
        reason,
        flow_id: flowId,
        flow_name: String(row.display_name || row.name || flowId),
        is_flow: true,
      });
    }
  }
  return entries;
}

function planLines(repo, manifest, flowIndexPath, revise, groups = null) {
  const scoped = new Set(groups || []);
  const docs = (manifest.documents || []).filter(
    (doc) => !["skipped", "retired"].includes(doc.status) && (!scoped.size || scoped.has(doc.group)),
  );
  const project = manifest.project || {};
  const lines = [`Generation plan — tier: ${project.tier || "unknown"}`];
  const profiles = project.profiles || {};
  for (const dimension of ["shapes", "platforms", "frameworks", "concerns", "audiences"]) {
    lines.push(`  ${dimension}: ${(profiles[dimension] || []).join(", ") || "none"}`);
  }
  lines.push("");
  const entries = planEntries(repo, manifest, flowIndexPath, revise);
  for (const entry of entries.filter((item) => !item.is_flow)) {
    lines.push(`${entry.id.padEnd(28)}  ${entry.path}`);
    lines.push(`     action: ${entry.action} — ${entry.reason}`);
  }
  const flowEntries = entries.filter((item) => item.is_flow);
  if (flowEntries.length) {
    lines.push("");
    lines.push("Flows:");
    for (const entry of flowEntries) {
      const label = entry.flow_id ? `${entry.flow_name} (${entry.flow_id})` : entry.path;
      lines.push(`  ${label} → ${entry.path}  [${entry.action}] ${entry.reason}`);
    }
  }
  lines.push("");
  const flowCount = docs.filter((doc) => (doc.requires || []).includes("flow_graph")).length;
  let summary = `${docs.length} manifest documents; ${flowCount} require a flow graph`;
  if (flowEntries.length) summary += `; ${flowEntries.length} main-priority flow documents`;
  lines.push(`${summary}.`);
  return lines;
}

module.exports = { planLines, planEntries, documentAction, flowIsMainPriority };
