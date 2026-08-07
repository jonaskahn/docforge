#!/usr/bin/env node
"use strict";
/* Restricted YAML frontmatter codec for Docforge provenance 2.0.
 * Emits a deterministic YAML subset and parses that subset plus plain
 * unquoted scalars. Standard library / Node built-ins only.
 */

const crypto = require("crypto");

const SCHEMA_VERSION = "2.1";
const SUPPORTED_SCHEMA_VERSIONS = new Set(["2.0", "2.1"]);
const LEGACY_SCHEMA = "1.0";
const GENERATOR_NAME = "docforge";
const GENERATOR_VERSION = "2.8.0";
const PROVENANCE_FIELDS = new Set([
  "schema", "doc_id", "path", "generated_at", "generator", "tier",
  "target_depth", "graph", "sections",
]);
const OPTIONAL_FIELDS = new Set(["git_commit", "content_hash", "review"]);
const SOURCE_ROLES = new Set(["code", "config", "manifest", "doc", "test", "history"]);
const FLOW_VALUES = new Set(["native", "derived", "none"]);
const BLOB = /^[0-9a-f]{40}$/;
const SCAFFOLD_TOKEN = /^<[A-Z][A-Z0-9_]{2,}>$/;
const CONTENT_HASH = /^sha256:[0-9a-f]{64}$/;

const PROVENANCE_KEY_ORDER = [
  "schema", "doc_id", "path", "generated_at", "generator",
  "tier", "target_depth", "git_commit", "content_hash", "review",
  "graph", "sections",
];
const GENERATOR_KEY_ORDER = ["name", "version"];
const GRAPH_KEY_ORDER = ["provider", "flow"];
const SECTION_KEY_ORDER = ["id", "sources", "unresolved"];
const SOURCE_KEY_ORDER = [
  "path", "git_blob", "git_blob_normalized", "evidence_range", "range_blob", "role",
];
const EVIDENCE_RANGE_KEY_ORDER = ["start", "end"];
const REVIEW_KEY_ORDER = ["mode", "verdict", "report"];

class YamlCodecError extends Error {
  constructor(message) {
    super(message);
    this.name = "YamlCodecError";
  }
}

function quoteScalar(value) {
  return JSON.stringify(String(value));
}

function contentHash(body) {
  return `sha256:${crypto.createHash("sha256").update(body, "utf8").digest("hex")}`;
}

function scaffoldProvenance(docId, pathValue, options = {}) {
  return {
    schema: SCHEMA_VERSION,
    doc_id: docId,
    path: pathValue,
    generated_at: options.generated_at || "<GENERATED_AT>",
    generator: { name: GENERATOR_NAME, version: GENERATOR_VERSION },
    tier: options.tier || "<TIER>",
    target_depth: options.target_depth || "<TARGET_DEPTH>",
    graph: {
      provider: options.provider || "<GRAPH_PROVIDER>",
      flow: options.flow || "<FLOW_CAPABILITY>",
    },
    sections: [],
  };
}

function inferSourceRole(pathValue) {
  const lower = String(pathValue).replace(/\\/g, "/").toLowerCase();
  const name = lower.split("/").pop() || "";
  if (["/test/", "/tests/", "/__tests__/", "_test.", ".test.", ".spec."].some((m) => lower.includes(m))) {
    return "test";
  }
  if (
    [
      "package.json", "pyproject.toml", "cargo.toml", "go.mod", "gemfile",
      "pom.xml", "composer.json", "build.gradle", "build.gradle.kts",
    ].includes(name)
    || name.endsWith(".csproj")
    || name.endsWith(".gemspec")
  ) {
    return "manifest";
  }
  if (
    [".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf", ".env", ".properties"].some((ext) => name.endsWith(ext))
    || `/${lower}/`.includes("/config/")
    || name.startsWith(".")
  ) {
    return "config";
  }
  if ([".md", ".rst", ".txt", ".adoc"].some((ext) => name.endsWith(ext)) || lower.startsWith("docs/")) {
    return "doc";
  }
  return "code";
}

