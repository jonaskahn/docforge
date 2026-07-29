#!/usr/bin/env node
"use strict";
/** Detect Docforge shape, platform, framework, and concern profile candidates. */

const fs = require("fs");
const path = require("path");
const manifestDeps = require("./manifest_deps.js");

const SKILL_ROOT = path.resolve(__dirname, "..");
const CATALOG_PATH = path.join(SKILL_ROOT, ".metadata", "catalog.json");
const DIMENSIONS = ["shapes", "platforms", "frameworks", "concerns"];
const IGNORED = new Set([
  ".git", ".codegraph", ".gitnexus", ".docforge", "node_modules",
  ".build", "build", "dist", "DerivedData", ".venv", "venv", "__pycache__",
]);
const MAX_FILES = 25000;
const MAX_CONTENT_BYTES = 1024 * 1024;
const MAX_TOTAL_CONTENT_BYTES = 32 * 1024 * 1024;
const MAX_EVIDENCE = 20;
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
function inventory(repo) {
  const found = [];
  function walk(directory) {
    if (found.length >= MAX_FILES) return;
    for (const entry of fs.readdirSync(directory, { withFileTypes: true }).sort((a, b) => compareText(a.name, b.name))) {
      if (IGNORED.has(entry.name)) continue;
      const target = path.join(directory, entry.name);
      if (entry.isDirectory()) walk(target);
      else if (entry.isFile()) found.push([path.relative(repo, target).split(path.sep).join("/"), target]);
      if (found.length >= MAX_FILES) return;
    }
  }
  walk(repo);
  return found;
}
function detect(repo) {
  const catalog = JSON.parse(fs.readFileSync(CATALOG_PATH, "utf8"));
  const files = inventory(repo);
  const dependencies = manifestDeps.extractDependencies(files);
  const cache = new Map();
  let cachedBytes = 0;
  const results = [];
  for (const dimension of DIMENSIONS) {
    for (const profile of catalog.profiles[dimension]) {
      const evidence = new Set();
      const matchedKinds = new Set();
      for (const signal of profile.signals || []) {
        if (signal.kind === "dependency") {
          const ecosystem = signal.ecosystem || "";
          const key = manifestDeps.normalize(ecosystem, signal.name || "");
          const bucket = (dependencies[ecosystem] || {})[key] || [];
          for (const manifestPath of bucket) {
            evidence.add(manifestPath);
            matchedKinds.add("dependency");
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
          matchedKinds.add(signal.kind);
        }
      }
      if (!evidence.size) continue;
      const paths = [...evidence].sort(compareText);
      results.push({
        dimension,
        id: profile.id,
        confidence: matchedKinds.has("path") || matchedKinds.has("dependency") || paths.length >= 2 ? "confirmed" : "candidate",
        evidence: paths.slice(0, MAX_EVIDENCE),
      });
    }
  }
  return results;
}
function parseArgs(argv) {
  const result = { json: false };
  for (let index = 0; index < argv.length; index++) {
    const token = argv[index];
    if (token === "--json") result.json = true;
    else if (token === "--repo") {
      if (index + 1 >= argv.length || argv[index + 1].startsWith("--")) throw new Error("option requires a value: --repo");
      result.repo = argv[++index];
    } else if (token === "-h" || token === "--help") result.help = true;
    else throw new Error(`unknown option: ${token}`);
  }
  return result;
}
function usage() {
  console.log("usage: detect_profiles.js --repo <path> [--json]");
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
    console.log(`${result.confidence.toUpperCase().padEnd(9)} ${result.dimension.padEnd(10)} ${result.id} — ${result.evidence.join(", ")}`);
  }
  return 0;
}
if (require.main === module) process.exit(main());
module.exports = { detect };
