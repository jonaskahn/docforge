# Graph sources — capability dispatch

Docforge reads exactly one thing regardless of source: `.ua/knowledge-graph.json` and `.ua/domain-graph.json` at the project root. Two tools can currently produce them, and this table is the single place that maps "I need capability X" to "run this, for whichever source is active."

**Priority order, always:** if `.ua/*.json` already exists, use it as-is — it does not matter which source built it. Only consult the "how do I build it" row when the graph is genuinely missing. `check_preconditions.py`/`.js` (`scripts/graph_source_ua.py`/`.js`, `scripts/graph_source_gitnexus.py`/`.js`) implement this detection; `references/gitnexus-bridge.md` is the GitNexus build recipe.

| Capability | understand-anything | GitNexus | Notes |
|---|---|---|---|
| Build the initial graph | `/understand` | `references/gitnexus-bridge.md` (Cypher queries → `graph_source_gitnexus.py build`) | Both write the same two files; downstream docs can't tell which ran |
| Refresh after code changes | `/understand` (incremental) or `/understand --auto-update` | `npx gitnexus analyze`, then re-run the bridge's three queries + `build` | GitNexus's own commit hook re-indexes `.gitnexus/`, but does **not** re-run the bridge — `.ua/*.json` goes stale until the bridge is re-run manually |
| Scope analysis to a subdirectory | `/understand src/frontend` | not supported — GitNexus always indexes the whole repo | |
| Stricter graph validation | `/understand --review` | none | |
| Business domain / flow graph | `/understand-domain` | the bridge's `processes.json` query | GitNexus path is flows-only (no domain grouping) — see "Community clusters" note in `gitnexus-bridge.md` |
| Deep-dive a symbol (L2/L3 depth) | `/understand-explain <path>` | `context` MCP tool (360-degree symbol view) | `references/depth-and-audience.md` documents the L0–L3 ladder both feed into |
| Trace an execution flow | `/understand-explain` + graph query | `query` MCP tool (process-grouped code intelligence) | |
| Blast radius / change impact | inferred from graph edges | `impact` MCP tool | understand-anything has no dedicated command; read edges from `.ua/knowledge-graph.json` directly |
| Diff a PR / working-tree change | `/understand-diff` | `detect_changes` MCP tool | |
| Visual exploration | `/understand-dashboard` | none | |
| Onboarding guide generation | `/understand-onboard` | none | |
| Read the graph offline (no tool call) | `graph_extract.py --graph .ua/knowledge-graph.json` | same command — the file is source-agnostic once built | |

## Adding a source

See the closing section of `references/gitnexus-bridge.md` — a new `graph_source_<name>.py`/`.js` pair plus one row here and one branch in `check_preconditions.py`/`.js`'s MISSING path is the entire integration surface.
