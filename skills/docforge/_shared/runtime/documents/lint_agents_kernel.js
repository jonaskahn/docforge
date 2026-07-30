#!/usr/bin/env node
"use strict";
/* lint_agents_kernel.js — mechanical rubric check for the coding-agents audience.
 *
 * Runs the format-specific checks runtime/cli/js/lint_document.js has no concept of: the
 * 100-line cap, the 7-numbered-section shape, the tagline/test-sentence convention,
 * and dangling `@docs/agents/...` references. Run alongside lint_document.js, which
 * still covers this file's generic checks (scaffold markers, empty headings, dead
 * `[](...)` links, unlinked mentions) — this script never replaces it.
 *
 * Checks, for the single AGENTS.md-shaped file given:
 *   * line count <= 100                                         (defect; 85-100 is a
 *                                                                  non-fatal warning)
 *   * line 1 is a level-1 heading, line 2 is non-heading prose   (defect)
 *   * every "## " heading matches "## <n>. <Title>"              (defect)
 *   * no "### " heading outside section 6 (Absolute Rules)       (defect)
 *   * a bold "**tagline**" as the first non-blank line of every
 *     section                                                    (defect)
 *   * a "The test: ... ." line in every section except 2
 *     (Boundaries) and 6 (Absolute Rules)                        (defect)
 *   * no bare MUST/NEVER/ALWAYS outside section 6                (defect)
 *   * at most one fenced code block                              (defect)
 *   * no " you "/" we "/" I " in prose                            (defect)
 *   * last non-blank line starts with "Working if:"              (defect)
 *   * no bare http(s):// URL outside an HTML comment              (defect)
 *   * a provenance HTML comment in the first 10 lines            (defect)
 *   * every "@docs/agents/..." reference resolves to a file on
 *     disk, relative to --repo                                   (defect)
 *
 * Usage:
 *   node lint_agents_kernel.js --file AGENTS.md --repo .
 *   node lint_agents_kernel.js --file AGENTS.md --repo . --json
 *
 * Exit code 0 if no defects, 1 if any defect, 2 on a usage/IO error. Node.js built-ins only.
 */

const fs = require("fs");
const path = require("path");

