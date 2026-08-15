---
docforge_provenance:
  schema: "2.1"
  doc_id: "<DOC_ID>"
  path: "<DOCUMENT_PATH>"
  generated_at: "<GENERATED_AT>"
  generator:
    name: "docforge"
    version: "2.17.0"
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

**Fixtures:** {{source — factory, fixture file, seed script}} · **Reset:** {{per-test / per-suite / not needed}} · **Data:** {{synthetic / sanitized-production / none}}

## Integration

```bash
{{command}}
```

**Covers:** {{scope}} · **Does not cover:** {{scope}} · **Isolation:** {{real/mocked dependencies}}

**Fixtures:** {{source}} · **Reset:** {{strategy}} · **Data:** {{synthetic / sanitized-production / none}} · **Shared dependency owner:** {{team or role, or "none shared"}}

## End-to-end

```bash
{{command}}
```

**Covers:** {{scope}} · **Does not cover:** {{scope}} · **Isolation:** {{real/mocked dependencies}}

**Fixtures:** {{source}} · **Reset:** {{strategy}} · **Data:** {{synthetic / sanitized-production / none}} · **Shared dependency owner:** {{team or role, or "none shared"}}

## Diagnosing failures

| Symptom | Usually means | First check |
|---|---|---|
| {{flaky pattern}} | {{likely cause}} | {{what to check first}} |
