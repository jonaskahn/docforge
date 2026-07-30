# Depth and audience

Depth is the amount of decision-relevant detail, not file count or word count.

- **Orientation:** purpose, audience, boundaries, and next links.
- **Working depth:** ordered behavior, important rules, inputs/outputs, and
  common failures.
- **Deep dive:** mechanism, invariants, edge cases, failure containment,
  observability, and adjacent dependencies.
- **Reference:** exhaustive lookup fields with stable labels and provenance.

The catalog assigns a target depth to every document. Code-graph evidence feeds
architecture and implementation depth. Flow-graph evidence feeds only selected
flow-dependent documents. Manifests feed setup, testing, configuration, and
dependency facts; history feeds rationale and chronology.

Audience changes ordering and vocabulary, not truth. Shared behavior remains in
the owning flow or architecture document. Business Analyst views emphasize
rules and traceability; Product Owner views emphasize value and measures; agent
views compress navigation and commands.
