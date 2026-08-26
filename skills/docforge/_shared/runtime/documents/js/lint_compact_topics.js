#!/usr/bin/env node
"use strict";
/** Cross-topic isolation lint for the compact coding-agent reference. */

const fs = require("fs");

const H2_RE = /^##\s+(.+?)\s*#*\s*$/;
const POINTER_RE = /\b(?:see (?:also )?|as described in|refer to|per the)\b/i;

function lintCompactTopics(filePath) {
  const text = fs.readFileSync(filePath, "utf8");
  const lines = text.split("\n");
  const headings = [];
  lines.forEach((line, index) => {
    const match = line.match(H2_RE);
    if (match) headings.push({ index, title: match[1].trim() });
  });
  const sections = headings.map((entry, position) => ({
    title: entry.title,
    line: entry.index + 1,
    start: entry.index + 1,
    end: position + 1 < headings.length ? headings[position + 1].index : lines.length,
  }));
  const titles = sections.map((s) => s.title);
  const defects = [];
  sections.forEach((section, position) => {
    const others = titles.filter((_, i) => i !== position);
    const body = lines.slice(section.start, section.end);
    body.forEach((line, offset) => {
      const number = section.start + offset + 1;
      if (line.match(H2_RE)) return;
      for (const other of others) {
        const escaped = other.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
        const re = new RegExp("\\b" + escaped + "\\b");
        if (re.test(line)) {
          defects.push({ kind: "cross-topic-mention", line: number, detail: section.title + " mentions " + other });
        }
      }
      if (POINTER_RE.test(line)) {
        defects.push({ kind: "cross-topic-pointer", line: number, detail: line.trim().slice(0, 80) });
      }
    });
  });
  return { file: filePath, defects };
}

function main() {
  const args = process.argv.slice(2);
  let filePath = null;
  let asJson = false;
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--file" && i + 1 < args.length) filePath = args[++i];
    else if (args[i] === "--json") asJson = true;
  }
  if (!filePath) { console.error("error: --file is required"); process.exit(2); }
  if (!fs.existsSync(filePath)) { console.error("error: not a file: " + filePath); process.exit(2); }
  const result = lintCompactTopics(filePath);
  if (asJson) { console.log(JSON.stringify(result, null, 2)); }
  else {
    if (result.defects.length === 0) console.log("CLEAN    " + result.file);
    for (const defect of result.defects) {
      console.log("DEFECT   " + result.file + ":" + defect.line + "  " + defect.kind + ": " + defect.detail);
    }
  }
  process.exit(result.defects.length === 0 ? 0 : 1);
}

if (require.main === module) main();
module.exports = { lintCompactTopics };
