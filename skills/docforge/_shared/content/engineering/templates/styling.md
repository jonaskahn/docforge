---
docforge_provenance:
  schema: "2.1"
  doc_id: "<DOC_ID>"
  path: "<DOCUMENT_PATH>"
  generated_at: "<GENERATED_AT>"
  generator:
    name: "docforge"
    version: "2.15.0"
  tier: "<TIER>"
  target_depth: "<TARGET_DEPTH>"
  graph:
    provider: "<GRAPH_PROVIDER>"
    flow: "<FLOW_CAPABILITY>"
  sections: []
---
# Styling

_Last reviewed: {{YYYY-MM-DD}}_

## Component responsibilities

| Component | Owns (styling concern) | Consumes tokens from |
|---|---|---|
| {{component}} | {{e.g. spacing, color, elevation}} | {{token group}} |

General component hierarchy and composition: [../architecture/ui-components.md](../architecture/ui-components.md).

## Tokens

| Token | Value | Type |
|---|---|---|
| {{name}} | {{value}} | {{color / dimension / typography / other}} |

## Theming

**Mechanism:** {{CSS variables / theme provider / build-time generation}}

**On missing token:** {{degradation behavior}}

## Browser support

| Browser / engine | Minimum version | Evidenced by |
|---|---|---|
| {{browser}} | {{version}} | {{browserslist config / CI matrix / polyfill}} |

## Degradation

{{Fallback behavior when a browser or feature isn't supported — feature detection, polyfill, or graceful degradation. State only what is evidenced; never assert support that isn't tested.}}