function inferProviderFromSnapshot(snapshot) {
  const lower = String(snapshot).replace(/\\/g, "/").toLowerCase();
  if (`/${lower}`.includes("/.ua/") || lower.startsWith(".ua/") || lower.includes("understand-anything")) {
    return "understand-anything";
  }
  if (lower.includes("gitnexus")) return "gitnexus";
  if (lower.includes("codegraph")) return "codegraph";
  return null;
}

function normalizeSections(sections) {
  if (!Array.isArray(sections)) return [];
  const normalized = [];
  for (const section of sections) {
    if (!section || typeof section !== "object" || Array.isArray(section)) continue;
    const sources = [];
    if (Array.isArray(section.sources)) {
      for (const source of section.sources) {
        if (!source || typeof source !== "object" || Array.isArray(source)) continue;
        const pathValue = source.path;
        const blob = source.git_blob;
        if (typeof pathValue !== "string" || !pathValue || typeof blob !== "string" || !blob) continue;
        const entry = { path: pathValue, git_blob: blob };
        const normalizedBlob = source.git_blob_normalized;
        if (typeof normalizedBlob === "string" && BLOB.test(normalizedBlob)) {
          entry.git_blob_normalized = normalizedBlob;
        }
        const evidenceRange = source.evidence_range;
        const rangeBlob = source.range_blob;
        if (
          evidenceRange && typeof evidenceRange === "object" && !Array.isArray(evidenceRange)
          && typeof evidenceRange.start === "string" && /^[1-9][0-9]*$/.test(evidenceRange.start)
          && typeof evidenceRange.end === "string" && /^[1-9][0-9]*$/.test(evidenceRange.end)
          && Number(evidenceRange.end) >= Number(evidenceRange.start)
          && typeof rangeBlob === "string" && BLOB.test(rangeBlob)
        ) {
          entry.evidence_range = { start: evidenceRange.start, end: evidenceRange.end };
          entry.range_blob = rangeBlob;
        }
        const role = SOURCE_ROLES.has(source.role) ? source.role : inferSourceRole(pathValue);
        entry.role = role;
        sources.push(entry);
      }
    }
    normalized.push({
      id: String(section.id || "main"),
      sources,
      unresolved: Array.isArray(section.unresolved) ? section.unresolved.slice() : [],
    });
  }
  return normalized;
}

function migrateV1ToV2(provenance, body = "", defaults = {}) {
  if (!provenance || typeof provenance !== "object" || Array.isArray(provenance)) {
    throw new YamlCodecError("provenance must be an object");
  }
  const opts = defaults && typeof defaults === "object" && !Array.isArray(defaults) ? defaults : {};
  if (SUPPORTED_SCHEMA_VERSIONS.has(provenance.schema) && provenance.generator) {
    const migrated = { ...provenance };
    if (Array.isArray(migrated.sections)) migrated.sections = normalizeSections(migrated.sections);
    return migrated;
  }
  if (
    provenance.schema !== LEGACY_SCHEMA
    && !("tool_version" in provenance)
    && provenance.schema != null
  ) {
    throw new YamlCodecError(`unsupported provenance schema: ${provenance.schema}`);
  }
  let toolVersion = provenance.tool_version || GENERATOR_VERSION;
  if (typeof toolVersion !== "string" || !toolVersion) toolVersion = GENERATOR_VERSION;
  const pathValue = provenance.path || provenance.doc || opts.path || "";
  const docId = provenance.doc_id || opts.doc_id || "";
  let graph;
  if (provenance.graph && typeof provenance.graph === "object" && !Array.isArray(provenance.graph)) {
    graph = {
      provider: String(provenance.graph.provider || opts.provider || "<GRAPH_PROVIDER>"),
      flow: String(provenance.graph.flow || opts.flow || "<FLOW_CAPABILITY>"),
    };
  } else {
    let inferred = null;
    if (typeof provenance.graph_snapshot === "string" && provenance.graph_snapshot) {
      inferred = inferProviderFromSnapshot(provenance.graph_snapshot);
    }
    graph = {
      provider: String(inferred || opts.provider || "<GRAPH_PROVIDER>"),
      flow: String(opts.flow || "<FLOW_CAPABILITY>"),
    };
    if (inferred === "understand-anything" && graph.flow === "<FLOW_CAPABILITY>") {
      graph.flow = "native";
    }
  }
  const migrated = {
    schema: SCHEMA_VERSION,
    doc_id: String(docId),
    path: String(pathValue),
    generated_at: String(provenance.generated_at || opts.generated_at || ""),
    generator: { name: GENERATOR_NAME, version: toolVersion },
    tier: String(provenance.tier || opts.tier || ""),
    target_depth: String(provenance.target_depth || opts.target_depth || ""),
    graph,
    sections: normalizeSections(provenance.sections),
  };
  if (typeof provenance.git_commit === "string") migrated.git_commit = provenance.git_commit;
  if (typeof provenance.content_hash === "string") migrated.content_hash = provenance.content_hash;
  else if (body) migrated.content_hash = contentHash(body);
  if (provenance.review && typeof provenance.review === "object") migrated.review = provenance.review;
  return migrated;
}

