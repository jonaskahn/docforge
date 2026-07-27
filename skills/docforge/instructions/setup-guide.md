# Setup Guide — Instruction Template

Craft guidance for writing `docs/engineering/setup.md`.
Content contract (must-present, keep-out, Diátaxis mode — Tutorial, one guaranteed happy path):
`references/document-catalog.md` → "engineering/setup.md — zero to running".
Depth: `references/depth-and-audience.md`.

## Purpose
Take a developer from a clean machine to a running instance via one ordered, forkless path.

## Data Requirements
- Direct inspection (run every setup step yourself first)
- Manifests / package files for exact version constraints
- Knowledge graph (optional)

## Template Structure
- Lead with: "This guide sets up [system] for [purpose]" and a wall-clock time estimate.
- Prerequisites with exact versions (from the manifests).
- Numbered install steps with exact shell commands — no pseudo-code, no forks. Per step: what it
  does and the expected result.
- A verification section showing a visible expected result ("you should see X").
- A bounded troubleshooting list of failures that actually happened.

## Provenance Requirements
- Reference the config/manifest files (pyproject.toml, package.json, …) behind each version.
- Record which scripts or manual steps you ran and confirmed working.

## Notes
- This is a primary onboarding document — invest in clarity and test every command before writing it.
- Show secrets as environment-variable examples; never store a real value.
- Spell out repo root or use $HOME / $(pwd); no bare relative paths.
