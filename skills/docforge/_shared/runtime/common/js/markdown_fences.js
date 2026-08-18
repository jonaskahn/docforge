"use strict";

const OPEN_RE = /^\s{0,3}(`{3,}|~{3,})([^`]*)$/;
const SOURCE_LINK_RE = /\[[^\]]+\]\(([^)]+\.(?:c|cc|cpp|cs|go|java|js|jsx|json|mjs|properties|py|rb|rs|swift|toml|ts|tsx|xml|ya?ml)(?:#[^)]+)?)\)/g;
const SOURCE_LINE_RE = /[A-Za-z0-9][A-Za-z0-9_./-]*\.(?:c|cc|cpp|cs|go|java|js|jsx|json|mjs|properties|py|rb|rs|swift|toml|ts|tsx|xml|ya?ml)(?:#L\d+(?:-L\d+)?|:\d+(?:-\d+)?)(?!\s*@\s*[0-9a-f]{40})\b/g;
const LOCATOR_RE = /[A-Za-z0-9][A-Za-z0-9_./-]*#L\d+(?:-L\d+)?\s*@\s*[0-9a-f]{40}/;
const SHELL_LANGUAGES = new Set(["bash", "sh", "shell", "zsh", "fish", "powershell", "pwsh"]);

function inferredRole(language) {
  if (language === "mermaid") return "diagram";
  if (SHELL_LANGUAGES.has(language)) return "command";
  if (["markdown", "mdx"].includes(language)) return "markup";
  if (["text", "ascii", "console", ""].includes(language)) return "ambiguous";
  return "code";
}

function scanFences(text) {
  const fences = []; let current = null;
  for (const [index, line] of text.split(/\r?\n/).entries()) {
    const number = index + 1; const match = line.match(OPEN_RE);
    if (!current) {
      if (!match) continue;
      const info = match[2].trim().split(/\s+/).filter(Boolean);
      const language = info[0] || "";
      const explicitRole = info.slice(1).map((part) => part.startsWith("docforge-role=") ? part.slice("docforge-role=".length) : null).find(Boolean) || null;
      current = { start: number, marker: match[1], language, role: explicitRole || inferredRole(language), explicit_role: explicitRole, lines: [] };
      continue;
    }
    if (match && match[1][0] === current.marker[0] && match[1].length >= current.marker.length) {
      current.end = number; fences.push(current); current = null;
    } else current.lines.push([number, line]);
  }
  if (current) { current.end = null; fences.push(current); }
  return fences;
}

/**
 * Presentation defects outside fences.
 *
 * `webBase` is the repository's declared permalink base. A link built from it is
 * the sanctioned way to send a reader into source, so it is exempt from the
 * source-link and source-line rules -- both of which are otherwise scheme-blind
 * and would fire on the very form the expander produces. An unexpanded
 * authoring-form link stays a defect: it means `link_sources` never ran, and it
 * would 404 in the rendered site.
 */
function visiblePresentationDefects(text, webBase = null) {
  const defects = []; const fences = scanFences(text);
  const fencedLines = new Set(fences.flatMap((fence) => fence.lines.map(([number]) => number)));
  const base = (webBase || "").replace(/\/+$/, "");
  for (const [index, line] of text.split(/\r?\n/).entries()) {
    const number = index + 1; if (fencedLines.has(number)) continue;
    if (LOCATOR_RE.test(line)) defects.push({ kind: "visible-source-locator", line: number, detail: "use provenance, not a path/range/blob citation" });
    const pinned = [];
    SOURCE_LINK_RE.lastIndex = 0; let match;
    while ((match = SOURCE_LINK_RE.exec(line)) !== null) {
      const target = match[1];
      if (base && target.startsWith(base)) {
        pinned.push([match.index, match.index + match[0].length]);
        continue;
      }
      defects.push({ kind: base ? "unpinned-source-link" : "source-code-link", line: number, detail: target });
    }
    SOURCE_LINE_RE.lastIndex = 0; let sourceLineMatch;
    while ((sourceLineMatch = SOURCE_LINE_RE.exec(line)) !== null) {
      // The `#L97-104` inside a pinned permalink is part of the URL, not a
      // citation a reader has to decode.
      const start = sourceLineMatch.index;
      const finish = start + sourceLineMatch[0].length;
      if (pinned.some(([from, to]) => from <= start && finish <= to)) continue;
      defects.push({ kind: "visible-source-line", line: number, detail: sourceLineMatch[0] });
    }
  }
  for (const fence of fences) {
    if (!["command", "code", "diagram", "structure", "ambiguous"].includes(fence.role)) continue;
    const content = fence.lines.map(([, line]) => line.trim()).filter(Boolean);
    const words = content.reduce((total, line) => total + (line.match(/[A-Za-z]{2,}/g) || []).length, 0);
    const sentenceLines = content.filter((line) => /[.!?]["')\]]?$/.test(line));
    const syntaxLines = content.filter((line) => /[{};]|=>|\$ |^[-+]?\w+[=:]|\|/.test(line));
    if (content.length >= 2 && words >= 20 && sentenceLines.length / content.length >= 0.7 && syntaxLines.length / content.length < 0.3) {
      defects.push({ kind: "prose-in-code-fence", line: fence.start, detail: `${fence.role} fence contains explanatory prose` });
    }
  }
  return defects;
}

module.exports = { inferredRole, scanFences, visiblePresentationDefects };
