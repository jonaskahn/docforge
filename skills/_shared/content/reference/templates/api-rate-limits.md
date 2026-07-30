---
docforge_provenance:
  schema: "2.0"
  doc_id: "<DOC_ID>"
  path: "<DOCUMENT_PATH>"
  generated_at: "<GENERATED_AT>"
  generator:
    name: "docforge"
    version: "2.6.0"
  tier: "<TIER>"
  target_depth: "<TARGET_DEPTH>"
  graph:
    provider: "<GRAPH_PROVIDER>"
    flow: "<FLOW_CAPABILITY>"
  sections: []
---
# Rate limits

_Last reviewed: {{YYYY-MM-DD}}_

## Limits

| Dimension | Sustained | Burst | Applies to |
|---|---|---|---|
| {{per key / per IP / per endpoint / per tier}} | {{rate}} | {{burst allowance}} | {{scope}} |

## Response contract

**Status on limit exceeded:** {{status code}}

| Header | Meaning |
|---|---|
| `{{header name}}` | {{what it tells the caller}} |

```http
HTTP/1.1 {{status}} {{reason}}
{{Header}}: {{value}}
```

## What to do on {{status}}

{{Imperative: back off for the stated duration, then retry — the exact
caller-side behavior expected.}}
