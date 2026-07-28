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

const SCAFFOLD_RE = /\{\{.*?\}\}/g;
const TOKEN_RE = /<[A-Z][A-Z0-9_]*>/g;
const HEADING_RE = /^(#{1,6})\s+(.*\S)\s*$/;
const LINK_RE = /\[[^\]]*\]\(([^)]+)\)/g;
// A backtick-quoted path ending in .md — a candidate cross-reference that
// should be an actual link, not bare text naming the file.
const MENTION_RE = /`([A-Za-z0-9_./-]+\.md)`/g;
const FORGE_RE = /\b(github|gitlab|bitbucket|gitea|forgejo|sourcehut|azure devops|github actions|gitlab ci|codeowners)\b/gi;

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

function checkDocument(filePath, requireHeadings) {
  const text = fs.readFileSync(filePath, "utf8");
  const lines = text.split("\n");
  const defects = [];
  const tokens = [];

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
