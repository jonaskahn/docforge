# Agent retrieval protocol

1. Read the active skill entrypoint (`docforge` or `docforge-revise`), then
   this cartridge’s [`rules.md`](rules.md) and [`flags.md`](flags.md).
2. Select the applicable workflow from
   [`workflows/README.md`](workflows/README.md).
3. For a document task, resolve it in one call (from this cartridge root):
   `python3 runtime/cli/python/query_catalog.py --route <document-id>`
   (or `node` / `bun` / `deno run -A` against
   `runtime/cli/js/query_catalog.js`; see
   [`runtime/catalog/README.md`](runtime/catalog/README.md)).
4. Read only what that call returns: the named workflow, the document
   definition, the contract, the optional instruction, and the template
   (only when materializing).
5. Load additional policy files only when the workflow links them for the
   current decision.
6. Never read an entire category directory. Never load every catalog record
   to answer a single-document question. Use `--category` only when
   choosing among documents, before an id is known.

The canonical machine contract is `.metadata/catalog/index.json` plus
per-document record files under `.metadata/catalog/documents/`, accessed
only through `runtime/cli/python/query_catalog.py` /
`runtime/cli/js/query_catalog.js`; prose explains that contract but never
replaces it.

Every command has a standard-library Python peer and a built-in-only JS
peer (node / bun / deno) with identical flags, JSON shapes, filesystem
effects, and exit codes. Unknown flags exit `2`. The agent locks one
engine for the session (see [`rules.md`](rules.md)). Full reference:
[`workflows/tools.md`](workflows/tools.md).
