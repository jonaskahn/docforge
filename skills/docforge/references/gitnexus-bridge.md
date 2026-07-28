# GitNexus bridge — building `.ua/*.json` from a GitNexus index

Second source for docforge's Precheck. Use only when both are true:

- `.ua/knowledge-graph.json` / `.ua/domain-graph.json` are **missing** (understand-anything graphs always take priority when present — see `references/graph-sources.md`).
- A GitNexus index exists for the repo — `python scripts/graph_source_gitnexus.py detect --repo <path>` reports READY, or `check_preconditions.py`'s MISSING output shows "GitNexus index detected".

**Ask the user for permission before running this**, same rule as the existing `/understand` path (`SKILL.md` Precheck). If they decline, stop and wait.

## Step 0 — install and index, if no GitNexus index exists yet

If `python scripts/graph_source_gitnexus.py detect --repo <path>` reports MISSING (no `.gitnexus/meta.json` anywhere up to the git root), GitNexus has never indexed this repo. From the repo root:

```
npx gitnexus analyze
npx gitnexus setup
```

`analyze` builds the index (`.gitnexus/`); `setup` is one-time and connects the current editor/agent (auto-detects Claude Code, Cursor, Codex, …) so the `cypher` and other MCP tools referenced below become callable. Re-run `detect` to confirm READY before continuing to Step 1.

## Why this is agent-mediated, not a script

GitNexus's graph lives in an opaque embedded database (`.gitnexus/lbug`) reachable only through its MCP tools (`cypher`, resources) — no file a standalone script can parse, and no MCP client available outside an agent turn. So the acting agent runs the queries below via the `cypher` MCP tool, saves each raw result to a scratch JSON file, then calls a deterministic script to do the transform and write. This mirrors how understand-anything itself splits a structural pass from an agent-driven pass.

## Step 1 — freshness check

Read `gitnexus://repo/{name}/context`. If it warns the index is stale, run `npx gitnexus analyze` first (ask permission — this can consume tokens on a large first run, same caveat as `/understand`).

## Step 2 — read the schema before querying

Read `gitnexus://repo/{name}/schema`. The three queries below are the reference form — if a property name (e.g. a step-ordering field on `STEP_IN_PROCESS`) differs from what's shown here, adjust the **left-hand side** of that one property access to match the real schema. **Never change the right-hand side (`AS <alias>`) of any `RETURN` clause below** — `graph_source_gitnexus.py`/`.js`'s `build` command depends on these exact column names and will refuse a dump that's missing one.

## Step 3 — run the three fixed queries via the `cypher` MCP tool

**Nodes** → save as `nodes.json`:
```cypher
MATCH (n)
WHERE n:File OR n:Function OR n:Class OR n:Interface OR n:Method
RETURN n.filePath + '#' + n.name AS id, n.name AS name, n.filePath AS path, labels(n)[0] AS type
```

**Edges** → save as `edges.json`:
```cypher
MATCH (a)-[r:CodeRelation]->(b)
RETURN a.filePath + '#' + a.name AS source, b.filePath + '#' + b.name AS target, r.type AS type
```

**Process steps** → save as `processes.json`:
```cypher
MATCH (p:Process)-[r:CodeRelation {type: 'STEP_IN_PROCESS'}]->(s)
RETURN p.name AS processName, r.stepIndex AS stepIndex, s.filePath + '#' + s.name AS symbolId, s.name AS symbolName, s.filePath AS path
ORDER BY p.name, r.stepIndex
```

Node/edge identity is built from `filePath + '#' + name` rather than an engine-specific internal id function, so the composite stays stable across engines and is human-readable in the output JSON. Each MCP `cypher` result may arrive either as a plain JSON array of row objects, or as a `{"columns": [...], "rows": [[...], ...]}` envelope — the build script accepts both.

`Community` clusters are not folded into `domain-graph.json` in this first pass — there is no reliable cluster-to-process linkage without a fourth query, and inventing a `domains` grouping without solid data would violate docforge's "never invent" rule. `domain-graph.json` from this bridge is flows-only (one flow per `Process`, steps ordered by the step index).

## Step 4 — build

```
python scripts/graph_source_gitnexus.py build --repo <path> \
    --nodes nodes.json --edges edges.json --processes processes.json
```
(or the `.js` twin with `node`). This writes `.ua/knowledge-graph.json` and `.ua/domain-graph.json` and prints node/edge/flow counts.

## Step 5 — confirm

```
python scripts/check_preconditions.py --repo <path> --need domain
```
Both graphs should now report READY. Proceed to docforge Step 1.

## Adding a future third source

Same shape every time: a `graph_source_<name>.py`/`.js` pair exporting `detect(repo)` (and `build(...)` if the source needs agent-mediated construction like this one), built on `graph_common.py`/`.js`'s `find`/`display`/`write_graph`. `check_preconditions.py`/`.js` only needs one new import and one new branch in its MISSING path — nothing else in docforge changes, because every downstream document only ever reads `.ua/knowledge-graph.json` / `.ua/domain-graph.json`, never the source that built them.
