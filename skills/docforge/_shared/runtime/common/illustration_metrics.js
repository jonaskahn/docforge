"use strict";
/** Portable, bounded illustration metrics for Docforge Markdown. */

const FENCE = /^\s*(`{3,})([\w-]*)/;
const CONNECTOR = /(?:-->|--|\|\|--|->>|-->>)/;
const BUDGETS = { orientation: [1, 5], "deep-dive": [3, 12], reference: [1, 12], router: [0, 0] };
function illustrationDefects(text, targetDepth) {
  const defects = []; const blocks = []; let active = null;
  for (const [index, line] of text.split(/\r?\n/).entries()) {
    const match = line.match(FENCE);
    if (match) { const [marker, language] = [match[1], match[2]]; if (!active) active = { language, line: index + 1, rows: [], marker }; else if (marker === active.marker) { blocks.push(active); active = null; } continue; }
    if (active) active.rows.push(line);
  }
  if (active) defects.push({ kind: "unclosed illustration fence", line: active.line, detail: active.language || "untagged" });
  let illustrations = 0; const [maxIllustrations, maxElements] = BUDGETS[targetDepth] || BUDGETS["deep-dive"];
  for (const block of blocks) {
    const structuralAscii = ["text", "ascii"].includes(block.language) && block.rows.some((row) => CONNECTOR.test(row));
    if (!(["mermaid", "text", "ascii"].includes(block.language)) || (["text", "ascii"].includes(block.language) && !structuralAscii)) continue;
    illustrations += 1; const content = block.rows.map((row) => row.trim()).filter((row) => row && !row.startsWith("%%")); let elements;
    if (block.language === "mermaid") {
      const kind = content.length ? content[0].split(/\s+/)[0] : "";
      if (kind === "stateDiagram") defects.push({ kind: "deprecated state diagram", line: block.line, detail: "use stateDiagram-v2" });
      if (content.some((row) => /(?:^|\s)(?:style|classDef|click)\b/.test(row))) defects.push({ kind: "invalid mermaid", line: block.line, detail: "forbidden directive" });
      if (kind === "sequenceDiagram") { const participants = content.filter((row) => row.startsWith("participant ")).length; const messages = content.filter((row) => /(?:->>|-->>)/.test(row)).length; if (participants > 5 || messages > 12) defects.push({ kind: "illustration budget", line: block.line, detail: "sequence exceeds 5 participants or 12 messages" }); }
      elements = content.slice(1).filter((row) => CONNECTOR.test(row) || /^(participant |state |    )/.test(row)).length;
    } else elements = content.filter((row) => !CONNECTOR.test(row)).length;
    if (elements > maxElements) defects.push({ kind: "illustration budget", line: block.line, detail: `${elements} elements exceeds ${maxElements}` });
  }
  if (illustrations > maxIllustrations) defects.push({ kind: "illustration budget", line: 1, detail: `${illustrations} illustrations exceeds ${maxIllustrations}` });
  return defects;
}
module.exports = { illustrationDefects, BUDGETS };