function emitMapping(lines, mapping, keyOrder, indent) {
  const prefix = " ".repeat(indent);
  for (const key of keyOrder) {
    if (!(key in mapping)) continue;
    const value = mapping[key];
    if (value && typeof value === "object" && !Array.isArray(value)) {
      lines.push(`${prefix}${key}:`);
      if (key === "generator") emitMapping(lines, value, GENERATOR_KEY_ORDER, indent + 2);
      else if (key === "graph") emitMapping(lines, value, GRAPH_KEY_ORDER, indent + 2);
      else if (key === "review") emitMapping(lines, value, REVIEW_KEY_ORDER, indent + 2);
      else emitMapping(lines, value, Object.keys(value), indent + 2);
    } else if (Array.isArray(value)) {
      if (!value.length) {
        lines.push(`${prefix}${key}: []`);
        continue;
      }
      lines.push(`${prefix}${key}:`);
      for (const item of value) {
        if (item && typeof item === "object" && !Array.isArray(item)) {
          let first = true;
          const itemOrder = ("sources" in item)
            ? SECTION_KEY_ORDER
            : ("git_blob" in item)
              ? SOURCE_KEY_ORDER
              : Object.keys(item);
          for (const itemKey of itemOrder) {
            if (!(itemKey in item)) continue;
            const itemValue = item[itemKey];
            const bullet = first ? "- " : "  ";
            first = false;
            if (Array.isArray(itemValue)) {
              if (!itemValue.length) {
                lines.push(`${prefix}  ${bullet}${itemKey}: []`);
              } else {
                lines.push(`${prefix}  ${bullet}${itemKey}:`);
                for (const nested of itemValue) {
                  if (nested && typeof nested === "object" && !Array.isArray(nested)) {
                    let nestedFirst = true;
                    for (const nestedKey of SOURCE_KEY_ORDER) {
                      if (!(nestedKey in nested)) continue;
                      const nestedBullet = nestedFirst ? "- " : "  ";
                      nestedFirst = false;
                      const nestedValue = nested[nestedKey];
                      if (nestedValue && typeof nestedValue === "object" && !Array.isArray(nestedValue)) {
                        lines.push(`${prefix}      ${nestedBullet}${nestedKey}:`);
                        const subOrder = nestedKey === "evidence_range"
                          ? EVIDENCE_RANGE_KEY_ORDER
                          : Object.keys(nestedValue);
                        for (const subKey of subOrder) {
                          if (!(subKey in nestedValue)) continue;
                          lines.push(`${prefix}          ${subKey}: ${quoteScalar(nestedValue[subKey])}`);
                        }
                      } else {
                        lines.push(
                          `${prefix}      ${nestedBullet}${nestedKey}: ${quoteScalar(nestedValue)}`,
                        );
                      }
                    }
                  } else {
                    lines.push(`${prefix}      - ${quoteScalar(nested)}`);
                  }
                }
              }
            } else {
              lines.push(`${prefix}  ${bullet}${itemKey}: ${quoteScalar(itemValue)}`);
            }
          }
        } else {
          lines.push(`${prefix}  - ${quoteScalar(item)}`);
        }
      }
    } else {
      lines.push(`${prefix}${key}: ${quoteScalar(value)}`);
    }
  }
}

