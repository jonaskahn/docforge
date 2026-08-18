# Depth and audience

Depth is the amount of decision-relevant detail, not file count or word count.
The catalog's target depth is a minimum contract: deepen a section only when
evidence changes a reader decision, implementation, diagnosis, review, or risk
judgment.

- **Orientation (`orientation`):** purpose, audience, boundary, selection condition, and next
  links. Section READMEs at this depth are self-introductions: what the
  section is, its scope, a reading path, and the reader question each child
  answers — without summarizing child content or carrying child-owned facts.
- **Working depth:** ordered behavior, important rules, inputs/outputs, common
  failures, and a success or verification condition — the minimum mechanism
  needed to execute or maintain the work safely. (Catalog machine values are
  `orientation`, `deep-dive`, `reference`, `router`; working depth is the
  content budget applied across standard documents.)
- **Deep dive (`deep-dive`):** mechanism, invariants, edge cases, failure containment,
  observability, adjacent dependencies, and the evidence or uncertainty behind
  material claims. Name the boundary at which recovery, escalation, or another
  document takes over.
- **Reference (`reference`):** exhaustive, stable lookup fields with provenance, value
  semantics, valid ranges or states, compatibility boundaries, and an explicit
  source of truth for volatile values.
- **Router (`router`):** purpose, audience, and a structured index routing readers to
  children without summarizing them.

Promote rather than pad: move from orientation when a reader must act; from
working depth when they must diagnose, review, or change a non-obvious
boundary; to reference when omission of one stable field makes lookup unsafe.
**Never** raise depth to restate facts owned by another document.

The catalog assigns a target depth to every document. Code-graph evidence feeds
architecture and implementation depth. Flow-graph evidence feeds only selected
flow-dependent documents. Manifests feed setup, testing, configuration, and
dependency facts; history feeds rationale and chronology.

Audience changes ordering, vocabulary, examples, and evidence questions, not
truth or fact ownership. Shared behavior remains in the owning flow,
architecture, operations, security, or reference document. Business Analyst
views emphasize rules and traceability; Product Owner views emphasize value and
measures; agent views compress navigation and commands; operator views
emphasize safe execution, observability, and recovery; security-reviewer views
emphasize boundaries, controls, residual risk, and evidence. Engineers and
beginners use the default contracts unless a selected specialist profile
applies.

The routed presentation policy applies those differences consistently:
Business Analyst and Product Owner documents use business and outcome language
without implementation excerpts; engineers, beginners, operators, and coding
agents receive only task-relevant commands or examples; security reviewers
receive control and traceability detail without source citations. See
[`code-presentation.md`](code-presentation.md) and
[`evidence-presentation.md`](evidence-presentation.md). How each group's
documents are phrased at that depth is the adjacent axis owned by
[`voice.md`](voice.md).

When the evidence cannot establish an audience-critical fact, record its limit
or typed external unknown in the owning document. **Never** fill a depth tier
with plausible commands, thresholds, ownership, risk ratings, or intent.
