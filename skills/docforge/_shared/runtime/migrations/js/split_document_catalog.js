#!/usr/bin/env node
"use strict";
/* One-shot: split references/document-catalog.md into references/catalog-contracts/.
 *
 * Rows keyed by Type may list multiple aliased types (`docs-index / folder-index / ...`);
 * each listed type becomes its own contract file so lookups by type resolve.
 * Mirrors migrations/python/split_document_catalog.py.
 */

const fs = require("fs");
const path = require("path");

const DEFAULT_ROOT = path.resolve(__dirname, "..", "..", "..");

const HEADER = `# Document catalog contracts

This directory owns content contracts: must-present material, keep-out
boundaries, primary mode, and target depth. Selection, paths, evidence
capabilities, write order, templates, and audit profiles are machine-readable
via \`query_catalog\` against \`.metadata/catalog/\`.

## Universal contract

Every substantive document must:

- answer the reader question implied by its type;
- cite the repository evidence used by each section;
- describe current behavior, boundaries, failure modes, and adjacent systems;
- keep rationale in decision records and volatile lookup facts in reference
  documents;
- link to facts owned elsewhere instead of repeating them;
- contain no unresolved scaffold markers.

Router/index documents orient and link. Procedure documents are executable in
order. Reference documents optimize lookup. Explanation documents establish
mechanism, constraints, and tradeoffs.

## Index

`;

const ROW_RE = /^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$/;

function layout(root) {
  return {
    source: path.join(root, "references", "document-catalog.md"),
    outDir: path.join(root, "references", "catalog-contracts"),
  };
}

function parseRows(text) {
  const rows = [];
  let inTable = false;
  for (const line of text.split(/\r?\n/)) {
    if (line.startsWith("| Type | Must present |")) {
      inTable = true;
      continue;
    }
    if (inTable && line.startsWith("|---")) continue;
    if (inTable && !line.startsWith("|")) break;
    if (!inTable) continue;
    const match = ROW_RE.exec(line);
    if (!match) continue;
    const types = match[1].split("/").map((part) => part.trim()).filter(Boolean);
    rows.push({
      types,
      must: match[2].trim(),
      keep: match[3].trim(),
      mode: match[4].trim(),
      depth: match[5].trim(),
    });
  }
  return rows;
}

function trailingSections(text) {
  const marker = "## Risk-register routing";
  const idx = text.indexOf(marker);
  if (idx < 0) return "";
  return `${text.slice(idx).trimEnd()}\n`;
}

function contractBody(typeId, row, aliases) {
  let aliasNote = "";
  if (aliases.length) {
    aliasNote = `\nAliased with: ${aliases.map((alias) => `\`${alias}\``).join(", ")} `
      + "(same content contract).\n";
  }
  return (
    `# \`${typeId}\`\n\n`
    + `Content contract for document type \`${typeId}\`.\n`
    + `${aliasNote}\n`
    + "| Type | Must present | Keep out | Primary mode | Depth |\n"
    + "|---|---|---|---|---|\n"
    + `| ${typeId} | ${row.must} | ${row.keep} | ${row.mode} | ${row.depth} |\n`
  );
}

function emit(dryRun, root) {
  const L = layout(root);
  if (!fs.existsSync(L.source)) {
    process.stderr.write(`error: missing ${L.source}\n`);
    return 1;
  }
  const text = fs.readFileSync(L.source, "utf8");
  const rows = parseRows(text);
  if (!rows.length) {
    process.stderr.write("error: no contract table rows parsed\n");
    return 1;
  }

  const files = {};
  const indexLines = [];
  for (const row of rows) {
    for (const typeId of row.types) {
      const aliases = row.types.filter((candidate) => candidate !== typeId);
      files[typeId] = contractBody(typeId, row, aliases);
      let gist = row.must;
      if (gist.length > 90) {
        gist = `${gist.slice(0, 87).trimEnd()}…`;
      }
      indexLines.push(`- \`${typeId}\` — ${gist} → [${typeId}.md](${typeId}.md)`);
    }
  }

  const trailing = trailingSections(text);
  const readme = HEADER + indexLines.join("\n") + "\n\n" + trailing;

  if (dryRun) {
    console.log(`would write ${Object.keys(files).length} contract files + README.md`);
    for (const name of Object.keys(files).sort()) {
      console.log(`  ${name}.md`);
    }
    return 0;
  }

  fs.mkdirSync(L.outDir, { recursive: true });
  // Clear prior contract files (keep directory).
  for (const entry of fs.readdirSync(L.outDir)) {
    if (entry.endsWith(".md")) fs.unlinkSync(path.join(L.outDir, entry));
  }
  fs.writeFileSync(path.join(L.outDir, "README.md"), readme, "utf8");
  for (const [typeId, body] of Object.entries(files)) {
    fs.writeFileSync(path.join(L.outDir, `${typeId}.md`), body, "utf8");
  }

  // Stub the monolith so leftover links still resolve.
  const stub = (
    "# Document catalog\n\n"
    + "This file has been split for context efficiency. Content contracts live in\n"
    + "[`catalog-contracts/`](catalog-contracts/README.md). The machine catalog is\n"
    + "queried via `runtime/cli/python/query_catalog.py` against `.metadata/catalog/`.\n\n"
    + "Universal contract, risk-register routing, and typed profile behavior are\n"
    + "preserved in [`catalog-contracts/README.md`](catalog-contracts/README.md).\n"
  );
  fs.writeFileSync(L.source, stub, "utf8");
  console.log(`Wrote ${Object.keys(files).length} contracts under ${path.relative(root, L.outDir)}/`);
  return 0;
}

function main(argv) {
  const args = { dryRun: false, root: null };
  for (let i = 2; i < argv.length; i += 1) {
    const token = argv[i];
    if (token === "--dry-run") args.dryRun = true;
    else if (token === "--root") args.root = argv[++i];
    else if (token === "--help" || token === "-h") {
      console.log("usage: split_document_catalog.js [--dry-run] [--root <path>]");
      return 0;
    } else {
      process.stderr.write(`error: unknown argument: ${token}\n`);
      return 2;
    }
  }
  const root = args.root ? path.resolve(args.root) : DEFAULT_ROOT;
  return emit(args.dryRun, root);
}

module.exports = { main, emit, parseRows, layout };

if (require.main === module) {
  process.exitCode = main(process.argv);
}
