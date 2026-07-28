#!/usr/bin/env node
"use strict";
/* Read a JSON code (knowledge) graph and extract the inventories that seed a
 * documentation set.
 *
 * This reads a JSON graph on disk — understand-anything's
 * .ua/knowledge-graph.json (or the legacy .understand-anything/ path). A
 * DB-backed source (GitNexus's ladybug .gitnexus/lbug) is not a JSON file and
 * is not read here: query it via the gitnexus MCP, or offline with
 * scripts/graph_source_gitnexus_reader.js — see references/graph-sources.md.
 *
 * The on-disk schema is not assumed. The script probes the JSON, reports the
 * shape it found, and extracts only fields it can actually see. Where a field
 * is absent it says so rather than substituting a guess — the whole point of
 * reading the graph is to stop inventing.
 *
 * Typical use:
 *   node read_graph.js --summary
 *   node read_graph.js --graph <path/to/knowledge-graph.json> --probe
 *   node read_graph.js --modules --deps
 *
 * If --graph is omitted, the graph is located at the repository root by
 * searching the known JSON store locations (`.ua/`, legacy
 * `.understand-anything/`) up every parent to the git root, so it works when
 * invoked from a subdirectory.
 *
 * Node.js built-ins only. Output is an inventory to verify, not finished prose.
 */

const fs = require("fs");
const path = require("path");

const DEFAULT_RELPATHS = [
  path.join(".ua", "knowledge-graph.json"),
  path.join(".understand-anything", "knowledge-graph.json"),
];

function parents(dir) {
  const out = [];
  let cur = dir;
  for (;;) {
    const up = path.dirname(cur);
    if (up === cur) break;
    out.push(up);
    cur = up;
  }
  return out;
}

function findDefaultGraph(start) {
  const base = path.resolve(start || process.cwd());
  for (const cur of [base, ...parents(base)]) {
    for (const rel of DEFAULT_RELPATHS) {
      const candidate = path.join(cur, rel);
      if (isFile(candidate)) return candidate;
    }
    if (fs.existsSync(path.join(cur, ".git"))) break;
  }
  return null;
}

function isFile(p) {
  try {
    return fs.statSync(p).isFile();
  } catch {
    return false;
  }
}

// Candidate key names, in preference order. The pipeline's schema may evolve
// or differ by version, so every lookup is a search rather than an assumption.
const NODE_KEYS = ["nodes", "files", "entities", "items"];
const EDGE_KEYS = ["edges", "links", "relationships", "relations"];
const ID_KEYS = ["id", "nodeId", "key", "name"];
const PATH_KEYS = ["path", "filePath", "file", "relativePath", "location"];
const LABEL_KEYS = ["name", "label", "title", "symbol"];
const KIND_KEYS = ["type", "kind", "nodeType", "category"];
const LAYER_KEYS = ["layer", "architecturalLayer", "group", "tier"];
const SUMMARY_KEYS = ["summary", "description", "explanation", "doc"];
const SRC_KEYS = ["source", "from", "src", "start"];
const DST_KEYS = ["target", "to", "dst", "end"];
const EDGEKIND_KEYS = ["type", "kind", "relation", "label"];
const EXTERNAL_HINTS = ["external", "isExternal", "thirdParty", "builtin"];

function firstPresent(d, keys) {
  if (!d || typeof d !== "object") return null;
  for (const k of keys) {
    if (k in d && d[k] !== null && d[k] !== "" && d[k] !== undefined) return d[k];
  }
  return null;
}

function isPlainObject(v) {
  return v !== null && typeof v === "object" && !Array.isArray(v);
}

// Locate a list of dicts under one of `keys`, searching nested objects.
function locateCollection(doc, keys, depth = 3) {
  if (!isPlainObject(doc) || depth < 0) return ["", []];
  for (const k of keys) {
    const v = doc[k];
    if (Array.isArray(v) && (v.length === 0 || isPlainObject(v[0]))) return [k, v];
    if (isPlainObject(v)) {
      const vals = Object.values(v);
      if (vals.length && isPlainObject(vals[0])) return [k, vals];
    }
  }
  for (const [k, v] of Object.entries(doc)) {
    if (isPlainObject(v)) {
      const [subPath, found] = locateCollection(v, keys, depth - 1);
      if (found.length) return [`${k}.${subPath}`, found];
    }
  }
  return ["", []];
}

