---
docforge_provenance:
  schema: "2.0"
  doc_id: "<DOC_ID>"
  path: "<DOCUMENT_PATH>"
  generated_at: "<GENERATED_AT>"
  generator:
    name: "docforge"
    version: "2.7.0"
  tier: "<TIER>"
  target_depth: "<TARGET_DEPTH>"
  graph:
    provider: "<GRAPH_PROVIDER>"
    flow: "<FLOW_CAPABILITY>"
  sections: []
---
# API reference

_Last reviewed: {{YYYY-MM-DD}}_

**Source of truth:** {{path to spec/schema/generator — e.g. `openapi.yaml`,
generated client types, GraphQL schema}}. This page narrates that source; if
the two disagree, the source wins.

## {{Resource group, e.g. Orders}}

{{One clause: what this resource represents.}}

| Operation | Method + path | Auth | Rate limit class |
|---|---|---|---|
| {{operation}} | `{{METHOD}} {{/path}}` | {{auth requirement}} | {{class}} |

### `{{METHOD}} {{/path}}`

{{One clause: what this operation does.}}

**Request**

| Field | Type | Required | Description |
|---|---|---|---|
| {{field}} | {{type}} | {{yes/no}} | {{description}} |

**Response**

| Field | Type | Description |
|---|---|---|
| {{field}} | {{type}} | {{description}} |

```json
{{realistic example}}
```

Errors: see [error-catalog.md](error-catalog.md) for the shared envelope and
status codes.

## Deprecated operations

| Operation | Deprecated in | Removed in | Replacement |
|---|---|---|---|
| {{operation}} | {{version}} | {{version or "not scheduled"}} | {{replacement or "none"}} |
