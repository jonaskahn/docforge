#!/usr/bin/env node
"use strict";
/** Mechanical rubric check for generated AGENTS.md and CLAUDE.md kernels.
 *
 * The kernel must stay concise and self-contained: required operating
 * sections, verified commands, hard safety boundaries, and no documentation
 * references. Run this in place of the generic document linter for an
 * `agents-kernel` output.
 */

const fs = require("fs");
const path = require("path");

const HEADING_RE = /^(#{1,6})\s+(.*\S)\s*$/;
const H2_RE = /^##\s+(.+?)\s*#*\s*$/;
const FENCE_MARKER_RE = /^\s*(`{3,}|~{3,})/;
const BARE_URL_RE = /https?:\/\//;
const RAW_URL_TOKEN_RE = /\bhttps?:\/\/[^\s<>)\]"']+/g;
const MARKDOWN_LINK_RE = /!?\[([^\]\r\n]*)\]\(([^)\r\n]*)\)/g;
const AT_IMPORT_RE = /(?<![\w@])@((?:(?:\.{1,2}\/|\/)?[\w.~+-]+)(?:\/[\w.~+-]+)*\/?(?:#[\w.~:-]+)?)/g;
const DOC_PATH_RE = /(?<![\w@])((?:(?:\.{1,2}\/|\/)?(?:[\w.~+-]+\/)*[\w.~+-]+\.(?:md|mdx|markdown|rst|adoc|asciidoc)(?:#[\w.~:-]+)?|docs\/[\w.~+/-]*))(?![\w./-])/gi;
const DOCUMENT_SUFFIXES = new Set([".md", ".mdx", ".markdown", ".rst", ".adoc", ".asciidoc"]);
const REQUIRED_SECTIONS = ["Commands", "Repository map", "Precedence", "Boundaries", "Validation"];
const SECTION_ORDER = ["Commands", "Repository map", "Precedence", "Boundaries", "Conventions", "Validation"];
const MAX_NONBLANK_LINES = 80;
const LINE_WARNING_AT = 68;
const GUARD_RE = /\b(?:never|must not|do not|without)\b/i;
const SECRET_RE = /(?:\b(?:secret|credential)\w*\b|\.env\b)/i;
const VALIDATION_ACTION_RE = /\b(?:disable|skip|bypass|remove)\w*\b/i;
const VALIDATION_TARGET_RE = /\b(?:test|validation|check)\w*\b/i;
const DESTRUCTIVE_RE = /\bdestructive\b/i;
const APPROVAL_RE = /\b(?:approval|permission|ask)\w*\b/i;

function cleanReference(raw) {
  return raw.trim().replace(/^[`"'<>]+|[`"'<>]+$/g, "").replace(/[.,;:!?]+$/g, "");
}

function linkTarget(raw) {
  const value = raw.trim();
  if (value.startsWith("<") && value.includes(">")) return value.slice(1, value.indexOf(">"));
  return value ? value.split(/\s+/, 1)[0] : "";
}

function looksLikeDocumentReference(raw) {
  const value = cleanReference(raw).split("#", 1)[0].split("?", 1)[0].replace(/\/$/, "");
  return value.startsWith("docs/") || DOCUMENT_SUFFIXES.has(path.posix.extname(value).toLowerCase());
}

function maskSpans(line, spans) {
  const chars = line.split("");
  for (const [start, end] of spans) {
    for (let index = start; index < end; index += 1) chars[index] = " ";
  }
  return chars.join("");
}

function fenceBlocks(lines) {
  const blocks = [];
  const protectedLines = new Set();
  let current = null;
  for (let index = 0; index < lines.length; index++) {
    const line = lines[index];
    if (current) {
      protectedLines.add(index);
      const trimmed = line.trim();
      if (
        trimmed.length >= current.marker.length
        && [...trimmed].every((character) => character === current.marker[0])
      ) {
        current.end = index;
        current = null;
      }
      continue;
    }
    const match = line.match(FENCE_MARKER_RE);
    if (match) {
      current = { start: index, end: null, marker: match[1] };
      blocks.push(current);
      protectedLines.add(index);
    }
  }
  return [blocks, protectedLines];
}

function sectionsFor(lines, protectedLines, end) {
  const headings = [];
  for (let index = 0; index < end; index++) {
    if (protectedLines.has(index)) continue;
    const match = lines[index].match(H2_RE);
    if (match) headings.push([index, match[1].trim()]);
  }
  return headings.map(([index, title], position) => ({
    title,
    line: index + 1,
    start: index + 1,
    end: position + 1 < headings.length ? headings[position + 1][0] : end,
  }));
}

function canonicalTitle(title) {
  return SECTION_ORDER.find((candidate) => candidate.toLowerCase() === title.toLowerCase()) || null;
}

function sectionFor(sections, title) {
  return sections.find((item) => item.title.toLowerCase() === title.toLowerCase()) || null;
}

function documentReferenceDefects(lines) {
  const defects = [];
  for (let index = 0; index < lines.length; index++) {
    const number = index + 1;
    const line = lines[index];
    const linkSpans = [];
    MARKDOWN_LINK_RE.lastIndex = 0;
    let match;
    while ((match = MARKDOWN_LINK_RE.exec(line)) !== null) {
      defects.push({
        kind: "doc-reference",
        line: number,
        detail: `markdown-link: ${linkTarget(match[2]) || "<empty>"}`,
      });
      linkSpans.push([match.index, match.index + match[0].length]);
    }
    let working = maskSpans(line, linkSpans);

    RAW_URL_TOKEN_RE.lastIndex = 0;
    const urlSpans = [...working.matchAll(RAW_URL_TOKEN_RE)]
      .map((item) => [item.index, item.index + item[0].length]);
    working = maskSpans(working, urlSpans);

    const importSpans = [];
    AT_IMPORT_RE.lastIndex = 0;
    while ((match = AT_IMPORT_RE.exec(working)) !== null) {
      const target = match[1];
      if (looksLikeDocumentReference(target)) {
        defects.push({
          kind: "doc-reference",
          line: number,
          detail: `at-import: @${cleanReference(target)}`,
        });
        importSpans.push([match.index, match.index + match[0].length]);
      }
    }
    working = maskSpans(working, importSpans);

    DOC_PATH_RE.lastIndex = 0;
    while ((match = DOC_PATH_RE.exec(working)) !== null) {
      defects.push({
        kind: "doc-reference",
        line: number,
        detail: `bare-path: ${cleanReference(match[1])}`,
      });
    }
  }
  return defects;
}

function requiredSectionDefects(sections) {
  const defects = [];
  for (const title of REQUIRED_SECTIONS) {
    const matches = sections.filter((item) => item.title.toLowerCase() === title.toLowerCase());
    if (!matches.length) {
      defects.push({
        kind: "missing-section",
        line: 0,
        detail: `missing required section: ${title}`,
      });
    }
    for (const duplicate of matches.slice(1)) {
      defects.push({ kind: "duplicate-section", line: duplicate.line, detail: title });
    }
  }

  const ordered = sections
    .map((item) => [item, canonicalTitle(item.title)])
    .filter(([_item, canonical]) => canonical !== null);
  const positions = ordered.map(([_item, canonical]) => SECTION_ORDER.indexOf(canonical));
  for (let index = 1; index < positions.length; index++) {
    if (positions[index] < positions[index - 1]) {
      defects.push({
        kind: "section-order",
        line: ordered[index][0].line,
        detail: `expected: ${SECTION_ORDER.join(", ")}`,
      });
      break;
    }
  }
  return defects;
}

function commandDefects(lines, sections, blocks) {
  const commands = sectionFor(sections, "Commands");
  if (!commands) return [];
  const commandBlocks = blocks.filter(
    (block) => commands.start <= block.start && block.start < commands.end,
  );
  if (!commandBlocks.length) {
    return [{
      kind: "missing-command-block",
      line: commands.line,
      detail: "Commands must contain a fenced block",
    }];
  }
  const block = commandBlocks[0];
  if (block.end === null) return [];
  const commandsInBlock = lines.slice(block.start + 1, block.end)
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith("#") && !line.includes("{{") && !line.includes("TODO("));
  if (commandsInBlock.length) return [];
  return [{
    kind: "empty-command-block",
    line: block.start + 1,
    detail: "Commands must contain at least one concrete command",
  }];
}

