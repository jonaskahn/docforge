#!/usr/bin/env node
"use strict";
/* lint_document.js — mechanical pre-audit of ONE docforge document.
 *
 * Runs the purely mechanical checks so the independent audit
 * (references/document-audit.md) spends its judgement on depth, grounding and
 * mode rather than on things a regex catches. It never replaces the agent: a
 * clean mechanical pass is necessary, not sufficient.
 *
 * Checks, for the single file given:
 *   * unfilled `{{…}}` scaffold markers                          (defect)
 *   * empty headings (a heading with no body before the next     (defect)
 *     heading or EOF)
 *   * dead relative links (a `](path)` whose target file does    (defect)
 *     not exist on disk)
 *   * unlinked file mentions (a backtick-quoted path naming a     (defect)
 *     real file on disk, written as plain text instead of a link)
 *   * missing must-present headings passed via --require-heading (defect)
 *     (repeatable, substring match)
 * Typed `<UPPER_SNAKE>` tokens are reported separately and are NOT defects.
 *
 * Usage:
 *   node lint_document.js --file docs/architecture/high-level.md
 *   node lint_document.js --file docs/flows/checkout.md \
 *       --require-heading "## " --require-heading "Steps"
 *   node lint_document.js --file docs/x.md --json
 *
 * Exit code 0 if no defects, 1 if any defect, 2 on a usage/IO error.
 * Node.js built-ins only.
 */

const fs = require("fs");
const path = require("path");
const pf = require("../../common/js/provenance_frontmatter.js");
const store = require("../../common/js/provenance_store.js");
const { illustrationDefects: budgetDefects } = require("../../common/js/illustration_metrics.js");
const { SPECIAL_DOC_OUTPUTS } = require("../../common/js/special_files.js");
const { visiblePresentationDefects } = require("../../common/js/markdown_fences.js");

