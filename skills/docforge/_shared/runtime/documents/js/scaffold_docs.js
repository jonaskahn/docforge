#!/usr/bin/env node
"use strict";
/** Preview, materialize, or audit the exact tree in a Docforge manifest. */

const fs = require("fs");
const path = require("path");
const { ensureDocforgeGitignore, fail, loadManifest, unmanagedPaths } = require("../../common/js/_util.js");
const pf = require("../../common/js/provenance_frontmatter.js");
const store = require("../../common/js/provenance_store.js");
const { planEntries } = require("../../common/js/plan.js");
const { scanFences } = require("../../common/js/markdown_fences.js");
const { SPECIAL_DOC_OUTPUTS } = require("../../common/js/special_files.js");
const {
  AGENT_CONTEXT_GROUP,
  agentContextLeaks,
  agentContextOutboundFindings,
} = require("../../common/js/agent_context.js");
const queryCatalog = require("../../catalog/js/query_catalog.js");
const { identityOf } = require("../../common/js/repo_identity.js");
const SKILL_ROOT = path.resolve(fs.realpathSync(__dirname), "..", "..", "..");
const PLACEHOLDER = /\{\{[^}]+\}\}|TODO\([^)]*\)/g;
const TOKEN = /<[A-Z][A-Z0-9_]{2,}>/g;
const LINK = /\[[^\]]*\]\(([^)]+)\)/g;
const FORGE = /\b(github|gitlab|bitbucket|gitea|forgejo|sourcehut|azure devops|github actions|gitlab ci|codeowners)\b/gi;
const MARKDOWN_EXCEPTIONS = SPECIAL_DOC_OUTPUTS;
const WRITTEN = new Set(["generated", "needs_review", "complete"]);
const INDEX_TYPES = new Set([
  "folder-index", "docs-index", "portfolio-index", "portfolio-decisions-index",
  "ba-index", "po-index", "decision-index", "flow-index",
]);
// A merged compact file replaces its folder's index and inherits its routing
// duty; it is not in INDEX_TYPES because it is not otherwise an index.
const COMPACT_TYPE = "compact-doc";
const CHILDREN_START = "<!-- docforge-children:start -->";
const CHILDREN_END = "<!-- docforge-children:end -->";
const TABLE_SEPARATOR = /^\|(?:\s*:?-{3,}:?\s*\|)+$/;
// Folders whose contents are dynamically discovered, mapped to whether the
// collection root itself must hold a child.
//
// `docs/flows/` is exempt at the root: its index is a discovery report that
// also records deferred, placeholder, and skipped candidates, so it earns its
// place with no promoted flow. Every other collection index is pure routing --
// with no child it is a promise the tree never keeps, which is how `concepts/`,
// `decisions/`, and `runbooks/` shipped holding nothing but an index explaining
// its own emptiness, in two separate repositories, with the audit recording
// PASS. Family subfolders are checked under every prefix.
const COLLECTION_PREFIXES = {
  "docs/flows/": false,
  "docs/architecture/concepts/": true,
  "docs/architecture/decisions/": true,
  "docs/architecture/contracts/": true,
  "docs/operations/runbooks/": true,
  "docs/product/migrations/": true,
  "docs-portfolio/epics/": true,
  "docs-portfolio/decisions/": true,
};
const SCALAR_PROVENANCE_FIELDS = new Set(
  [...pf.PROVENANCE_FIELDS].filter((key) => !["graph", "sections", "generator"].includes(key)),
);

