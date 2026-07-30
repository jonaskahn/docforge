---
docforge_provenance:
  schema: "2.0"
  doc_id: "<DOC_ID>"
  path: "<DOCUMENT_PATH>"
  generated_at: "<GENERATED_AT>"
  generator:
    name: "docforge"
    version: "2.6.1"
  tier: "<TIER>"
  target_depth: "<TARGET_DEPTH>"
  graph:
    provider: "<GRAPH_PROVIDER>"
    flow: "<FLOW_CAPABILITY>"
  sections: []
---
# Contract system

_Last reviewed: {{YYYY-MM-DD}}_

## {{Contract name}}

**Network(s):** {{deployed networks}}

**Upgrade boundary:** {{immutable | proxy-upgradeable | governance-gated}}

| Storage item | Purpose |
|---|---|
| {{item}} | {{purpose}} |

**Privileged authorities**

| Authority | Can call | Held by |
|---|---|---|
| {{role}} | {{functions}} | {{account / multisig / governance}} |

Economic and security invariants: see
[economic-invariants.md](economic-invariants.md).
