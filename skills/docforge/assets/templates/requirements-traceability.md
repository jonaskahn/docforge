# Requirements traceability

_Last generated: {{YYYY-MM-DD}}_

Maps requirement → implementation → verification. Open this file when a stakeholder asks whether the system actually does what was asked for.

---
docforge_provenance:
  doc: docs/product/business-analyst/requirements-traceability.md
  generated_at: {{ISO-8601 timestamp}}
  sections:
    - id: traceability-table
      sources:
        - path: {{src/module/file.ext}}
          git_blob: {{git hash-object output}}
---

### Traceability table

| Requirement (stakeholder's own wording, if available) | Business rule(s) implementing it | Code location | Test coverage | Status |
|---|---|---|---|---|
| {{requirement text, or `> TODO(owner): confirm original requirement wording` if wording isn't recoverable}} | [{{rule name}}](./business-rules.md#{{rule-slug}}) | `{{symbol}}` | {{test file/name, or "none — flag"}} | {{implemented / partial / not started}} |

<!-- One row per requirement. Never invent stakeholder wording that isn't
     recoverable from a connected source — write the TODO placeholder instead. -->