function emitYaml(provenance) {
  if (!provenance || typeof provenance !== "object" || Array.isArray(provenance)) {
    throw new YamlCodecError("provenance must be an object");
  }
  const lines = ["---", "docforge_provenance:"];
  emitMapping(lines, provenance, PROVENANCE_KEY_ORDER, 2);
  lines.push("---", "");
  return lines.join("\n");
}

function emitDocumentFrontmatter(docId, title, provenance, description = null) {
  if (!docId || !title) throw new YamlCodecError("document id and title must be non-empty");
  const lines = ["---", `id: ${quoteScalar(docId)}`, `title: ${quoteScalar(title)}`];
  if (description !== null && description !== undefined) {
    lines.push(`description: ${quoteScalar(description)}`);
  }
  lines.push("docforge_provenance:");
  emitMapping(lines, provenance, PROVENANCE_KEY_ORDER, 2);
  lines.push("---", "");
  return lines.join("\n");
}

function wrapDocument(provenance, body) {
  let next = body;
  if (next.startsWith("\n")) next = next.replace(/^\n+/, "");
  if (next && !next.endsWith("\n")) next += "\n";
  return emitYaml(provenance) + next;
}

function rejectUnsupported(raw) {
  for (const line of raw.split(/\r?\n/)) {
    const stripped = line.trim();
    if (!stripped || stripped.startsWith("#")) continue;
    if (stripped === "---" || stripped.startsWith("...")) {
      throw new YamlCodecError("unsupported yaml construct: multi-document marker");
    }
    if (stripped.includes("&") || stripped.includes("*")) {
      throw new YamlCodecError("unsupported yaml construct: anchor or alias");
    }
    if (
      stripped.endsWith("|") || stripped.endsWith(">")
      || stripped.endsWith("|-") || stripped.endsWith(">-")
    ) {
      throw new YamlCodecError("unsupported yaml construct: block scalar");
    }
    if (/:\s*[\[{].+[\]}]/.test(stripped)) {
      throw new YamlCodecError("unsupported yaml construct: non-empty flow collection");
    }
  }
}

function parseScalar(raw) {
  const value = raw.trim();
  if (value === "[]") return [];
  if (value === "{}") return {};
  if (value === "null" || value === "~") return null;
  if (value === "true") return true;
  if (value === "false") return false;
  if (value.length >= 2 && value[0] === value[value.length - 1] && (value[0] === '"' || value[0] === "'")) {
    if (value[0] === '"') return JSON.parse(value);
    return value.slice(1, -1);
  }
  return value;
}

function indentOf(line) {
  return line.length - line.trimStart().length;
}

function parseYamlMapping(raw) {
  rejectUnsupported(raw);
  const lines = raw.split(/\r?\n/).filter((line) => line.trim() && !line.trim().startsWith("#"));
  const root = {};
  const stack = [[-1, root]];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    const indent = indentOf(line);
    const content = line.trim();
    while (stack.length > 1 && indent <= stack[stack.length - 1][0]) stack.pop();
    const parent = stack[stack.length - 1][1];
    if (content.startsWith("- ")) {
      if (!Array.isArray(parent)) throw new YamlCodecError("list item without list parent");
      const itemContent = content.slice(2);
      if (itemContent.includes(": ") || itemContent.endsWith(":")) {
        const item = {};
        parent.push(item);
        stack.push([indent, item]);
        if (itemContent.endsWith(":")) {
          const key = itemContent.slice(0, -1).trim();
          if (i + 1 < lines.length && indentOf(lines[i + 1]) > indent) {
            const nxt = lines[i + 1].trim();
            if (nxt.startsWith("- ")) {
              item[key] = [];
              stack.push([indent + 2, item[key]]);
            } else if (nxt === "[]") {
              i += 1;
              item[key] = [];
            } else {
              item[key] = {};
              stack.push([indent + 2, item[key]]);
            }
          } else {
            item[key] = {};
          }
        } else {
          const idx = itemContent.indexOf(":");
          const key = itemContent.slice(0, idx).trim();
          item[key] = parseScalar(itemContent.slice(idx + 1));
        }
      } else {
        parent.push(parseScalar(itemContent));
      }
      i += 1;
      continue;
    }
    if (content.includes(": ") || content.endsWith(":")) {
      if (!parent || typeof parent !== "object" || Array.isArray(parent)) {
        throw new YamlCodecError("mapping entry without mapping parent");
      }
      if (content.endsWith(":")) {
        const key = content.slice(0, -1).trim();
        if (i + 1 < lines.length && indentOf(lines[i + 1]) > indent) {
          const nxt = lines[i + 1].trim();
          if (nxt === "[]") {
            i += 1;
            parent[key] = [];
          } else if (nxt.startsWith("- ")) {
            parent[key] = [];
            stack.push([indent, parent[key]]);
          } else {
            parent[key] = {};
            stack.push([indent, parent[key]]);
          }
        } else {
          parent[key] = {};
        }
      } else {
        const idx = content.indexOf(":");
        const key = content.slice(0, idx).trim();
        parent[key] = parseScalar(content.slice(idx + 1));
      }
      i += 1;
      continue;
    }
    throw new YamlCodecError(`unsupported yaml construct: ${content}`);
  }
  return root;
}

