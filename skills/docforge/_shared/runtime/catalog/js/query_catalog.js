#!/usr/bin/env node
"use strict";
/** Query the split Docforge catalog. Agents and scripts use this — not raw files. */

const fs = require("fs");
const path = require("path");
const { dumpJson, fail } = require("../../common/js/_util.js");

const SKILL_ROOT = path.resolve(fs.realpathSync(__dirname), "..", "..", "..");
const CATALOG_DIR = path.join(SKILL_ROOT, ".metadata", "catalog");
// Depth brakes for a compact merge. The *core* cap is an authoring rule the
// catalog can check: a group may declare at most this many tier-driven members
// (no selectors, no condition). Beyond it the group is too broad for one file
// and the fix is a second group with its own `compact_target`, not a bigger cap.
const COMPACT_CORE_CAP = 8;
// The *section* cap bounds the file a project actually materializes. Profile-
// and audience-driven members are evidence-gated, so how many a group carries
// is not knowable from the catalog; foldCompactGroups enforces this one at
// plan time and spills the overflow to standard paths.
const COMPACT_SECTION_CAP = 14;
// Instances of a dynamic collection (flows, decisions, concepts, runbooks) that
// get a full `##` section in the merged file. The rest stay rows in the file's
// candidate matrix — the same main/deferred split the flow index already uses.
const COMPACT_DYNAMIC_CAP = 6;
const INDEX_PATH = path.join(CATALOG_DIR, "index.json");
const TYPES_DIR = path.join(CATALOG_DIR, "types");
const PROFILES_DIR = path.join(CATALOG_DIR, "profiles");
const PROFILE_DIMENSIONS = ["shapes", "platforms", "frameworks", "concerns", "audiences"];
// `timeline`, `mindmap`, `sankey`, `treemap`, and `C4` are documented by Mermaid
// as experimental ("the syntax and properties can change in future releases"),
// and `architecture-beta` / `block-beta` still require a `-beta` keyword. A
// diagram that stops rendering on a dependency bump is worse than the prose it
// replaced, so none of them is declarable.
const ALLOWED_DOMINANT_FORMS = new Set([
  null,
  undefined,
  "table",
  "text",
  "flowchart",
  "sequenceDiagram",
  "erDiagram",
  "stateDiagram-v2",
  "journey",
]);
// A declared view is always a real illustration, so `table` is not a view form.
const ALLOWED_VIEW_FORMS = new Set(
  [...ALLOWED_DOMINANT_FORMS].filter((form) => form && form !== "table"),
);
const VIEW_DEPTHS = new Set(["orientation", "working", "deep-dive", "reference", "router"]);
const TARGET_DEPTHS = new Set(["orientation", "deep-dive", "reference", "router"]);
const MODEL_DEPTHS = {
  c4: ["context", "container", "component", "component-evidence"],
  arc42: ["context", "building-block-l1", "building-block-l2", "runtime-scenarios"],
  stride: ["boundary-element", "full-element", "interaction-risk"],
  adr: ["nygard", "madr-min", "madr-full"],
  prov: ["core", "expanded", "qualified"],
  mermaid: ["single-form", "complementary", "annotated"],
};
const MODEL_DEPTH_ORDER = ["c4", "arc42", "stride", "adr", "prov", "mermaid"];
const CONTRACT_REVISION_RE = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/;
const REQUIRED_DOC_FIELDS = [
  "id",
  "type",
  "path",
  "group",
  "selection",
  "summary",
  "contract_file",
  "template_file",
  "requires",
  "target_depth",
  "write_order",
  "provenance_mode",
  "audit_profile",
];
const CATALOG_VERSION = "2.24.0";
const PRESENTATION_VALUES = {
  code: new Set(["contract-only", "task-focused"]),
  related_docs: new Set(["none", "compact", "traceability"]),
  repository_paths: new Set(["hidden", "actionable-only"]),
};

function loadIndex() {
  if (!fs.existsSync(INDEX_PATH)) throw new Error(`catalog index not found: ${INDEX_PATH}`);
  return JSON.parse(fs.readFileSync(INDEX_PATH, "utf8"));
}

function loadProfile(dimension) {
  const aliases = {
    shape: "shapes",
    platform: "platforms",
    framework: "frameworks",
    concern: "concerns",
    audience: "audiences",
  };
  dimension = aliases[dimension] || dimension;
  if (!PROFILE_DIMENSIONS.includes(dimension)) {
    throw new Error(
      `unknown profile dimension: ${dimension}; expected one of: ${PROFILE_DIMENSIONS.join(", ")}`,
    );
  }
  const target = path.join(PROFILES_DIR, `${dimension}.json`);
  if (!fs.existsSync(target)) throw new Error(`profile file not found: ${target}`);
  return JSON.parse(fs.readFileSync(target, "utf8"));
}

function loadProfiles() {
  const profiles = {};
  for (const dimension of PROFILE_DIMENSIONS) profiles[dimension] = loadProfile(dimension);
  return profiles;
}

function indexRow(docId) {
  const index = loadIndex();
  const row = index.document_types.find((r) => r.id === docId);
  if (!row) throw new Error(`unknown document type id: ${docId}`);
  return row;
}
function resolveCatalogId(value) {
  const index = loadIndex();
  if (index.document_types.some((row) => row.id === value)) return value;
  const matches = index.document_types
    .filter((row) => {
      const detail = loadType(row.id);
      return detail.selection && detail.selection.mode === "dynamic" && detail.type === value;
    })
    .map((row) => row.id);
  if (matches.length === 1) return matches[0];
  throw new Error(`unknown document type id or dynamic type: ${value}`);
}

