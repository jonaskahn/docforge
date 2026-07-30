---
docforge_provenance:
  schema: "2.0"
  doc_id: "<DOC_ID>"
  path: "<DOCUMENT_PATH>"
  generated_at: "<GENERATED_AT>"
  generator:
    name: "docforge"
    version: "2.1.0"
  tier: "<TIER>"
  target_depth: "<TARGET_DEPTH>"
  graph:
    provider: "<GRAPH_PROVIDER>"
    flow: "<FLOW_CAPABILITY>"
  sections: []
---
# Network deployment

_Last reviewed: {{YYYY-MM-DD}}_

## {{Network, e.g. Mainnet}}

**Roles**

| Role | Can do | Held by |
|---|---|---|
| {{role}} | {{capability}} | {{account / multisig}} |

**Deploy**

1. {{step}}
2. {{step}}

```bash
{{verification command}}
```

{{What normal looks like.}}

## Upgrade and rollback

1. {{step}}

{{Rollback path, with the same rigor as deploy.}}
