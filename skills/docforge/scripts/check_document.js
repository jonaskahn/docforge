#!/usr/bin/env node
"use strict";
/* check_document.js — mechanical pre-audit of ONE docforge document.
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
 *   * missing must-present headings passed via --require-heading (defect)
 *     (repeatable, substring match)
 * Typed `<UPPER_SNAKE>` tokens are reported separately and are NOT defects.
 *
 * Usage:
 *   node check_document.js --file docs/architecture/high-level.md
 *   node check_document.js --file docs/flows/checkout.md \
 *       --require-heading "## " --require-heading "Steps"
 *   node check_document.js --file docs/x.md --json
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
  for (let i = 0; i < lines.length; i++) {
    let m;
    LINK_RE.lastIndex = 0;
    while ((m = LINK_RE.exec(lines[i])) !== null) {
      const target = m[1].trim();
      if (isExternalLink(target)) continue;
      const filePart = target.split("#")[0];
      if (!filePart) continue;
      const resolved = path.resolve(repoDir, filePart);
      if (!fs.existsSync(resolved)) {
        defects.push({ kind: "dead-link", line: i + 1, detail: target });
      }
    }
  }

  // required headings
  for (const req of requireHeadings) {
    if (!headingsText.some((h) => h.includes(req))) {
      defects.push({ kind: "missing-heading", line: 0, detail: req });
    }
  }

  return { file: filePath, defects, tokens: [...new Set(tokens)].sort() };
}

function parseArgs(argv) {
  const args = { file: null, requireHeading: [], json: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--file") args.file = argv[++i];
    else if (a === "--require-heading") args.requireHeading.push(argv[++i]);
    else if (a === "--json") args.json = true;
  }
  return args;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
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
