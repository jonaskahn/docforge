# Graph source: GitNexus (ladybug DB)

**When to read this:** the active (or chosen) graph source is GitNexus — i.e. the repo has `.gitnexus/lbug` (and `.gitnexus/meta.json`), or you are about to build one. This is the source-specific companion to the provider-neutral dispatch in `references/graph-sources.md`. For the understand-anything (JSON) source, that file's dispatch table plus the `/understand-*` bindings cover it; this file has no bearing on it.

## What GitNexus stores

GitNexus ([github.com/abhigyanpatwari/GitNexus](https://github.com/abhigyanpatwari/GitNexus)) indexes a repo into a **ladybug property-graph database** at `.gitnexus/lbug` — a single binary file — with a sidecar `.gitnexus/meta.json` recording the index stats (`files`, `nodes`, `edges`, `communities`, `processes`) and the commit it was built at (`lastCommit`).

Unlike understand-anything's JSON, this is a **database, not a file docforge parses**. But it is *not* opaque: it satisfies **both** docforge capabilities the moment it exists —

- **code graph** — `File`/`Function`/`Class`/`Method`/`Interface` nodes and `CodeRelation` edges (`CALLS`, `IMPORTS`, `CONTAINS`, `EXTENDS`, `HAS_METHOD`, …);
- **flow graph** — native `Process` nodes (execution traces) with ordered `STEP_IN_PROCESS` edges, and `Community` clusters (functional areas) via `MEMBER_OF`.

So when GitNexus is the source, docforge **never derives** a flow graph — the processes are already there. There is no copy-to-JSON step: docforge reads the DB directly.

## Detect

```
python scripts/graph_source_gitnexus.py detect --repo <path>
```

`READY` prints the lbug path and the index stats (and flags `STALE vs HEAD` when `meta.lastCommit` differs from the current commit). `MISSING` prints how to build one. `precheck_graph.py` calls the same detection through the registry.

## Read it — three ways, in preference order

1. **The gitnexus MCP (preferred).** When the GitNexus plugin is loaded, its tools query the DB live — no dependency, richest results. This is the read path the capability dispatch in `references/graph-sources.md` points at:
   - `query({query, goal})` — ranked execution flows (processes) with their symbols and file locations;
   - `context({name})` — 360° view of one symbol (callers, callees, the flows it's in) — the L2/L3 deep-dive engine, in place of `/understand-explain`;
   - `cypher({query})` — arbitrary structural queries (read `gitnexus://repo/{name}/schema` first);
   - resources: `gitnexus://repo/{name}/context` (overview + staleness), `.../processes`, `.../process/{name}` (step-by-step trace), `.../clusters` (Community functional areas).
2. **The offline reader (no MCP).** `scripts/graph_source_gitnexus_reader.{py,js}` opens `.gitnexus/lbug` read-only and prints a module / functional-area / flow / most-imported inventory — the DB-source counterpart to `read_graph.py`. The Node twin uses the published `@ladybugdb/core` native module (`npm install @ladybugdb/core`); the Python twin needs a ladybug Python binding. Either is an **optional** dependency — the single documented exception to docforge's "no install" rule. If it is not installed the reader prints this and exits non-zero; fall back to the MCP.
   ```
   node scripts/graph_source_gitnexus_reader.js --repo <path> --summary
   python scripts/graph_source_gitnexus_reader.py --repo <path> --flows
   ```
3. Neither of the above reads structure docforge cannot otherwise get — they are the two ways to *read* an existing DB, not substitutes for each other's data.

**Reading Cypher directly** (via the `cypher` tool or the offline reader), the load-bearing shapes:
- flows + ordered steps — `MATCH (s)-[r:CodeRelation {type:'STEP_IN_PROCESS'}]->(p:Process) RETURN p.heuristicLabel, s.name, r.step ORDER BY p.heuristicLabel, r.step`
- functional areas — `MATCH (f)-[:CodeRelation {type:'MEMBER_OF'}]->(c:Community) RETURN c.heuristicLabel, count(f)`
- module map — `MATCH (f:File) RETURN f.filePath`
- **Caveat:** Process labels are code-derived (`Entry → Terminal`), not business phrases. Keep them faithful by default; rename to business language only where a node summary supports it, and say so (`references/domain-derivation.md`).

## Build or refresh

Ask the user before running either — a first index spends tokens/time on a large repo (`SKILL.md` Step 0's permission model; under `--auto-accept`, notice then run).

```
npx gitnexus analyze     # builds/refreshes .gitnexus/lbug
npx gitnexus setup        # one-time: connects the MCP tools to this agent
```

`analyze` builds or incrementally refreshes the index; run it when `detect` reports `STALE`. `setup` is one-time and makes the `cypher`/`query`/`context` tools callable. Re-run `detect` to confirm `READY` before proceeding to docforge Step 1.
