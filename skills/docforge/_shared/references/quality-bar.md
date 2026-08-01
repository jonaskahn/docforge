# Quality bar

This file owns mechanical and whole-tree acceptance.

## Per-document mechanical checks

- no `{{...}}` scaffold marker or retired TODO punt;
- complete provenance-2.0 restricted YAML at byte one when supported, with
  concrete write metadata, valid source blobs, and heading-matched sections;
- valid, accessible illustrations that satisfy `illustration.md` when present;
- no dead relative links;
- no invented claims or untyped external unknowns;
- no links into Docforge’s internal `references/` directory;
- one primary mode and the catalog’s must-present/keep-out contract;
- required review date uses `_Last reviewed: YYYY-MM-DD_`;
- provider and forge neutrality outside their explicit integration references
  (vocabulary and confinement craft: [`host-neutrality.md`](host-neutrality.md)).

Mechanical success does not complete a document; the independent audit in
`document-audit.md` does.

## Whole-tree checks

1. **Manifest agreement:** active manifest paths exactly equal the planned
   scaffold paths; every expected file exists and no fake dynamic seed exists.
2. **Reachability:** every reader document is reachable from `docs/README.md`
   within two links; portfolio content is reachable from
   `docs-portfolio/README.md`.
3. **Onboarding:** a competent new contributor can reach a verified local run
   without asking a human.
4. **Location:** each fact is in the document whose reader question owns it.
5. **Reviewer:** risk, security, dependency, and diligence claims expose both
   evidence and uncertainty.
6. **Stranger:** terms, boundaries, failure behavior, and next links make sense
   without prior team lore.
7. **No duplication:** shared facts have one owner and other views link.
8. **Promotion integrity:** no flow or concept folder contains only README.

`scaffold_docs --audit` must exit nonzero on any mechanical defect and zero on
a clean tree. If a whole-tree correction changes one document, independently
audit that document again.
