"use strict";
/** Flow-index schema versioning shared by the flows runtime and metadata
 * migration.
 *
 * Both `flow_index` and `migrate_metadata` need the same additive upgrade, so
 * it lives here in `common` rather than inside the flows runtime. Internal
 * only: no CLI launcher.
 */

const FLOW_INDEX_VERSION = "1.2";
const SUPPORTED_FLOW_INDEX_VERSIONS = ["1.1", "1.2"];

function upgradeIndex(index) {
  // Additively upgrade a 1.1 flow index to the current schema. Mutates and
  // returns the same object; throws on unsupported versions.
  const version = String(index.version || "1.1");
  if (version === FLOW_INDEX_VERSION) return index;
  if (!SUPPORTED_FLOW_INDEX_VERSIONS.includes(version)) {
    throw new Error(`unsupported flow index version: ${version}`);
  }
  index.version = FLOW_INDEX_VERSION;
  if (index.summary && !("written" in index.summary)) {
    index.summary.written = (index.flows || [])
      .filter((row) => row && row.status === "documented" && Boolean(row.summary))
      .length;
  }
  return index;
}

module.exports = { FLOW_INDEX_VERSION, SUPPORTED_FLOW_INDEX_VERSIONS, upgradeIndex };
