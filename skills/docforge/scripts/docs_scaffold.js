#!/usr/bin/env node
"use strict";
/* Scaffold and audit a repository documentation tree.
 *
 * Two modes:
 *
 *   scaffold  create the docs/ tree for a tier and overlays, seeding files from
 *             assets/templates/ where a template exists
 *
 *   audit     report what is missing, what still holds unfilled {{…}} scaffold
 *             markers, which internal links are broken, which other generated
 *             documents are named in backtick text instead of being linked to
 *             (unlinked file mentions), where forge-specific language has
 *             leaked into documents that are supposed to be host-neutral, and
 *             which flow/concept folders were promoted without a real subfile
 *             (folder-only-readme). Typed <UPPER_SNAKE> human-fill tokens are
 *             listed separately and do not count as defects.
 *
 * Examples
 * --------
 *   node docs_scaffold.js --repo ../my-service --tier 2 --overlay api
 *   node docs_scaffold.js --repo ../my-service --tier 2 --overlay api --dry-run
 *   node docs_scaffold.js --repo ../my-service --audit
 *
 * Node.js built-ins only.
 */

const fs = require("fs");
const path = require("path");

const SKILL_ROOT = path.resolve(__dirname, "..");
const TEMPLATES = path.join(SKILL_ROOT, "assets", "templates");

// ---------------------------------------------------------------------------
// Tree specification.  [path, tier, template-or-null]
// Directories are implied by their files; every directory also gets a README.md.
// ---------------------------------------------------------------------------

const SPINE = [
  ["README.md", 1, "root-readme.md"],
  ["CHANGELOG.md", 1, "changelog.md"],
  ["SECURITY.md", 2, "root-security.md"],
  ["docs/README.md", 1, "docs-index.md"],
  ["docs/product/overview.md", 1, null],
  ["docs/product/capabilities.md", 2, null],
  ["docs/product/roadmap.md", 2, null],
  ["docs/flows/README.md", 2, null],
  ["docs/architecture/high-level.md", 1, "architecture-high-level.md"],
  ["docs/architecture/low-level.md", 2, "architecture-low-level.md"],
  ["docs/architecture/data-flow.md", 2, null],
  ["docs/architecture/dependencies.md", 2, "dependencies.md"],
  ["docs/architecture/tech-debt.md", 2, "tech-debt.md"],
  ["docs/architecture/constraints.md", 2, "constraints.md"],
  ["docs/architecture/concepts/README.md", 2, null],
  ["docs/architecture/decisions/0001-record-architecture-decisions.md", 2, "adr.md"],
  ["docs/engineering/setup.md", 1, "setup.md"],
  ["docs/engineering/testing.md", 1, null],
  ["docs/engineering/conventions.md", 2, null],
  ["docs/engineering/release.md", 2, null],
  ["docs/operations/deployment.md", 2, null],
  ["docs/operations/observability.md", 2, null],
  ["docs/operations/runbooks/example-symptom.md", 2, "runbook.md"],
  ["docs/reference/configuration.md", 1, null],
  ["docs/reference/limitations.md", 1, "limitations.md"],
  ["docs/reference/glossary.md", 2, null],
  ["docs/security/threat-model.md", 2, null],
  ["docs/security/data-handling.md", 2, null],
  ["docs/contributing/README.md", 2, null],
  ["docs/contributing/ownership.md", 2, null],
  ["docs/contributing/templates/bug-report.md", 2, null],
  ["docs/contributing/templates/feature-request.md", 2, null],
  ["docs/contributing/templates/change-proposal.md", 2, null],
];

