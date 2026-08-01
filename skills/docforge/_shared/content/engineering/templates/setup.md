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
# Local setup

_Last reviewed: {{YYYY-MM-DD}}_ · Expect roughly **{{N}} minutes** for a first run.

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| {{runtime}} | {{exact version or range}} | {{how to install}} |
| {{tool}} | {{version}} | |

Access you will need, and who grants it: {{credential or system}} — <ACCESS_GRANTOR>.

## Steps

1. Clone the repository and enter it.
2. `{{install command}}`
3. Copy the example configuration: `cp {{.env.example}} {{.env}}` and fill in the
   values described in [../reference/configuration.md](../reference/configuration.md).
4. `{{start dependencies — database, queue, etc.}}`
5. `{{run the application}}`

## Verify

```bash
{{verification command}}
```

Expected output:

```
{{what success looks like}}
```

## Common problems

**{{Symptom}}** — {{cause and fix}}.

**{{Symptom}}** — {{cause and fix}}.

## Next

- Understand the codebase: [../architecture/high-level.md](../architecture/high-level.md)
- Run the tests: [testing.md](testing.md)
- Make a change: [../contributing/README.md](../contributing/README.md)
