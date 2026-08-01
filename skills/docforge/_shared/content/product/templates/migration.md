---
docforge_provenance:
  schema: "2.0"
  doc_id: "<DOC_ID>"
  path: "<DOCUMENT_PATH>"
  generated_at: "<GENERATED_AT>"
  generator:
    name: "docforge"
    version: "2.8.0"
  tier: "<TIER>"
  target_depth: "<TARGET_DEPTH>"
  graph:
    provider: "<GRAPH_PROVIDER>"
    flow: "<FLOW_CAPABILITY>"
  sections: []
---
# Migrating from {{source version}} to {{target version}}

_Last reviewed: {{YYYY-MM-DD}}_

## Breaking changes, in order

### {{Change}}

**Before**

```{{language}}
{{old}}
```

**After**

```{{language}}
{{new}}
```

{{Codemod or search-and-replace, if mechanical.}}

## Verify

```bash
{{verification command}}
```

## Rollback

{{Path back, or "not supported."}}

Full version matrix: see [compatibility.md](compatibility.md).
