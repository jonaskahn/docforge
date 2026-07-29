---
{
  "docforge_provenance": {
    "schema": "1.0",
    "doc_id": "<DOC_ID>",
    "path": "<DOCUMENT_PATH>",
    "generated_at": "<GENERATED_AT>",
    "tool_version": "2.0.0",
    "tier": "<TIER>",
    "target_depth": "<TARGET_DEPTH>",
    "graph": {
      "provider": "<GRAPH_PROVIDER>",
      "flow": "<FLOW_CAPABILITY>"
    },
    "sections": []
  }
}
---
# Business rules

_Last reviewed: {{YYYY-MM-DD}}_

One entry per rule the codebase actually enforces. Verify against the conditional logic itself; never infer a rule from a variable or function name.


### Rule: {{plain-language rule name}}

**Statement:** {{the rule, in one sentence a business stakeholder would recognize}}
**Enforced in:** {{the module/file by path — describe the behaviour; never a `module::function` symbol or line number}}
**Applies to:** {{which flow, which entity}}
**Exceptions:** {{override conditions, if any — state "none found" rather than omitting the field}}
**Source:** verified against the selected flow evidence and repository source for `{{flow-name}}`, {{date}}

<!-- Repeat the block above per rule. Each rule needs its own `sections` entry
     in the frontmatter above, with its own section id matching the anchor
     this heading generates (e.g. "### Rule: Order approval threshold" ->
     id: order-approval-threshold). -->