function safetyDefects(lines, sections) {
  const boundaries = sectionFor(sections, "Boundaries");
  if (!boundaries) return [];
  const body = lines.slice(boundaries.start, boundaries.end);
  const checks = {
    secrets: body.some((line) => GUARD_RE.test(line) && SECRET_RE.test(line)),
    validation: body.some(
      (line) => GUARD_RE.test(line) && VALIDATION_ACTION_RE.test(line) && VALIDATION_TARGET_RE.test(line),
    ),
    "destructive commands": body.some((line) => DESTRUCTIVE_RE.test(line) && APPROVAL_RE.test(line)),
  };
  return Object.entries(checks)
    .filter(([_name, present]) => !present)
    .map(([name]) => ({
      kind: "missing-safety-rule",
      line: boundaries.line,
      detail: `Boundaries must cover ${name}`,
    }));
}

function checkAgentsKernel(filePath, repoDir = null) {
  // Retained for API compatibility. References are never resolved against disk
  // now that every document reference is a defect.
  void repoDir;
  const text = fs.readFileSync(filePath, "utf8");
  const lines = text.split("\n");
  let contentEnd = lines.length;
  while (contentEnd > 0 && !lines[contentEnd - 1].trim()) contentEnd--;

  const defects = [];
  const warnings = [];
  const nonblankLines = lines.slice(0, contentEnd)
    .map((line, index) => line.trim() ? index + 1 : null)
    .filter((line) => line !== null);
  const nonblankCount = nonblankLines.length;
  if (nonblankCount > MAX_NONBLANK_LINES) {
    defects.push({
      kind: "line-cap",
      line: nonblankLines[MAX_NONBLANK_LINES],
      detail: `${nonblankCount} nonblank lines, cap is ${MAX_NONBLANK_LINES}`,
    });
  } else if (nonblankCount >= LINE_WARNING_AT) {
    warnings.push({
      kind: "line-cap-warning",
      line: nonblankLines[nonblankLines.length - 1],
      detail: `${nonblankCount} nonblank lines, approaching the ${MAX_NONBLANK_LINES}-line cap`,
    });
  }

  if (!lines.length || !lines[0].startsWith("# ")) {
    defects.push({ kind: "opening-shape", line: 1, detail: "line 1 must be a level-1 heading" });
  }

  const [blocks, protectedLines] = fenceBlocks(lines.slice(0, contentEnd));
  const sections = sectionsFor(lines, protectedLines, contentEnd);
  const firstH2 = sections.length ? sections[0].line - 1 : contentEnd;
  const preamble = lines.slice(1, firstH2);
  if (!preamble.some(
    (line) => line.trim() && !HEADING_RE.test(line) && !line.trimStart().startsWith("<!--"),
  )) {
    defects.push({
      kind: "opening-shape",
      line: 2,
      detail: "no description prose between the title and first section",
    });
  }

  defects.push(...requiredSectionDefects(sections));
  defects.push(...commandDefects(lines, sections, blocks));
  defects.push(...safetyDefects(lines, sections));

  if (blocks.length > 1) {
    defects.push({
      kind: "too-many-code-blocks",
      line: blocks[1].start + 1,
      detail: `${blocks.length} fenced blocks, max 1`,
    });
  }
  for (const block of blocks) {
    if (block.end === null) {
      defects.push({
        kind: "unclosed-code-block",
        line: block.start + 1,
        detail: "fenced block is not closed",
      });
    }
  }

  if (!lines.slice(0, 10).some((line) => line.includes("<!--"))) {
    defects.push({
      kind: "missing-provenance",
      line: 0,
      detail: "no HTML-comment provenance in first 10 lines",
    });
  }

  for (let index = 0; index < lines.length; index++) {
    const line = lines[index];
    MARKDOWN_LINK_RE.lastIndex = 0;
    const withoutLinks = maskSpans(
      line,
      [...line.matchAll(MARKDOWN_LINK_RE)]
        .map((match) => [match.index, match.index + match[0].length]),
    );
    if (BARE_URL_RE.test(withoutLinks)) {
      defects.push({ kind: "bare-url", line: index + 1, detail: line.trim() });
    }
  }

  defects.push(...documentReferenceDefects(lines));
  return { file: filePath, defects, warnings };
}

