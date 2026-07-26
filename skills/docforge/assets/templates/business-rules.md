# Business rules

_Last generated: {{YYYY-MM-DD}}_

One entry per rule the codebase actually enforces. Verified against the conditional logic itself — never inferred from a variable or function name. See `../../../references/overlay-business-analyst.md` for how these are sourced.

---
docforge_provenance:
  doc: docs/product/business-analyst/business-rules.md
  generated_at: {{ISO-8601 timestamp}}
  graph_snapshot: {{knowledge-graph version marker, or omit}}
  sections:
    - id: {{rule-slug}}
      sources:
        - path: {{src/module/file.ext}}
          git_blob: {{output of `git hash-object <path>`}}
---

### Rule: {{plain-language rule name}}

**Statement:** {{the rule, in one sentence a business stakeholder would recognize}}
**Enforced in:** {{the module/file by path — describe the behaviour; never a `module::function` symbol or line number}}
**Applies to:** {{which flow, which entity}}
**Exceptions:** {{override conditions, if any — state "none found" rather than omitting the field}}
**Source:** verified via `/understand-chat "what conditions gate {{rule}}"` against `{{flow-name}}`, {{date}}

<!-- Repeat the block above per rule. Each rule needs its own `sections` entry
     in the frontmatter above, with its own section id matching the anchor
     this heading generates (e.g. "### Rule: Order approval threshold" ->
     id: order-approval-threshold). -->
