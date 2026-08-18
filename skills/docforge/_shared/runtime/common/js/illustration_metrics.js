"use strict";
/** Portable, bounded illustration metrics for Docforge Markdown. */

const FENCE = /^\s*(`{3,})([\w-]*)/;
const CONNECTOR = /(?:-->|--|\|\|--|->>|-->>)/;
// Maximum meaningful elements within a single illustration, per target depth.
// There is deliberately no cap on the number of illustrations in a document:
// every documentation authority surveyed prescribes splitting a dense diagram
// into several simpler ones, so a count cap would forbid the recommended remedy.
// `working` is documented in illustration.md's budget table and was previously
// unenforced: the missing key silently resolved to the deep-dive bound of 12. A
// view may declare `depth: working` to be sized at this bound inside a document
// of a different depth.
const BUDGETS = { orientation: 5, working: 8, "deep-dive": 12, reference: 12, router: 12 };
// Below this a diagram carries no relationship a sentence could not carry.
// Adding one is decoration, and decoration is not neutral: the seductive-detail
// effect is small, negative, and reproduced across dozens of studies, while the
// coherence principle (exclude extraneous pictures) is among the best-supported
// findings in multimedia learning.
const MIN_MEANINGFUL_ELEMENTS = 3;

/** A sentence a reader could use instead of seeing the picture. */
function isExplanatoryProse(line) {
  const stripped = line.trim();
  if (!stripped) return false;
  for (const prefix of ["#", "|", ">", "```", "~~~", "<!--", "_Last reviewed"]) {
    if (stripped.startsWith(prefix)) return false;
  }
  return (stripped.match(/[A-Za-z]{2,}/g) || []).length >= 6;
}

/**
 * Prose within `window` lines above the opening or below the closing fence.
 *
 * Adjacency is the point, not mere presence somewhere in the document: a reader
 * whose renderer or screen reader drops the diagram must find the same
 * relationships right there, and splitting the explanation away from the
 * picture splits the reader's attention.
 */
function hasAdjacentProse(lines, start, end, window = 4) {
  const before = lines.slice(Math.max(0, start - 1 - window), Math.max(0, start - 1));
  const after = lines.slice(end, end + window);
  return [...before, ...after].some(isExplanatoryProse);
}
function illustrationDefects(text, targetDepth) {
  const defects = []; const blocks = []; let active = null;
  const lines = text.split(/\r?\n/);
  for (const [index, line] of lines.entries()) {
    const match = line.match(FENCE);
    if (match) { const [marker, language] = [match[1], match[2]]; if (!active) active = { language, line: index + 1, rows: [], marker }; else if (marker === active.marker) { active.end = index + 1; blocks.push(active); active = null; } continue; }
    if (active) active.rows.push(line);
  }
  if (active) defects.push({ kind: "unclosed illustration fence", line: active.line, detail: active.language || "untagged" });
  const maxElements = BUDGETS[targetDepth] || BUDGETS["deep-dive"];
  for (const block of blocks) {
    const structuralAscii = ["text", "ascii"].includes(block.language) && block.rows.some((row) => CONNECTOR.test(row));
    if (!(["mermaid", "text", "ascii"].includes(block.language)) || (["text", "ascii"].includes(block.language) && !structuralAscii)) continue;
    const content = block.rows.map((row) => row.trim()).filter((row) => row && !row.startsWith("%%")); let elements;
    if (block.language === "mermaid") {
      const kind = content.length ? content[0].split(/\s+/)[0] : "";
      if (kind === "stateDiagram") defects.push({ kind: "deprecated state diagram", line: block.line, detail: "use stateDiagram-v2" });
      if (content.some((row) => /(?:^|\s)(?:style|classDef|click)\b/.test(row))) defects.push({ kind: "invalid mermaid", line: block.line, detail: "forbidden directive" });
      if (kind === "sequenceDiagram") { const participants = content.filter((row) => row.startsWith("participant ")).length; const messages = content.filter((row) => /(?:->>|-->>)/.test(row)).length; if (participants > 5 || messages > 12) defects.push({ kind: "illustration budget", line: block.line, detail: "sequence exceeds 5 participants or 12 messages" }); }
      if (kind === "journey") { const sections = content.filter((row) => row.startsWith("section ")).length; if (sections > 4) defects.push({ kind: "illustration budget", line: block.line, detail: "journey exceeds 4 sections" }); }
      if (kind === "journey" || kind === "timeline") {
        elements = content.slice(1).filter((row) => row && row !== "title" && !/^(title |section )/.test(row)).length;
      } else {
        elements = content.slice(1).filter((row) => CONNECTOR.test(row) || /^(participant |state |    )/.test(row)).length;
      }
    } else elements = content.filter((row) => !CONNECTOR.test(row)).length;
    if (elements > maxElements) defects.push({ kind: "illustration budget", line: block.line, detail: `${elements} elements exceeds ${maxElements}` });
    if (block.language === "mermaid" && elements && elements < MIN_MEANINGFUL_ELEMENTS) {
      defects.push({ kind: "decorative illustration", line: block.line, detail: `${elements} meaningful elements; state this in a sentence instead` });
    }
    if (!hasAdjacentProse(lines, block.line, block.end)) {
      defects.push({ kind: "undescribed illustration", line: block.line, detail: "no explanatory sentence beside the fence" });
    }
    if (block.language === "mermaid" && content.some((row) => /(?:^|[\s[(>|-])end(?:[\s\])<|-]|$)/.test(row))) {
      defects.push({ kind: "invalid mermaid", line: block.line, detail: "lowercase `end` breaks rendering; capitalize or wrap it" });
    }
  }
  return defects;
}
module.exports = { illustrationDefects, BUDGETS };
