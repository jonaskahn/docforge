# Dependencies Inventory — Instruction Template

Craft guidance for writing `docs/architecture/dependencies.md`.
Content contract (must-present, keep-out, Diátaxis mode) and the NTIA SBOM minimum fields:
`references/document-catalog.md` → "architecture/dependencies.md" and `references/risk-docs.md`.
Depth: `references/depth-and-audience.md`.

## Purpose
Document external libraries and services, why the system depends on each, and how each fails.

## Data Requirements
- Knowledge graph (for import/use patterns)
- Direct inspection of manifests (package.json, pyproject.toml, go.mod, …)
- Dependency-registry lookups (for licence / status when needed)

## Template Structure
Organize by category (build tools, runtime libraries, services). Per dependency:
- Name and purpose (what feature it backs).
- Current version and constraint.
- Where it's used (modules/packages).
- Failure mode: what breaks if it fails.
- Fallback/mitigation: can it be swapped or degrade.
- Licence (SPDX) and compliance implication.

## Provenance Requirements
- Reference the package-manifest files for versions; link lock files rather than copying pins.
- Tag each use with the modules that import it (from the knowledge graph).
- Record the version source (lock file, git blob hash).

## Notes
- Include external services (cloud APIs, databases), not only libraries.
- The exhaustive machine list is the generated SBOM — this file is the human judgement layer;
  point to the SBOM rather than hand-enumerating transitive trees.
- For security-sensitive dependencies, reference SECURITY.md / security.txt.
