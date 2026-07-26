# Success metrics

_Last generated: {{YYYY-MM-DD}}_

One entry per feature or epic with a stated success metric — only where instrumented in code or explicitly given by a stakeholder. Never invent a target.

---
docforge_provenance:
  doc: docs/product/product-owner/success-metrics.md
  generated_at: {{ISO-8601 timestamp}}
  sections:
    - id: {{feature-slug}}
      sources:
        - path: {{src/module/file.ext}}
          git_blob: {{git hash-object output}}
---

### {{Feature}}

**Metric:** {{what's measured}}
**Instrumented via:** {{the emitted `<event/metric name>` — a stable event/metric name is a public contract, never a private symbol; or the `<module>` by path, or "not instrumented — flag"}}
**Target:** {{only if stated by a stakeholder; omit this line entirely rather than guess}}

<!-- Repeat per feature with a real, checkable metric. Skip features with no
     instrumented or stated metric rather than filling this in speculatively. -->
