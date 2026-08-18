#!/usr/bin/env node
"use strict";
/**
 * Expand repo-relative source links into pinned permalinks.
 *
 * The writer must never hand-assemble a URL containing a 40-character commit
 * sha, so it writes the readable authoring form:
 *
 *     ([the crawl-job runner](src/lib/crawler/crawlerjob.js#L397-L399))
 *
 * and this pass rewrites it, at materialization and again on revise, into an
 * absolute permalink at the commit the document was grounded against.
 *
 * Every target is validated first -- the path must exist and the range must be
 * inside the file -- so a stale reference fails loudly here rather than 404ing
 * for a reader later. That is the whole point of doing this mechanically: the
 * previous output carried 1,064 hand-written `path:line` mentions, none of them
 * checked, all of them pinned to a commit that had already moved.
 *
 * Read-only unless `--write`. Exit `0` clean, `1` unresolved, `2` usage.
 */

const fs = require("fs");
const path = require("path");

const { dumpJson, fail, loadManifest } = require("../../common/js/_util.js");
const { AGENT_CONTEXT_GROUP } = require("../../common/js/agent_context.js");
const { blobUrl, headCommit, identityOf } = require("../../common/js/repo_identity.js");
const store = require("../../common/js/provenance_store.js");

// `[label](target)` where the target is a repository-relative source path with an
// optional line fragment. An absolute URL, an anchor, and a `.md` link are all
// left alone: only the authoring form is rewritten.
const AUTHORING_LINK = new RegExp(
  "\\[(?<label>[^\\]]+)\\]\\((?<path>(?!https?://|mailto:|#|/)[A-Za-z0-9_][A-Za-z0-9_./-]*" +
    "\\.(?:c|cc|cpp|cs|go|java|js|jsx|json|mjs|properties|py|rb|rs|swift|toml|ts|tsx|xml|ya?ml|sh|sql|tf)" +
    ")(?<fragment>#L(?<start>\\d+)(?:-L?(?<end>\\d+))?)?\\)",
  "g",
);
const FENCE = /^\s{0,3}(`{3,}|~{3,})/;
// A whole link wrapped in a single backtick on each side. Markdown renders
// that as a code span, not a link, so the wrap is always a defect -- strip it
// before expanding the link inside, regardless of authoring or pinned form.
const BACKTICK_WRAP = /`(\[[^\]]+\]\([^)]+\))`/g;
// A path or `file.ext:line` as the visible text defeats the purpose: the reader
// is owed a readable noun phrase, and the URL already carries the location.
const PATH_LABEL =
  /^[A-Za-z0-9_./-]*\.(?:c|cc|cpp|cs|go|java|js|jsx|json|mjs|py|rb|rs|swift|toml|ts|tsx|xml|ya?ml)(?::\d+(?:-\d+)?)?$/;

/** Line numbers inside a fence, which this pass never rewrites. */
function fencedLines(text) {
  const inside = new Set();
  let marker = null;
  text.split("\n").forEach((line, index) => {
    const number = index + 1;
    const match = line.match(FENCE);
    if (match) {
      if (marker === null) {
        marker = match[1];
        inside.add(number);
        return;
      }
      if (line.trim().startsWith(marker)) {
        inside.add(number);
        marker = null;
        return;
      }
    }
    if (marker !== null) inside.add(number);
  });
  return inside;
}

function lineCount(target) {
  try {
    return fs.readFileSync(target, "utf8").split("\n").filter((line, index, all) => index < all.length - 1 || line !== "").length;
  } catch {
    return 0;
  }
}

/** Rewrite every authoring-form source link; report the ones that cannot be. */
function expand(text, repo, identity, commit) {
  const protectedLines = fencedLines(text);
  const problems = [];
  const lines = text.split("\n");
  const out = lines.map((line, index) => {
    const number = index + 1;
    if (protectedLines.has(number)) return line;
    const unwrapped = line.replace(BACKTICK_WRAP, "$1");
    return unwrapped.replace(AUTHORING_LINK, (match, ...rest) => {
      const groups = rest[rest.length - 1];
      const rel = groups.path;
      const label = groups.label;
      const target = path.join(repo, rel);
      if (!fs.existsSync(target) || !fs.statSync(target).isFile()) {
        problems.push(`line ${number}: no such file: ${rel}`);
        return match;
      }
      if (PATH_LABEL.test(label.replace(/`/g, ""))) {
        problems.push(`line ${number}: link text '${label}' is a path; name the thing, not its location`);
        return match;
      }
      if (groups.start === undefined) {
        return `[${label}](${blobUrl(identity, commit, rel)})`;
      }
      const first = Number(groups.start);
      const last = Number(groups.end === undefined ? groups.start : groups.end);
      if (first < 1 || last < first) {
        problems.push(`line ${number}: invalid range L${first}-${last} for ${rel}`);
        return match;
      }
      const total = lineCount(target);
      if (last > total) {
        problems.push(`line ${number}: ${rel} has ${total} lines; range L${first}-${last} is out of bounds`);
        return match;
      }
      return `[${label}](${blobUrl(identity, commit, rel, first, last)})`;
    });
  });
  return [out.join("\n"), problems];
}

