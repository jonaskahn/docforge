"use strict";
/** Validate immutable implementation evidence locators in generated Markdown. */

const crypto = require("crypto");
const fs = require("fs");
const path = require("path");
const pf = require("./provenance_frontmatter.js");

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
function validateLocators(document, text = null) {
  const contents = text == null ? fs.readFileSync(document, "utf8") : text;
  const parsed = pf.parseFrontmatter(contents);
  if (parsed.state !== "ok" || !parsed.provenance || typeof parsed.provenance !== "object") return [];
  const headings = [];
  for (const [index, line] of contents.slice(parsed.end).split(/\r?\n/).entries()) {
    const match = line.match(HEADING); if (match) headings.push([parsed.end + index + 1, anchor(match[2])]);
  }
  const sourcePairs = new Map();
  for (const section of parsed.provenance.sections || []) {
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
      const bytes = fs.readFileSync(target); const expected = crypto.createHash("sha1").update(Buffer.concat([Buffer.from(`blob ${bytes.length}\0`, "ascii"), bytes])).digest("hex");
      if (digest !== expected) defects.push({ kind: "stale evidence blob", line: lineNumber, detail: rel });
      if (end < start || end > bytes.toString("utf8").split(/\r?\n/).length) defects.push({ kind: "invalid evidence range", line: lineNumber, detail: `${rel}#L${start}-L${end}` });
      const heading = [...headings].reverse().find(([headingLine]) => headingLine <= lineNumber);
      if (!heading) defects.push({ kind: "unknown evidence heading", line: lineNumber, detail: rel });
      else if (!(sourcePairs.get(heading[1]) || new Set()).has(`${rel}\0${digest}`)) defects.push({ kind: "evidence provenance mismatch", line: lineNumber, detail: rel });
    }
  }
  return defects;
}
module.exports = { validateLocators };
