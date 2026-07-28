# Graph source: CodeGraph (SQLite index, MCP-only)

**When to read this:** the active (or chosen) graph source is CodeGraph — i.e.
the repo has `.codegraph/codegraph.db`, or you are about to build one. This is
the source-specific companion to the provider-neutral dispatch in
`references/graph-sources.md`. For understand-anything (JSON) see that file's
dispatch table; for GitNexus (ladybug DB) see `references/graph-source-gitnexus.md`.
This file has no bearing on either of those.

## What CodeGraph stores

CodeGraph ([github.com/colbymchenry/codegraph](https://github.com/colbymchenry/codegraph))
indexes a repo into a **SQLite database** at `.codegraph/codegraph.db` — every
symbol, call edge, import edge, and file in the repo, plus FTS5 full-text
search over symbol names.

It satisfies **only** the code-graph capability. There is no business-flow or
process concept in CodeGraph's schema — no equivalent of GitNexus's `Process`
nodes or understand-anything's domain graph — so it never satisfies
`flow_graph`. When CodeGraph is the only ready source, flow/product/BA-PO
docs still fall back to docforge's own derivation from the code graph
(`references/domain-derivation.md`).

CodeGraph's own file watcher debounces and re-syncs the index on every save,
and reconciles it again at MCP-connect time, so a present `.codegraph/codegraph.db`
is current by construction — there is no staleness check to run here, unlike
GitNexus's `meta.lastCommit` comparison against HEAD.

## Detect

```
python scripts/graph_source_codegraph.py detect --repo <path>
```

`READY` prints the db path. `MISSING` prints how to build one.
`precheck_graph.py` calls the same detection through the registry. **A
`READY` result here only means the db file exists on disk** — see the
two-gate note below before treating it as readable.

## Read it — one way, and a hard gate before you can

CodeGraph is **MCP-only**. There is no JSON export and no
`graph_source_codegraph_reader.{py,js}` — unlike GitNexus, there is no
offline fallback if the MCP tool isn't available. This means CodeGraph's
readiness is a genuine **two-gate** check that GitNexus and understand-anything
don't have:

1. **On disk:** `.codegraph/codegraph.db` exists (what `detect`/`precheck_graph`
   check — a filesystem check only).
2. **Wired to this session:** the `codegraph_explore` MCP tool is actually in
   *this agent's* tool list (possibly listed as deferred). Only the agent can
   check this — no script can see another process's tool list.

**Both gates must pass before reading.** Before calling `codegraph_explore`:

- If it's listed (even deferred) — load it via tool search if needed, then
  call it directly. One call returns the relevant symbols' verbatim source
  grouped by file, the call paths between them, and a blast-radius summary —
  treat the returned source as already read; do not also grep/re-read the
  same files.
- If it's **not listed at all** — the MCP server was never wired into this
  agent, regardless of whether the db exists. Tell the user to run
  `codegraph install` (outside this agent) and restart. There is nothing else
  to fall back to; do not attempt to open `.codegraph/codegraph.db` directly
  (it is not a documented-stable schema and docforge does not parse it).

`codegraph_explore` also accepts a file or symbol name in the query to return
its current line-numbered source — the same shape as the `Read` tool.

## Build or refresh

Ask the user before instructing either — see `SKILL.md` Step 0's permission
model. Per the bootstrap decision tree, **the agent never runs these commands
itself** for CodeGraph — both end with an MCP-wiring step that requires an
agent restart, so the whole sequence runs outside the agent, by the user:

```
codegraph install     # one-time per machine: wires the codegraph MCP server into this agent
codegraph init         # per project: creates .codegraph/ and builds codegraph.db in one step
```

After that, **refresh is automatic** — CodeGraph's file watcher keeps the
index in sync on every save while an MCP session is connected, and
reconciles any edits made while disconnected the next time one connects.
There is no `codegraph sync`-equivalent step docforge itself ever needs to
run or instruct. Re-run `detect` only to confirm the db exists; then confirm
gate 2 (the tool is in this session) before reading.