function loadType(docId) {
  const row = indexRow(docId);
  const record = row.record || `types/${docId}.json`;
  const target = path.join(CATALOG_DIR, record);
  if (!fs.existsSync(target)) throw new Error(`unknown document type id: ${docId}`);
  const detail = JSON.parse(fs.readFileSync(target, "utf8"));
  return detail;
}

function loadAllTypes() {
  return loadIndex().document_types.map((row) => loadType(row.id));
}

// Every catalog document is materialized through the same per-document
// writing procedure, regardless of group.
const ROUTE_WORKFLOW = "workflows/writing.md";
const GROUP_SUMMARIES = {
  root: "Root-level entrypoints: repository README, changelog, and the docs index.",
  product: "Product surface: overview, quickstart, and audience-specific product views.",
  architecture: "System architecture: structure, boundaries, and integration surfaces.",
  flows: "End-to-end flow documentation derived from the flow index.",
  engineering: "Engineering practices: conventions, testing, and tech debt.",
  operations: "Deployment, observability, and operational runbooks.",
  reference: "Reference lookups: APIs, configuration, and glossary.",
  security: "Security posture, permissions, and threat model.",
  contributing: "Contribution guidelines and root-level contributor docs.",
  records: "Architecture decision records.",
  portfolio: "Cross-repository portfolio layer for multi-repo diligence.",
  "agent-context": "Agent-facing context: AGENTS.md and coding-agent views.",
};
// Spoken names for a group, so `--group` and `/docforge-revise <area>` accept
// what a person would actually type. `flow`/`flows` is deliberately absent:
// it is a reserved revise keyword for the full harvest pipeline, which is
// strictly more than revising the `flows` group.
const GROUP_ALIASES = {
  readme: "root", "root-files": "root",
  overview: "product",
  arch: "architecture",
  eng: "engineering",
  ops: "operations", runbooks: "operations",
  ref: "reference", api: "reference",
  sec: "security",
  contrib: "contributing",
  decisions: "records", adr: "records", adrs: "records",
  agents: "agent-context", agent: "agent-context",
  "coding-agents": "agent-context", ai: "agent-context",
};

// Canonical group ids for user-supplied names, aliases accepted. An empty or
// absent list means "every group" -- the filter is subtractive and is applied
// after tier/selector/condition selection, so omitting it reproduces the
// unscoped selection exactly.
function normalizeGroups(values) {
  if (!values || !values.length) return [];
  const known = new Set(loadIndex().groups || []);
  const resolved = [];
  for (const value of values) {
    const canonical = GROUP_ALIASES[value] || value;
    if (!known.has(canonical)) {
      throw new Error(`unknown group: ${value} (choose from ${[...known].sort().join(", ")})`);
    }
    if (!resolved.includes(canonical)) resolved.push(canonical);
  }
  return resolved;
}

// Every catalog group with the audiences that unlock it. A group whose every
// document is audience-gated selects nothing on its own; `audiences` is what
// intake pre-checks and what the empty-selection guard names when a scope
// would produce no documents.
function groups() {
  const index = loadIndex();
  const rows = [];
  for (const group of index.groups || []) {
    const unlocking = [];
    for (const row of index.document_types) {
      const detail = loadType(row.id);
      if (detail.group !== group) continue;
      for (const audience of (detail.selection.selectors || {}).audiences || []) {
        if (!unlocking.includes(audience)) unlocking.push(audience);
      }
    }
    rows.push({
      id: group,
      summary: GROUP_SUMMARIES[group] || "",
      aliases: Object.keys(GROUP_ALIASES).filter((name) => GROUP_ALIASES[name] === group).sort(),
      audiences: unlocking,
    });
  }
  return rows;
}

/** Audiences that unlock any document in `group`; empty when ungated. */
function groupAudiences(group) {
  const canonical = normalizeGroups([group])[0];
  return groups().find((row) => row.id === canonical).audiences;
}

function category(group) {
  const index = loadIndex();
  if (!(index.groups || []).includes(group)) throw new Error(`unknown group: ${group}`);
  const matches = [];
  for (const row of index.document_types) {
    const detail = loadType(row.id);
    if (detail.group !== group) continue;
    const record = row.record || `types/${row.id}.json`;
    matches.push([detail.write_order || 0, detail.id, detail, record]);
  }
  matches.sort((a, b) => (a[0] - b[0]) || a[1].localeCompare(b[1]));
  return {
    category: group,
    summary: GROUP_SUMMARIES[group] || `${group} document definitions`,
    index: ".metadata/catalog/index.json",
    documents: matches.map(([, docId, detail, record]) => ({
      id: docId,
      summary: detail.summary,
      record: `.metadata/catalog/${record}`,
    })),
  };
}

function orderedAudiences(values) {
  const profiles = loadProfiles();
  const canonical = normalizeProfileIds("audiences", values, profiles);
  const order = Object.fromEntries(profiles.audiences.map((item) => [item.id, item.order]));
  return canonical.sort((a, b) => (order[a] - order[b]) || a.localeCompare(b));
}