const OVERLAYS = {
  "data-pipeline": [
    ["docs/architecture/data-flow.md", null],
    ["docs/architecture/contracts/README.md", null],
    ["docs/architecture/contracts/example-dataset.md", "data-contract.md"],
    ["docs/engineering/data-quality.md", null],
    ["docs/reference/data-types.md", null],
    ["docs/operations/runbooks/backfill.md", "runbook.md"],
    ["docs/operations/runbooks/failed-run.md", "runbook.md"],
    ["docs/operations/runbooks/schema-change.md", "runbook.md"],
  ],
  api: [
    ["docs/product/quickstart.md", null],
    ["docs/product/versioning.md", null],
    ["docs/reference/api.md", null],
    ["docs/reference/errors.md", "error-catalog.md"],
    ["docs/reference/rate-limits.md", null],
    ["docs/security/authentication.md", null],
  ],
  web: [
    ["docs/architecture/rendering.md", null],
    ["docs/architecture/state.md", null],
    ["docs/architecture/ui-components.md", null],
    ["docs/engineering/styling.md", null],
    ["docs/reference/browser-support.md", null],
  ],
  library: [
    ["docs/product/quickstart.md", null],
    ["docs/product/migration/README.md", null],
    ["docs/reference/api.md", null],
    ["docs/reference/compatibility.md", null],
    ["docs/engineering/publishing.md", null],
  ],
  infrastructure: [
    ["docs/architecture/environments.md", null],
    ["docs/architecture/network.md", null],
    ["docs/operations/apply.md", null],
    ["docs/operations/state.md", null],
    ["docs/operations/disaster-recovery.md", null],
    ["docs/reference/resources.md", null],
    ["docs/reference/access.md", null],
  ],
  "business-analyst": [
    ["docs/product/business-analyst/README.md", "ba-readme.md"],
    ["docs/product/business-analyst/business-rules.md", "business-rules.md"],
    ["docs/product/business-analyst/process-flows.md", "process-flows.md"],
    ["docs/product/business-analyst/requirements-traceability.md", "requirements-traceability.md"],
  ],
  "product-owner": [
    ["docs/product/product-owner/README.md", "po-readme.md"],
    ["docs/product/product-owner/feature-catalog.md", "feature-catalog.md"],
    ["docs/product/product-owner/success-metrics.md", "success-metrics.md"],
    ["docs/product/product-owner/release-notes.md", "release-notes.md"],
    ["docs/product/product-owner/backlog-traceability.md", "backlog-traceability.md"],
  ],
  // AI-agent context files (AGENTS.md kernel + docs/agents/ brief stubs). See
  // references/overlay-agent-context.md. agents-conventions.md (conditional on an
  // existing CONVENTIONS.md) and the cross-vendor mirrors are deliberately excluded
  // here — they're hand-pulled at finalization time, never scaffolded up front.
  "agent-context": [
    ["AGENTS.md", "agents-kernel.md"],
    ["CLAUDE.md", "claude-md.md"],
    ["CLAUDE.local.md", "claude-local-md.md"],
    [".claude/settings.json", "claude-settings.json"],
    ["docs/agents/architecture.md", "agents-architecture.md"],
    ["docs/agents/patterns.md", "agents-patterns.md"],
    ["docs/agents/glossary.md", "agents-glossary.md"],
    ["docs/agents/testing.md", "agents-testing.md"],
    ["docs/agents/tech-debt.md", "agents-tech-debt.md"],
    ["docs/agents/flow.md", "agents-flow.md"],
  ],
};

const FOLDER_BLURBS = {
  "docs/product": "What this does and why it exists — written for business readers.",
  "docs/flows": "One file per business flow, flat by default; promoted to a folder only once a real per-reader deep-dive is written.",
  "docs/architecture": "How the system is built, and why — high-level map, low-level detail, concepts, decisions.",
  "docs/architecture/concepts": "Deep-dive subsystems, flat by default; promoted to a folder only once a real engineering deep-dive is written.",
  "docs/architecture/decisions": "Architecture decision records. Append-only; superseded records keep their number.",
  "docs/architecture/contracts": "Data contracts for every dataset consumed or published.",
  "docs/engineering": "Setup, testing, conventions and release — everything a contributor needs.",
  "docs/operations": "Deployment, observability and runbooks.",
  "docs/operations/runbooks": "One file per recurring incident or procedure, named by symptom.",
  "docs/reference": "Lookup material: configuration, limitations, errors, glossary.",
  "docs/security": "Threat model, data handling and disclosure process.",
  "docs/contributing": "How changes are proposed, reviewed and merged.",
  "docs/contributing/templates": "Host-neutral issue and change templates.",
  "docs/product/migration": "One guide per major version transition.",
  "docs/product/business-analyst": "Business rules, process flows and requirements traceability — for a Business Analyst.",
  "docs/product/product-owner": "Feature value, success metrics and release notes — for a Product Owner.",
  "docs/agents": "Machine-consumption context for AI coding agents — brief stubs that link to (never restate) the human-facing documents that own each fact. The entry kernel is root AGENTS.md, not this folder's index.",
};

