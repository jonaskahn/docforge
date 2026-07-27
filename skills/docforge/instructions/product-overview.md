# Product Overview — Instruction Template

Craft guidance for writing `docs/product/overview.md`.
Content contract (must-present, keep-out, Diátaxis mode): `references/document-catalog.md`
→ "product/overview.md". Depth: `references/depth-and-audience.md`.

## Purpose
Describe what the system does from the business perspective.

## Data Requirements
- Domain graph (REQUIRED — hard gate, no fallback; see SKILL.md)
- Knowledge graph (optional — only if architecture context is needed for a link-out; not a
  requirement for this document)

## Template Structure
- Lead with a 1–2 sentence summary of what the system is to the business.
- Organize capabilities by domain (domains come from the domain graph).
- Per domain: the problem it solves and the capabilities that enable it.
- Use business terminology from the domain graph, never code names or internal jargon.

## Provenance Requirements
- Tag each capability with its domain-graph nodes.
- Reference the implementing modules at module level (not file level).
- Record git blob hashes of the core business logic behind each capability.

## Notes
- This is business narrative, not a feature matrix. The exhaustive feature list lives in the
  capabilities catalog (see its catalog entry) — cross-link, don't duplicate.
