# Dependency-inventory writing craft

**Preferred illustration:** Follow
[`../references/illustration.md`](../references/illustration.md); the compact
risk table is primary, with a flowchart only for an evidenced dependency map
whose relationships matter.

Lead with a compact risk-oriented table, ordered by criticality — the dependency whose
failure or removal would hurt most goes first, not the alphabetically first package. Keep an
"if it disappeared" column (or equivalent prose): it forces concentration-risk assessment
that a plain package list hides. Always include licence for every direct dependency — a
copyleft surprise in a proprietary product is the kind of finding that stops a review.
Give short integration notes only for dependencies whose failure or replacement changes
system behavior; a pinned linting tool doesn't need a paragraph.

Group by runtime library, external service, build/tooling, and generated inventory. Keep
versions and licenses scannable in the table; keep judgment — criticality, failure handling,
replacement effort — in prose beside it, not squeezed into a table cell. Automate the
exhaustive inventory; hand-write only direct dependencies and assessment. When pointing to
the generated machine-readable inventory, name what kind it is: a CycloneDX-style SBOM
(component graph, built for vulnerability and dependency-risk tracking) answers different
questions than an SPDX-style one (license and provenance focus) — say which, so a reader
knows what the generated file can and can't tell them. Prefer SBOMs that carry the NTIA
minimum fields (supplier, name, version, unique id such as PURL/CPE/hash, dependency
relationship, SBOM author, timestamp). This document carries the judgment a generated file
cannot; it does not restate the file's contents.