function resolvePresentation(detail, audiences = []) {
  const index = loadIndex();
  const defaults = index.presentation_defaults;
  const selected = orderedAudiences(audiences);
  const override = detail.presentation || {};
  const selectorAudiences = (((detail.selection || {}).selectors || {}).audiences || []);
  const selectedForDocument = selected.filter((audience) => selectorAudiences.includes(audience));
  let primary;
  let primaryOrigin;
  if (override.primary_audience) {
    primary = override.primary_audience;
    primaryOrigin = "record";
  } else if (selectedForDocument.length) {
    primary = selectedForDocument[0];
    primaryOrigin = "selector";
  } else if (selectorAudiences.length) {
    primary = orderedAudiences(selectorAudiences)[0];
    primaryOrigin = "selector";
  } else {
    primary = defaults.primary_audience_by_group[detail.group] || "engineers";
    primaryOrigin = "group";
  }
  const audienceDefaults = defaults.by_audience[primary];
  const presentation = {
    code: audienceDefaults.code,
    related_docs: audienceDefaults.related_docs,
    repository_paths: audienceDefaults.repository_paths,
    source_evidence: defaults.source_evidence,
  };
  const origins = {
    primary_audience: primaryOrigin,
    code: `audience:${primary}`,
    related_docs: `audience:${primary}`,
    repository_paths: `audience:${primary}`,
    source_evidence: "catalog",
  };
  for (const field of Object.keys(PRESENTATION_VALUES)) {
    if (Object.prototype.hasOwnProperty.call(override, field)) {
      presentation[field] = override[field];
      origins[field] = "record";
    }
  }
  return [primary, presentation, origins];
}

// True when a catalog record is a *core* compact member: selected by tier
// alone, with no profile selector and no evidence condition. Only core members
// count against COMPACT_CORE_CAP, because only they are knowable from the
// catalog — everything else depends on the project's confirmed profiles and
// discovered evidence.
function isCoreMember(detail) {
  const rule = detail.selection || {};
  const selectors = rule.selectors || {};
  const hasSelector = Object.values(selectors).some((values) => (values || []).length > 0);
  return !hasSelector && !rule.condition;
}

// The catalog id behind a `compact_members` entry. A static member is the id
// itself; a folded dynamic instance is `{id, slug, title}`, where `id` is the
// dynamic *type* whose contract and template the section is written from.
function memberTypeId(member) {
  return member && typeof member === "object" ? member.id : member;
}

// The manifest's own folded `compact_members` for docId, or null when no
// manifest is available or the entry has none. Entries are catalog id strings,
// or `{id, slug, title}` objects for folded dynamic instances.
//
// A compact group spanning tiers (e.g. `architecture_compact` at Spine and
// Diligence) declares its *full* member roster in the catalog, but only a
// tier-appropriate subset is ever actually selected and folded for one
// project. The manifest entry — built by foldCompactGroups from the
// tier-filtered selection — already carries the correct subset; prefer it
// over the catalog's full list whenever a manifest is available.
function manifestCompactMembers(repo, docId) {
  if (!repo) return null;
  const manifestPath = path.join(repo, ".docforge", "manifest.json");
  if (!fs.existsSync(manifestPath)) return null;
  let manifest;
  try {
    manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  } catch {
    return null;
  }
  for (const doc of manifest.documents || []) {
    if (doc.id === docId) {
      return Array.isArray(doc.compact_members) && doc.compact_members.length ? doc.compact_members : null;
    }
  }
  return null;
}

// Compose the merged file's content contract at route time: the group's
// short header contract plus each member's existing contract as a named
// section, in `compact_members` order. Member contracts are reused, never
// rewritten. `repo`, when given, narrows a tier-spanning group's full
// catalog roster to what this project's manifest actually folded — see
// manifestCompactMembers.
function composedCompactContract(detail, repo = null) {
  const parts = [];
  const members = [];
  const header = detail.contract_file;
  if (header && fs.existsSync(path.join(SKILL_ROOT, header))) {
    parts.push(fs.readFileSync(path.join(SKILL_ROOT, header), "utf8").trimEnd());
  }
  let order = 0;
  const entries = manifestCompactMembers(repo, detail.id) || detail.compact_members || [];
  const seenMembers = new Set();
  for (const entry of entries) {
    order += 1;
    const memberId = memberTypeId(entry);
    const member = loadType(memberId);
    const memberContract = member.contract_file;
    const row = {
      id: memberId,
      order,
      contract: memberContract,
      instruction: member.instruction_file === undefined ? null : member.instruction_file,
      template: member.template_file,
      requires: member.requires || [],
      target_depth: member.target_depth === undefined ? null : member.target_depth,
      model_depth: member.model_depth || {},
      dominant_form: member.dominant_form === undefined ? null : member.dominant_form,
      illustration_views: member.illustration_views || [],
    };
    if (entry && typeof entry === "object") {
      row.slug = entry.slug === undefined ? null : entry.slug;
      row.title = entry.title === undefined ? null : entry.title;
    }
    members.push(row);
    // Every folded instance of one dynamic type is the same member id, so emit
    // that type's contract once rather than once per section. Distinct static
    // members that happen to share an aliased contract file still each get
    // their own `## <member id>` block.
    if (memberContract && !seenMembers.has(memberId) && fs.existsSync(path.join(SKILL_ROOT, memberContract))) {
      seenMembers.add(memberId);
      const text = fs.readFileSync(path.join(SKILL_ROOT, memberContract), "utf8").trimEnd();
      parts.push(`## ${memberId}\n\n${text}`);
    }
  }
  return [parts.join("\n\n"), members];
}

