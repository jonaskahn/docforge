#!/usr/bin/env node
"use strict";
/* Three-way project-scale classification shared by intake discovery and
 * manifest backfill. Not a public CLI. Mirrors common/python/scale.py.
 *
 * Classifies a repository `small | medium | large` from one existing walk
 * (`detect_profiles.inventory`) plus the confirmed-profile count detection
 * already produces, so no caller re-traverses the tree and no new ignore
 * rules exist. Declared-dependency breadth (`manifest_deps.extractDependencies`)
 * and flow breadth (`.docforge/flow-index.json` when present) promote a class
 * at most one step above its source-file class — they never demote. The
 * profile count still nudges boundary-adjacent repos. `suggested_layout`
 * follows the class; a user override is recorded on the manifest and never
 * re-derived.
 */

const fs = require("fs");
const path = require("path");
const detectProfiles = require("../../catalog/js/detect_profiles.js");
const manifestDeps = require("./manifest_deps.js");

const SMALL_MAX_SOURCE_FILES = 49;
const MEDIUM_MAX_SOURCE_FILES = 200;
const DEP_NUDGE_SMALL = 40;
const DEP_NUDGE_MEDIUM = 200;
const FLOW_NUDGE_SMALL = 10;
const FLOW_NUDGE_MEDIUM = 40;
const BOUNDARY_NUDGE_RATIO = 0.20;
const PROFILE_NUDGE_THRESHOLD = 3;

const SOURCE_SUFFIXES = new Set([
  ".c", ".cc", ".cpp", ".cs", ".dart", ".go", ".gradle", ".h", ".hpp",
  ".java", ".js", ".jsx", ".kt", ".kts", ".m", ".mm", ".php", ".py", ".rb",
  ".rs", ".sh", ".sol", ".swift", ".ts", ".tsx",
]);

const LAYOUT_BY_CLASS = { small: "compact", medium: "standard", large: "standard" };

const COMPACT_TIERS = new Set(["spine", "diligence"]);

// An explicitly requested layout the tier does not permit.
class LayoutTierError extends Error {}

// Resolve the layout a tier permits, as `{ layout, decided_by }`.
//
// Portfolio is the whole point of this function: its value is per-member
// separation — an inventory row and a system-context view per repository — so
// folding the collection layer into one file erases exactly the distinctions
// the tier exists to make. Compact therefore covers Spine and Diligence only.
//
// An explicit compact pick at Portfolio throws instead of being coerced: a
// user decision is never silently rewritten. A *detected* compact layout is
// forced to standard and says so via `tier-constraint`, because a small
// collection root would otherwise inherit compact from LAYOUT_BY_CLASS.
function layoutFor(tier, layout, { explicit }) {
  if (layout !== "compact" || COMPACT_TIERS.has(tier)) {
    return { layout, decided_by: explicit ? "user" : "detected" };
  }
  if (explicit) {
    throw new LayoutTierError(
      `${tier} tier requires standard layout; `
        + "compact covers spine and diligence only",
    );
  }
  return { layout: "standard", decided_by: "tier-constraint" };
}

// True when `sourceFiles` sits within BOUNDARY_NUDGE_RATIO below a class
// boundary (e.g. 40-49 source files under the small/medium boundary of 50).
function nudgeEligible(sourceFiles, boundary) {
  return sourceFiles >= Math.ceil(boundary * (1 - BOUNDARY_NUDGE_RATIO));
}

// Rows in the harvested flow index, or 0 when no index exists yet. A single
// read-only file read — never a tree walk.
function flowCandidates(repo) {
  const indexPath = path.join(repo, ".docforge", "flow-index.json");
  let data;
  try {
    data = JSON.parse(fs.readFileSync(indexPath, "utf8"));
  } catch (error) {
    return 0;
  }
  if (data && typeof data === "object" && data.summary && typeof data.summary === "object" && Number.isInteger(data.summary.total)) {
    return data.summary.total;
  }
  return Array.isArray(data && data.flows) ? data.flows.length : 0;
}

// Pass `files`, `detections`, and/or `dependencies` when the caller already
// has them — all derive from the same single `inventory(repo)` walk.
function computeScale(repo, files = null, detections = null, dependencies = null) {
  if (files === null) files = detectProfiles.inventory(repo);
  const trackedFiles = files.length;
  let sourceFiles = 0;
  for (const [relative, target] of files) {
    if (SOURCE_SUFFIXES.has(path.extname(target).toLowerCase())) sourceFiles += 1;
  }
  if (detections === null) detections = detectProfiles.detect(repo, false, files);
  const confirmedProfiles = detections.filter((item) => item.confidence === "confirmed").length;
  if (dependencies === null) dependencies = manifestDeps.extractDependencies(files);
  let declaredDependencies = 0;
  for (const ecosystem of Object.keys(dependencies)) {
    declaredDependencies += Object.keys(dependencies[ecosystem]).length;
  }
  const flowCandidatesCount = flowCandidates(repo);
  let scaleClass = "small";
  if (sourceFiles > MEDIUM_MAX_SOURCE_FILES) scaleClass = "large";
  else if (sourceFiles > SMALL_MAX_SOURCE_FILES) scaleClass = "medium";
  // Dependency and flow breadth promote at most one class above the
  // source-file class; the profile count nudges boundary-adjacent repos.
  if (scaleClass === "small") {
    if (declaredDependencies >= DEP_NUDGE_SMALL || flowCandidatesCount >= FLOW_NUDGE_SMALL) {
      scaleClass = "medium";
    } else if (
      confirmedProfiles >= PROFILE_NUDGE_THRESHOLD &&
      nudgeEligible(sourceFiles, SMALL_MAX_SOURCE_FILES + 1)
    ) {
      scaleClass = "medium";
    }
  } else if (scaleClass === "medium") {
    if (declaredDependencies >= DEP_NUDGE_MEDIUM || flowCandidatesCount >= FLOW_NUDGE_MEDIUM) {
      scaleClass = "large";
    } else if (
      confirmedProfiles >= PROFILE_NUDGE_THRESHOLD &&
      nudgeEligible(sourceFiles, MEDIUM_MAX_SOURCE_FILES + 1)
    ) {
      scaleClass = "large";
    }
  }
  return {
    class: scaleClass,
    suggested_layout: LAYOUT_BY_CLASS[scaleClass],
    signals: {
      tracked_files: trackedFiles,
      source_files: sourceFiles,
      confirmed_profiles: confirmedProfiles,
      declared_dependencies: declaredDependencies,
      flow_candidates: flowCandidatesCount,
    },
  };
}

module.exports = {
  SMALL_MAX_SOURCE_FILES,
  MEDIUM_MAX_SOURCE_FILES,
  DEP_NUDGE_SMALL,
  DEP_NUDGE_MEDIUM,
  FLOW_NUDGE_SMALL,
  FLOW_NUDGE_MEDIUM,
  BOUNDARY_NUDGE_RATIO,
  PROFILE_NUDGE_THRESHOLD,
  SOURCE_SUFFIXES,
  LAYOUT_BY_CLASS,
  COMPACT_TIERS,
  LayoutTierError,
  layoutFor,
  computeScale,
};
