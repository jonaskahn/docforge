"use strict";
/** Flow-index schema versioning shared by the flows runtime and metadata
 * migration.
 *
 * Both `flow_index` and `migrate_metadata` need the same additive upgrade, so
 * it lives here in `common` rather than inside the flows runtime. Internal
 * only: no CLI launcher.
 */

const FLOW_INDEX_VERSION = "1.4";
const SUPPORTED_FLOW_INDEX_VERSIONS = ["1.1", "1.2", "1.3", "1.4"];

function upgradeIndex(index) {
  // Additively upgrade a 1.1–1.3 flow index to the current schema. Mutates and
  // returns the same object; throws on unsupported versions.
  const version = String(index.version || "1.1");
  if (!SUPPORTED_FLOW_INDEX_VERSIONS.includes(version)) {
    throw new Error(`unsupported flow index version: ${version}`);
  }
  if (version === "1.1" && index.summary && !("written" in index.summary)) {
    index.summary.written = (index.flows || [])
      .filter((row) => row && row.status === "documented" && Boolean(row.summary))
      .length;
  }
  if (version === "1.1" || version === "1.2") {
    for (const row of index.flows || []) {
      if (!row || typeof row !== "object") continue;
      if (!("parent_flow" in row)) row.parent_flow = null;
      if (!("analysis_state" in row)) {
        row.analysis_state = row.status === "documented" || Boolean(row.written)
          ? "ready" : "not-analyzed";
      }
    }
  }
  if (["1.1", "1.2", "1.3"].includes(version)) {
    for (const row of index.flows || []) {
      if (!row || typeof row !== "object") continue;
      if (!("surface_ref" in row)) row.surface_ref = null;
      if (!("evidence_refs" in row)) row.evidence_refs = [];
    }
  }
  index.version = FLOW_INDEX_VERSION;
  return index;
}

module.exports = { FLOW_INDEX_VERSION, SUPPORTED_FLOW_INDEX_VERSIONS, upgradeIndex };