// Resolve one document's canonical writing card.
function route(value, audiences = [], repo = null) {
  const docId = resolveCatalogId(value);
  const row = indexRow(docId);
  const detail = loadType(docId);
  const record = row.record || `types/${docId}.json`;
  const modelDepth = {};
  for (const model of MODEL_DEPTH_ORDER) {
    if (detail.model_depth && Object.prototype.hasOwnProperty.call(detail.model_depth, model)) {
      modelDepth[model] = detail.model_depth[model];
    }
  }
  const [primaryAudience, presentation, presentationOrigin] = resolvePresentation(detail, audiences);
  const result = {
    id: docId,
    group: detail.group,
    summary: detail.summary,
    definition: `.metadata/catalog/${record}`,
    contract: detail.contract_file,
    instruction: detail.instruction_file === undefined ? null : detail.instruction_file,
    template: detail.template_file,
    workflow: ROUTE_WORKFLOW,
    requires: detail.requires || [],
    target_depth: detail.target_depth,
    audit_profile: detail.audit_profile,
    dominant_form: detail.dominant_form === undefined ? null : detail.dominant_form,
    illustration_views: detail.illustration_views || [],
    contract_revision: detail.contract_revision === undefined ? null : detail.contract_revision,
    model_depth: modelDepth,
    primary_audience: primaryAudience,
    presentation,
    presentation_origin: presentationOrigin,
  };
  if (detail.compact_members && detail.compact_members.length) {
    const [composed, members] = composedCompactContract(detail, repo);
    result.contract = composed;
    result.compact = {
      header_contract: detail.contract_file,
      members,
    };
  }
  return result;
}

// Field order and shape of a pre-2.5 type-detail record. --id/--ids/--tier/
// --legacy must keep emitting exactly this shape; summary/contract_file/
// template_file are 2.5 additions that must not leak into those modes.
const LEGACY_DOC_FIELD_ORDER = [
  "id", "type", "path", "group", "selection", "scaffold_template",
  "instruction_file", "requires", "target_depth", "write_order",
  "provenance_mode", "audit_profile", "dominant_form", "schema_min",
];

function legacyDocumentView(detail) {
  const view = {};
  for (const key of LEGACY_DOC_FIELD_ORDER) {
    if (key === "scaffold_template") {
      const templateFile = detail.template_file;
      if (templateFile) {
        view[key] = templateFile.split("/").pop();
      } else if ("scaffold_template" in detail) {
        view[key] = detail.scaffold_template;
      }
    } else if (key === "instruction_file") {
      const instructionFile = detail.instruction_file;
      view[key] = instructionFile ? instructionFile.split("/").pop() : null;
    } else if (key in detail) {
      view[key] = detail[key];
    }
  }
  return view;
}

function legacyIndexRow(row) {
  return { id: row.id, tier: row.tier, path: row.path };
}

function asLegacyCatalog() {
  const index = loadIndex();
  const tiers = index.tiers;
  const tierList = Array.isArray(tiers)
    ? tiers
    : Object.entries(tiers).map(([id, meta]) => ({ id, order: meta.order }));
  return {
    $schema: "catalog-schema.json",
    version: index.version,
    tiers: tierList,
    profiles: loadProfiles(),
    groups: index.groups || [],
    capabilities: index.capabilities || [],
    documents: loadAllTypes().map(legacyDocumentView),
    cue_hints: index.cue_hints || [],
  };
}

function tierRows(tier) {
  const index = loadIndex();
  const tiers = index.tiers;
  const known = Array.isArray(tiers) ? new Set(tiers.map((t) => t.id)) : new Set(Object.keys(tiers));
  if (!known.has(tier)) throw new Error(`unknown tier: ${tier}`);
  return index.document_types.filter((row) => row.tier === tier).map(legacyIndexRow);
}

function mergedRecord(docId) {
  const index = loadIndex();
  const row = index.document_types.find((r) => r.id === docId);
  if (!row) throw new Error(`unknown document type id: ${docId}`);
  const view = legacyDocumentView(loadType(docId));
  return { ...view, tier: row.tier, index_path: row.path };
}

function normalizeProfileIds(dimension, values, profiles) {
  const aliases = {};
  for (const definition of profiles[dimension]) {
    aliases[definition.id] = definition.id;
    for (const alias of definition.aliases || []) aliases[alias] = definition.id;
  }
  const resolved = [];
  for (const value of values) {
    if (!(value in aliases)) throw new Error(`unknown ${dimension.slice(0, -1)}: ${value}`);
    const canonical = aliases[value];
    if (!resolved.includes(canonical)) resolved.push(canonical);
  }
  return resolved;
}

function applicable(options = {}) {
  const index = loadIndex();
  const profiles = loadProfiles();
  const selected = {
    shapes: normalizeProfileIds("shapes", options.shape || [], profiles),
    platforms: normalizeProfileIds("platforms", options.platform || [], profiles),
    frameworks: normalizeProfileIds("frameworks", options.framework || [], profiles),
    concerns: normalizeProfileIds("concerns", options.concern || [], profiles),
    audiences: normalizeProfileIds("audiences", options.audience || [], profiles),
  };
  const scopedGroups = new Set(normalizeGroups(options.group));
  const tiers = index.tiers;
  const ranks = Array.isArray(tiers)
    ? Object.fromEntries(tiers.map((t) => [t.id, t.order]))
    : Object.fromEntries(Object.entries(tiers).map(([id, meta]) => [id, meta.order]));
  const tier = options.tier || "diligence";
  if (!(tier in ranks)) throw new Error(`unknown tier: ${tier}`);
  const tierRank = ranks[tier];
  const ids = [];
  for (const row of index.document_types) {
    const detail = loadType(row.id);
    const rule = detail.selection;
    if ((rule.mode === "dynamic" || rule.mode === "compact") && !options.includeDynamic) continue;
    if (scopedGroups.size && !scopedGroups.has(detail.group)) continue;
    if (ranks[rule.min_tier] > tierRank) continue;
    const selectors = rule.selectors || {};
    const hasSelectors = Object.values(selectors).some((v) => v && v.length);
    if (hasSelectors) {
      let matched = false;
      for (const [dimension, values] of Object.entries(selectors)) {
        if (dimension === "frameworks") continue;
        const selectedValues = selected[dimension] || [];
        if (values.some((value) => selectedValues.includes(value))) {
          matched = true;
          break;
        }
      }
      if (!matched) continue;
    }
    ids.push(detail.id);
  }
  return ids;
}