const PLACEHOLDER = /\{\{[^}]+\}\}/g; // {{…}} scaffold marker — must be filled
const TODO = /TODO\(([^)]*)\)/g; // retired punt form — treated as a defect
// Typed human-fill token: <UPPER_SNAKE> standing in for one genuinely external value.
// These are intentional and expected; they are reported separately, not as defects.
const TOKEN = /<[A-Z][A-Z0-9_]{2,}>/g;
const LINK = /\[[^\]]*\]\(([^)]+)\)/g;
// A backtick-quoted path ending in .md — a candidate cross-reference that
// should be an actual link, not bare text naming the file.
const MENTION = /`([A-Za-z0-9_./-]+\.md)`/g;
const FORGE = new RegExp(
  "\\b(github|gitlab|bitbucket|gitea|forgejo|sourcehut|azure devops|" +
    "pull request|merge request|github actions|gitlab ci|codeowners)\\b",
  "gi"
);
const NEUTRAL_ZONE = ["docs/contributing/"];

function toPosix(p) {
  return p.split(path.sep).join("/");
}

// Mirrors Python's str.title(): capitalize the first letter of every run of
// alphabetic characters, lowercase the rest.
function titleCase(s) {
  return s.replace(/-/g, " ").replace(/[A-Za-z]+/g, (w) => w[0].toUpperCase() + w.slice(1).toLowerCase());
}

// ---------------------------------------------------------------------------
// Scaffold
// ---------------------------------------------------------------------------

function folderReadme(relDir) {
  const blurb = FOLDER_BLURBS[relDir] || "{{One line: what lives in this folder.}}";
  const title = titleCase(relDir.replace(/\/$/, "").split("/").pop());
  return `# ${title}\n\n${blurb}\n\n| Document | Contents |\n|---|---|\n| | |\n`;
}

function collect(tier, overlays) {
  const wanted = new Map();
  for (const [p, t, tpl] of SPINE) {
    if (t <= tier) wanted.set(p, tpl);
  }
  for (const name of overlays) {
    for (const [p, tpl] of OVERLAYS[name] || []) {
      if (!wanted.has(p)) wanted.set(p, tpl);
    }
  }
  return wanted;
}

function scaffold(repo, tier, overlays, dryRun) {
  const wanted = collect(tier, overlays);

  // every directory under docs/ gets an index
  const dirs = new Set();
  for (const p of wanted.keys()) {
    if (p.startsWith("docs/")) dirs.add(toPosix(path.dirname(p)));
  }
  for (const d of dirs) {
    const idx = `${d}/README.md`;
    if (!wanted.has(idx)) wanted.set(idx, "__folder_readme__");
  }

  let created = 0;
  let skipped = 0;
  const relSorted = [...wanted.keys()].sort();
  for (const rel of relSorted) {
    const target = path.join(repo, rel);
    if (fs.existsSync(target)) {
      skipped++;
      continue;
    }
    const tpl = wanted.get(rel);
    let body;
    if (tpl === "__folder_readme__") {
      body = folderReadme(toPosix(path.dirname(rel)));
    } else if (tpl && fs.existsSync(path.join(TEMPLATES, tpl))) {
      body = fs.readFileSync(path.join(TEMPLATES, tpl), "utf8");
    } else {
      const title = titleCase(path.basename(rel, ".md"));
      body =
        `# ${title}\n\n_Last reviewed: {{YYYY-MM-DD}}_\n\n` +
        "{{Write this section from evidence in the repository. " +
        "Delete this file if it does not apply.}}\n";
    }
    console.log(`${dryRun ? "would create" : "create"}  ${rel}`);
    if (!dryRun) {
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.writeFileSync(target, body, "utf8");
    }
    created++;
  }

  console.log(`\n${created} created, ${skipped} already present.`);
  if (created && !dryRun) {
    console.log(
      "\nThese are scaffolds, not deliverables. Write every section you have " +
        "evidence for in full; the only marks that may survive are typed " +
        "<UPPER_SNAKE> tokens for genuinely external facts. No {{…}} marker " +
        "should remain before presenting."
    );
  }
  return 0;
}

