#!/usr/bin/env node
"use strict";
/* GitNexus offline reader — inventory the ladybug DB (.gitnexus/lbug) directly.
 *
 * USE THIS ONLY for the GitNexus source, and only when the gitnexus MCP is not
 * wired into this session. When the MCP is available it is the better read
 * path (richer, no dependency); this script exists for offline/scripted reads.
 *
 * It opens .gitnexus/lbug read-only via @ladybugdb/core and prints the same
 * kind of inventory read_graph.js gives for a JSON graph — module map,
 * functional areas, flows, most-imported targets — to seed a documentation
 * set. Output is an inventory to verify, not finished prose.
 *
 * @ladybugdb/core is an optional native dependency and the single documented
 * exception to docforge's "no install" rule. If it is not installed this script
 * prints how to get it (or to use the MCP instead) and exits non-zero — it
 * never crashes with a raw stack trace.
 *
 * `--interchange` is the one non-inventory mode: it writes the deterministic
 * `.docforge/tmp/gitnexus-flows.json` that `flow_index harvest` discovers, with
 * each process carrying its ordered STEP_IN_PROCESS steps. Producing that file
 * used to be an unautomated manual step, so it usually never happened and a
 * ready GitNexus index went unread.
 *
 * Usage:
 *   node graph_source_gitnexus_reader.js --repo <path> --summary
 *   node graph_source_gitnexus_reader.js --repo <path> --modules --flows
 *   node graph_source_gitnexus_reader.js --db <path/to/lbug> --layers
 *   node graph_source_gitnexus_reader.js --repo <path> --interchange
 */

const fs = require("fs");
const path = require("path");
const { findGraphFile } = require("./graph_storage.js");
const { ensureGitignoredDir } = require("../../common/js/_util.js");

const HINT = [
  "Could not read the ladybug DB offline. Either:",
  "  - read it via the gitnexus MCP (cypher/query/context) — the preferred path; or",
  "  - install the optional native reader:  npm install @ladybugdb/core",
  "See references/graph/graph-source-gitnexus.md.",
];

function abortLines(lines) {
  for (const line of lines) console.error(line);
  process.exit(1);
}

function parseArgs(argv) {
  const args = { limit: 40, sections: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--repo") args.repo = argv[++i];
    else if (a === "--db") args.db = argv[++i];
    else if (a === "--limit") args.limit = parseInt(argv[++i], 10);
    else if (a === "--summary") args.summary = true;
    else if (a === "--interchange") args.interchange = true;
    else if (["--modules", "--layers", "--flows", "--deps"].includes(a)) args.sections.push(a.slice(2));
  }
  return args;
}

function loadLbug() {
  try {
    return require("@ladybugdb/core");
  } catch {
    return null;
  }
}

/** Build the deterministic `{routes, processes, communities}` interchange
 * flow_index harvests, with each process carrying its ordered steps. */
function buildInterchange(query, rowsOr) {
  const routes = rowsOr(query(
    "MATCH (r:Route) RETURN r.id AS id, r.path AS path, r.filePath AS filePath, r.name AS symbol"
  )).map((row) => ({ id: row.id, path: row.path, filePath: row.filePath, symbol: row.symbol }));

  const communities = rowsOr(query(
    "MATCH (c:Community) RETURN c.id AS id, c.heuristicLabel AS heuristicLabel"
  )).map((row) => ({ id: row.id, heuristicLabel: row.heuristicLabel }));

  const processes = new Map();
  for (const row of rowsOr(query(
    "MATCH (s)-[r:CodeRelation {type:'STEP_IN_PROCESS'}]->(p:Process) " +
      "RETURN p.id AS processId, p.heuristicLabel AS name, p.entryPointId AS entry, " +
      "p.terminalId AS terminal, p.processType AS type, s.id AS stepId, " +
      "s.filePath AS file, s.name AS symbol, r.order AS ord ORDER BY p.id, r.order"
  ))) {
    const pid = String(row.processId);
    if (!processes.has(pid)) {
      processes.set(pid, {
        id: pid,
        heuristicLabel: row.name,
        entryPointId: row.entry,
        terminalId: row.terminal,
        processType: row.type,
        communities: [],
        steps: [],
      });
    }
    const record = processes.get(pid);
    record.steps.push({
      order: Number.isInteger(row.ord) ? row.ord : record.steps.length + 1,
      nodeId: row.stepId,
      filePath: row.file,
      symbol: row.symbol,
    });
  }

  for (const row of rowsOr(query(
    "MATCH (p:Process)-[:CodeRelation {type:'MEMBER_OF'}]->(c:Community) " +
      "RETURN p.id AS processId, c.id AS communityId"
  ))) {
    const record = processes.get(String(row.processId));
    if (record && row.communityId !== null && row.communityId !== undefined) {
      record.communities.push(String(row.communityId));
    }
  }

  for (const record of processes.values()) record.stepCount = record.steps.length;

  return {
    routes,
    processes: [...processes.values()].sort((a, b) => String(a.id).localeCompare(String(b.id))),
    communities,
  };
}

