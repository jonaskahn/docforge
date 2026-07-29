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
# Testing (agent view)

<!-- Brief stub — strategy and rationale live in engineering/testing.md, link only. -->

## Runner

```
{{full-suite command}}
{{single-test command}}
```

## Layout

{{one line: where tests live, naming convention}}

## Mock stance

{{one line: what's mocked vs real in tests — use a typed <MOCK_STANCE> token only if genuinely not inferable from the test suite}}

For strategy, coverage policy, and the test pyramid, see [engineering/testing.md](../engineering/testing.md).
