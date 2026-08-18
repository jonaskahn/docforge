#!/usr/bin/env node
"use strict";
/**
 * Harvest decision and concept candidates a run should consider documenting.
 *
 * `concept` and `adr` are dynamic catalog types gated on `discovered_concept`
 * and `discovered_decision` -- conditions no code evaluates and, until now, no
 * step produced. Flows had a harvest pipeline; decisions and concepts had only
 * the instruction "must be added after discovery", with nothing to discover
 * from. The result was a `decisions/` and `concepts/` folder holding nothing
 * but an index explaining its own emptiness.
 *
 * This produces *candidates only*. Nothing is selected, nothing is written, and
 * no document is invented: every candidate carries the repository evidence that
 * suggested it, and the user decides at the write-start selection gate. The
 * decision signals are the ones `references/decision-records.md` already
 * prescribes for backfilling, including its five-to-ten ceiling.
 */

const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const { dumpJson, fail } = require("../../common/js/_util.js");

const CANDIDATES_REL = path.join(".docforge", "candidates.json");
const SCHEMA_VERSION = "1.0";
// references/decision-records.md: "Backfill five to ten load-bearing ones per
// repo -- enough to cover the architecture a reviewer will ask about -- rather
// than attempting completeness."
const DEFAULT_DECISION_LIMIT = 10;
const DEFAULT_CONCEPT_LIMIT = 8;

const DEPENDENCY_MANIFESTS = [
  "package.json", "requirements.txt", "pyproject.toml", "Pipfile",
  "go.mod", "Cargo.toml", "pom.xml", "build.gradle", "build.gradle.kts",
  "Gemfile", "composer.json", "mix.exs", "pubspec.yaml", "*.csproj",
];
const SOURCE_DIRS = ["src", "lib", "app", "internal", "pkg", "cmd", "services", "packages", "modules"];
const EXISTING_RECORD_RE = /(?:^|\/)(?:adr|adrs|rfc|rfcs|decisions?)\/|(?:^|\/)(?:ADR|RFC|DESIGN)[-_0-9]/i;
const SKIP_DIRS = new Set([
  "node_modules", "dist", "build", "target", "vendor", "__pycache__",
  ".git", ".venv", "venv", "coverage", "test", "tests", "spec", "__tests__",
  "fixtures", "migrations", "generated",
]);
const SOURCE_SUFFIXES = new Set([
  ".py", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".go", ".rs", ".java",
  ".kt", ".rb", ".php", ".cs", ".swift", ".c", ".cc", ".cpp", ".h", ".hpp",
  ".scala", ".ex", ".exs", ".dart",
]);
// Docforge's own generated trees are output, never evidence.
const GENERATED_TREES = ["docs/", "docs-portfolio/", ".docforge/"];
// A directory this large is a container, not an idea: descend one level so the
// candidate is `src/lib/kafka` rather than all 304 files under `src/lib`.
const CONTAINER_FILE_COUNT = 40;
// Below this a directory is too small to carry a concept of its own.
const MIN_CLUSTER_FILES = 3;
// Trees that hold no mechanism at any depth. Pruned outright: descending finds
// only more of the same, which is how email-template subfolders surfaced as
// architecture "concepts".
const PRUNE_TREES = new Set([
  "template", "templates", "mjmltemplates", "asset", "assets", "static",
  "style", "styles", "css", "scss", "img", "images", "icon", "icons",
  "font", "fonts", "locale", "locales", "i18n", "translations",
  "mock", "mocks", "stub", "stubs", "example", "examples", "sample",
  "samples", "snapshot", "snapshots", "seed", "seeds", "script", "scripts",
]);
// Names that describe a bag of code rather than an idea. Not emitted as a
// concept, but still descended: `src/lib/kafka` is a real subject even though
// `src/lib` is not. A "utils" or "constants" page is exactly the decorative
// documentation this harvest exists to avoid producing.
const NON_CONCEPT_NAMES = new Set([
  "util", "utils", "helper", "helpers", "common", "shared", "misc", "lib",
  "constant", "constants", "enum", "enums", "type", "types", "interface",
  "interfaces", "dto", "dtos", "model", "models", "schema", "schemas",
  "config", "configs", "settings", "doc", "docs", "internal", "core",
]);

function slugify(value) {
  const slug = value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  return slug.slice(0, 60) || "untitled";
}

/** Run a read-only git command; an unavailable repo yields no signal. */
function git(repo, ...args) {
  try {
    const stdout = execFileSync("git", ["-C", repo, ...args], {
      encoding: "utf8",
      timeout: 30000,
      stdio: ["ignore", "pipe", "ignore"],
      maxBuffer: 32 * 1024 * 1024,
    });
    return stdout.split("\n").filter((line) => line.trim());
  } catch {
    return [];
  }
}