function loadGraph(p) {
  let raw;
  try {
    raw = fs.readFileSync(p, "utf8");
  } catch {
    console.error(
      `No graph at ${p}. Build a code graph from any configured source ` +
        "first — see references/graph-sources.md."
    );
    process.exit(1);
  }
  let data;
  try {
    data = JSON.parse(raw);
  } catch (e) {
    console.error(`${p} is not valid JSON (${e.message}). The graph may be mid-write.`);
    process.exit(1);
  }
  if (!isPlainObject(data)) {
    console.error(`Unexpected top-level type in ${p}: ${Array.isArray(data) ? "array" : typeof data}`);
    process.exit(1);
  }
  return data;
}

// ---------------------------------------------------------------------------

function describeShape(doc, nkey, nodes, ekey, edges) {
  console.log("SHAPE");
  console.log(`  top-level keys : ${Object.keys(doc).sort().slice(0, 20).join(", ")}`);
  console.log(`  nodes          : ${nkey || "(not found)"} — ${nodes.length}`);
  console.log(`  edges          : ${ekey || "(not found)"} — ${edges.length}`);
  if (nodes.length) {
    const sample = nodes[0];
    console.log(`  node fields    : ${Object.keys(sample).sort().slice(0, 24).join(", ")}`);
    const rows = [
      ["id", ID_KEYS],
      ["path", PATH_KEYS],
      ["kind", KIND_KEYS],
      ["layer", LAYER_KEYS],
      ["summary", SUMMARY_KEYS],
    ];
    for (const [label, keys] of rows) {
      const v = firstPresent(sample, keys);
      const shown = v !== null ? String(v).slice(0, 70) : "(absent in sample)";
      console.log(`    ${label.padEnd(8)}-> ${shown}`);
    }
  }
  if (edges.length) {
    console.log(`  edge fields    : ${Object.keys(edges[0]).sort().slice(0, 24).join(", ")}`);
  }
  if (!nodes.length) {
    console.log(
      "\n  No node collection recognized. Inspect the file directly and\n" +
        "  adapt, rather than reporting facts this script did not read."
    );
  }
}

function counterTop(counter, n) {
  return Object.entries(counter)
    .sort((a, b) => b[1] - a[1])
    .slice(0, n);
}

function modules(nodes, limit) {
  const counts = new Map(); // mod -> {kind: count}
  const summaries = new Map();
  for (const n of nodes) {
    if (EXTERNAL_HINTS.some((h) => n[h] === true)) continue;
    const p = firstPresent(n, PATH_KEYS) || firstPresent(n, LABEL_KEYS);
    if (!p) continue;
    const parts = String(p).replace(/\\/g, "/").split("/");
    const mod = parts.slice(0, -1).join("/") || ".";
    if (!counts.has(mod)) counts.set(mod, {});
    const kind = firstPresent(n, KIND_KEYS) || "unknown";
    counts.get(mod)[kind] = (counts.get(mod)[kind] || 0) + 1;
    const s = firstPresent(n, SUMMARY_KEYS);
    if (s && !summaries.has(mod)) summaries.set(mod, String(s).split(/\s+/).join(" ").slice(0, 150));
  }

  console.log(`MODULES (${counts.size})`);
  const sortedMods = [...counts.entries()].sort(
    (a, b) => Object.values(b[1]).reduce((x, y) => x + y, 0) - Object.values(a[1]).reduce((x, y) => x + y, 0)
  );
  for (const [mod, kinds] of sortedMods.slice(0, limit)) {
    const total = Object.values(kinds).reduce((x, y) => x + y, 0);
    const detail = counterTop(kinds, 4)
      .map(([k, v]) => `${k}:${v}`)
      .join(", ");
    console.log(`  ${mod}/  [${total}] ${detail}`);
    if (summaries.has(mod)) console.log(`      ${summaries.get(mod)}`);
  }
  if (counts.size > limit) console.log(`  ... ${counts.size - limit} more (raise --limit)`);
  console.log(
    "\n  Seeds the code map in docs/architecture/high-level.md. Confirm each\n" +
      "  module's purpose with a subsystem deep-dive (references/graph-sources.md,\n" +
      "  'Deep-dive a symbol') before describing it."
  );
}