const SCAFFOLD_RE = /\{\{.*?\}\}/g;
const TOKEN_RE = /<[A-Z][A-Z0-9_]*>/g;
const HEADING_RE = /^(#{1,6})\s+(.*\S)\s*$/;
const DESCRIPTION_LIMIT = 160;
const LINK_RE = /\[[^\]]*\]\(([^)]+)\)/g;
// A backtick-quoted path ending in .md — a candidate cross-reference that
// should be an actual link, not bare text naming the file.
const MENTION_RE = /`([A-Za-z0-9_./-]+\.md)`/g;
const FORGE_RE = /\b(github|gitlab|bitbucket|gitea|forgejo|sourcehut|azure devops|github actions|gitlab ci|codeowners)\b/gi;
const FENCE_RE = /^(`{3,})(\w*)/;
const MERMAID_FORBIDDEN_RE = /(?:^|\s)(style\s|classDef|click\s)/;
const MERMAID_RESERVED_NODE_RE = /\b(end|graph|subgraph)\b\s*[\[\(\{]/i;
const TREE_GLYPH_RE = /[│├└┌]/;
const SCALAR_PROVENANCE_FIELDS = new Set(
  [...pf.PROVENANCE_FIELDS].filter((key) => !["graph", "sections", "generator"].includes(key)),
);
const MARKDOWN_EXCEPTIONS = SPECIAL_DOC_OUTPUTS;

function isExternalLink(target) {
  const t = target.trim();
  return (
    t.startsWith("http://") ||
    t.startsWith("https://") ||
    t.startsWith("mailto:") ||
    t.startsWith("#") ||
    t.startsWith("<")
  );
}
function headingAnchor(value) {
  return value.trim().toLowerCase().replace(/[^\p{L}\p{N}_\s-]/gu, "").replace(/[\s-]+/g, "-").replace(/^-|-$/g, "");
}
function repositoryRoot(filePath) {
  let current = path.dirname(filePath);
  while (true) {
    if (fs.existsSync(path.join(current, ".git")) || fs.existsSync(path.join(current, ".docforge"))) return current;
    const parent = path.dirname(current);
    if (parent === current) return path.dirname(filePath);
    current = parent;
  }
}
function illustrationDefects(text) {
  const defects = [];
  let inFence = false;
  let fenceMarker = "";
  let fenceLang = "";
  const lines = text.split(/\r?\n/);
  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i];
    const stripped = line.trim();
    const fenceMatch = stripped.match(FENCE_RE);
    if (fenceMatch) {
      const marker = fenceMatch[1];
      const lang = fenceMatch[2];
      if (!inFence) {
        inFence = true;
        fenceMarker = marker;
        fenceLang = lang;
      } else if (marker === fenceMarker) {
        inFence = false;
        fenceMarker = "";
        fenceLang = "";
      }
      continue;
    }
    if (!inFence) continue;
    const lineNo = i + 1;
    if (fenceLang === "mermaid") {
      if (MERMAID_FORBIDDEN_RE.test(line) || MERMAID_RESERVED_NODE_RE.test(line)) {
        defects.push({ kind: "invalid mermaid", line: lineNo, detail: "forbidden directive or reserved node id" });
      }
    } else if (fenceLang !== "text" && fenceLang !== "ascii" && TREE_GLYPH_RE.test(line)) {
      defects.push({ kind: "untagged ascii fence", line: lineNo, detail: "tree glyphs in non-text fence" });
    }
  }
  return defects;
}
function metadataContext(filePath, text) {
  // Resolve { state, provenance, bodyStart, public } for one document.
  // The folder sidecar wins; inline frontmatter that has not been migrated
  // yet reports state `inline` so lint flags it.
  const root = repositoryRoot(filePath);
  const rel = path.relative(root, filePath).split(path.sep).join("/");
  const entry = store.entryFor(root, rel);
  if (entry && entry.provenance && typeof entry.provenance === "object") {
    const publicMeta = {};
    for (const key of store.PUBLIC_FIELDS) {
      if (entry[key]) publicMeta[key] = entry[key];
    }
    return { state: "ok", provenance: entry.provenance, bodyStart: 0, public: publicMeta };
  }
  const parsedInline = pf.parseFrontmatter(text);
  const inlineState = parsedInline.state === "ok" ? "inline" : parsedInline.state;
  const publicInline = {};
  if (inlineState === "inline") {
    const split = pf.splitFrontmatter(text);
    if (split.raw != null) {
      try {
        const data = pf.parseYamlMapping(split.raw);
        for (const key of store.PUBLIC_FIELDS) {
          if (data[key]) publicInline[key] = data[key];
        }
      } catch {
        // provenance defects report parsing
      }
    }
  }
  return { state: inlineState, provenance: parsedInline.provenance, bodyStart: parsedInline.end, public: publicInline };
}

function provenanceDefects(filePath, text) {
  const defects = [];
  if (MARKDOWN_EXCEPTIONS.has(path.basename(filePath))) return defects;
  const context = metadataContext(filePath, text);
  const parsed = { state: context.state, provenance: context.provenance, end: context.bodyStart };
  if (parsed.state === "missing") return [{ kind: "missing provenance", line: 1, detail: "frontmatter absent" }];
  if (parsed.state === "unparseable") return [{ kind: "unparseable provenance", line: 1, detail: "frontmatter unparseable" }];
  if (parsed.state === "obsolete") return [{ kind: "obsolete schema", line: 1, detail: "run migrate_metadata.js" }];
  if (parsed.state === "legacy") return [{ kind: "legacy provenance", line: 1, detail: "schema absent" }];
  if (parsed.state === "inline") {
    return [{ kind: "legacy provenance", line: 1, detail: "inline provenance; run migrate_metadata to move it into the sidecar" }];
  }
  const provenance = parsed.provenance;
  if (!provenance || typeof provenance !== "object" || Array.isArray(provenance)) {
    return [{ kind: "missing provenance", line: 1, detail: "docforge_provenance absent" }];
  }
  const missing = [...pf.PROVENANCE_FIELDS].filter((key) => !(key in provenance)).sort();
  const graph = provenance.graph;
  if (!graph || typeof graph !== "object" || !("provider" in graph) || !("flow" in graph)) missing.push("graph.provider/flow");
  const generator = provenance.generator;
  if (!generator || typeof generator !== "object" || !("name" in generator) || !("version" in generator)) {
    missing.push("generator.name/version");
  }
  const invalid = [...SCALAR_PROVENANCE_FIELDS]
    .filter((key) => typeof provenance[key] !== "string" || !provenance[key] || pf.SCAFFOLD_TOKEN.test(provenance[key]));
  if (generator && typeof generator === "object") {
    for (const key of ["name", "version"]) {
      if (typeof generator[key] !== "string" || !generator[key] || pf.SCAFFOLD_TOKEN.test(generator[key])) {
        invalid.push(`generator.${key}`);
      }
    }
  } else if (!invalid.includes("generator")) {
    invalid.push("generator");
  }
  if (graph && typeof graph === "object") {
    for (const key of ["provider", "flow"]) {
      if (typeof graph[key] !== "string" || !graph[key] || pf.SCAFFOLD_TOKEN.test(graph[key])) {
        invalid.push(`graph.${key}`);
      }
    }
  }
  if (missing.length || invalid.length || !pf.SUPPORTED_SCHEMA_VERSIONS.has(provenance.schema) || "graph_snapshot" in provenance) {
    const detail = [...missing, ...invalid.map((item) => `non-concrete ${item}`)].join(", ")
      || "invalid schema or obsolete graph_snapshot";
    defects.push({ kind: "missing provenance", line: 1, detail });
  }
  if (graph && !pf.FLOW_VALUES.has(graph.flow)) defects.push({ kind: "missing provenance", line: 1, detail: "invalid graph.flow" });
  if ("git_commit" in provenance && (typeof provenance.git_commit !== "string" || !pf.BLOB.test(provenance.git_commit))) {
    defects.push({ kind: "missing provenance", line: 1, detail: "invalid git_commit" });
  }
  const sections = provenance.sections;
  if (!Array.isArray(sections)) {
    defects.push({ kind: "missing provenance", line: 1, detail: "sections must be an array" });
    return defects;
  }
  if (!sections.length) defects.push({ kind: "empty provenance", line: 1, detail: "sections is empty" });
  const anchors = new Set();
  for (const line of text.slice(parsed.end).split(/\r?\n/)) {
    const match = line.match(HEADING_RE);
    if (match) anchors.add(headingAnchor(match[2]));
  }
  const root = repositoryRoot(filePath);
  for (const section of sections) {
    const sectionId = section && typeof section.id === "string" ? section.id : null;
    if (!sectionId || !anchors.has(sectionId)) defects.push({ kind: "unknown section", line: 1, detail: sectionId || "<missing>" });
    if (!section || !Array.isArray(section.sources) || !Array.isArray(section.unresolved)) {
      defects.push({ kind: "missing provenance", line: 1, detail: `section ${sectionId || "<missing>"} shape` });
      continue;
    }
    for (const source of section.sources) {
      const sourcePath = source && typeof source.path === "string" ? source.path : "";
      if (!source || typeof source.git_blob !== "string" || !pf.BLOB.test(source.git_blob)) {
        defects.push({ kind: "invalid blob", line: 1, detail: sourcePath || "<missing>" });
      }
      const target = path.join(root, ...sourcePath.split("/"));
      if (!sourcePath || !fs.existsSync(target) || !fs.statSync(target).isFile()) {
        defects.push({ kind: "unknown source", line: 1, detail: sourcePath || "<missing>" });
      }
      if (!source || !pf.SOURCE_ROLES.has(source.role)) {
        defects.push({ kind: "missing provenance", line: 1, detail: `${sourcePath || "<missing>"}: invalid role` });
      }
    }
  }
  return defects;
}

function publicMetadataDefects(filePath, text) {
  // Public metadata contract for written documents: a non-empty
  // `description` of at most 160 characters.
  if (MARKDOWN_EXCEPTIONS.has(path.basename(filePath))) return [];
  const context = metadataContext(filePath, text);
  if (context.state !== "ok" && context.state !== "inline") return [];
  const description = context.public.description;
  if (typeof description !== "string" || !description.trim()) {
    return [{ kind: "missing description", line: 1, detail: "public description is required" }];
  }
  if (description.length > DESCRIPTION_LIMIT) {
    return [{
      kind: "long description",
      line: 1,
      detail: `description exceeds ${DESCRIPTION_LIMIT} characters`,
    }];
  }
  return [];
}

function checkDocument(filePath, requireHeadings) {
  const text = fs.readFileSync(filePath, "utf8");
  const lines = text.split("\n");
  const defects = [];
  const tokens = [];
  defects.push(...provenanceDefects(filePath, text));
  defects.push(...publicMetadataDefects(filePath, text));
  defects.push(...illustrationDefects(text));
  const context = metadataContext(filePath, text);
  const targetDepth = context.provenance && typeof context.provenance === "object"
    ? context.provenance.target_depth || "deep-dive"
    : "deep-dive";
  defects.push(...budgetDefects(text, targetDepth));
  defects.push(...visiblePresentationDefects(text));

  // scaffold markers + tokens, with line numbers
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    let m;
    SCAFFOLD_RE.lastIndex = 0;
    while ((m = SCAFFOLD_RE.exec(line)) !== null) {
      defects.push({ kind: "scaffold-marker", line: i + 1, detail: m[0] });
    }
    TOKEN_RE.lastIndex = 0;
    while ((m = TOKEN_RE.exec(line)) !== null) {
      tokens.push(m[0]);
    }
  }

  // headings
  const heads = [];
  for (let i = 0; i < lines.length; i++) {
    const m = lines[i].match(HEADING_RE);
    if (m) heads.push({ index: i, match: m });
  }
  const headingsText = heads.map((h) => h.match[2]);

  // empty headings
  for (let idx = 0; idx < heads.length; idx++) {
    const i = heads[idx].index;
    const nextHeadLine = idx + 1 < heads.length ? heads[idx + 1].index : lines.length;
    let bodyFound = false;
    for (let j = i + 1; j < nextHeadLine; j++) {
      if (lines[j].trim()) {
        bodyFound = true;
        break;
      }
    }
    if (!bodyFound) {
      defects.push({ kind: "empty-heading", line: i + 1, detail: heads[idx].match[2] });
    }
  }

  // dead relative links
  const repoDir = path.dirname(filePath);
  const linkedTargets = new Set();
  for (let i = 0; i < lines.length; i++) {
    let m;
    LINK_RE.lastIndex = 0;
    while ((m = LINK_RE.exec(lines[i])) !== null) {
      const target = m[1].trim();
      linkedTargets.add(target.split("#")[0]);
      if (isExternalLink(target)) continue;
      const filePart = target.split("#")[0];
      if (!filePart) continue;
      const resolved = path.resolve(repoDir, filePart);
      if (!fs.existsSync(resolved)) {
        defects.push({ kind: "dead-link", line: i + 1, detail: target });
      }
    }
  }

  // unlinked file mentions: a real file named in backticks, never linked
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    let m;
    MENTION_RE.lastIndex = 0;
    while ((m = MENTION_RE.exec(line)) !== null) {
      const target = m[1];
      const basename = target.split("/").pop();
      if (linkedTargets.has(target) || linkedTargets.has(basename)) continue;
      const before = m.index > 0 ? line[m.index - 1] : "";
      const after = line.slice(m.index + m[0].length, m.index + m[0].length + 2);
      if (before === "[" && after.startsWith("(")) continue;
      const resolved = path.resolve(repoDir, target);
      if (fs.existsSync(resolved)) {
        defects.push({ kind: "unlinked-mention", line: i + 1, detail: target });
      }
    }
  }

  // required headings
  for (const req of requireHeadings) {
    if (!headingsText.some((h) => h.includes(req))) {
      defects.push({ kind: "missing-heading", line: 0, detail: req });
    }
  }

  for (let i = 0; i < lines.length; i++) {
    FORGE_RE.lastIndex = 0;
    let m;
    while ((m = FORGE_RE.exec(lines[i])) !== null) {
      defects.push({ kind: "forge-leakage", line: i + 1, detail: m[0] });
    }
  }

  return { file: filePath, defects, tokens: [...new Set(tokens)].sort() };
}

function parseArgs(argv) {
  const args = { file: null, requireHeading: [], json: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--file" || a === "--require-heading") {
      if (i + 1 >= argv.length || argv[i + 1].startsWith("--")) {
        throw new Error(`option requires a value: ${a}`);
      }
      if (a === "--file") args.file = argv[++i];
      else args.requireHeading.push(argv[++i]);
    }
    else if (a === "--json") args.json = true;
    else if (a === "-h" || a === "--help") args.help = true;
    else throw new Error(`unknown option: ${a}`);
  }
  return args;
}

function main() {
  let args;
  try {
    args = parseArgs(process.argv.slice(2));
  } catch (error) {
    console.error(`error: ${error.message}`);
    return 2;
  }
  if (args.help) {
    console.log("usage: lint_document.js --file <path> [--require-heading <text>] [--json]");
    return 0;
  }
  if (!args.file || !fs.existsSync(args.file) || !fs.statSync(args.file).isFile()) {
    console.error(`error: not a file: ${args.file}`);
    return 2;
  }

  const result = checkDocument(args.file, args.requireHeading);

  if (args.json) {
    console.log(JSON.stringify(result, null, 2));
  } else {
    if (!result.defects.length) console.log(`CLEAN    ${result.file}`);
    for (const d of result.defects) {
      const loc = d.line ? `:${d.line}` : "";
      console.log(`DEFECT   ${result.file}${loc}  ${d.kind}: ${d.detail}`);
    }
    if (result.tokens.length) {
      console.log(`tokens (external, not defects): ${result.tokens.join(", ")}`);
    }
  }

  return result.defects.length ? 1 : 0;
}

process.exit(main());