const HEADING_RE = /^(#{1,6})\s+(.*\S)\s*$/;
const H2_NUMBERED_RE = /^## (\d+)\. [A-Z]/;
const TAGLINE_RE = /^\*\*.+\*\*$/;
const TEST_LINE_RE = /^The test: .+\.$/;
const BARE_MODAL_RE = /(?<![\w-])(MUST|NEVER|ALWAYS)(?![\w-])/;
const FENCE_RE = /^```/;
const BARE_URL_RE = /https?:\/\//;
const AT_REF_RE = /@([\w./-]+\.md)/g;
const WEAK_PRONOUN_RE = / (you|we|I) /;

const EXEMPT_SECTIONS = ["2", "6"]; // Boundaries, Absolute Rules — no "The test:" line required

function checkAgentsKernel(filePath, repoDir) {
  const text = fs.readFileSync(filePath, "utf8");
  const lines = text.split("\n");

  let n = lines.length;
  while (n > 0 && !lines[n - 1].trim()) n--; // trailing blank lines don't count toward the cap

  const defects = [];
  const warnings = [];

  if (n > 100) {
    defects.push({ kind: "line-cap", line: n, detail: `${n} lines, cap is 100` });
  } else if (n >= 85) {
    warnings.push({ kind: "line-cap-warning", line: n, detail: `${n} lines, approaching the 100-line cap` });
  }

  if (!lines.length || !lines[0].startsWith("# ")) {
    defects.push({ kind: "opening-shape", line: 1, detail: "line 1 must be a level-1 heading" });
  }

  const heads = [];
  for (let i = 0; i < lines.length; i++) {
    const m = lines[i].match(HEADING_RE);
    if (m) heads.push({ index: i, match: m });
  }
  const h2s = heads.filter((h) => h.match[1] === "##");

  const firstH2 = h2s.length ? h2s[0].index : n;
  const preamble = lines.slice(1, firstH2);
  if (!preamble.some((l) => l.trim() && !HEADING_RE.test(l))) {
    defects.push({ kind: "opening-shape", line: 2, detail: "no description prose between the title and the first section" });
  }

  // locate section 6 (Absolute Rules)'s line range so its exemptions apply only inside it
  let section6Range = [n, n];
  for (let idx = 0; idx < h2s.length; idx++) {
    const i = h2s[idx].index;
    const numbered = lines[i].match(H2_NUMBERED_RE);
    if (numbered && numbered[1] === "6") {
      const end = idx + 1 < h2s.length ? h2s[idx + 1].index : n;
      section6Range = [i, end];
    }
  }
  const inSection6 = (i) => section6Range[0] <= i && i < section6Range[1];

  for (let i = 0; i < lines.length; i++) {
    const l = lines[i];
    if (l.startsWith("## ") && !H2_NUMBERED_RE.test(l)) {
      defects.push({ kind: "heading-shape", line: i + 1, detail: l.trim() });
    }
    if (l.startsWith("### ") && !inSection6(i)) {
      defects.push({ kind: "stray-h3", line: i + 1, detail: l.trim() });
    }
    if (BARE_MODAL_RE.test(l) && !inSection6(i) && !l.trimStart().startsWith("#")) {
      defects.push({ kind: "bare-modal-outside-rules", line: i + 1, detail: l.trim() });
    }
    if (WEAK_PRONOUN_RE.test(l)) {
      defects.push({ kind: "weak-pronoun", line: i + 1, detail: l.trim() });
    }
    if (BARE_URL_RE.test(l) && !l.includes("<!--")) {
      defects.push({ kind: "bare-url", line: i + 1, detail: l.trim() });
    }
  }

  for (let idx = 0; idx < h2s.length; idx++) {
    const i = h2s[idx].index;
    const numbered = lines[i].match(H2_NUMBERED_RE);
    const secNo = numbered ? numbered[1] : null;
    const end = idx + 1 < h2s.length ? h2s[idx + 1].index : n;
    const body = lines.slice(i + 1, end);
    const firstNonblank = body.find((l) => l.trim()) || "";
    if (!TAGLINE_RE.test(firstNonblank.trim())) {
      defects.push({ kind: "missing-tagline", line: i + 1, detail: lines[i].trim() });
    }
    if (!EXEMPT_SECTIONS.includes(secNo)) {
      if (!body.some((l) => TEST_LINE_RE.test(l.trim()))) {
        defects.push({ kind: "missing-test-line", line: i + 1, detail: lines[i].trim() });
      }
    }
  }

  const fenceCount = Math.floor(lines.filter((l) => FENCE_RE.test(l.trim())).length / 2);
  if (fenceCount > 1) {
    defects.push({ kind: "too-many-code-blocks", line: 0, detail: `${fenceCount} fenced blocks, max 1` });
  }

  if (!lines.slice(0, 10).some((l) => l.includes("<!--"))) {
    defects.push({ kind: "missing-provenance", line: 0, detail: "no HTML-comment provenance in first 10 lines" });
  }

  const stripped = lines.slice(0, n).filter((l) => l.trim());
  if (!stripped.length || !stripped[stripped.length - 1].startsWith("Working if:")) {
    defects.push({ kind: "missing-working-if", line: n, detail: "last line must start with 'Working if:'" });
  }

  for (let i = 0; i < lines.length; i++) {
    AT_REF_RE.lastIndex = 0;
    let m;
    while ((m = AT_REF_RE.exec(lines[i])) !== null) {
      const target = m[1];
      const resolved = path.resolve(repoDir, target);
      if (!fs.existsSync(resolved)) {
        defects.push({ kind: "dangling-at-ref", line: i + 1, detail: `@${target}` });
      }
    }
  }

  return { file: filePath, defects, warnings };
}

function parseArgs(argv) {
  const args = { file: null, repo: ".", json: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--file") args.file = argv[++i];
    else if (a === "--repo") args.repo = argv[++i];
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

  const result = checkAgentsKernel(args.file, args.repo);

  if (args.json) {
    console.log(JSON.stringify(result, null, 2));
  } else {
    if (!result.defects.length) console.log(`CLEAN    ${result.file}`);
    for (const d of result.defects) {
      const loc = d.line ? `:${d.line}` : "";
      console.log(`DEFECT   ${result.file}${loc}  ${d.kind}: ${d.detail}`);
    }
    for (const w of result.warnings) {
      const loc = w.line ? `:${w.line}` : "";
      console.log(`WARNING  ${result.file}${loc}  ${w.kind}: ${w.detail}`);
    }
  }

  return result.defects.length ? 1 : 0;
}

process.exit(main());
