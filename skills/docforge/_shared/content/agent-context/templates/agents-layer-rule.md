# {{layer_name}}

_Glob: `{{layer_glob}}`_

<!-- docforge-provenance v{{skill_version}} | graph {{graph_hash_short}} | {{graph_analyzed_date}} | regenerate: re-run the coding-agents audience -->

{{One sentence: what this layer contains and its role in the dependency order.}}

## Conventions

| Convention | Required shape | Evidence |
|---|---|---|
| {{name}} | {{concise implementation rule}} | `{{durable source path}}` |

Omit this section when no non-obvious convention is evidenced for the layer.

## Hotspots

| Source path | Why it is sensitive | Safe edit constraint |
|---|---|---|
| `{{durable path}}` | {{branching, coupling, churn, or boundary role}} | {{constraint}} |

Omit this section when the layer has no evidenced complexity hotspot.

## Validation

- Minimum for a change inside this layer: `{{verified command}}`
