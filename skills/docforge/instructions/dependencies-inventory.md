# Dependency-inventory writing craft

**Preferred illustration:** Follow
[`../references/illustration.md`](../references/illustration.md); the compact
risk table is primary, with a flowchart only for an evidenced dependency map
whose relationships matter.

Lead with a compact risk-oriented table, ordered by criticality — the dependency whose
failure or removal would hurt most goes first, not the alphabetically first package. Give
short integration notes only for dependencies whose failure or replacement changes system
behavior; a pinned linting tool doesn't need a paragraph.

Group by runtime library, external service, build/tooling, and generated inventory. Keep
versions and licenses scannable in the table; keep judgment — criticality, failure handling,
replacement effort — in prose beside it, not squeezed into a table cell. When pointing to
the generated machine-readable inventory, name what kind it is: a CycloneDX-style SBOM
(component graph, built for vulnerability and dependency-risk tracking) answers different
questions than an SPDX-style one (license and provenance focus) — say which, so a reader
knows what the generated file can and can't tell them. This document carries the judgment a
generated file cannot; it does not restate the file's contents.
