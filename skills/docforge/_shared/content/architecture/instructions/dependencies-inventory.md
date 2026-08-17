# Dependency-inventory writing craft

- For every direct dependency, cite manifest, lockfile, or SBOM evidence and
  its integration path.
- Mark an unverified license, failure mode, or replacement assumption as
  unknown; do not turn package metadata into an operational claim.
- Lead with a compact risk-oriented table, ordered by criticality — the
  dependency whose failure or removal would hurt most goes first, not the
  alphabetically first package. Keep an "if it disappeared" column (or
  equivalent prose): it forces concentration-risk assessment that a plain
  package list hides.
- Always include licence for every direct dependency.
- Give short integration notes only for dependencies whose failure or
  replacement changes system behavior; a pinned linting tool doesn't need a
  paragraph.
- Group by runtime library, external service, build/tooling, and generated
  inventory.
- Keep versions and licenses scannable in the table; keep judgment —
  criticality, failure handling, replacement effort — in prose beside it,
  not squeezed into a table cell.
- Automate the exhaustive inventory; hand-write only direct dependencies and
  assessment.
- When pointing to the generated machine-readable inventory, name what kind
  it is: a CycloneDX-style SBOM (component graph, built for vulnerability
  and dependency-risk tracking) answers different questions than an
  SPDX-style one (license and provenance focus) — say which.
- Prefer SBOMs that carry the NTIA minimum fields (supplier, name, version,
  unique id such as PURL/CPE/hash, dependency relationship, SBOM author,
  timestamp).
- This document carries the judgment a generated file cannot; it does not
  restate the file's contents.

## Illustration

- **Form:** a Markdown table (criticality-ordered) is primary; a Mermaid
  `flowchart` only for an evidenced dependency map whose relationships
  matter beyond a flat list.
- **Renders:** the risk table, or (rarely) which services a critical
  dependency chains through.
- **Trigger:** the flowchart only when a dependency's blast radius spans
  more than one downstream system — per
  [`illustration.md`](../../../references/illustration.md)'s deep-dive budget.

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Direct dependencies/integrations, purpose, criticality, failure behavior | `reference/tech-stack` | tech-stack states what the repository is built with; this document adds the failure-framing judgment tech-stack omits |
| A dependency's known weakness or accepted risk | `tech-debt-register` or `security/threat-model`'s accepted-risk section | route by whether it's fixable (debt) or an accepted external risk (threat model), never both |
| A network boundary a dependency crosses | `network` | the trust-zone crossing is owned there; this document owns the dependency's criticality judgment |
