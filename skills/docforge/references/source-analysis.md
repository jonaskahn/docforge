# Source analysis — grounding documentation in a knowledge graph

Every document this skill produces makes claims about a codebase. The failure mode that destroys a documentation set is not bad prose; it is a confident claim that turns out to be false, because one falsified claim causes readers to discount the rest, including the true parts.

The knowledge graph exists to remove the guessing. It gives you the module inventory, the import and call edges, the architectural layer assignment, the business domains and flows, and a queryable interface for anything it does not already state. Building it is a precondition for writing, not an optimization.

Contents:
1. Building and refreshing the graph
2. Reading the graph directly
3. Command-to-document mapping
4. Asking good questions
5. Documenting the graph itself
6. External values and tokens, never graphs

---

## 1. Building and refreshing the graph

```
/understand
```

A multi-agent pipeline scans the project, extracts files, functions, classes and dependencies, and writes the result to the project root — `$PROJECT_ROOT/.ua/knowledge-graph.json` (the domain graph lands beside it at `$PROJECT_ROOT/.ua/domain-graph.json`). Projects that already carry a `.understand-anything/` directory keep using it — substitute that path where this document says `.ua/`. Because the graphs live at the root, both helper scripts search the current directory and every parent up to the git root, so they resolve the graph even when invoked from a subdirectory.

**Check before building.** If `.ua/knowledge-graph.json` already exists and is newer than the last substantive commit, use it as is. If it is stale, re-running is incremental — only changed files are re-analysed — so a refresh is cheap. A first run on a large codebase is not: it analyses everything and consumes tokens accordingly. Tell the user before starting one on a repo of significant size.

**Confirm the graph actually landed.** When `/understand` reports success but a later step still says the graph is missing, the write and the expectation have diverged — verify against the disk rather than re-running blind: `python scripts/validate_graphs.py --repo . --verbose` prints what sits in `.ua/` and `.understand-anything/` (filenames, sizes, JSON validity, node/edge counts), separating a false "not found" from a truncated or absent file. `check_preconditions.py` is the workflow gate; this is the probe for when the gate's answer surprises you.

**Useful invocations:**

| Purpose | Command |
|---|---|
| Full or incremental analysis | `/understand` |
| Scope to one part of a large repo | `/understand src/frontend` |
| Stricter graph validation | `/understand --review` |
| Keep the graph current on every commit | `/understand --auto-update` |
| Non-English output | `/understand --language <en\|zh\|zh-TW\|ja\|ko\|ru>` |
| Visual exploration | `/understand-dashboard` |

**`/understand` is a skill, not universally a slash command.** Some agents expose it as `/understand`; Codex uses `$understand`; others show no command until the understand-anything skill or plugin is loaded. If no command is recognized, load or enable it the way this agent loads skills (skill listing, plugin registry, an explicit load/`Skill` call) before concluding it is missing, then invoke it — in plain language where no command form exists: *"Use the understand skill to analyze this project."* If the plugin is genuinely absent (loading it is not possible here), stop per `SKILL.md`'s "Precheck" section — tell the user to install `understand-anything` before anything else runs.

---

## 2. Reading the graph directly

The graph is JSON on disk, so you can read it rather than asking questions about it — faster, cheaper, and exact.

```bash
python scripts/graph_extract.py --graph .ua/knowledge-graph.json --summary
```

The helper probes the file's actual shape before extracting anything and reports what it found: node and edge counts, the layer distribution, the module inventory, and external dependency references. Use `--modules`, `--layers`, `--deps` or `--probe` for narrower output. Because it adapts to the shape it finds rather than assuming one, treat its output as a starting inventory to verify, not as finished prose.

What the graph is good for, and what it is not:

| Reliable from the graph | Needs another source |
|---|---|
| Module and file inventory | Version pins and dependency ranges (read the manifest) |
| Import, call and inheritance edges | Why a choice was made (`git log`, the team) |
| Architectural layer grouping | Runtime behaviour under load |
| Which modules touch which others | Operational procedures and on-call reality |
| Business domains and process flows | Anything not yet built |

