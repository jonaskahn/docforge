#!/usr/bin/env node
"use strict";
/* Three-way project-scale classification shared by intake discovery and
 * manifest backfill. Not a public CLI. Mirrors common/python/scale.py.
 *
 * Classifies a repository `small | medium | large` from one existing walk
 * (`detect_profiles.inventory`) plus the confirmed-profile count detection
 * already produces, so no caller re-traverses the tree and no new ignore
 * rules exist. `suggested_layout` follows the class; a user override is
 * recorded on the manifest and never re-derived.
 */

const path = require("path");
const detectProfiles = require("../../catalog/js/detect_profiles.js");

const SMALL_MAX_SOURCE_FILES = 15;
const MEDIUM_MAX_SOURCE_FILES = 200;
const BOUNDARY_NUDGE_RATIO = 0.20;
const PROFILE_NUDGE_THRESHOLD = 3;

const SOURCE_SUFFIXES = new Set([
  ".c", ".cc", ".cpp", ".cs", ".dart", ".go", ".gradle", ".h", ".hpp",
  ".java", ".js", ".jsx", ".kt", ".kts", ".m", ".mm", ".php", ".py", ".rb",
  ".rs", ".sh", ".sol", ".swift", ".ts", ".tsx",
]);

const LAYOUT_BY_CLASS = { small: "compact", medium: "standard", large: "standard" };

// True when `sourceFiles` sits within BOUNDARY_NUDGE_RATIO below a class
// boundary (e.g. 13-15 source files under the small/medium boundary of 16).
function nudgeEligible(sourceFiles, boundary) {
  return sourceFiles >= Math.ceil(boundary * (1 - BOUNDARY_NUDGE_RATIO));
}

function computeScale(repo) {
  const files = detectProfiles.inventory(repo);
  const trackedFiles = files.length;
  let sourceFiles = 0;
  for (const [relative, target] of files) {
    if (SOURCE_SUFFIXES.has(path.extname(target).toLowerCase())) sourceFiles += 1;
  }
  const detections = detectProfiles.detect(repo, false);
  const confirmedProfiles = detections.filter((item) => item.confidence === "confirmed").length;
  let scaleClass = "small";
  if (sourceFiles > MEDIUM_MAX_SOURCE_FILES) scaleClass = "large";
  else if (sourceFiles > SMALL_MAX_SOURCE_FILES) scaleClass = "medium";
  if (
    confirmedProfiles >= PROFILE_NUDGE_THRESHOLD &&
    scaleClass === "small" &&
    nudgeEligible(sourceFiles, SMALL_MAX_SOURCE_FILES + 1)
  ) {
    scaleClass = "medium";
  } else if (
    confirmedProfiles >= PROFILE_NUDGE_THRESHOLD &&
    scaleClass === "medium" &&
    nudgeEligible(sourceFiles, MEDIUM_MAX_SOURCE_FILES + 1)
  ) {
    scaleClass = "large";
  }
  return {
    class: scaleClass,
    suggested_layout: LAYOUT_BY_CLASS[scaleClass],
    signals: {
      tracked_files: trackedFiles,
      source_files: sourceFiles,
      confirmed_profiles: confirmedProfiles,
    },
  };
}

module.exports = {
  SMALL_MAX_SOURCE_FILES,
  MEDIUM_MAX_SOURCE_FILES,
  BOUNDARY_NUDGE_RATIO,
  PROFILE_NUDGE_THRESHOLD,
  SOURCE_SUFFIXES,
  LAYOUT_BY_CLASS,
  computeScale,
};