function layers(nodes) {
  const c = {};
  for (const n of nodes) {
    const lv = firstPresent(n, LAYER_KEYS);
    if (lv) c[String(lv)] = (c[String(lv)] || 0) + 1;
  }
  const entries = counterTop(c, Infinity);
  if (!entries.length) {
    console.log(
      "LAYERS\n  No layer field found on nodes. Derive grouping from the\n" +
        "  module inventory instead, or rebuild the code graph " +
        "(references/graph-sources.md)."
    );
    return;
  }
  console.log(`LAYERS (${entries.length})`);
  for (const [layer, n] of entries) {
    console.log(`  ${String(layer).padEnd(24)} ${n}`);
  }
}

function deps(nodes, edges, limit) {
  const known = new Set();
  for (const n of nodes) {
    for (const k of [...ID_KEYS, ...PATH_KEYS]) {
      const v = isPlainObject(n) ? n[k] : null;
      if (v) known.add(String(v));
    }
  }

  const external = {};
  for (const n of nodes) {
    if (EXTERNAL_HINTS.some((h) => n[h] === true)) {
      const name = firstPresent(n, LABEL_KEYS) || firstPresent(n, PATH_KEYS);
      if (name) external[String(name)] = (external[String(name)] || 0) + 1;
    }
  }

  for (const e of edges) {
    const kind = String(firstPresent(e, EDGEKIND_KEYS) || "").toLowerCase();
    if (!kind.includes("import") && !kind.includes("depend") && !kind.includes("require")) continue;
    const tgt = firstPresent(e, DST_KEYS);
    if (tgt === null) continue;
    const t = String(tgt);
    if (known.has(t) || /^(\.|\/|src|app|lib|pkg)/.test(t)) continue;
    const key = t.startsWith("@") ? t.split("/").slice(0, 2).join("/") : t.split("/")[0];
    external[key] = (external[key] || 0) + 1;
  }

  const entries = counterTop(external, limit);
  if (!Object.keys(external).length) {
    console.log(
      "EXTERNAL REFERENCES\n  None distinguishable from this graph. Take the\n" +
        "  inventory from the manifest and lockfile instead."
    );
    return;
  }
  console.log(`EXTERNAL REFERENCES (${Object.keys(external).length})`);
  for (const [name, n] of entries) {
    console.log(`  ${name.padEnd(40)} ${n} reference(s)`);
  }
  console.log(
    "\n  Candidates for docs/architecture/dependencies.md. Versions and\n" +
      "  licences come from the manifest; criticality and failure behaviour\n" +
      "  come from the team or a targeted graph query (references/graph-sources.md)."
  );
}