function validate() {
  const errors = [];
  let index;
  try {
    index = loadIndex();
  } catch (error) {
    return [error.message];
  }
  if (index.version !== CATALOG_VERSION) {
    errors.push(`catalog version must be ${CATALOG_VERSION}, got ${index.version}`);
  }
  for (const key of ["tiers", "groups", "capabilities", "profiles", "presentation_defaults", "document_types"]) {
    if (!(key in index)) errors.push(`index.json missing ${key}`);
  }
  const tiers = index.tiers || {};
  const tierIds = Array.isArray(tiers) ? new Set(tiers.map((t) => t.id)) : new Set(Object.keys(tiers));

  const profiles = {};
  const profileIds = {};
  for (const dimension of PROFILE_DIMENSIONS) {
    const target = path.join(PROFILES_DIR, `${dimension}.json`);
    if (!fs.existsSync(target)) {
      errors.push(`missing profile file: ${path.basename(target)}`);
      profiles[dimension] = [];
      profileIds[dimension] = new Set();
      continue;
    }
    const definitions = JSON.parse(fs.readFileSync(target, "utf8"));
    profiles[dimension] = definitions;
    const ids = new Set(definitions.map((item) => item.id));
    if (ids.size !== definitions.length) errors.push(`${dimension}: duplicate profile id`);
    profileIds[dimension] = ids;
    const names = {};
    for (const item of definitions) {
      for (const name of [item.id, ...(item.aliases || [])]) {
        if (typeof name !== "string" || !/^[a-z0-9][a-z0-9-]*$/.test(name)) {
          errors.push(`${dimension}: invalid profile name ${name}`);
          continue;
        }
        if (name in names) {
          errors.push(
            `${dimension}: profile name collision ${name} between ${names[name]} and ${item.id}`,
          );
        }
        names[name] = item.id;
      }
    }
  }

  const presentationDefaults = index.presentation_defaults || {};
  const audienceIds = profileIds.audiences || new Set();
  if (presentationDefaults.source_evidence !== "provenance-only") {
    errors.push("presentation_defaults.source_evidence must be provenance-only");
  }
  let groupDefaults = presentationDefaults.primary_audience_by_group;
  if (!groupDefaults || typeof groupDefaults !== "object" || Array.isArray(groupDefaults)) {
    errors.push("presentation_defaults.primary_audience_by_group must be an object");
    groupDefaults = {};
  }
  for (const [group, audience] of Object.entries(groupDefaults)) {
    if (!(index.groups || []).includes(group)) errors.push(`presentation_defaults: unknown group ${group}`);
    if (!audienceIds.has(audience)) errors.push(`presentation_defaults: unknown primary audience ${audience}`);
  }
  let audienceDefaults = presentationDefaults.by_audience;
  if (!audienceDefaults || typeof audienceDefaults !== "object" || Array.isArray(audienceDefaults)) {
    errors.push("presentation_defaults.by_audience must be an object");
    audienceDefaults = {};
  }
  for (const audience of audienceIds) {
    const value = audienceDefaults[audience];
    if (!value || typeof value !== "object" || Array.isArray(value)) {
      errors.push(`presentation_defaults: missing audience defaults for ${audience}`);
      continue;
    }
    validatePresentation(value, `presentation_defaults.by_audience.${audience}`, errors, { requireAll: true });
  }
  for (const audience of Object.keys(audienceDefaults)) {
    if (!audienceIds.has(audience)) errors.push(`presentation_defaults: unknown audience ${audience}`);
  }

  const declaredProfiles = index.profiles || {};
  for (const dimension of PROFILE_DIMENSIONS) {
    const rel = declaredProfiles[dimension];
    if (!rel) {
      errors.push(`index.json profiles.${dimension} is missing`);
    } else if (!fs.existsSync(path.join(CATALOG_DIR, rel))) {
      errors.push(`index.json profiles.${dimension} points to missing file: ${rel}`);
    }
  }

  const indexIds = (index.document_types || []).map((row) => row.id);
  if (new Set(indexIds).size !== indexIds.length) {
    errors.push("index.json has duplicate document type ids");
  }
  const declaredRecords = new Set();
  for (const row of index.document_types || []) {
    const record = row.record;
    if (!record) {
      errors.push(`${row.id}: index.json entry missing record path`);
      continue;
    }
    const recordPath = path.join(CATALOG_DIR, record);
    if (!fs.existsSync(recordPath)) {
      errors.push(`${row.id}: record path does not resolve: ${record}`);
      continue;
    }
    declaredRecords.add(fs.realpathSync(recordPath));
  }
  // Records may live flat in types/ (pre-migration) or under documents/
  // (per-group folders + flat small groups, post-migration); scan both.
  // Generated routers (index.json, README.md) are excluded, not records.
  function walkJsonFiles(dir, out) {
    for (const name of fs.readdirSync(dir)) {
      const full = path.join(dir, name);
      const stat = fs.statSync(full);
      if (stat.isDirectory()) walkJsonFiles(full, out);
      else if (name.endsWith(".json") && name !== "index.json") out.push(full);
    }
  }
  const onDiskRecords = new Set();
  for (const base of [TYPES_DIR, path.join(CATALOG_DIR, "documents")]) {
    if (!fs.existsSync(base)) continue;
    const found = [];
    walkJsonFiles(base, found);
    for (const full of found) onDiskRecords.add(fs.realpathSync(full));
  }
  for (const full of [...onDiskRecords].filter((f) => !declaredRecords.has(f)).sort()) {
    errors.push(`orphan record file not in index: ${path.relative(CATALOG_DIR, full)}`);
  }

  const groups = new Set(index.groups || []);
  const capabilities = new Set(index.capabilities || []);
  const staticIds = new Set();
  const staticPaths = new Set();
  const dynamicTypes = new Set();

  for (const docId of indexIds) {
    let doc;
    try {
      doc = loadType(docId);
    } catch (error) {
      errors.push(error.message);
      continue;
    }
    const missing = REQUIRED_DOC_FIELDS.filter((field) => !(field in doc));
    if (missing.length) {
      errors.push(`${docId}: missing fields: ${missing.join(", ")}`);
      continue;
    }
    if (doc.id !== docId) errors.push(`${docId}: id field mismatch (${doc.id})`);
    const selection = doc.selection || {};
    if (!groups.has(doc.group)) errors.push(`${docId}: unknown group ${doc.group}`);
    if (!tierIds.has(selection.min_tier)) {
      errors.push(`${docId}: unknown tier ${selection.min_tier}`);
    }
    if (!TARGET_DEPTHS.has(doc.target_depth)) {
      errors.push(`${docId}: target_depth must be one of: ${[...TARGET_DEPTHS].sort().join(", ")}`);
    }
    if (doc.model_depth !== undefined) {
      if (!doc.model_depth || typeof doc.model_depth !== "object" || Array.isArray(doc.model_depth) || !Object.keys(doc.model_depth).length) {
        errors.push(`${docId}: model_depth must be a non-empty object`);
      } else {
        for (const [model, rung] of Object.entries(doc.model_depth)) {
          if (!(model in MODEL_DEPTHS)) errors.push(`${docId}: unknown model_depth model ${model}`);
          else if (!MODEL_DEPTHS[model].includes(rung)) errors.push(`${docId}: invalid ${model} model_depth rung ${rung}`);
        }
      }
    }
    if (doc.contract_revision !== undefined && (typeof doc.contract_revision !== "string" || !CONTRACT_REVISION_RE.test(doc.contract_revision))) {
      errors.push(`${docId}: contract_revision must be MAJOR.MINOR.PATCH`);
    }
    if (doc.presentation !== undefined) {
      validatePresentation(doc.presentation, `${docId}: presentation`, errors, { audienceIds });
    }
    if (doc.selection_evidence_required !== undefined && typeof doc.selection_evidence_required !== "boolean") {
      errors.push(`${docId}: selection_evidence_required must be boolean`);
    }
    const selectors = selection.selectors || {};
    if (selectors.frameworks && selectors.frameworks.length) {
      errors.push(`${docId}: frameworks may tailor evidence but must not select documents`);
    }
    for (const [dimension, values] of Object.entries(selectors)) {
      if (!(dimension in profileIds)) {
        errors.push(`${docId}: unknown selector dimension ${dimension}`);
        continue;
      }
      for (const value of values) {
        if (!profileIds[dimension].has(value)) {
          errors.push(`${docId}: unknown ${dimension} selector ${value}`);
        }
      }
    }
    for (const requirement of doc.requires || []) {
      if (!capabilities.has(requirement)) {
        errors.push(`${docId}: unknown requirement ${requirement}`);
      }
    }
    if (!Number.isInteger(doc.write_order)) {
      errors.push(`${docId}: write_order must be an integer`);
    }
    if (doc.nav_order !== undefined && doc.nav_order !== null && !Number.isInteger(doc.nav_order)) {
      errors.push(`${docId}: nav_order must be an integer`);
    }
    if (!ALLOWED_DOMINANT_FORMS.has(doc.dominant_form)) {
      errors.push(`${docId}: invalid dominant_form ${JSON.stringify(doc.dominant_form)}`);
    }
    errors.push(...validateIllustrationViews(doc, docId));
    const summary = doc.summary;
    if (!summary || typeof summary !== "string" || summary.length > 160) {
      errors.push(`${docId}: summary must be a non-empty string of at most 160 characters`);
    }
    const contract = doc.contract_file;
    if (!contract || !fs.existsSync(path.join(SKILL_ROOT, contract))) {
      errors.push(`${docId}: missing contract ${contract}`);
    }
    const template = doc.template_file;
    if (!template || !fs.existsSync(path.join(SKILL_ROOT, template))) {
      errors.push(`${docId}: missing template ${template}`);
    }
    if ("scaffold_template" in doc) {
      errors.push(`${docId}: obsolete scaffold_template field remains; use template_file`);
    }
    if (doc.instruction_file) {
      if (!fs.existsSync(path.join(SKILL_ROOT, doc.instruction_file))) {
        errors.push(`${docId}: missing instruction ${doc.instruction_file}`);
      }
    }
    if (selection.mode === "static") {
      if (staticIds.has(doc.id)) errors.push(`duplicate static id: ${doc.id}`);
      if (staticPaths.has(doc.path)) errors.push(`duplicate static path: ${doc.path}`);
      staticIds.add(doc.id);
      staticPaths.add(doc.path);
    } else if (selection.mode === "dynamic") {
      if (dynamicTypes.has(doc.type)) errors.push(`duplicate dynamic type: ${doc.type}`);
      dynamicTypes.add(doc.type);
      if (indexIds.includes(doc.type) && doc.type !== docId) errors.push(`${docId}: dynamic type collides with catalog id ${doc.type}`);
    } else if (selection.mode === "compact") {
      if (!doc.compact_members || !doc.compact_members.length) errors.push(`${docId}: compact documents must declare compact_members`);
      if (doc.compact_target && doc.compact_target !== doc.path) errors.push(`${docId}: compact_target must match path`);
      if (staticIds.has(doc.id)) errors.push(`duplicate static id: ${doc.id}`);
      if (staticPaths.has(doc.path)) errors.push(`duplicate static path: ${doc.path}`);
      staticIds.add(doc.id);
      staticPaths.add(doc.path);
    } else {
      errors.push(`${docId}: selection.mode must be static or dynamic`);
    }
  }
  const compactIds = new Set(indexIds.filter((docId) => (loadType(docId).selection || {}).mode === "compact"));
  for (const docId of indexIds) {
    const doc = loadType(docId);
    const group = doc.compact_group;
    if (group !== undefined && !compactIds.has(group)) {
      errors.push(`${docId}: compact_group references missing compact document ${group}`);
    }
    for (const memberId of doc.compact_members || []) {
      if (!indexIds.includes(memberId)) {
        errors.push(`${docId}: compact_members references unknown document ${memberId}`);
      } else if (loadType(memberId).compact_group !== docId) {
        errors.push(`${docId}: member ${memberId} does not declare compact_group ${docId}`);
      }
      if ((doc.selection || {}).mode !== "compact") {
        errors.push(`${docId}: compact_members belongs on a compact document`);
      }
    }
    const core = (doc.compact_members || []).filter(
      (memberId) => indexIds.includes(memberId) && isCoreMember(loadType(memberId)),
    );
    if (core.length > COMPACT_CORE_CAP) {
      errors.push(
        `${docId}: ${core.length} core compact_members exceeds the `
        + `${COMPACT_CORE_CAP}-member depth brake (document-composition.md)`,
      );
    }
  }

  const infra = (profiles.shapes || []).find((item) => item.id === "infrastructure-platform");
  if (!infra) {
    errors.push("shapes: infrastructure-platform missing");
  } else {
    const patterns = new Set((infra.signals || []).map((s) => s.pattern));
    for (const required of ["ansible.cfg", "**/kustomization.yaml", "**/playbook*.yml"]) {
      if (!patterns.has(required)) {
        errors.push(`infrastructure-platform missing signal pattern ${required}`);
      }
    }
    const aliases = new Set(infra.aliases || []);
    for (const alias of ["deployment-config", "iac"]) {
      if (!aliases.has(alias)) {
        errors.push(`infrastructure-platform missing alias ${alias}`);
      }
    }
  }
  return errors;
}

