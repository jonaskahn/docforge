"use strict";
/** Validate immutable implementation evidence locators in generated Markdown. */

const fs = require("fs");
const path = require("path");
const pf = require("./provenance_frontmatter.js");
const { lineCount, rangeBlobHash, rawBlobHash } = require("./evidence_hash.js");

const LOCATOR = /([A-Za-z0-9][A-Za-z0-9_./-]*)#L([1-9]\d*)-L([1-9]\d*) @ ([0-9a-f]{40})/g;
const HEADING = /^(#{1,6})\s+(.*\S)\s*$/;
function anchor(value) { return value.toLowerCase().replace(/[^\p{L}\p{N}_\s-]/gu, "").trim().replace(/[\s-]+/g, "-"); }
function root(filePath) {
  let current = path.dirname(filePath);
  while (true) {
    if (fs.existsSync(path.join(current, ".git")) || fs.existsSync(path.join(current, ".docforge"))) return current;
    const parent = path.dirname(current);
    if (parent === current) return path.dirname(filePath);
    current = parent;
  }
}
function outsideFences(text) {
  const lines = []; let inFence = false; let marker = "";
  for (const [index, line] of text.split(/\r?\n/).entries()) {
    const match = line.match(/^\s*(`{3,})/);
    if (match) { if (!inFence) { inFence = true; marker = match[1]; } else if (match[1] === marker) { inFence = false; marker = ""; } continue; }
    if (!inFence) lines.push([index + 1, line]);
  }
  return lines;
}
/* `provenance` and `bodyStart` come from the caller's already-resolved
 * metadata. Passing them is what makes this work under sidecar storage, where
 * the markdown carries no frontmatter to parse — without them the check would
 * find no provenance and silently pass every document. When they are omitted
 * the frontmatter is parsed directly, for callers holding a legacy document. */
function validateLocators(document, text = null, provenance = null, bodyStart = null) {
  document = path.resolve(document);
  const contents = text == null ? fs.readFileSync(document, "utf8") : text;
  if (provenance === null) {
    const parsed = pf.parseFrontmatter(contents);
    if (parsed.state !== "ok" || !parsed.provenance || typeof parsed.provenance !== "object") return [];
    provenance = parsed.provenance;
    if (bodyStart === null) bodyStart = parsed.end;
  }
  if (!provenance || typeof provenance !== "object") return [];
  if (bodyStart === null) bodyStart = 0;
  const headings = [];
  // Newlines before the body, so the first body line is 1-based like the
  // locator scan below. `split().length` would count lines, not newlines.
  const bodyLine0 = contents.slice(0, bodyStart).split(/\r?\n/).length - 1;
  for (const [index, line] of contents.slice(bodyStart).split(/\r?\n/).entries()) {
    const match = line.match(HEADING); if (match) headings.push([bodyLine0 + index + 1, anchor(match[2])]);
  }
  const sourcePairs = new Map();
  for (const section of provenance.sections || []) {
    sourcePairs.set(section.id, new Set((section.sources || []).map((source) => `${source.path}\0${source.git_blob}`)));
  }
  const repo = root(document); const defects = [];
  for (const [lineNumber, line] of outsideFences(contents)) {
    LOCATOR.lastIndex = 0; let match;
    while ((match = LOCATOR.exec(line)) !== null) {
      const [, rel, startRaw, endRaw, digest] = match; const start = Number(startRaw); const end = Number(endRaw);
      if (path.posix.isAbsolute(rel) || rel.split("/").includes("..")) { defects.push({ kind: "evidence path escape", line: lineNumber, detail: rel }); continue; }
      const target = path.resolve(repo, ...rel.split("/"));
      if (!fs.existsSync(target) || !fs.statSync(target).isFile() || !(target === repo || target.startsWith(`${repo}${path.sep}`))) { defects.push({ kind: "evidence source missing", line: lineNumber, detail: rel }); continue; }
      const bytes = fs.readFileSync(target);
      const wholeFile = rawBlobHash(bytes);
      const scoped = rangeBlobHash(bytes, start, end);
      if (digest !== wholeFile && digest !== scoped) defects.push({ kind: "stale evidence blob", line: lineNumber, detail: rel });
      const count = lineCount(bytes);
      if (end < start || count === null || end > count) defects.push({ kind: "invalid evidence range", line: lineNumber, detail: `${rel}#L${start}-L${end}` });
      const heading = [...headings].reverse().find(([headingLine]) => headingLine <= lineNumber);
      if (!heading) defects.push({ kind: "unknown evidence heading", line: lineNumber, detail: rel });
      else if (!(sourcePairs.get(heading[1]) || new Set()).has(`${rel}\0${digest}`)) defects.push({ kind: "evidence provenance mismatch", line: lineNumber, detail: rel });
    }
  }
  return defects;
}
module.exports = { validateLocators };
