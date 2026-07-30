# Understand Anything source

Understand Anything writes a code graph to `.ua/knowledge-graph.json`
and a native flow graph to `.ua/domain-graph.json`. Repositories already
using `.understand-anything/` keep that legacy data directory. Because the
artifacts are JSON, Docforge can deterministically inventory them with
`read_graph.{py,js}` and can also use the provider’s own skills for semantic
exploration.

## Prepare

Plugin/skill installation is user-run and may require an agent restart. On
Codex the skills are invoked with `$`; on hosts that support slash commands
they use `/`.

After explicit approval, invoke the installed `understand` skill to build the
code graph:

```text
/understand
```

The first run analyzes the full codebase and can consume substantial tokens;
state that cost before approval. It also creates intermediate directories,
may build its plugin dependencies on first use, and pauses for ignore-rule
review; disclose those expected phases. Later runs are incremental. Large
monorepos may be scoped to a subdirectory, but the resulting graph scope must
be stated in the Docforge plan.

Only when the selected manifest contains a `flow_graph` requirement, invoke
the provider's flow-extraction skill:

```text
/understand-domain
```

With an existing code graph it derives flow knowledge cheaply; without
one it can perform a lightweight scan, though Docforge’s universal code-graph
gate means the normal Docforge path already has the code graph. This
adds business domains, flows, and ordered steps. `--auto-accept` never supplies
approval for either graph-generation run. Optional provider auto-update hooks
are also a separate side effect.

## Query

Use the installed provider skills when available:

- `understand-chat` for a narrow architecture or behavior question;
- `understand-explain` for a focused file or symbol;
- `understand-diff` for change impact;
- `understand-onboard` for orientation evidence;
- `understand-domain` to create or refresh native flow data.

For deterministic inventory or environments without the interactive MCP/skill
path, read the JSON in place:

```sh
python runtime/cli/python/read_graph.py --graph <repo>/.ua/knowledge-graph.json --probe
node runtime/cli/js/read_graph.js --graph <repo>/.ua/knowledge-graph.json --probe
# bun  runtime/cli/js/read_graph.js --graph <repo>/.ua/knowledge-graph.json --probe
# deno run -A runtime/cli/js/read_graph.js --graph <repo>/.ua/knowledge-graph.json --probe
python runtime/cli/python/read_graph.py --graph <repo>/.ua/knowledge-graph.json --layers
node runtime/cli/js/read_graph.js --graph <repo>/.ua/knowledge-graph.json --layers
# bun  runtime/cli/js/read_graph.js --graph <repo>/.ua/knowledge-graph.json --layers
# deno run -A runtime/cli/js/read_graph.js --graph <repo>/.ua/knowledge-graph.json --layers
python runtime/cli/python/read_graph.py --graph <repo>/.ua/knowledge-graph.json --entry-points
node runtime/cli/js/read_graph.js --graph <repo>/.ua/knowledge-graph.json --entry-points
# bun  runtime/cli/js/read_graph.js --graph <repo>/.ua/knowledge-graph.json --entry-points
# deno run -A runtime/cli/js/read_graph.js --graph <repo>/.ua/knowledge-graph.json --entry-points
```

The code graph contains files, functions, classes, dependencies, summaries,
and architectural layers. The flow graph contains domains, flows,
and steps. Do not assume a semantic summary or domain label is authoritative:
confirm business rules, failures, and externally visible behavior in source.

## Use in Docforge

- Use layers, imports, symbols, and tours to plan the architecture and agent
  views.
- Add dynamic flow documents from actual flows in `.ua/domain-graph.json`—never from example
  seeds.
- Generate the BA process view, rules, and requirements links from native flow
  evidence plus source confirmation.
- Use PO feature and metric evidence only when code, history, instrumentation,
  or stakeholder material supports it.

The graph can be committed and shared by the target repository under the
provider’s own guidance. Docforge neither moves it into `docs/` nor records it
as generated documentation.