/**
 * Every declared view names a real form, a section, and its own question.
 *
 * The question is the load-bearing field: a view that cannot say which reader
 * question it answers, that no other view here answers, is decoration.
 */
function validateIllustrationViews(doc, docId) {
  const views = doc.illustration_views;
  if (views === undefined || views === null) return [];
  if (!Array.isArray(views) || !views.length) {
    return [`${docId}: illustration_views must be a non-empty array`];
  }
  const errors = [];
  const seen = new Set();
  views.forEach((view, index) => {
    const where = `${docId}: illustration_views[${index}]`;
    if (typeof view !== "object" || view === null || Array.isArray(view)) {
      errors.push(`${where} must be an object`);
      return;
    }
    if (!ALLOWED_VIEW_FORMS.has(view.form)) {
      errors.push(`${where} invalid form ${JSON.stringify(view.form)}`);
    }
    for (const field of ["section", "question"]) {
      if (!view[field] || typeof view[field] !== "string") {
        errors.push(`${where} ${field} must be a non-empty string`);
      }
    }
    if (view.depth !== undefined && !VIEW_DEPTHS.has(view.depth)) {
      errors.push(`${where} invalid depth ${JSON.stringify(view.depth)}`);
    }
    if ("required" in view && typeof view.required !== "boolean") {
      errors.push(`${where} required must be boolean`);
    }
    const key = `${view.form}${view.section}`;
    if (seen.has(key)) {
      errors.push(`${where} duplicates form ${JSON.stringify(view.form)} in section ${JSON.stringify(view.section)}`);
    }
    seen.add(key);
  });
  const declared = doc.dominant_form;
  const forms = new Set(views.filter((view) => view && typeof view === "object").map((view) => view.form));
  if (ALLOWED_VIEW_FORMS.has(declared) && !forms.has(declared)) {
    errors.push(`${docId}: dominant_form ${JSON.stringify(declared)} is not among illustration_views forms`);
  }
  return errors;
}

