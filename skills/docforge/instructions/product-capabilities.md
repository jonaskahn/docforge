# Product Capabilities — Instruction Template

Craft guidance for writing `docs/product/capabilities.md`.
Content contract (must-present, keep-out, Diátaxis mode): `references/document-catalog.md`
→ "product/capabilities.md — the feature catalog in business language". Depth: `references/depth-and-audience.md`.

## Purpose
Give a reference-style catalog of every capability the system provides, in business language, one
entry per capability.

## Data Requirements
- Domain graph (REQUIRED — hard gate, no fallback; see SKILL.md)

## Template Structure
- Group entries by domain or user journey; each group uses the same per-entry shape.
- Per capability: name in domain language (never a code symbol); what it does; the user/business
  outcome it enables; who uses it (role); the scenario it supports; status (GA/beta/deprecated) and
  edition gating where relevant.
- Cross-link each entry to its how-to and flow documents rather than restating their steps here.

## Provenance Requirements
- Tag each capability with its domain-graph nodes.
- Reference the implementing modules at module level (not file level).

## Notes
- This is the exhaustive feature list — distinct from `product/overview.md`, which stays a curated,
  narrative 2–5 use-case summary and links here rather than enumerating. Don't duplicate either
  direction.
- Never hand-type this list from route files or screen names — the domain graph is what surfaces a
  capability a writer would otherwise miss.