---

## 3. Command-to-document mapping

Run the query when you reach the document, not all at once up front — answers gathered early go stale in your context and tempt you into writing from memory.

### `architecture/high-level.md` and `low-level.md` — the two-altitude map

The graph is the primary source for both. `high-level.md` takes the module inventory, layer
assignment and boundaries straight from the graph — breadth, kept stable. `low-level.md` and
the `concepts/<subsystem>/` deep-dives need depth, and depth comes from `/understand-explain`,
which here is **required, not optional** — it is the engine for every L2/L3 layer:

```
/understand-explain src/<module>
```

Run it per significant subsystem, and treat its output as evidence for a behavioural
description — never paste its code excerpts through. For **invariants** — the absences that a
reader cannot recover from the code — the edge list is what makes them provable. If nothing in
`core/` has an outbound edge to `adapters/`, that is an invariant worth stating, and you have
evidence for it rather than a belief. Confirm the intent before asserting it:

```
/understand-chat Does anything under core/ import from adapters/, or perform I/O directly?
```

### `flows/<flow>.md` — aligned flow documents, flat by default

First confirm `python scripts/check_preconditions.py --repo <path> --need domain` reports
READY — flows are never enumerated by hand. Then `/understand-domain` returns the domains,
flows and steps, and that list *is* the set of flow documents to build, one flat `<flow>.md`
each. For each flow, source the plain steps from `/understand-domain`. Only promote a flow to
`<flow>/README.md` + subfile in the same pass you also source and write: the
`business-analyst.md` rules from `/understand-chat "what business rules gate <flow>"`, or the
`engineering.md` mechanism from `/understand-explain <flow module>`. See `depth-and-audience.md`
for the full command-to-cell mapping and `document-composition.md` for the flat-file default
and the atomic promotion rule.

### `architecture/data-flow.md`

```
/understand-domain
```

Domains, flows and process steps in the code's own terms. For a specific path, ask narrowly: *"Trace what happens between the ingest entry point and the first write to storage."*

### `product/overview.md` and `capabilities.md`

`/understand-domain` again, read differently — the business domains it extracts are the vocabulary a non-engineer needs, and using the code's own domain terms keeps the product documentation and the system from drifting apart.

### `engineering/setup.md`

```
/understand-onboard
```

Produces an onboarding guide ordered by dependency. Treat it as a draft: **every command it names must be run before it appears in your output.** An unverified setup step is the single most damaging kind of documentation error, because it fails the reader at their first contact with the project.

### `architecture/dependencies.md`

External packages and services appear in the graph as import edges leaving the project's own modules; `scripts/graph_extract.py --deps` collects them. Cross-check against the manifest for versions and ranges, then ask about behaviour, which no static source carries:

```
/understand-chat For each external service this calls, what are the timeout, retry and fallback behaviours?
```

### `reference/configuration.md`

```
/understand-chat Which environment variables or configuration keys does this code read, where is each read, and what happens when one is absent?
```

Verify against the code before publishing. Configuration documentation copied from an old example file is a recurring source of wasted hours.

### `reference/limitations.md`

Limitations are the hardest content to source, because nothing declares them. Productive probes:

- *"Where does this code have hard-coded limits, bounds, or size caps?"*
- *"Which error paths are unhandled or only logged?"*
- *"Where are the TODO and FIXME clusters, and what do they concern?"*
- *"Which operations are not idempotent?"*
- *"What assumptions does this make about its inputs that are not validated?"*

Each answer is a candidate row. Confirm with the team before publishing anything that reads as a defect rather than a design choice.

### `architecture/decisions/` — backfilled ADRs

The graph shows what was chosen, never why. Use it to find *where* a decision is embodied, then reconstruct the reasoning from history:

```
/understand-chat Which parts of the system depend on <technology>, and how deeply?
```

Combine with `git log --diff-filter=A -- <path>` and the manifest's history. Mark every backfilled record as reconstructed — see `decision-records.md`.

### Overlay documents

| Overlay | Ask |
|---|---|
| API | *"List every route, its method, its handler, and the authentication it requires."* · *"What error types and codes can each endpoint return?"* |
| Data pipeline | *"What are the pipeline stages in order, and what does each read and write?"* · *"Which stages are idempotent?"* |
| Web app | *"Which routes render on the server and which on the client, and where does each fetch data?"* |
| Library | *"What is exported from the package root, and what is reachable only through deeper paths?"* |
| Infrastructure | *"Which resources are declared here, and which are referenced but managed elsewhere?"* |

### Keeping documentation current

```
/understand-diff
```

Impact analysis for uncommitted changes. Run it before a release to find which documents a change has invalidated — the same edges that show blast radius in code show it in documentation, once the code map names its modules.

---

## 4. Asking good questions

**Narrow beats broad.** "Which modules write to the database, and through what layer" retrieves cleanly. "Explain the architecture" returns prose you then have to verify line by line, which costs more than asking three precise questions.

**Ask for structure when you need structure.** "List each route as method, path, handler, auth requirement" gives you a table. An open question gives you paragraphs you must then disassemble.

**Ask about absences explicitly.** Invariants, unhandled cases and missing validation are the highest-value content in a documentation set and the least visible in code. They only surface if you ask.

**Never paste answers through.** They are evidence, not prose. Write the document in its own voice, in the structure the template specifies, citing what the answers established. An answer copied verbatim reads as a transcript and usually carries a level of detail wrong for the document's audience.

**Verify before asserting.** Where a claim is load-bearing — a security boundary, a data guarantee, an idempotency promise — check it against the code directly rather than relying on a single retrieved answer.

---

## 5. Documenting the graph itself

Once a repo carries a graph, it becomes an onboarding asset worth mentioning in the documentation it helped produce:

- The graph is JSON and can be committed, letting teammates explore without re-running the pipeline. Commit everything under `.ua/` **except** `intermediate/` and `diff-overlay.json`, which are local scratch. Track graphs of 10 MB or more with git-lfs.
- A committed graph can be viewed without any AI tooling — Node.js 18+ and the published viewer package are enough, served read-only from local disk.
- If the team enables the post-commit auto-update hook, each commit lands with a matching graph.

Where this applies, one line in `docs/engineering/setup.md` under a "understanding the codebase" heading is the right weight. Do not turn the documentation set into an advertisement for its own toolchain.

---

## 6. External values and tokens, never graphs

**Do not generate or write around a missing graph.** Both the knowledge graph and domain graph are checked at the start of every docforge invocation (see `SKILL.md`'s "Precheck" section). If either is missing, docforge stops and tells the user which command to run — there is no inspection fallback, no adequate substitute, and no scenario in which a docforge run proceeds without both.

**Distinguish between external values and derivable facts.** A fact that lives in code, config, or git history (a retry policy, a business rule, a flow step, a module boundary) is derivable — query the graph or read the source directly to obtain it. A fact that lives nowhere in the repository (a contact address, an SLA number, a roadmap date, a production URL) is external — represent it as a typed `<UPPER_SNAKE_CASE>` token and never downgrade it to a placeholder just because querying might be inconvenient. The distinction is the integrity of the document: over-claiming (saying X when you cannot verify it) is worse than under-claiming (using a token for something genuinely unknowable), and guessing at derivable content while ignoring a graph is the worst of both.

**Do not generate a tree from the repository name.** The knowledge graph surfaces the actual architecture; a name-derived guess is a liability, not helpful. If you cannot access the source at all (the plugin is not installed, the source is not reachable), docforge will not run — it stops at the Precheck step.
