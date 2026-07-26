# Process flows

_Last generated: {{YYYY-MM-DD}}_

The business process as actually executed by the system — business-language steps a domain expert recognizes, not the technical call graph. Sourced from `/understand-domain`; decision points link to `business-rules.md` rather than restating the condition.

---
docforge_provenance:
  doc: docs/product/business-analyst/process-flows.md
  generated_at: {{ISO-8601 timestamp}}
  sections:
    - id: {{flow-slug}}
      sources:
        - path: {{src/module/file.ext}}
          git_blob: {{git hash-object output}}
---

### Flow: {{business name, e.g. "Order approval"}}

1. {{step, in business language}} — enforced in {{the `<module>` by path, not a private symbol}}
2. {{step}} — enforced in {{the `<module>` by path}}
3. {{...}}

**Decision points:** {{where the flow branches, and on what business condition}} — see [business-rules.md](./business-rules.md#{{rule-slug}})

<!-- Repeat per flow. One `sections` entry per flow, id matching its heading anchor. -->
