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
# Testing guide

_Last reviewed: {{YYYY-MM-DD}}_

## Unit

```bash
{{command}}
```

**Covers:** {{scope}} · **Does not cover:** {{scope}} · **Isolation:** {{real/mocked dependencies}}

## Integration

```bash
{{command}}
```

**Covers:** {{scope}} · **Does not cover:** {{scope}} · **Isolation:** {{real/mocked dependencies}}

## End-to-end

```bash
{{command}}
```

**Covers:** {{scope}} · **Does not cover:** {{scope}} · **Isolation:** {{real/mocked dependencies}}

## Diagnosing failures

| Symptom | Usually means | First check |
|---|---|---|
| {{flaky pattern}} | {{likely cause}} | {{what to check first}} |