function validatePresentation(value, label, errors, options = {}) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    errors.push(`${label} must be an object`);
    return;
  }
  const allowed = new Set(["primary_audience", ...Object.keys(PRESENTATION_VALUES)]);
  const unknown = Object.keys(value).filter((field) => !allowed.has(field)).sort();
  if (unknown.length) errors.push(`${label}: unknown fields: ${unknown.join(", ")}`);
  if (options.requireAll) {
    const missing = Object.keys(PRESENTATION_VALUES).filter((field) => !(field in value)).sort();
    if (missing.length) errors.push(`${label}: missing fields: ${missing.join(", ")}`);
  }
  if ("primary_audience" in value && options.audienceIds && !options.audienceIds.has(value.primary_audience)) {
    errors.push(`${label}: unknown primary audience ${value.primary_audience}`);
  }
  for (const [field, allowedValues] of Object.entries(PRESENTATION_VALUES)) {
    if (field in value && !allowedValues.has(value[field])) {
      errors.push(`${label}: invalid ${field} ${value[field]}`);
    }
  }
}

function parseArgs(argv) {
  const args = {
    shape: [],
    platform: [],
    framework: [],
    concern: [],
    audience: [],
    group: [],
    applicableTier: "diligence",
    includeDynamic: false,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = () => {
      i += 1;
      return argv[i];
    };
    if (arg === "--tier") args.tier = next();
    else if (arg === "--id") args.docId = next();
    else if (arg === "--ids") args.ids = next();
    else if (arg === "--profile") args.profile = next();
    else if (arg === "--applicable") args.applicable = true;
    else if (arg === "--shape") args.shape.push(next());
    else if (arg === "--platform") args.platform.push(next());
    else if (arg === "--framework") args.framework.push(next());
    else if (arg === "--concern") args.concern.push(next());
    else if (arg === "--audience") args.audience.push(next());
    else if (arg === "--group") args.group.push(next());
    else if (arg === "--groups") args.groups = true;
    else if (arg === "--applicable-tier") args.applicableTier = next();
    else if (arg === "--include-dynamic") args.includeDynamic = true;
    else if (arg === "--legacy") args.legacy = true;
    else if (arg === "--validate") args.validate = true;
    else if (arg === "--category") args.category = next();
    else if (arg === "--route") args.routeId = next();
    else if (arg === "--repo") args.repo = next();
    else throw new Error(`unknown flag: ${arg}`);
  }
  return args;
}