/**
 * Record the pinned commit in the document's provenance sidecar.
 *
 * Best-effort: a document whose sidecar entry does not exist yet is being
 * written for the first time and gets its commit when provenance is stamped.
 */
function stampCommit(repo, docPath, commit) {
  const entry = store.entryFor(repo, docPath);
  if (!entry || typeof entry !== "object") return;
  const provenance = entry.provenance;
  if (!provenance || typeof provenance !== "object") return;
  if (provenance.git_commit === commit) return;
  provenance.git_commit = commit;
  store.writeEntry(repo, docPath, entry);
}

function documentPaths(manifest, repo) {
  const out = [];
  for (const doc of manifest.documents || []) {
    // Agent-context outputs carry no links or URLs of any kind; expanding one
    // would breach an isolation boundary the audit enforces.
    if (doc.group === AGENT_CONTEXT_GROUP) continue;
    const docPath = doc.path || "";
    if (docPath.endsWith(".md") && fs.existsSync(path.join(repo, docPath))) {
      out.push(path.join(repo, docPath));
    }
  }
  return out;
}

function parseArgs(argv) {
  const args = { repo: null, manifest: null, files: [], commit: null, write: false, json: false };
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index];
    if (flag === "--repo") args.repo = argv[++index];
    else if (flag === "--manifest") args.manifest = argv[++index];
    else if (flag === "--file") args.files.push(argv[++index]);
    else if (flag === "--commit") args.commit = argv[++index];
    else if (flag === "--write") args.write = true;
    else if (flag === "--json") args.json = true;
    else throw new Error(`unknown argument: ${flag}`);
  }
  if (!args.repo) throw new Error("--repo is required");
  if (!args.manifest && !args.files.length) throw new Error("pass --manifest or at least one --file");
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
  let manifest = {};
  if (args.manifest) {
    try {
      manifest = loadManifest(args.manifest);
    } catch (error) {
      return fail(error.message, 2);
    }
  }
  const identity = identityOf(manifest);
  if (identity === null) {
    return fail(
      "project.repository is not declared; source links stay in their authoring " +
        "form until a repository web base is declared (manage_manifest set-repository)",
      2,
    );
  }
  const commit = args.commit || headCommit(repo);
  if (commit === null) return fail("cannot resolve a commit to pin to; pass --commit", 2);

  const targets = args.files.length
    ? args.files.map((value) => path.resolve(value))
    : documentPaths(manifest, repo);
  const changed = [];
  const problems = [];
  for (const target of targets) {
    if (!fs.existsSync(target) || !fs.statSync(target).isFile()) {
      problems.push(`${target}: not a file`);
      continue;
    }
    const original = fs.readFileSync(target, "utf8");
    const [updated, issues] = expand(original, repo, identity, commit);
    const rel = path.relative(repo, target);
    problems.push(...issues.map((issue) => `${rel}: ${issue}`));
    if (updated !== original) {
      changed.push(rel);
      if (args.write) {
        fs.writeFileSync(target, updated, "utf8");
        // `provenance.git_commit` has been schema-declared and validated since
        // 2.0 but was never produced. Stamp it here: it names the commit this
        // document's links resolve against, so a reader who finds a stale link
        // can see exactly which revision it pinned.
        stampCommit(repo, rel, commit);
      }
    }
  }
  const payload = {
    commit,
    web_base: identity.web_base,
    forge: identity.forge,
    expanded: changed.slice().sort(),
    problems: problems.slice().sort(),
    written: Boolean(args.write),
  };
  if (args.json) {
    process.stdout.write(dumpJson(payload));
  } else {
    const verb = args.write ? "expanded" : "would expand";
    console.log(`${verb} source links in ${changed.length} document(s) at ${commit.slice(0, 12)}`);
    for (const item of payload.expanded) console.log(`  ${item}`);
    if (problems.length) {
      console.log(`\nUNRESOLVED (${problems.length})`);
      for (const item of payload.problems) console.log(`  ${item}`);
    }
  }
  return problems.length ? 1 : 0;
}

module.exports = { expand, fencedLines, main };

if (require.main === module) {
  process.exitCode = main();
}