function resolveManifest(value, repo) {
  if (path.isAbsolute(value)) return value;
  const direct = path.resolve(value);
  const repoRelative = path.resolve(repo, value);
  return fs.existsSync(direct) ? direct : repoRelative;
}
function activeDocuments(manifest) {
  return manifest.documents.filter((doc) => doc.status !== "skipped" && doc.status !== "retired");
}
// Agent outputs are never routing rows. This keeps human indexes isolated and
// prevents a legacy agent index from enumerating peer agent outputs. Entries
// without a group predate the field and remain human-facing.
function routableChildren(doc, manifest) {
  return activeDocuments(manifest).filter((child) => child.group !== AGENT_CONTEXT_GROUP);
}
// `groups` is the transient `<area>` work filter: it narrows which documents
// this run reports on and never touches `project.groups`.
function preview(manifest, repo, revise, groups = null) {
  const scoped = new Set(groups || []);
  const docs = activeDocuments(manifest).filter((doc) => !scoped.size || scoped.has(doc.group));
  const project = manifest.project || {};
  console.log(`Generation plan — tier: ${project.tier || "unknown"}`);
  const profiles = project.profiles || {};
  for (const dimension of ["shapes", "platforms", "frameworks", "concerns", "audiences"]) {
    console.log(`  ${dimension}: ${(profiles[dimension] || []).join(", ") || "none"}`);
  }
  console.log();
  const flowIndexPath = path.join(repo, ".docforge", "flow-index.json");
  const entries = planEntries(repo, manifest, flowIndexPath, revise, groups);
  const manifestEntries = new Map(entries.filter((entry) => !entry.is_flow).map((entry) => [entry.id, entry]));
  const flowEntries = entries.filter((entry) => entry.is_flow);
  for (const doc of docs) {
    const entry = manifestEntries.get(doc.id) || {};
    const action = entry.action || "?";
    const reason = entry.reason || "";
    console.log(`${String(doc.write_order).padStart(3, "0")}  ${doc.id.padEnd(28)}  ${doc.path}`);
    const requires = (doc.requires || []).join(", ") || "none";
    const origins = (((doc.selection || {}).origins) || [])
      .map((origin) => `${origin.kind}:${origin.id}`).join(", ") || "manifest";
    console.log(`     ${doc.group} / ${doc.type} | depth: ${doc.target_depth} | requires: ${requires} | selected by: ${origins} | action: ${action} — ${reason}`);
  }
  if (flowEntries.length) {
    console.log("");
    console.log("Flows:");
    for (const entry of flowEntries) {
      const label = entry.flow_id ? `${entry.flow_name} (${entry.flow_id})` : entry.path;
      console.log(`  ${label} → ${entry.path}  [${entry.action}] ${entry.reason}`);
    }
  }
  const flowCount = docs.filter((doc) => (doc.requires || []).includes("flow_graph")).length;
  let summary = `\n${docs.length} manifest documents; ${flowCount} require a flow graph`;
  if (flowEntries.length) summary += `; ${flowEntries.length} main-priority flow documents`;
  console.log(`${summary}.`);
  return 0;
}
function posixDirname(value) {
  return path.posix.dirname(value);
}
function titleFor(doc) {
  return doc.title || doc.id.replace(/[-_]/g, " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
}
function scaffoldEntry(doc, manifest) {
  const publicMeta = store.publicFromManifest(doc);
  const entry = { ...publicMeta };
  entry.provenance = pf.scaffoldProvenance(doc.id, doc.path, {
    tier: (manifest.project || {}).tier || "<TIER>",
    target_depth: doc.target_depth,
  });
  return entry;
}
function isDirectChild(directory, candidate) {
  const relative = path.posix.relative(directory, candidate.path);
  const parts = relative.split("/");
  return !relative.startsWith("..") && (parts.length === 1 || (parts.length === 2 && parts[1] === "README.md"));
}
// Each index template carries its own table header inside the managed markers,
// and the templates disagree on width (2 columns for a section README, 5 for
// the decision log, 8 for the flow index). Regenerating the block has to
// re-emit that header: rows alone render as literal pipe text, not a table.
function tableHeader(block) {
  const lines = block.split("\n").filter((line) => line.trim());
  for (let index = 0; index < lines.length - 1; index += 1) {
    const head = lines[index].trim();
    const rule = lines[index + 1].trim();
    if (head.startsWith("|") && TABLE_SEPARATOR.test(rule)) {
      return { header: [head, rule], columns: (rule.replace(/^\||\|$/g, "").match(/\|/g) || []).length + 1 };
    }
  }
  return { header: ["| Document | Answers |", "|---|---|"], columns: 2 };
}
function padRow(cells, columns) {
  const padded = cells.slice(0, columns);
  while (padded.length < columns) padded.push("—");
  return `| ${padded.join(" | ")} |`;
}
function childRows(doc, manifest, columns = 2) {
  const directory = posixDirname(doc.path);
  const children = routableChildren(doc, manifest)
    .filter((candidate) => candidate.id !== doc.id && isDirectChild(directory, candidate))
    .sort((a, b) => a.write_order - b.write_order || a.path.localeCompare(b.path));
  const rows = children.map((child) => {
    const relative = path.posix.relative(directory, child.path);
    return padRow([`[${titleFor(child)}](${relative})`, `{{the reader question ${child.id} answers}}`], columns);
  });
  if (!rows.length) {
    return [
      padRow(
        ["_No documents are selected in this section yet; they are written when repository evidence selects them._", "—"],
        columns,
      ),
    ];
  }
  return rows;
}
function expandChildrenBlock(body, doc, manifest) {
  const start = body.indexOf(CHILDREN_START);
  const end = body.indexOf(CHILDREN_END);
  if (start === -1 || end === -1) return body;
  const { header, columns } = tableHeader(body.slice(start + CHILDREN_START.length, end));
  const block = [CHILDREN_START, ...header, ...childRows(doc, manifest, columns), CHILDREN_END].join("\n");
  return body.slice(0, start) + block + body.slice(end + CHILDREN_END.length);
}
function scaffoldBody(doc, manifest) {
  if (INDEX_TYPES.has(doc.type)) {
    const template = path.join(SKILL_ROOT, doc.scaffold_template);
    if (!fs.existsSync(template)) throw new Error(`template not found for ${doc.id}: ${doc.scaffold_template}`);
    let body = fs.readFileSync(template, "utf8");
    const parsed = pf.parseFrontmatter(body);
    if (parsed.state !== "missing") body = body.slice(parsed.end);
    body = expandChildrenBlock(body, doc, manifest);
    return body.replace("{{TITLE}}", titleFor(doc));
  }
  const template = path.join(SKILL_ROOT, doc.scaffold_template);
  if (!fs.existsSync(template)) throw new Error(`template not found for ${doc.id}: ${doc.scaffold_template}`);
  let body = fs.readFileSync(template, "utf8");
  const parsed = pf.parseFrontmatter(body);
  if (parsed.state !== "missing") body = body.slice(parsed.end);
  return body;
}
function deepMerge(existing, defaults) {
  if (Array.isArray(existing) && Array.isArray(defaults)) return existing.concat(defaults.filter((item) => !existing.some((old) => JSON.stringify(old) === JSON.stringify(item))));
  if (existing && defaults && typeof existing === "object" && typeof defaults === "object" && !Array.isArray(existing) && !Array.isArray(defaults)) {
    const result = { ...existing };
    for (const [key, value] of Object.entries(defaults)) result[key] = key in result ? deepMerge(result[key], value) : value;
    return result;
  }
  return existing;
}
function ensureLocalIgnore(repo) {
  const target = path.join(repo, ".gitignore");
  const text = fs.existsSync(target) ? fs.readFileSync(target, "utf8") : "";
  if (!text.split(/\r?\n/).includes("CLAUDE.local.md")) {
    const suffix = !text || text.endsWith("\n") ? "" : "\n";
    fs.writeFileSync(target, text + suffix + "CLAUDE.local.md\n");
  }
}
function writeDocument(repo, doc, manifest) {
  const target = path.join(repo, ...doc.path.split("/"));
  const body = scaffoldBody(doc, manifest);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  let action;
  if (doc.type === "machine-config" && fs.existsSync(target)) {
    const existing = JSON.parse(fs.readFileSync(target, "utf8"));
    const defaults = JSON.parse(body);
    fs.writeFileSync(target, JSON.stringify(deepMerge(existing, defaults), null, 2) + "\n");
    action = "merge";
  } else if (fs.existsSync(target)) {
    action = "exists";
  } else {
    fs.writeFileSync(target, body);
    action = "create";
  }
  if (
    action === "create"
    && doc.provenance_mode === "sections"
    && doc.type !== "machine-config"
    && !MARKDOWN_EXCEPTIONS.has(doc.path)
  ) {
    store.writeEntry(repo, doc.path, scaffoldEntry(doc, manifest));
  }
  if (doc.path === "CLAUDE.local.md") ensureLocalIgnore(repo);
  console.log(`${action}  ${doc.path}`);
}
function requiredIndexes(doc, manifest) {
  const ancestors = [];
  let parent = posixDirname(doc.path);
  while (parent && parent !== ".") {
    ancestors.push(`${parent}/README.md`);
    parent = posixDirname(parent);
  }
  const byPath = Object.fromEntries(activeDocuments(manifest).map((item) => [item.path, item]));
  return ancestors.reverse().filter((item) => item !== doc.path && byPath[item]).map((item) => byPath[item]);
}
function materialize(repo, manifest, docId) {
  ensureDocforgeGitignore(path.join(repo, ".docforge"));
  const doc = activeDocuments(manifest).find((item) => item.id === docId);
  if (!doc) return fail(`document id not found or skipped: ${docId}`, 2);
  try {
    for (const index of requiredIndexes(doc, manifest)) {
      if (!fs.existsSync(path.join(repo, ...index.path.split("/")))) writeDocument(repo, index, manifest);
    }
    writeDocument(repo, doc, manifest);
    return 0;
  } catch (error) {
    return fail(error.message, 2);
  }
}
function provenanceDefects(repo, doc, state, provenance, body, tier) {
  const result = {
    "missing provenance": [], "unparseable provenance": [],
    "legacy provenance": [], "obsolete schema": [], "empty provenance": [],
    "invalid blob": [], "unknown source": [], "unknown section": [],
  };
  if (state === "missing") {
    result["missing provenance"].push(doc.path);
    return result;
  }
  if (state === "unparseable") {
    result["unparseable provenance"].push(doc.path);
    return result;
  }
  if (state === "obsolete") {
    result["obsolete schema"].push(`${doc.path}: run migrate_metadata.js`);
    return result;
  }
  if (state === "legacy") {
    result["legacy provenance"].push(doc.path);
    return result;
  }
  if (!provenance || typeof provenance !== "object" || Array.isArray(provenance)) {
    result["missing provenance"].push(doc.path);
    return result;
  }
  const missing = [...pf.PROVENANCE_FIELDS].filter((key) => !(key in provenance)).sort();
  const graph = provenance.graph;
  if (!graph || typeof graph !== "object" || !("provider" in graph) || !("flow" in graph)) missing.push("graph.provider/flow");
  const generator = provenance.generator;
  if (!generator || typeof generator !== "object" || !("name" in generator) || !("version" in generator)) {
    missing.push("generator.name/version");
  }
  if (missing.length || !pf.SUPPORTED_SCHEMA_VERSIONS.has(provenance.schema) || "graph_snapshot" in provenance) {
    const detail = missing.length ? missing.join(", ") : "invalid schema or obsolete graph_snapshot";
    result["missing provenance"].push(`${doc.path}: ${detail}`);
  }
  const sections = provenance.sections;
  if (!Array.isArray(sections)) {
    result["missing provenance"].push(`${doc.path}: sections`);
    return result;
  }
  if (WRITTEN.has(doc.status)) {
    const concrete = [...SCALAR_PROVENANCE_FIELDS]
      .filter((key) => typeof provenance[key] !== "string" || !provenance[key] || pf.SCAFFOLD_TOKEN.test(provenance[key]));
    if (generator && typeof generator === "object") {
      for (const key of ["name", "version"]) {
        if (typeof generator[key] !== "string" || !generator[key] || pf.SCAFFOLD_TOKEN.test(generator[key])) {
          concrete.push(`generator.${key}`);
        }
      }
    } else if (!concrete.includes("generator")) {
      concrete.push("generator");
    }
    if (graph && typeof graph === "object") {
      for (const key of ["provider", "flow"]) {
        if (typeof graph[key] !== "string" || !graph[key] || pf.SCAFFOLD_TOKEN.test(graph[key])) {
          concrete.push(`graph.${key}`);
        }
      }
    }
    if (concrete.length) result["missing provenance"].push(`${doc.path}: non-concrete ${concrete.sort().join(", ")}`);
    const expected = { doc_id: doc.id, path: doc.path, tier, target_depth: doc.target_depth };
    const invalidFields = [];
    for (const [key, value] of Object.entries(expected)) {
      if (value !== undefined && provenance[key] !== value) invalidFields.push(key);
    }
    if (graph && !pf.FLOW_VALUES.has(graph.flow)) invalidFields.push("graph.flow");
    if ("git_commit" in provenance && (typeof provenance.git_commit !== "string" || !pf.BLOB.test(provenance.git_commit))) invalidFields.push("git_commit");
    if (invalidFields.length) result["missing provenance"].push(`${doc.path}: invalid ${invalidFields.sort().join(", ")}`);
    if (!sections.length) result["empty provenance"].push(doc.path);
  }
  const anchors = new Set();
  for (const line of body.split(/\r?\n/)) {
    const match = line.match(/^(#{1,6})\s+(.+?)\s*#*\s*$/);
    if (match) anchors.add(headingAnchor(match[2]));
  }
  for (const section of sections) {
    const sectionId = section && typeof section.id === "string" ? section.id : null;
    if (!sectionId || !anchors.has(sectionId)) result["unknown section"].push(`${doc.path}: ${sectionId || "<missing>"}`);
    for (const source of (section && Array.isArray(section.sources)) ? section.sources : []) {
      const sourcePath = source && typeof source.path === "string" ? source.path : "";
      if (!source || typeof source.git_blob !== "string" || !pf.BLOB.test(source.git_blob)) {
        result["invalid blob"].push(`${doc.path}: ${sourcePath || "<missing>"}`);
      }
      const target = path.join(repo, ...sourcePath.split("/"));
      if (!sourcePath || !fs.existsSync(target) || !fs.statSync(target).isFile()) {
        result["unknown source"].push(`${doc.path}: ${sourcePath || "<missing>"}`);
      }
      if (!source || !pf.SOURCE_ROLES.has(source.role)) {
        result["missing provenance"].push(`${doc.path}: invalid source role`);
      }
    }
    if (!section || !Array.isArray(section.sources) || !Array.isArray(section.unresolved)) result["missing provenance"].push(`${doc.path}: invalid section shape`);
  }
  return result;
}
function headingAnchor(value) {
  return value.trim().toLowerCase().replace(/[^\p{L}\p{N}_\s-]/gu, "").replace(/[\s-]+/g, "-").replace(/^-|-$/g, "");
}
// `[childrenFolders, linkBase]` for a routing document.
//
// For an index the two coincide: `docs/reference/README.md` owns
// `docs/reference` and its links also resolve from there. For a merged compact
// file they diverge — `docs/reference.md` stands in for the index of
// `docs/reference`, so it owns that folder's children, but its own links
// resolve from `docs`. Using the parent for both is what silently exempted
// every merged file from this check.
//
// A merged file can stand in for more than one folder, and for folders its own
// path does not name: `docs/decisions.md` folds `docs/architecture/decisions/`,
// and `docs/operations.md` folds both `docs/operations/` and
// `docs/operations/runbooks/`. Take the folders from the members the file
// actually merged, not from its own path.
function coverageScope(doc) {
  const parent = posixDirname(doc.path);
  if (doc.type !== COMPACT_TYPE) return [[parent], parent];
  const folders = new Set(
    (doc.compact_members || []).map(
      (member) => posixDirname(queryCatalog.loadType(queryCatalog.memberTypeId(member)).path),
    ),
  );
  folders.add(doc.path.replace(/\.[^./]+$/, ""));
  return [[...folders].sort(), parent];
}
// Every materialized direct child of a section index must be linked.
//
// Merged compact files carry the same duty. A group that spilled past the
// compact section cap keeps children at their own standard paths with no README
// above them — if the merged file does not link them, nothing does.
function readmeChildCoverage(repo, doc, manifest, text) {
  if (!INDEX_TYPES.has(doc.type) && doc.type !== COMPACT_TYPE) return [];
  const [childrenFolders, linkBase] = coverageScope(doc);
  const missing = new Set();
  for (const candidate of routableChildren(doc, manifest)) {
    if (candidate.id === doc.id) continue;
    if (!childrenFolders.some((folder) => isDirectChild(folder, candidate))) continue;
    if (!fs.existsSync(path.join(repo, ...candidate.path.split("/")))) continue;
    const relative = path.posix.relative(linkBase, candidate.path);
    const link = relative.startsWith("..") ? candidate.path : relative;
    if (!text.includes(link) && !text.includes(`./${link}`)) missing.add(candidate.path);
  }
  return [...missing].sort();
}

const STRUCTURAL_GLYPHS = /[│├└┌┐┘┬┴┤─]/;
// Accessibility directives and a closing `}` may precede the diagram
// declaration inside a mermaid fence.
const MERMAID_DIRECTIVE = /^(?:accTitle|accDescr)\s*:|^\}$/;

/**
 * The form of every illustration in the document, in order.
 *
 * A Mermaid fence's form is the first token of its content, so a declared
 * `sequenceDiagram` is no longer satisfied by whatever diagram happens to be
 * present -- which is how a pre-baked ASCII layout tree passed for the one
 * runtime scenario a 30 KB document owed.
 */
function illustrationForms(text) {
  const forms = [];
  for (const fence of scanFences(text)) {
    const lines = fence.lines.map(([, line]) => line.trim()).filter((line) => line);
    if (fence.language === "mermaid") {
      // `%%` comments and the `accTitle:` / `accDescr:` accessibility directives
      // may precede the declaration, so the kind is the first line that is
      // neither.
      const body = lines.filter((line) => !line.startsWith("%%") && !MERMAID_DIRECTIVE.test(line));
      if (body.length) forms.push(body[0].split(/\s+/)[0]);
      continue;
    }
    if (["text", "ascii", ""].includes(fence.language) && lines.some((line) => STRUCTURAL_GLYPHS.test(line))) {
      forms.push("text");
    }
  }
  return forms;
}

/** True when the file carries any recognized illustration. */
function hasDeclaredIllustration(text) {
  return illustrationForms(text).length > 0;
}

/**
 * Every view a document declares must be present, by form.
 *
 * `illustration_views` lists the reader questions this type owes an answer to;
 * a missing view is a question the document leaves unanswered. A view marked
 * `required: false` is conditional on evidence (a data model that does not
 * exist, a flow with one outcome) and is never demanded. Falls back to
 * `dominant_form` for a type that declares no views.
 */
function illustrationCoverage(doc, text) {
  if (doc.group === AGENT_CONTEXT_GROUP) return [];
  if (MARKDOWN_EXCEPTIONS.has(doc.path) || doc.type === "machine-config") return [];
  if (!WRITTEN.has(doc.status)) return [];
  const present = illustrationForms(text);
  const views = (doc.illustration_views || []).filter((view) => view.required !== false);
  if (views.length) {
    const findings = [];
    const remaining = [...present];
    for (const view of views) {
      const index = remaining.indexOf(view.form);
      if (index >= 0) {
        remaining.splice(index, 1);
        continue;
      }
      findings.push(
        `${doc.path}: missing the ${view.form} view in "${view.section}" (${view.question})`,
      );
    }
    return findings;
  }
  const form = doc.dominant_form;
  if (form == null || form === "table") return [];
  if (present.length) return [];
  return [`${doc.path}: declared dominant_form ${form}, no mermaid or structural text fence`];
}

function cohesionDefects(docs, texts) {
  // No document is an island: in a section folder holding two or more
  // written non-router documents, each either links a sibling or is linked
  // by one. The section README alone does not satisfy it.
  const findings = [];
  const byFolder = new Map();
  for (const doc of docs) {
    if (doc.group === AGENT_CONTEXT_GROUP) continue;
    if (INDEX_TYPES.has(doc.type) || doc.type === COMPACT_TYPE) continue;
    if (!WRITTEN.has(doc.status)) continue;
    const folder = posixDirname(doc.path);
    if (!byFolder.has(folder)) byFolder.set(folder, []);
    byFolder.get(folder).push(doc);
  }
  for (const [folder, members] of [...byFolder.entries()].sort((a, b) => a[0].localeCompare(b[0]))) {
    if (members.length < 2) continue;
    const siblingPaths = new Set(members.map((member) => member.path));
    const outgoing = new Map();
    for (const member of members) {
      const base = posixDirname(member.path);
      const linked = new Set();
      const body = texts.get(member.path) || "";
      for (const match of body.matchAll(LINK)) {
        const target = match[1].split("#", 1)[0].trim();
        if (!target || /^(https?:\/\/|mailto:)/.test(target)) continue;
        if (/\{\{[^}]+\}\}|<[A-Z][A-Z0-9_]{2,}>/.test(target)) continue;
        const normalized = path.posix.normalize(path.posix.join(base, target));
        if (siblingPaths.has(normalized) && normalized !== member.path) linked.add(normalized);
      }
      outgoing.set(member.path, linked);
    }
    const linkedBy = new Set([...outgoing.values()].flatMap((set) => [...set]));
    for (const member of members) {
      if (!(outgoing.get(member.path) || new Set()).size && !linkedBy.has(member.path)) {
        findings.push(`${folder}: ${member.path} is an island — links no sibling and no sibling links it`);
      }
    }
  }
  return findings;
}
function audit(repo, manifest) {
  const identity = identityOf(manifest);
  const webBase = identity ? identity.web_base : null;
  const findings = {
    missing: [],
    "unfilled scaffold": [],
    "missing provenance": [],
    "unparseable provenance": [],
    "legacy provenance": [],
    "obsolete schema": [],
    "empty provenance": [],
    "invalid blob": [],
    "unknown source": [],
    "unknown section": [],
    "broken links": [],
    "readme child coverage": [],
    "illustration coverage": [],
    "section cohesion": [],
    "agent-context leak": [],
    "agent-context outbound": [],
    "invalid json": [],
    "folder-only promotion": [],
    "forge leakage": [],
    unexpected: [],
  };
  const tokens = [];
  const texts = new Map();
  const docs = activeDocuments(manifest);
  const expected = new Set(docs.map((doc) => doc.path));
  const selfManaged = unmanagedPaths(manifest);
  for (const rootName of ["docs", "docs-portfolio"]) {
    const root = path.join(repo, rootName);
    if (!fs.existsSync(root) || !fs.statSync(root).isDirectory()) continue;
    const stack = [root];
    while (stack.length) {
      const current = stack.pop();
      for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
        const target = path.join(current, entry.name);
        if (entry.isDirectory()) {
          if (entry.name !== "_archive") stack.push(target);
        } else if (entry.isFile() && entry.name.endsWith(".md")) {
          const rel = path.relative(repo, target).split(path.sep).join("/");
          if (!expected.has(rel) && !selfManaged.has(rel)) findings.unexpected.push(rel);
        }
      }
    }
  }
  for (const doc of docs) {
    const target = path.join(repo, ...doc.path.split("/"));
    if (!fs.existsSync(target) || !fs.statSync(target).isFile()) {
      findings.missing.push(doc.path);
      continue;
    }
    const text = fs.readFileSync(target, "utf8");
    for (const finding of agentContextLeaks(doc, manifest, text)) {
      findings["agent-context leak"].push(`${doc.path}:${finding.line} [${finding.kind}] -> ${finding.target}`);
    }
    for (const finding of agentContextOutboundFindings(doc, manifest, text)) {
      findings["agent-context outbound"].push(`${doc.path}:${finding.line} [${finding.kind}] -> ${finding.target}`);
    }
    if (doc.type === "machine-config") {
      try { JSON.parse(text); } catch { findings["invalid json"].push(doc.path); }
      continue;
    }
    const placeholders = text.match(PLACEHOLDER) || [];
    if (placeholders.length) findings["unfilled scaffold"].push(`${doc.path} (${placeholders.length})`);
    const foundTokens = [...new Set(text.match(TOKEN) || [])].sort();
    if (foundTokens.length) tokens.push(`${doc.path}: ${foundTokens.join(", ")}`);
    // A declared permalink base is the one sanctioned place a forge name may
    // appear; without this every GitHub- or GitLab-hosted repository would trip
    // on every source link it is now expected to carry.
    const scrubbed = webBase ? text.split(webBase).join("") : text;
    const forgeHits = [...new Set((scrubbed.match(FORGE) || []).map((item) => item.toLowerCase()))].sort();
    if (forgeHits.length) findings["forge leakage"].push(`${doc.path}: ${forgeHits.join(", ")}`);
    if (doc.provenance_mode === "sections" && !MARKDOWN_EXCEPTIONS.has(doc.path)) {
      const meta = store.readDocMetadata(repo, doc);
      // An un-migrated inline document is a legacy finding, not a pass.
      const state = meta.state === "inline" ? "legacy" : meta.state;
      const provenance = meta.provenance;
      const body = text;
      const defects = provenanceDefects(repo, doc, state, provenance, body, (manifest.project || {}).tier);
      for (const [kind, items] of Object.entries(defects)) findings[kind].push(...items);
    }
    for (const match of text.matchAll(LINK)) {
      const link = match[1];
      const clean = link.split("#", 1)[0];
      if (!clean || /^(https?:\/\/|mailto:)/.test(clean)) continue;
      if (/\{\{[^}]+\}\}|<[A-Z][A-Z0-9_]{2,}>/.test(clean)) continue;
      if (!fs.existsSync(path.resolve(path.dirname(target), clean))) findings["broken links"].push(`${doc.path} -> ${link}`);
    }
    for (const item of readmeChildCoverage(repo, doc, manifest, text)) {
      findings["readme child coverage"].push(`${doc.path}: missing link to ${item}`);
    }
    findings["illustration coverage"].push(...illustrationCoverage(doc, text));
    texts.set(doc.path, text);
  }
  findings["section cohesion"].push(...cohesionDefects(docs, texts));
  for (const [prefix, rootCounts] of Object.entries(COLLECTION_PREFIXES)) {
    const root = prefix.replace(/\/$/, "");
    const folders = new Set([...expected].filter((value) => value.startsWith(prefix)).map(posixDirname));
    if (rootCounts) folders.add(root);
    else folders.delete(root);
    for (const folder of [...folders].sort()) {
      if (expected.has(`${folder}/README.md`)) {
        const children = [...expected].filter((value) => posixDirname(value) === folder && !value.endsWith("/README.md"));
        if (!children.length) findings["folder-only promotion"].push(folder);
      }
    }
  }
  const total = Object.values(findings).reduce((sum, items) => sum + items.length, 0);
  for (const [label, items] of Object.entries(findings)) {
    items.sort();
    if (items.length) {
      console.log(`${label.toUpperCase()} (${items.length})`);
      for (const item of items) console.log(`  ${item}`);
      console.log();
    }
  }
  if (tokens.length) {
    console.log(`EXTERNAL TOKENS (${tokens.length})`);
    for (const item of tokens) console.log(`  ${item}`);
    console.log();
  }
  console.log(`${docs.length} manifest documents checked, ${total} defects.`);
  return total ? 1 : 0;
}
function parseArgs(argv) {
  const result = { group: [] };
  const allowed = new Set(["repo", "manifest", "dry-run", "document", "audit", "revise", "group"]);
  for (let i = 0; i < argv.length; i++) {
    const token = argv[i];
    if (token === "-h" || token === "--help") return { help: true };
    if (!token.startsWith("--")) throw new Error(`unexpected argument: ${token}`);
    const raw = token.slice(2);
    if (!allowed.has(raw)) throw new Error(`unknown option: ${token}`);
    const key = raw.replace(/-/g, "_");
    if (raw === "dry-run" || raw === "audit" || raw === "revise") result[key] = true;
    else {
      if (i + 1 >= argv.length || argv[i + 1].startsWith("--")) throw new Error(`option requires a value: ${token}`);
      if (raw === "group") result.group.push(argv[++i]);
      else result[key] = argv[++i];
    }
  }
  return result;
}
function usage() {
  console.log("usage: scaffold_docs.js --repo <path> --manifest <path> (--dry-run [--revise] [--group <id>] | --document <id> | --audit)");
}
function main() {
  let args;
  try {
    args = parseArgs(process.argv.slice(2));
    if (args.help) { usage(); return 0; }
    if (!args.repo || !args.manifest) throw new Error("--repo and --manifest are required");
    const modes = [Boolean(args.dry_run), Boolean(args.document), Boolean(args.audit)].filter(Boolean).length;
    if (modes !== 1) throw new Error("choose exactly one of --dry-run, --document, or --audit");
    if (!fs.existsSync(args.repo) || !fs.statSync(args.repo).isDirectory()) return fail(`not a directory: ${args.repo}`, 2);
    const manifest = loadManifest(resolveManifest(args.manifest, args.repo), {
      requireDocuments: true,
    });
    if (args.dry_run) {
      let scopedGroups;
      try {
        scopedGroups = queryCatalog.normalizeGroups(args.group);
      } catch (error) {
        return fail(error.message, 2);
      }
      return preview(manifest, args.repo, args.revise, scopedGroups);
    }
    if (args.document) return materialize(args.repo, manifest, args.document);
    return audit(args.repo, manifest);
  } catch (error) {
    usage();
    return fail(error.message, 2);
  }
}
process.exit(main());
