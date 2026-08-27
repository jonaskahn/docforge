# Deep-dive frame

A shared completeness frame for every architecture explanation document. It is
not a heading checklist — a fixed section is never added merely to pad a
document. Instead, every architecture explanation should be able to answer
each question below about the subject it owns; where a question's answer is
material to the reader's decision it becomes content, and where it is
inapplicable it is omitted. Expected-but-unevidenced concerns are stated as
explicit evidence gaps, never silently dropped and never padded.

## The frame questions

- **What decision does this document support?** — the L0 claim: which
  decision, review, diagnosis, or risk judgment a reader comes here to make.
- **What boundary does it own?** — where the subject's responsibility starts
  and ends, including explicit non-responsibilities.
- **What enters and leaves?** — inputs, outputs, public contracts, and
  adjacent systems.
- **What state changes?** — state, data, transaction, and consistency
  behavior when the subject holds any.
- **Which invariants must hold?** — what is always enforced, or deliberately
  absent, stated as absence-based facts.
- **How does the normal path execute?** — the significant runtime path with
  a successful outcome.
- **What fails, where is it contained, and how does recovery proceed?** —
  failure containment, retry, rollback, degradation, and escalation
  boundaries.
- **What can operators observe?** — observability signals and operational
  handoff.
- **What quality or change pressure shaped it?** — only when supported by
  requirements, limits, benchmarks, tests, or extension points.
- **Which facts remain unknown?** — explicit evidence gaps, never invented
  facts.
- **Which neighboring document owns excluded detail?** — routing to the
  document that owns the detail this document deliberately leaves out.

## Applying the frame

Specialized architecture documents — AI integration, persistence, data flow,
state, lifecycle, networking, triggers/jobs, model lifecycle, platform
integration — retain their specific contracts and templates, and apply this
frame where relevant to their own subject. The completeness questions replace
word-count discipline: a document is deep enough when every question whose
answer is material is answered from evidence, and short enough when no
inapplicable section was added to look complete. Detail enforcement comes from
semantic completeness (boundaries, mechanisms, failures, invariants, runtime
scenarios, quality drivers), never from a minimum length.