function boundaries(nodes, edges) {
  const roots = new Set(["src", "app", "lib", "pkg", "internal", "packages", "source"]);

  function top(v) {
    if (!v) return "";
    let parts = String(v)
      .replace(/\\/g, "/")
      .split("/")
      .filter(Boolean);
    if (parts.length && roots.has(parts[0]) && parts.length > 1) parts = parts.slice(1);
    return parts.length ? parts[0] : "";
  }

  const idx = {};
  for (const n of nodes) {
    const nid = firstPresent(n, ID_KEYS);
    if (nid !== null) idx[String(nid)] = top(firstPresent(n, PATH_KEYS) || firstPresent(n, LABEL_KEYS));
  }

  const pairs = new Map(); // "a b" -> count
  for (const e of edges) {
    const s = firstPresent(e, SRC_KEYS);
    const t = firstPresent(e, DST_KEYS);
    if (!(String(s) in idx) || !(String(t) in idx)) continue;
    const a = idx[String(s)];
    const b = idx[String(t)];
    if (a && b && a !== b) {
      const key = `${a} ${b}`;
      pairs.set(key, (pairs.get(key) || 0) + 1);
    }
  }

  if (!pairs.size) {
    console.log("BOUNDARIES\n  No cross-module edges resolved. Check --probe output.");
    return;
  }
  const mods = new Set();
  for (const key of pairs.keys()) {
    const [a, b] = key.split(" ");
    mods.add(a);
    mods.add(b);
  }
  console.log(`CROSS-MODULE EDGES (${pairs.size} directed pairs over ${mods.size} modules)`);
  const sortedPairs = [...pairs.entries()].sort((a, b) => b[1] - a[1]).slice(0, 30);
  for (const [key, n] of sortedPairs) {
    const [a, b] = key.split(" ");
    console.log(`  ${a} -> ${b}   ${n}`);
  }
  const modsSorted = [...mods].sort();
  const absent = [];
  for (const a of modsSorted) {
    for (const b of modsSorted) {
      if (a === b) continue;
      if (!pairs.has(`${a} ${b}`) && pairs.has(`${b} ${a}`)) absent.push([a, b]);
    }
  }
  if (absent.length) {
    console.log("\n  One-directional (candidate invariants — confirm intent before asserting):");
    for (const [a, b] of absent.slice(0, 15)) {
      console.log(`    nothing in ${a} reaches ${b}`);
    }
  }
}

function parseArgs(argv) {
  const args = { limit: 40 };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--graph") args.graph = argv[++i];
    else if (a === "--probe") args.probe = true;
    else if (a === "--summary") args.summary = true;
    else if (a === "--modules") args.modules = true;
    else if (a === "--layers") args.layers = true;
    else if (a === "--deps") args.deps = true;
    else if (a === "--boundaries") args.boundaries = true;
    else if (a === "--limit") args.limit = parseInt(argv[++i], 10);
  }
  return args;
}

function main() {
  const args = parseArgs(process.argv.slice(2));

  let graphPath = args.graph;
  if (!graphPath) {
    graphPath = findDefaultGraph();
    if (!graphPath) {
      console.error(
        "No JSON code graph found in $PROJECT_ROOT/.ua/ or " +
          "$PROJECT_ROOT/.understand-anything/ (searched the current directory " +
          "and every parent up to the repo root). If the active source is " +
          "GitNexus, its graph is a ladybug DB — read it via the gitnexus MCP " +
          "or scripts/graph_source_gitnexus_reader.js (references/graph-sources.md), " +
          "not this script. Otherwise build a JSON code graph, or pass " +
          "--graph <path> explicitly."
      );
      return 1;
    }
  }

  const doc = loadGraph(graphPath);
  const [nkey, nodes] = locateCollection(doc, NODE_KEYS);
  const [ekey, edges] = locateCollection(doc, EDGE_KEYS);

  const sizeKb = fs.statSync(graphPath).size / 1024;
  console.log(`# ${graphPath}  (${sizeKb.toFixed(0)} KB)\n`);

  const wantAll =
    args.summary || !(args.probe || args.modules || args.layers || args.deps || args.boundaries);
  if (args.probe || wantAll) {
    describeShape(doc, nkey, nodes, ekey, edges);
    console.log();
  }
  if (!nodes.length) return 1;
  if (args.modules || wantAll) {
    modules(nodes, args.limit);
    console.log();
  }
  if (args.layers || wantAll) {
    layers(nodes);
    console.log();
  }
  if (args.deps || wantAll) {
    deps(nodes, edges, args.limit);
    console.log();
  }
  if (args.boundaries) {
    boundaries(nodes, edges);
    console.log();
  }
  return 0;
}

process.exit(main());
