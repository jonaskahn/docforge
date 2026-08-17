# Flows (agent view)

<!-- Standalone: no docs/flows/ exists to link, so this is the repository's only
     flow documentation. Own each entry from .docforge/flow-index.json and the
     graph. Gated the same as docs/flows/ — see
     runtime/cli/python/precheck_graph.py --need flow. Never infer a flow. -->

## Main flows

{{one row per main-priority flow}}

| Flow | Trigger | Entry | Path | Ends with |
|---|---|---|---|---|
| {{name}} | {{trigger or route}} | `{{entry file}}` | {{three to six durable module hops}} | {{terminal effect}} |

## Other flows

{{one row per remaining candidate — name, trigger, entry path only}}

| Flow | Trigger | Entry |
|---|---|---|
| {{name}} | {{trigger or route}} | `{{entry file}}` |