function main() {
  const args = parseArgs(process.argv.slice(2));

  let dbPath = args.db;
  if (!dbPath) {
    if (!args.repo) abortLines(["--repo <path> or --db <path/to/lbug> is required"]);
    dbPath = findGraphFile(args.repo, [".gitnexus/lbug"]);
    if (!dbPath) {
      abortLines([
        `No .gitnexus/lbug found from ${args.repo} up to the git root.`,
        "Build a GitNexus index first: npx gitnexus analyze (see references/graph/graph-source-gitnexus.md).",
      ]);
    }
  }

  const lbug = loadLbug();
  if (!lbug) abortLines(HINT);

  let conn;
  try {
    const db = new lbug.Database(dbPath, 0, true, /* readOnly */ true);
    conn = new lbug.Connection(db);
  } catch (error) {
    abortLines([`Failed to open ${dbPath}: ${error.message}`, "", ...HINT]);
  }

  const query = (cypher) => {
    try {
      return conn.querySync(cypher).getAllSync();
    } catch (error) {
      return { __error: error.message };
    }
  };
  const rowsOr = (result) => (Array.isArray(result) ? result : []);

  // The one non-inventory mode: hand flow_index the deterministic interchange,
  // with each process carrying its ordered STEP_IN_PROCESS steps. The
  // interchange used to carry only entry, terminal, and a step count, so a
  // twelve-step native process reached the flow index as `steps: 12`.
  if (args.interchange) {
    if (!args.repo) abortLines(["--interchange needs --repo <path> to know where to write"]);
    const interchange = buildInterchange(query, rowsOr);
    if (!interchange.processes.length && !interchange.routes.length) {
      abortLines([
        `No Route or Process nodes in ${dbPath} — nothing to hand the flow index.`,
        "Re-index with `npx gitnexus analyze` (see references/graph/graph-source-gitnexus.md).",
      ]);
    }
    const dir = path.join(path.resolve(args.repo), ".docforge", "tmp");
    ensureGitignoredDir(dir);
    const target = path.join(dir, "gitnexus-flows.json");
    fs.writeFileSync(target, `${JSON.stringify(interchange, null, 2)}\n`, "utf8");
    const steps = interchange.processes.reduce((sum, item) => sum + item.steps.length, 0);
    console.log(`Wrote ${target} — ${interchange.routes.length} route(s), ${interchange.processes.length} process(es), ${steps} ordered step(s).`);
    console.log("Next: flow_index.{py,js} harvest --repo <repo> discovers it automatically.");
    return 0;
  }

  const wantAll = args.summary || args.sections.length === 0;
  const want = (name) => wantAll || args.sections.includes(name);

  console.log(`# ${dbPath}  (ladybug DB)\n`);

  // SHAPE — counts per node label docforge cares about.
  if (args.summary || wantAll) {
    console.log("SHAPE");
    const total = rowsOr(query("MATCH (n) RETURN count(n) AS c"))[0];
    console.log(`  nodes total    : ${total ? total.c : "?"}`);
    for (const label of ["File", "Function", "Method", "Class", "Interface", "Community", "Process", "Route", "Tool"]) {
      const row = rowsOr(query(`MATCH (n:${label}) RETURN count(n) AS c`))[0];
      if (row && row.c) console.log(`  ${label.padEnd(14)}: ${row.c}`);
    }
    console.log();
  }

  // MODULES — File nodes grouped by directory.
  if (want("modules")) {
    const files = rowsOr(query("MATCH (f:File) RETURN f.filePath AS path"));
    const counts = new Map();
    for (const { path } of files) {
      if (!path) continue;
      const parts = String(path).split("/");
      const dir = parts.slice(0, -1).join("/") || ".";
      counts.set(dir, (counts.get(dir) || 0) + 1);
    }
    console.log(`MODULES (${counts.size})`);
    const sorted = [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, args.limit);
    for (const [dir, n] of sorted) console.log(`  ${dir}/  [${n} files]`);
    if (counts.size > args.limit) console.log(`  ... ${counts.size - args.limit} more (raise --limit)`);
    console.log("\n  Seeds docs/architecture/high-level.md. Confirm each module's purpose");
    console.log("  with the gitnexus MCP `context`/`query` before describing it.\n");
  }

  // LAYERS — GitNexus Community clusters (functional areas) by membership.
  if (want("layers")) {
    const areas = rowsOr(
      query(
        "MATCH (f)-[:CodeRelation {type:'MEMBER_OF'}]->(c:Community) " +
          "RETURN c.heuristicLabel AS area, count(f) AS n ORDER BY n DESC"
      )
    );
    if (!areas.length) {
      console.log("FUNCTIONAL AREAS\n  No Community membership found.\n");
    } else {
      console.log(`FUNCTIONAL AREAS (${areas.length}) — GitNexus Community clusters`);
      for (const { area, n } of areas.slice(0, args.limit)) {
        console.log(`  ${String(area || "(unnamed)").padEnd(28)} ${n} members`);
      }
      console.log();
    }
  }

  // FLOWS — Process nodes with their step counts.
  if (want("flows")) {
    const flows = rowsOr(
      query(
        "MATCH (s)-[r:CodeRelation {type:'STEP_IN_PROCESS'}]->(p:Process) " +
          "RETURN p.heuristicLabel AS name, count(r) AS steps ORDER BY steps DESC"
      )
    );
    if (!flows.length) {
      console.log("FLOWS\n  No Process/STEP_IN_PROCESS data found.\n");
    } else {
      console.log(`FLOWS (${flows.length}) — GitNexus Process execution traces`);
      for (const { name, steps } of flows.slice(0, args.limit)) {
        console.log(`  ${String(name || "(unnamed)")}  [${steps} steps]`);
      }
      if (flows.length > args.limit) console.log(`  ... ${flows.length - args.limit} more (raise --limit)`);
      console.log("\n  These are code-derived Entry → Terminal candidates, not one document each.");
      console.log("  Group them by entryPointId in the flow index, then document only ranked main");
      console.log("  entries whose behavior is confirmed (references/graph/flow-derivation.md).\n");
    }
  }

  // DEPS — most-imported targets (best-effort; versions/licences come from the manifest).
  if (want("deps")) {
    const imports = rowsOr(
      query(
        "MATCH ()-[r:CodeRelation {type:'IMPORTS'}]->(b) " +
          "RETURN b.name AS name, count(r) AS n ORDER BY n DESC"
      )
    );
    if (!imports.length) {
      console.log("IMPORTS\n  No IMPORTS edges found.\n");
    } else {
      console.log(`MOST-IMPORTED TARGETS (${imports.length})`);
      for (const { name, n } of imports.slice(0, args.limit)) {
        console.log(`  ${String(name || "(unnamed)").padEnd(40)} ${n} import(s)`);
      }
      console.log("\n  Candidates for docs/architecture/dependencies.md. Versions and licences");
      console.log("  come from the manifest/lockfile, not the graph.\n");
    }
  }

  return 0;
}

process.exit(main());
