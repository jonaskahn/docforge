# Quality bar

This file owns mechanical and whole-tree acceptance.

## Per-document mechanical checks

- no `{{...}}` scaffold marker or retired TODO punt;
- complete current-schema provenance in the document's folder sidecar, with
  concrete write metadata, valid source blobs, and heading-matched sections;
- valid, accessible illustrations that satisfy `illustration.md`: a document
  carries a diagram of **each** view its type declares, checked by form
  (mechanical `illustration coverage` defect in `scaffold_docs --audit`; a view
  marked `required: false` is evidence-conditional and never demanded);
- no illustration that answers no question of its own: a diagram with fewer
  than three meaningful elements is a `decorative illustration` defect, and one
  with no explanatory sentence beside its fence is an `undescribed
  illustration` defect — the prose is the only content a screen reader gets;
- no visible source-path `:line` or `#L<n>` citations in prose outside
  fences (mechanical `visible-source-line` defect); a source link is a
  commit-pinned permalink built from the declared `project.repository` base,
  never the unexpanded authoring form (mechanical `unpinned-source-link`
  defect) and never with a path as its visible text;
- no dead relative links;
- no invented claims or untyped external unknowns;
- no links into Docforge's internal `references/` directory;
- one primary mode, the shape its record declares
  ([`document-shapes.md`](document-shapes.md)), and every numbered row of its
  contract's `Must present` and `Keep out` tables;
- agent-context outputs contain no documentation references of any kind:
  Markdown links, URLs, `@` imports, peer-agent or human-document references,
  and bare generated-document paths are all defects; plain source/configuration
  paths and verified commands are allowed;
- generated non-agent documents never link or mention an agent-context output;
  the gate reports that direction as `agent-context leak` and a forbidden
  reference emitted by an agent output as `agent-context outbound`;
- section READMEs additionally: open with a self-introduction (what, why, for
  whom), state scope and boundaries, offer a start-here reading path, link
  every selected and materialized direct child **outside the agent-context
  group** with the reader question it answers, and state an honest empty state
  when no child is evidenced — never a placeholder row; they never navigate
  readers into source files;
- required review date uses `_Last reviewed: YYYY-MM-DD_`;
- provider and forge neutrality outside their explicit integration references
  (vocabulary and confinement craft: [`host-neutrality.md`](host-neutrality.md)).

Mechanical success does not complete a document; the independent audit in
`document-audit.md` does. Voice, level discipline
([`progressive-disclosure.md`](progressive-disclosure.md)), and shape
discipline ([`document-shapes.md`](document-shapes.md)) are judged there, not
here — no script can tell an L1 section that sprouted L2 detail from one written
at the right altitude, or a document that quietly abandoned its shape's travel
order partway through.

## Whole-tree checks

1. **Manifest agreement:** active manifest paths exactly equal the planned
   scaffold paths; every expected file exists and no fake dynamic seed exists.
2. **Reachability:** every human-facing reader document is reachable from
   `docs/README.md` within two links; portfolio content is reachable from
   `docs-portfolio/README.md`. Agent-context outputs are intentionally outside
   this link graph and are not linked from any generated document, including
   each other. The two root kernels are complete self-contained duplicates
   rather than a redirect chain.
3. **Onboarding:** a competent new contributor can reach a verified local run
   without asking a human.
4. **Location:** each non-agent fact is in the document whose reader question
   owns it; each agent output contains the facts its own question needs.
5. **Reviewer:** risk, security, dependency, and diligence claims expose both
   evidence and uncertainty.
6. **Stranger:** terms, boundaries, and failure behavior make sense without
   prior team lore; human-facing documents also provide useful next links.
7. **No duplication:** shared non-agent facts have one owner and other
   non-agent views link. Self-contained agent-context duplication is allowed.
8. **Promotion integrity:** no collection folder contains only a README. This
   covers the collection root itself, not just its family subfolders —
   `docs/architecture/concepts/`, `docs/architecture/decisions/`,
   `docs/architecture/contracts/`, `docs/operations/runbooks/`,
   `docs/product/migrations/`, `docs-portfolio/epics/`, and
   `docs-portfolio/decisions/`. In standard layout such an index is not
   selected at all until one of its dynamic children is seeded, so an
   index-only collection folder means a stale or hand-edited manifest.
   `docs/flows/` is the one exception: its index is a discovery report that
   also records deferred, placeholder, and skipped candidates, so it earns its
   place with no promoted flow; its family subfolders are still covered.
9. **Section cohesion:** in any section folder holding two or more
   non-router documents, no document is an island — each either links a
   sibling or is linked by one. The section README alone does not satisfy
   it. Applies to non-agent documents only; agent-context outputs are
   excluded exactly as they are from routing.
10. **Declared illustration coverage:** every written non-agent document
    carries a diagram of each view its manifest entry declares in
    `illustration_views`, matched by form, so the one question each view exists
    to answer is actually answered. A type declaring no views falls back to
    `dominant_form`: anything other than `table` or `null` requires at least
    one `mermaid` or structural `text` fence. Count follows declared
    obligations, never document length.
11. **Fact-map agreement:** for every row of
    [`../content/fact-map.md`](../content/fact-map.md), the owner's contract
    claims the fact class in its `Owns / links` table, and every contested
    type's `Keep out` table routes that fact to the owner.

`scaffold_docs.{py,js} --audit` must exit nonzero on any mechanical defect and
zero on a clean tree. If a whole-tree correction changes one document,
independently audit that document again.
