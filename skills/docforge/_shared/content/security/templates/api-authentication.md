---
docforge_provenance:
  schema: "2.1"
  doc_id: "<DOC_ID>"
  path: "<DOCUMENT_PATH>"
  generated_at: "<GENERATED_AT>"
  generator:
    name: "docforge"
    version: "2.16.0"
  tier: "<TIER>"
  target_depth: "<TARGET_DEPTH>"
  graph:
    provider: "<GRAPH_PROVIDER>"
    flow: "<FLOW_CAPABILITY>"
  sections: []
---
# Authentication

_Last reviewed: {{YYYY-MM-DD}}_

## {{Scheme name, e.g. API key / OAuth2 authorization code / mTLS}}

{{One clause: what this scheme is and when it applies.}}

**Credential lifecycle**

| Stage | Behavior |
|---|---|
| Issued | {{how a caller obtains the credential}} |
| Transmitted | {{header/field the credential travels in}} |
| Rotated | {{rotation mechanism, if any}} |
| Expires / revoked | {{what happens and how the caller detects it}} |

## Scopes and permissions

| Scope | Capability |
|---|---|
| {{scope}} | {{what it allows}} |

## Failure modes

| Condition | Status | Caller action |
|---|---|---|
| Missing credential | {{status}} | {{action}} |
| Expired credential | {{status}} | {{action}} |
| Revoked credential | {{status}} | {{action}} |
| Insufficient scope | {{status}} | {{action}} |

Never include a real credential, secret, or token value — placeholders
only.