function splitFrontmatter(text) {
  if (!text.startsWith("---\n")) return { raw: null, body: text, end: 0 };
  const end = text.indexOf("\n---\n", 4);
  if (end < 0) return { raw: null, body: text, end: 0 };
  return {
    raw: text.slice(4, end),
    body: text.slice(end + 5),
    end: end + 5,
  };
}

function parseFrontmatter(text) {
  const { raw, end } = splitFrontmatter(text);
  if (raw == null) return { state: "missing", provenance: null, end: 0 };
  const stripped = raw.trimStart();
  if (stripped.startsWith("{")) {
    let data;
    try {
      data = JSON.parse(raw);
    } catch {
      return { state: "unparseable", provenance: null, end };
    }
    const provenance = data && typeof data === "object" ? data.docforge_provenance : null;
    if (!provenance || typeof provenance !== "object" || Array.isArray(provenance)) {
      return { state: "missing", provenance: null, end };
    }
    if (!("schema" in provenance)) return { state: "legacy", provenance, end };
    return { state: "obsolete", provenance, end };
  }
  let data;
  try {
    data = parseYamlMapping(raw);
  } catch {
    return { state: "unparseable", provenance: null, end };
  }
  const provenance = data && typeof data === "object" ? data.docforge_provenance : null;
  if (!provenance || typeof provenance !== "object" || Array.isArray(provenance)) {
    return { state: "missing", provenance: null, end };
  }
  if (!("schema" in provenance)) return { state: "legacy", provenance, end };
  if (!SUPPORTED_SCHEMA_VERSIONS.has(provenance.schema) || "tool_version" in provenance) {
    return { state: "obsolete", provenance, end };
  }
  return { state: "ok", provenance, end };
}

function rewriteFrontmatter(text, provenance) {
  const { raw, body } = splitFrontmatter(text);
  if (raw == null) return wrapDocument(provenance, text);
  return emitYaml(provenance) + body;
}

module.exports = {
  SCHEMA_VERSION,
  SUPPORTED_SCHEMA_VERSIONS,
  LEGACY_SCHEMA,
  GENERATOR_NAME,
  GENERATOR_VERSION,
  PROVENANCE_FIELDS,
  OPTIONAL_FIELDS,
  SOURCE_ROLES,
  FLOW_VALUES,
  BLOB,
  SCAFFOLD_TOKEN,
  CONTENT_HASH,
  YamlCodecError,
  quoteScalar,
  contentHash,
  scaffoldProvenance,
  inferSourceRole,
  inferProviderFromSnapshot,
  normalizeSections,
  migrateV1ToV2,
  emitYaml,
  emitDocumentFrontmatter,
  wrapDocument,
  parseYamlMapping,
  splitFrontmatter,
  parseFrontmatter,
  rewriteFrontmatter,
};
