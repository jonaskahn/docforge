---
{
  "docforge_provenance": {
    "schema": "1.0",
    "doc_id": "<DOC_ID>",
    "path": "<DOCUMENT_PATH>",
    "generated_at": "<GENERATED_AT>",
    "tool_version": "2.0.0",
    "tier": "<TIER>",
    "target_depth": "<TARGET_DEPTH>",
    "graph": {
      "provider": "<GRAPH_PROVIDER>",
      "flow": "<FLOW_CAPABILITY>"
    },
    "sections": []
  }
}
---
# Low-level architecture

_Last reviewed: {{YYYY-MM-DD}}_

Component-level decomposition. Zooms into the building blocks named in
[high-level.md](high-level.md). Describes responsibilities and relationships in prose;
never pastes code or anchors to a private symbol a rename would break.

## Components

### `{{path/to/component}}/`

{{What it does, in one to three sentences. What crosses its boundary in and out.}}

- **Talks to:** {{which other components, and in which direction}}
- **Owns:** {{the data or responsibility that is exclusively its}}
- **Invariant:** {{what is deliberately absent or always enforced — the fact a reader
  cannot recover by reading code, because it is the absence of something}}

### `{{path/to/component}}/`

{{...}}

## Data model

{{The main entities and how they relate, described. Not a schema dump — a routine column
rename must not falsify this. Link the generated schema if one exists.}}

## Significant subsystems

The ones worth a full deep-dive get their own folder under
[concepts/](concepts/README.md):

| Subsystem | Deep-dive |
|---|---|
| {{name}} | [concepts/{{slug}}/](concepts/{{slug}}/README.md) |

## Cross-cutting concerns

| Concern | Where it lives | Notes |
|---|---|---|
| Configuration | `{{path}}` | See [../reference/configuration.md](../reference/configuration.md) |
| Error handling | `{{path}}` | |
| Logging | `{{path}}` | |
| Authentication | `{{path}}` | |
| Persistence | `{{path}}` | |