// ---------------------------------------------------------------------------
// Audit
// ---------------------------------------------------------------------------

function walkMdFiles(dir) {
  const out = [];
  function walk(cur) {
    let entries;
    try {
      entries = fs.readdirSync(cur, { withFileTypes: true });
    } catch {
      return;
    }
    for (const entry of entries) {
      const full = path.join(cur, entry.name);
      if (entry.isDirectory()) {
        walk(full);
      } else if (entry.isFile() && entry.name.endsWith(".md")) {
        if (!full.split(path.sep).includes("_archive")) out.push(full);
      }
    }
  }
  walk(dir);
  return out.sort();
}

function audit(repo, tier, overlays) {
  const docs = path.join(repo, "docs");
  if (!fs.existsSync(docs) || !fs.statSync(docs).isDirectory()) {
    console.log("No docs/ directory found. Run scaffold mode first.");
    return 1;
  }

  const files = walkMdFiles(docs);
  for (const extra of ["README.md", "SECURITY.md", "CONTRIBUTING.md", "AGENTS.md", "CLAUDE.md"]) {
    const p = path.join(repo, extra);
    if (fs.existsSync(p)) files.push(p);
  }

  const findings = {
    missing: [],
    "unfilled scaffold": [],
    empty: [],
    "broken links": [],
    "unlinked file mentions": [],
    "forge leakage": [],
    "no review date": [],
    "folder-only-readme": [],
  };
  // Informational, not a defect: typed <UPPER_SNAKE> tokens are the sanctioned
  // human-fill slots for genuinely external facts. Listed so a reviewer knows
  // exactly what remains to fill, but excluded from the defect total.
  const tokens = [];

  const wanted = collect(tier, overlays);
  for (const rel of [...wanted.keys()].sort()) {
    if (!fs.existsSync(path.join(repo, rel))) findings.missing.push(rel);
  }

  // A flow or concept promoted to a folder but never given a real subfile: the
  // exact shape that produces a dangling "Go deeper" link. Flat files are the
  // default and carry no defect; a folder must earn its existence with content.
  for (const parent of ["docs/flows", "docs/architecture/concepts"]) {
    const parentDir = path.join(repo, parent);
    if (!fs.existsSync(parentDir) || !fs.statSync(parentDir).isDirectory()) continue;
    const children = fs.readdirSync(parentDir).sort();
    for (const name of children) {
      if (name.startsWith("_")) continue;
      const child = path.join(parentDir, name);
      if (!fs.statSync(child).isDirectory()) continue;
      const siblings = fs.readdirSync(child).filter((f) => f.endsWith(".md") && f !== "README.md");
      if (fs.existsSync(path.join(child, "README.md")) && siblings.length === 0) {
        findings["folder-only-readme"].push(`${toPosix(path.relative(repo, child))}/`);
      }
    }
  }

  for (const filePath of files) {
    const rel = toPosix(path.relative(repo, filePath));
    const text = fs.readFileSync(filePath, "utf8");

    const nScaffold = (text.match(PLACEHOLDER) || []).length + (text.match(TODO) || []).length;
    if (nScaffold) findings["unfilled scaffold"].push(`${rel} (${nScaffold})`);

    const nToken = new Set(text.match(TOKEN) || []).size;
    if (nToken) tokens.push(`${rel} (${nToken})`);

    const body = text
      .split("\n")
      .filter((ln) => ln.trim() && !ln.trimStart().startsWith("#"))
      .join("\n");
    if (body.length < 120) findings.empty.push(rel);

    let m;
    const linkedTargets = new Set();
    LINK.lastIndex = 0;
    while ((m = LINK.exec(text)) !== null) {
      const target = m[1];
      linkedTargets.add(target.split("#")[0]);
      if (/^(https?:\/\/|mailto:|#)/.test(target)) continue;
      if (target.includes("{{") || target.includes("NNNN")) continue; // unfilled template link
      TOKEN.lastIndex = 0;
      if (TOKEN.test(target)) continue; // link points through a human-fill token
      const resolved = path.resolve(path.dirname(filePath), target.split("#")[0]);
      if (!fs.existsSync(resolved)) findings["broken links"].push(`${rel} -> ${target}`);
    }

    // a real file named in backticks but never actually linked to
    for (const line of text.split("\n")) {
      MENTION.lastIndex = 0;
      let mm;
      while ((mm = MENTION.exec(line)) !== null) {
        const target = mm[1];
        const basename = target.split("/").pop();
        if (linkedTargets.has(target) || linkedTargets.has(basename)) continue;
        const before = mm.index > 0 ? line[mm.index - 1] : "";
        const after = line.slice(mm.index + mm[0].length, mm.index + mm[0].length + 2);
        if (before === "[" && after.startsWith("(")) continue; // `` `file.md` `` used as its own link label
        const resolved = path.resolve(path.dirname(filePath), target);
        if (fs.existsSync(resolved)) findings["unlinked file mentions"].push(`${rel} -> ${target}`);
      }
    }

    if (!NEUTRAL_ZONE.some((z) => rel.startsWith(z)) && rel !== "CONTRIBUTING.md") {
      const hits = new Set();
      FORGE.lastIndex = 0;
      let fm;
      while ((fm = FORGE.exec(text)) !== null) hits.add(fm[0].toLowerCase());
      if (hits.size) findings["forge leakage"].push(`${rel}: ${[...hits].sort().join(", ")}`);
    }

    const volatile = [
      "limitations",
      "dependencies",
      "setup",
      "configuration",
      "overview",
      "high-level",
      "low-level",
      "tech-debt",
      "constraints",
      "runbook",
    ];
    if (volatile.some((v) => rel.includes(v)) && !rel.endsWith("README.md") && !text.includes("Last reviewed")) {
      findings["no review date"].push(rel);
    }
  }

  const total = Object.values(findings).reduce((a, v) => a + v.length, 0);
  for (const [label, items] of Object.entries(findings)) {
    if (!items.length) continue;
    console.log(`\n${label.toUpperCase()} (${items.length})`);
    for (const item of items.slice(0, 25)) console.log(`  ${item}`);
    if (items.length > 25) console.log(`  ... and ${items.length - 25} more`);
  }

  if (tokens.length) {
    console.log(`\nHUMAN-FILL TOKENS (${tokens.length})  — not defects; external facts for a human to fill in during review`);
    for (const item of tokens.slice(0, 25)) console.log(`  ${item}`);
    if (tokens.length > 25) console.log(`  ... and ${tokens.length - 25} more`);
  }

  console.log(
    `\n${files.length} documents checked, ${total} defects` +
      (tokens.length ? `, ${tokens.length} files with human-fill tokens.` : ".")
  );
  if (!total) {
    console.log(
      "No defects. Any UNFILLED SCAFFOLD count must be zero before presenting; " +
        "typed <UPPER_SNAKE> tokens are fine to leave for human review. Now apply " +
        "the judgement checks in references/quality-bar.md — this script cannot " +
        "tell you whether the content is true."
    );
  }
  return 0;
}

function parseArgs(argv) {
  const args = { tier: 2, overlay: [], audit: false, dryRun: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--repo") args.repo = argv[++i];
    else if (a === "--tier") args.tier = parseInt(argv[++i], 10);
    else if (a === "--overlay") args.overlay.push(argv[++i]);
    else if (a === "--audit") args.audit = true;
    else if (a === "--dry-run") args.dryRun = true;
  }
  return args;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.repo) {
    console.error("usage: docs_scaffold.js --repo <path> [--tier 1|2|3] [--overlay <name>]... [--audit] [--dry-run]");
    return 1;
  }
  if (![1, 2, 3].includes(args.tier)) {
    console.error(`--tier must be 1, 2 or 3, got ${args.tier}`);
    return 1;
  }
  for (const o of args.overlay) {
    if (!(o in OVERLAYS)) {
      console.error(`Unknown overlay '${o}'. One of: ${Object.keys(OVERLAYS).sort().join(", ")}`);
      return 1;
    }
  }
  if (!fs.existsSync(args.repo) || !fs.statSync(args.repo).isDirectory()) {
    console.error(`Not a directory: ${args.repo}`);
    return 1;
  }
  if (args.audit) return audit(args.repo, args.tier, args.overlay);
  return scaffold(args.repo, args.tier, args.overlay, args.dryRun);
}

process.exit(main());
