#!/usr/bin/env node
"use strict";
/** Detect Docforge shape, platform, framework, and concern profile candidates. */

const fs = require("fs");
const path = require("path");
const manifestDeps = require("../../common/js/manifest_deps.js");
const discoveryGate = require("./discovery_gate.js");
const queryCatalog = require("./query_catalog.js");

const SKILL_ROOT = path.resolve(fs.realpathSync(__dirname), "..", "..", "..");
const DIMENSIONS = ["shapes", "platforms", "frameworks", "concerns"];
const IGNORED = new Set([
  ".git", ".codegraph", ".gitnexus", ".docforge", "node_modules",
  ".build", "build", "dist", "DerivedData", ".venv", "venv", "__pycache__",
]);
const MAX_FILES = 25000;
const MAX_CONTENT_BYTES = 1024 * 1024;
const MAX_TOTAL_CONTENT_BYTES = 32 * 1024 * 1024;
const MAX_EVIDENCE = 20;
const MAX_EXCERPTS = 8;
const MAX_EXCERPT_CHARS = 400;
const TEXT_SUFFIXES = new Set([
  ".c", ".cc", ".cpp", ".cs", ".dart", ".go", ".gradle", ".h", ".hpp",
  ".csproj", ".html", ".java", ".js", ".json", ".jsx", ".kt", ".kts", ".m",
  ".md", ".mm", ".pbxproj", ".php", ".plist", ".properties", ".py", ".rb", ".rs", ".sh",
  ".sol", ".swift", ".toml", ".ts", ".tsx", ".txt", ".xml", ".yaml", ".yml",
]);
const TEXT_NAMES = new Set(["CMakeLists.txt", "Dockerfile", "Gemfile", "Makefile", "Podfile", "requirements.txt"]);