function commitRecords(repo, args, limit) {
  const mode = args.includes("--merges") ? "--merges" : "--no-merges";
  const lines = git(
    repo, "log", mode, `--max-count=${limit}`, "--date=short",
    "--pretty=format:%H\x1f%ad\x1f%s", ...args,
  );
  const records = [];
  for (const line of lines) {
    const parts = line.split("\x1f");
    if (parts.length !== 3) continue;
    records.push({ commit: parts[0], date: parts[1], subject: parts[2].trim() });
  }
  return records;
}

/** Each significant dependency added is a decision (decision-records.md). */
function dependencyDecisions(repo, limit) {
  const out = [];
  for (const pattern of DEPENDENCY_MANIFESTS) {
    for (const filePath of git(repo, "ls-files", pattern)) {
      const records = commitRecords(repo, ["--", filePath], limit);
      if (!records.length) continue;
      out.push({
        kind: "dependency-choice",
        title: `Dependency and toolchain choices recorded in ${filePath}`,
        signal: `${records.length} tracked change(s) to ${filePath}`,
        evidence: records.slice(0, 3),
        paths: [filePath],
      });
    }
  }
  return out;
}

function sourceFileCount(directory) {
  let total = 0;
  const stack = [directory];
  while (stack.length) {
    const current = stack.pop();
    let entries;
    try {
      entries = fs.readdirSync(current, { withFileTypes: true });
    } catch {
      continue;
    }
    for (const entry of entries) {
      if (entry.isDirectory()) {
        if (!SKIP_DIRS.has(entry.name)) stack.push(path.join(current, entry.name));
      } else if (entry.isFile() && SOURCE_SUFFIXES.has(path.extname(entry.name))) {
        total += 1;
      }
    }
  }
  return total;
}

/**
 * Source directories substantial enough to carry an idea, largest first.
 *
 * A directory-level signal, not a code-graph one: it says where to look, and
 * the agent still judges whether a cross-cutting concept lives there. A
 * directory over `CONTAINER_FILE_COUNT` files is replaced by its own
 * subdirectories, so a 300-file `src/lib` yields `src/lib/kafka` instead of one
 * useless candidate named after the container.
 */
function moduleClusters(repo) {
  const usableChildren = (directory) => {
    let entries;
    try {
      entries = fs.readdirSync(directory, { withFileTypes: true });
    } catch {
      return [];
    }
    return entries
      .filter((entry) => entry.isDirectory())
      .map((entry) => entry.name)
      .filter((name) => !SKIP_DIRS.has(name) && !PRUNE_TREES.has(name.toLowerCase()) && !name.startsWith("."))
      .sort()
      .map((name) => path.join(directory, name));
  };

  const clusters = [];
  const pending = [];
  for (const name of SOURCE_DIRS) {
    const root = path.join(repo, name);
    if (fs.existsSync(root) && fs.statSync(root).isDirectory()) pending.push(...usableChildren(root));
  }
  while (pending.length) {
    const directory = pending.shift();
    const count = sourceFileCount(directory);
    if (count < MIN_CLUSTER_FILES) continue;
    const children = usableChildren(directory);
    if (count > CONTAINER_FILE_COUNT && children.length) {
      pending.push(...children);
      continue;
    }
    if (NON_CONCEPT_NAMES.has(path.basename(directory).toLowerCase())) continue;
    clusters.push([count, path.relative(repo, directory).split(path.sep).join("/")]);
  }
  clusters.sort((a, b) => b[0] - a[0] || a[1].localeCompare(b[1]));
  return clusters;
}

function rootCommit(repo) {
  const commits = git(repo, "rev-list", "--max-parents=0", "HEAD");
  return commits.length ? commits[commits.length - 1] : null;
}

/**
 * `git log --diff-filter=A` on major directories: when did each appear?
 *
 * A subsystem that arrived in the repository's first commit came with the
 * import, not with a decision anyone made here, so it carries no rationale to
 * recover and is skipped. Substantial subsystems come first: the point is the
 * architecture a reviewer will ask about, not every directory.
 */
function subsystemDecisions(repo, limit) {
  const initial = rootCommit(repo);
  const out = [];
  for (const [count, rel] of moduleClusters(repo)) {
    const records = commitRecords(repo, ["--diff-filter=A", "--", rel], limit);
    if (!records.length) continue;
    const introduced = records[records.length - 1];
    if (initial && introduced.commit === initial) continue;
    out.push({
      kind: "subsystem-introduced",
      title: `Introduce the ${rel.split("/").pop()} subsystem`,
      signal: `${count} source files under ${rel}/, first added ${introduced.date} after the initial import`,
      evidence: [introduced],
      paths: [rel],
    });
  }
  return out;
}

