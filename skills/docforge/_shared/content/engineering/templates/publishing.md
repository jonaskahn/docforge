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
# Publishing

_Last reviewed: {{YYYY-MM-DD}}_

## Artifacts

| Artifact | Format | Produced by |
|---|---|---|
| {{name}} | {{package / image / binary / archive}} | {{build step or command}} |

**Version source:** {{file / tag / generator — the single place the version number is read from}}

## Build, sign, publish

1. Build — `{{command}}` — verify: {{signal}}
2. Sign — {{mechanism, e.g. provenance attestation, GPG, cosign}} — verify: {{signal}}
3. Publish to {{registry/channel}} — `{{command}}` — verify: {{signal}}

**Required gate:** {{approval, CI check, or "none"}} before step 3 runs.

## Verify

{{How a consumer confirms the right artifact landed — command or check, e.g. `{{command}}` matches expected {{version/checksum}}.}}

## Rollback / deprecate

**Unpublish:** {{condition under which a version is pulled, and how}} — only within {{evidenced window, or "not supported"}}.

**Deprecate:** {{how a version is marked deprecated without removing it}}.

**Patch forward:** {{when the fix is a new version instead}}.

Released changes: record in [changelog.md](changelog.md).
