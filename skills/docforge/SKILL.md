---
name: docforge
description: Catalog-driven repository documentation with bounded graph-grounded retrieval, manifest 3.1, YAML provenance 2.0, independent audits, and equivalent Python/Node tools.
---

# Docforge

Docforge builds a durable documentation system from repository evidence. The
canonical machine contract is `.metadata/catalog/index.json` plus per-document
record files under `.metadata/catalog/documents/`, accessed only through
`scripts/query_catalog.{py,js}`; prose explains that contract but never
replaces it.

## Code-graph precondition

A code graph is required before any analysis or writing; run
`precheck_graph.{py,js} --need code`. A flow graph is required only when a
selected document lists `flow_graph` in `requires`; check with `--need flow`
before writing the first such document. Detail:
[`workflows/planning.md`](workflows/planning.md).

## Provider sufficiency rule

One readable `code_graph` is enough. Missing competing providers are normal
and must never appear in an intake, plan summary, or readiness table. One
ready provider is the proposed default; several ready providers are offered
as a choice; no ready provider gets an explained setup path. Detail:
[`workflows/intake.md`](workflows/intake.md),
[`references/graph/graph-sources.md`](references/graph/graph-sources.md).

## Safety boundaries

1. Do not invent. Derive every fact from a graph, source, manifest, history,
   existing documentation, or user-provided evidence. Reserve typed
   `<UPPER_SNAKE_CASE>` tokens for atomic external values only.
2. Build and show the plan before writing. `--auto-accept` skips
   conversational pauses, never planning, evidence checks, linting, audit,
   or safety approvals.
3. Write one document at a time, in catalog `write_order`.
4. Stamp provenance while writing (YAML provenance 2.0, byte one). Replace
   every scaffold token with concrete write metadata and source blobs.
5. A writer never marks its own artifact complete; mechanical lint is
   necessary but never sufficient.
6. State a fact once in its owning document; link to it elsewhere.
7. Generated prose stays provider-neutral and host-neutral.

## Invocation routing

- Bare `/docforge`, no task or flags → [`workflows/intake.md`](workflows/intake.md).
- A task with tier/profile/flags already given →
  [`workflows/planning.md`](workflows/planning.md), then
  [`workflows/writing.md`](workflows/writing.md) for each document.
- `--resume`, `--status`, `--revise all|<area>|flow` →
  [`workflows/revision.md`](workflows/revision.md).
- Staleness, migration, or a whole-tree/cross-document check →
  [`workflows/validation.md`](workflows/validation.md).

## Workflow files

| File | Owns |
|---|---|
| `workflows/intake.md` | Bare invocation, discovery gate, scope questions, confirmation, graph-provider choice |
| `workflows/planning.md` | Repository inspection, tier/profile selection, dynamic-document discovery, manifest init, dry-run tree, plan checkpoint |
| `workflows/writing.md` | Per-document execution card, evidence, scaffolding, provenance, status transitions, independent audit |
| `workflows/revision.md` | Resume, status, revise all/area/flow, flow-index organization |
| `workflows/validation.md` | Staleness, migration, whole-tree audit, cross-document quality gate |
| `workflows/tools.md` | Every public script: Python/Node invocation, inputs, outputs, exit codes |

See [`workflows/README.md`](workflows/README.md) to route an unfamiliar
invocation to exactly one file.

## Public commands

Every script has standard-library Python and built-in-only Node peers with
identical flags, JSON shapes, filesystem effects, and exit codes. Unknown
flags exit `2`. Full reference: [`workflows/tools.md`](workflows/tools.md).

```sh
python scripts/query_catalog.py --route <document-id>
```

## Agent retrieval protocol

1. Read this file.
2. Select the applicable workflow from
   [`workflows/README.md`](workflows/README.md).
3. For a document task, resolve it in one call:
   `python scripts/query_catalog.py --route <document-id>`.
4. Read only what that call returns: the named workflow, the document
   definition, the contract, the optional instruction, and the template
   (only when materializing).
5. Load additional policy files only when the workflow links them for the
   current decision.
6. Never read an entire category directory. Never load every catalog record
   to answer a single-document question. Use `--category` only when
   choosing among documents, before an id is known.

## Completion requirement

A document reaches `complete` only after mechanical lint and an independent,
artifact-only audit pass ([`workflows/writing.md`](workflows/writing.md)),
and the whole tree passes `scaffold_docs --audit` plus the cross-document
quality gate ([`workflows/validation.md`](workflows/validation.md),
[`references/quality-bar.md`](references/quality-bar.md)).

## Canonical ownership

- [`references/docs-tree.md`](references/docs-tree.md): paths, naming, tiers,
  placement.
- [`content/README.md`](content/README.md): must-present content, keep-out
  boundaries, mode, and depth — one contract per document type, routed by
  group.
- [`references/graph/`](references/graph/README.md): provider dispatch and
  selection.
- [`references/document-composition.md`](references/document-composition.md):
  topic ownership and no-duplication.
- [`references/provenance-tracking.md`](references/provenance-tracking.md):
  metadata format and staleness.
- [`references/document-audit.md`](references/document-audit.md): independent
  completion gate.
- [`references/quality-bar.md`](references/quality-bar.md): mechanical and
  whole-tree acceptance.
- [`references/host-neutrality.md`](references/host-neutrality.md): neutral
  vocabulary, forge-confinement.
- [`references/portfolio.md`](references/portfolio.md): cross-repository
  diligence.
- `content/<group>/instructions/`: document-specific writing craft only.
- `content/<group>/templates/`: output scaffolds only.

When a rule changes, update its owner and replace other repetitions with a
link.
