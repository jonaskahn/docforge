"use strict";
/** Portable, bounded illustration metrics for Docforge Markdown. */

const FENCE = /^\s*(`{3,})([\w-]*)/;
const CONNECTOR = /(?:-->|--|\|\|--|->>|-->>)/;
// Maximum meaningful elements within a single illustration, per target depth.
// There is deliberately no cap on the number of illustrations in a document:
// every documentation authority surveyed prescribes splitting a dense diagram
// into several simpler ones, so a count cap would forbid the recommended remedy.
const BUDGETS = { orientation: 5, "deep-dive": 12, reference: 12, router: 12 };
function illustrationDefects(text, targetDepth) {
  const defects = []; const blocks = []; let active = null;
  for (const [index, line] of text.split(/\r?\n/).entries()) {
    const match = line.match(FENCE);
    if (match) { const [marker, language] = [match[1], match[2]]; if (!active) active = { language, line: index + 1, rows: [], marker }; else if (marker === active.marker) { blocks.push(active); active = null; } continue; }
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
  }
  return defects;
}
module.exports = { illustrationDefects, BUDGETS };