function parseArgs(argv) {
  const args = { file: null, repo: ".", json: false };
  for (let index = 0; index < argv.length; index++) {
    const value = argv[index];
    if (value === "--file") args.file = argv[++index];
    else if (value === "--repo") args.repo = argv[++index];
    else if (value === "--json") args.json = true;
  }
  return args;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.file || !fs.existsSync(args.file) || !fs.statSync(args.file).isFile()) {
    console.error(`error: not a file: ${args.file}`);
    return 2;
  }

  const result = checkAgentsKernel(args.file, args.repo);
  if (args.json) {
    console.log(JSON.stringify(result, null, 2));
  } else {
    if (!result.defects.length) console.log(`CLEAN    ${result.file}`);
    for (const defect of result.defects) {
      const location = defect.line ? `:${defect.line}` : "";
      console.log(`DEFECT   ${result.file}${location}  ${defect.kind}: ${defect.detail}`);
    }
    for (const warning of result.warnings) {
      const location = warning.line ? `:${warning.line}` : "";
      console.log(`WARNING  ${result.file}${location}  ${warning.kind}: ${warning.detail}`);
    }
  }
  return result.defects.length ? 1 : 0;
}

module.exports = { checkAgentsKernel, main };

if (require.main === module) {
  process.exitCode = main();
}