function main(argv = process.argv.slice(2)) {
  let args;
  try {
    args = parseArgs(argv);
  } catch (error) {
    return fail(error.message, 2);
  }
  const modes = [
    args.tier,
    args.docId,
    args.ids,
    args.profile,
    args.applicable,
    args.validate,
    args.legacy,
    args.category,
    args.routeId,
    args.groups,
  ].filter(Boolean).length;
  if (modes !== 1) {
    return fail(
      "specify exactly one of --tier, --id, --ids, --profile, --applicable, --legacy, --validate, --category, --route, --groups",
      2,
    );
  }
  try {
    if (args.validate) {
      const errors = validate();
      if (errors.length) {
        for (const error of errors) process.stderr.write(`error: ${error}\n`);
        process.stderr.write(`${errors.length} validation error(s)\n`);
        return 1;
      }
      process.stdout.write("catalog ok\n");
      return 0;
    }
    if (args.legacy) {
      process.stdout.write(dumpJson(asLegacyCatalog()));
      return 0;
    }
    if (args.tier) {
      process.stdout.write(dumpJson(tierRows(args.tier)));
      return 0;
    }
    if (args.docId) {
      process.stdout.write(dumpJson(mergedRecord(args.docId)));
      return 0;
    }
    if (args.ids) {
      const ids = args.ids.split(",").map((part) => part.trim()).filter(Boolean);
      process.stdout.write(dumpJson(ids.map((docId) => mergedRecord(docId))));
      return 0;
    }
    if (args.profile) {
      process.stdout.write(dumpJson(loadProfile(args.profile)));
      return 0;
    }
    if (args.applicable) {
      process.stdout.write(
        dumpJson(
          applicable({
            shape: args.shape,
            platform: args.platform,
            framework: args.framework,
            concern: args.concern,
            audience: args.audience,
            tier: args.applicableTier,
            group: args.group,
            includeDynamic: args.includeDynamic,
          }),
        ),
      );
      return 0;
    }
    if (args.groups) {
      process.stdout.write(dumpJson(groups()));
      return 0;
    }
    if (args.category) {
      process.stdout.write(dumpJson(category(args.category)));
      return 0;
    }
    if (args.routeId) {
      process.stdout.write(dumpJson(route(args.routeId, args.audience, args.repo || null)));
      return 0;
    }
  } catch (error) {
    return fail(error.message, 2);
  }
  return 2;
}

module.exports = {
  loadIndex,
  loadProfile,
  loadProfiles,
  loadType,
  loadAllTypes,
  asLegacyCatalog,
  tierRows,
  mergedRecord,
  applicable,
  category,
  groups,
  groupAudiences,
  normalizeGroups,
  route,
  resolvePresentation,
  validate,
  main,
  CATALOG_VERSION,
  COMPACT_CORE_CAP,
  COMPACT_SECTION_CAP,
  COMPACT_DYNAMIC_CAP,
  isCoreMember,
  memberTypeId,
  PRESENTATION_VALUES,
  GROUP_SUMMARIES,
  ALLOWED_DOMINANT_FORMS,
};

if (require.main === module) {
  process.exitCode = main();
}