function compareText(left, right) {
  return Buffer.compare(Buffer.from(left, "utf8"), Buffer.from(right, "utf8"));
}
function globRegex(pattern) {
  let expression = "";
  for (let index = 0; index < pattern.length; index++) {
    const char = pattern[index];
    if (char === "*" && pattern[index + 1] === "*") {
      expression += ".*";
      index++;
    } else if (char === "*") expression += "[^/]*";
    else if (char === "?") expression += "[^/]";
    else expression += char.replace(/[\\^$+?.()|[\]{}]/g, "\\$&");
  }
  return new RegExp(`^${expression}$`);
}
function matchesPath(relative, pattern) {
  const patterns = pattern.startsWith("**/") ? [pattern, pattern.slice(3)] : [pattern];
  return patterns.some((candidate) => {
    const regex = globRegex(candidate);
    return regex.test(relative) || (!candidate.includes("/") && regex.test(path.posix.basename(relative)));
  });
}
function signalStrength(signal) {
  if (signal.strength === "strong" || signal.strength === "weak") return signal.strength;
  if (signal.kind === "dependency") return "strong";
  if (signal.kind === "content") return "weak";
  return "strong";
}
function cueForSignal(signal, relative) {
  if (signal.kind === "dependency") return `dep:${signal.ecosystem || ""}:${signal.name || ""}`;
  if (signal.kind === "content") {
    const token = String(signal.contains || "content").trim().toLowerCase().replace(/ /g, "-");
    return `content:${token.slice(0, 48)}`;
  }
  const pattern = signal.pattern || "";
  const parts = pattern.replace(/\*\*\//g, "").split("/").filter((part) => part && !part.includes("*"));
  if (parts.length) return `path:${parts[parts.length - 1].toLowerCase()}`;
  if (relative) {
    const fragments = relative.split("/").filter((part) => part && part !== "." && part !== "..");
    if (fragments.length) {
      return `path:${(fragments.length > 1 ? fragments[fragments.length - 2] : fragments[0]).toLowerCase()}`;
    }
  }
  return "path:unknown";
}
// Collect files under `repo` for profile-signal matching. Stops short of a
// nested repository's own contents — a subdirectory that is itself a
// separate git repository (its own .git dir or file, the same marker a
// submodule worktree uses) is a distinct project; its source must not be
// blended into this repo's own profile evidence.
function inventory(repo) {
  const found = [];
  function walk(directory) {
    if (found.length >= MAX_FILES) return;
    for (const entry of fs.readdirSync(directory, { withFileTypes: true }).sort((a, b) => compareText(a.name, b.name))) {
      if (IGNORED.has(entry.name)) continue;
      const target = path.join(directory, entry.name);
      if (entry.isDirectory()) {
        const gitMarker = path.join(target, ".git");
        if (fs.existsSync(gitMarker)) continue; // nested repo boundary; its evidence is its own
        walk(target);
      }
      else if (entry.isFile()) found.push([path.relative(repo, target).split(path.sep).join("/"), target]);
      if (found.length >= MAX_FILES) return;
    }
  }
  walk(repo);
  return found;
}
function attachAmbiguousWith(results) {
  const byCue = new Map();
  for (const item of results) {
    for (const cue of item.cues || []) {
      if (cue.startsWith("path:") || cue.startsWith("content:")) {
        if (!byCue.has(cue)) byCue.set(cue, []);
        byCue.get(cue).push(item);
      }
    }
  }
  for (const item of results) {
    const peers = [];
    const seen = new Set();
    for (const cue of item.cues || []) {
      for (const peer of byCue.get(cue) || []) {
        const key = `${peer.dimension}\0${peer.id}`;
        if (key === `${item.dimension}\0${item.id}` || seen.has(key)) continue;
        if (peer.match_strength === "strong" && item.match_strength === "strong") continue;
        seen.add(key);
        peers.push({
          dimension: peer.dimension,
          id: peer.id,
          confidence: peer.confidence,
          cue,
        });
      }
    }
    peers.sort((a, b) => compareText(`${a.dimension}:${a.id}:${a.cue}`, `${b.dimension}:${b.id}:${b.cue}`));
    item.ambiguous_with = peers;
  }
}
function persistManifestDeps(repo, dependencies) {
  const scratch = path.join(repo, ".docforge", "scratch");
  fs.mkdirSync(scratch, { recursive: true });
  const target = path.join(scratch, "manifest-deps.json");
  fs.writeFileSync(
    target,
    `${JSON.stringify(
      {
        generated_at: new Date().toISOString().replace(/\.\d{3}Z$/, "+00:00"),
        dependencies,
      },
      null,
      2,
    )}\n`,
  );
  return target;
}

// Pass `files` to reuse an `inventory(repo)` the caller already has — the walk
// is the expensive part, and several callers need both.
function detect(repo, persist = true, files = null) {
  const profiles = queryCatalog.loadProfiles();
  if (files === null) files = inventory(repo);
  const dependencies = manifestDeps.extractDependencies(files);
  if (persist) persistManifestDeps(repo, dependencies);
  const cache = new Map();
  let cachedBytes = 0;
  const results = [];
  for (const dimension of DIMENSIONS) {
    for (const profile of profiles[dimension]) {
      const evidence = new Set();
      const matchedStrengths = new Set();
      const cues = new Set();
      for (const signal of profile.signals || []) {
        const strength = signalStrength(signal);
        if (signal.kind === "dependency") {
          const ecosystem = signal.ecosystem || "";
          const key = manifestDeps.normalize(ecosystem, signal.name || "");
          for (const manifestPath of (dependencies[ecosystem] || {})[key] || []) {
            evidence.add(manifestPath);
            matchedStrengths.add(strength);
            cues.add(cueForSignal(signal));
          }
          continue;
        }
        for (const [relative, target] of files) {
          if (!matchesPath(relative, signal.pattern)) continue;
          if (signal.kind === "content") {
            const size = fs.statSync(target).size;
            if (!TEXT_SUFFIXES.has(path.extname(target).toLowerCase()) && !TEXT_NAMES.has(path.basename(target))) continue;
            if (size > MAX_CONTENT_BYTES) continue;
            if (!cache.has(target)) {
              if (cachedBytes + size > MAX_TOTAL_CONTENT_BYTES) continue;
              cache.set(target, fs.readFileSync(target, "utf8"));
              cachedBytes += size;
            }
            if (!cache.get(target).includes(signal.contains || "")) continue;
          }
          evidence.add(relative);
          matchedStrengths.add(strength);
          cues.add(cueForSignal(signal, relative));
        }
      }
      if (!evidence.size) continue;
      const paths = [...evidence].sort(compareText);
      const cueList = [...cues].sort(compareText);
      const hasStrong = matchedStrengths.has("strong");
      results.push({
        dimension,
        id: profile.id,
        confidence: hasStrong ? "confirmed" : "candidate",
        evidence: paths.slice(0, MAX_EVIDENCE),
        match_strength: hasStrong ? "strong" : "weak",
        cues: cueList,
        ambiguous_with: [],
      });
    }
  }
  attachAmbiguousWith(results);
  return results;
}
function dependencySummary(dependencies) {
  const summary = {};
  for (const ecosystem of Object.keys(dependencies).sort(compareText)) {
    summary[ecosystem] = Object.keys(dependencies[ecosystem]).sort(compareText);
  }
  return summary;
}
function excerpts(repo, evidencePaths, files) {
  const index = new Map(files);
  const out = [];
  for (const relative of evidencePaths) {
    if (out.length >= MAX_EXCERPTS) break;
    const target = index.get(relative);
    if (!target) continue;
    if (!TEXT_SUFFIXES.has(path.extname(target).toLowerCase()) && !TEXT_NAMES.has(path.basename(target))) continue;
    let size;
    try { size = fs.statSync(target).size; } catch { continue; }
    if (size > MAX_CONTENT_BYTES) continue;
    const text = fs.readFileSync(target, "utf8").slice(0, MAX_EXCERPT_CHARS);
    out.push({ path: relative, text, max_chars: MAX_EXCERPT_CHARS });
  }
  return out;
}
function emitGatePack(repo) {
  const profiles = queryCatalog.loadProfiles();
  const files = inventory(repo);
  const dependencies = manifestDeps.extractDependencies(files);
  const detections = detect(repo, true, files);
  const strong = detections.filter((item) => item.confidence === "confirmed");
  const weak = detections.filter((item) => item.confidence === "candidate");
  const cueMap = new Map();
  for (const item of detections) {
    for (const cue of item.cues || []) {
      if (!cueMap.has(cue)) {
        cueMap.set(cue, {
          cue,
          surface: item.evidence[0] || cue,
          kind: cue.startsWith("dep:") ? "dependency" : cue.startsWith("content:") ? "content_keyword" : "path_fragment",
          candidate_profiles: [],
        });
      }
      const bucket = cueMap.get(cue);
      const entry = {
        dimension: item.dimension,
        id: item.id,
        why: item.match_strength === "strong" ? "strong signal" : "weak path or content signal",
      };
      if (!bucket.candidate_profiles.some((row) => row.dimension === entry.dimension && row.id === entry.id)) {
        bucket.candidate_profiles.push(entry);
      }
    }
  }
  const peerConcerns = ["persistence", "ai-ml"];
  for (const [, bucket] of cueMap) {
    if (!bucket.cue.startsWith("path:")) continue;
    const present = new Set(bucket.candidate_profiles.map((row) => `${row.dimension}\0${row.id}`));
    for (const concernId of peerConcerns) {
      const key = `concerns\0${concernId}`;
      if (present.has(key)) continue;
      bucket.candidate_profiles.push({
        dimension: "concerns",
        id: concernId,
        why: "catalog concern available; unconfirmed",
      });
    }
  }
  const cues = [...cueMap.values()].sort((a, b) => compareText(a.cue, b.cue));
  for (const bucket of cues) {
    bucket.candidate_profiles.sort((a, b) => compareText(`${a.dimension}:${a.id}`, `${b.dimension}:${b.id}`));
  }
  const evidencePaths = [];
  for (const item of detections) {
    for (const evidencePath of item.evidence) {
      if (!evidencePaths.includes(evidencePath)) evidencePaths.push(evidencePath);
    }
  }
  const catalogIds = {};
  for (const dimension of [...DIMENSIONS, "audiences"]) {
    catalogIds[dimension] = profiles[dimension].map((profile) => profile.id).sort(compareText);
  }
  const queryHints = {};
  for (const dimension of DIMENSIONS) {
    for (const profile of profiles[dimension]) {
      if (profile.query_hints && profile.query_hints.length) queryHints[profile.id] = [...profile.query_hints];
    }
  }
  return {
    repo: fs.realpathSync(repo),
    detections,
    strong_detections: strong,
    weak_detections: weak,
    cues,
    excerpts: excerpts(repo, evidencePaths, files),
    dependencies: dependencySummary(dependencies),
    // Lazy require: common/scale requires this module, so a module-level
    // require here would be circular. The pack reuses the same walk and
    // extraction.
    scale: require("../../common/js/scale.js").computeScale(repo, files, detections, dependencies),
    catalog_ids: catalogIds,
    query_hints: queryHints,
    cue_hints: queryCatalog.loadIndex().cue_hints || [],
    needs_gate: discoveryGate.needsGate(detections, cues),
  };
}
function parseArgs(argv) {
  const result = { json: false, emitGatePack: false };
  for (let index = 0; index < argv.length; index++) {
    const token = argv[index];
    if (token === "--json") result.json = true;
    else if (token === "--emit-gate-pack") result.emitGatePack = true;
    else if (token === "--repo") {
      if (index + 1 >= argv.length || argv[index + 1].startsWith("--")) throw new Error("option requires a value: --repo");
      result.repo = argv[++index];
    } else if (token === "-h" || token === "--help") result.help = true;
    else throw new Error(`unknown option: ${token}`);
  }
  return result;
}
function usage() {
  console.log("usage: detect_profiles.js --repo <path> [--json] [--emit-gate-pack]");
}
function main() {
  let args;
  try {
    args = parseArgs(process.argv.slice(2));
  } catch (error) {
    usage();
    console.error(`error: ${error.message}`);
    return 2;
  }
  if (args.help) {
    usage();
    return 0;
  }
  if (!args.repo || !fs.existsSync(args.repo) || !fs.statSync(args.repo).isDirectory()) {
    console.error(`error: not a directory: ${args.repo || ""}`);
    return 2;
  }
  const repo = fs.realpathSync(args.repo);
  if (args.emitGatePack) {
    console.log(JSON.stringify(emitGatePack(repo), null, 2));
    return 0;
  }
  const results = detect(repo);
  if (args.json) {
    console.log(JSON.stringify({ repo, detections: results }, null, 2));
    return 0;
  }
  console.log(`Profile detection for ${repo}`);
  if (!results.length) {
    console.log("No profiles detected.");
    return 0;
  }
  for (const result of results) {
    console.log(`${result.confidence.toUpperCase().padEnd(9)} ${result.dimension.padEnd(10)} ${result.id} [${result.match_strength}] — ${result.evidence.join(", ")}`);
  }
  return 0;
}
if (require.main === module) process.exit(main());
module.exports = { detect, emitGatePack, inventory, main };