/** A revert or a large merge encodes a decision that was re-argued. */
function reversalDecisions(repo, limit) {
  return commitRecords(repo, ["--grep=^Revert", "--regexp-ignore-case"], limit).map((record) => ({
    kind: "reversal",
    title: record.subject.replace(/^Revert /, "").replace(/^"|"$/g, ""),
    signal: "a reverted change is a decision that was re-argued",
    evidence: [record],
    paths: [],
  }));
}

/**
 * An ADR/RFC/design file already in the repo is a decision to migrate.
 *
 * Docforge's own output trees are excluded: `docs/architecture/decisions/` is
 * what this harvest exists to fill, so reading it back as evidence would let a
 * previous empty run justify itself.
 */
function existingRecordDecisions(repo) {
  const out = [];
  for (const filePath of git(repo, "ls-files")) {
    if (GENERATED_TREES.some((prefix) => filePath.startsWith(prefix))) continue;
    if (EXISTING_RECORD_RE.test(filePath)) {
      out.push({
        kind: "existing-record",
        title: `Existing decision material in ${filePath}`,
        signal: "already-written rationale; migrate rather than reconstruct",
        evidence: [],
        paths: [filePath],
      });
    }
  }
  return out;
}

function conceptCandidates(repo, limit) {
  return moduleClusters(repo).slice(0, limit).map(([count, rel]) => ({
    kind: "module-cluster",
    title: rel.split("/").pop().replace(/-/g, " ").replace(/_/g, " "),
    signal: `${count} source files under ${rel}/`,
    evidence: [],
    paths: [rel],
  }));
}

function finalize(rows, limit) {
  const seen = new Set();
  const out = [];
  for (const row of rows) {
    const slug = slugify(row.title);
    if (seen.has(slug)) continue;
    seen.add(slug);
    out.push({
      slug,
      title: row.title,
      kind: row.kind,
      signal: row.signal,
      paths: row.paths,
      evidence: row.evidence,
      status: "candidate",
    });
    if (out.length >= limit) break;
  }
  return out;
}

function harvest(repo, decisionLimit, conceptLimit) {
  const decisions = finalize(
    [
      ...existingRecordDecisions(repo),
      ...dependencyDecisions(repo, decisionLimit),
      ...subsystemDecisions(repo, decisionLimit),
      ...reversalDecisions(repo, decisionLimit),
    ],
    decisionLimit,
  );
  const concepts = finalize(conceptCandidates(repo, conceptLimit), conceptLimit);
  return {
    version: SCHEMA_VERSION,
    decisions,
    concepts,
    summary: {
      decision_candidates: decisions.length,
      concept_candidates: concepts.length,
    },
  };
}

function parseArgs(argv) {
  const args = {
    repo: null,
    decisionLimit: DEFAULT_DECISION_LIMIT,
    conceptLimit: DEFAULT_CONCEPT_LIMIT,
    json: false,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index];
    if (flag === "--repo") args.repo = argv[++index];
    else if (flag === "--decision-limit") args.decisionLimit = Number(argv[++index]);
    else if (flag === "--concept-limit") args.conceptLimit = Number(argv[++index]);
    else if (flag === "--json") args.json = true;
    else throw new Error(`unknown argument: ${flag}`);
  }
  if (!args.repo) throw new Error("--repo is required");
  return args;
}

function main(argv = process.argv.slice(2)) {
  let args;
  try {
    args = parseArgs(argv);
  } catch (error) {
    return fail(error.message, 2);
  }
  const repo = path.resolve(args.repo);
  if (!fs.existsSync(repo) || !fs.statSync(repo).isDirectory()) {
    return fail(`repository not found: ${args.repo}`, 2);
  }
  if (!(args.decisionLimit >= 1) || !(args.conceptLimit >= 1)) {
    return fail("limits must be positive", 2);
  }
  const payload = harvest(repo, args.decisionLimit, args.conceptLimit);
  if (args.json) {
    process.stdout.write(dumpJson(payload));
    return 0;
  }
  const target = path.join(repo, CANDIDATES_REL);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, dumpJson(payload), "utf8");
  console.log(
    `${payload.summary.decision_candidates} decision and ` +
      `${payload.summary.concept_candidates} concept candidate(s) -> ${CANDIDATES_REL}`,
  );
  console.log("Candidates only: none is selected until the write-start gate.");
  return 0;
}

module.exports = { harvest, moduleClusters, slugify, main };

if (require.main === module) {
  process.exitCode = main();
}
