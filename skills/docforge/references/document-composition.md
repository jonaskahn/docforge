# Document composition

This file owns topic ownership, promotion, durability, and no-duplication.

## One owner per fact

Choose the document whose reader question naturally owns a fact, write it there
once, and link from every other view. Indexes summarize only enough to route.
Agent and audience views do not restate architecture, flow steps, configuration,
limitations, or glossary definitions.

## Atomic promotion

A flow or concept begins as one flat file. Promote it to
`<topic>/README.md` only in the same operation that writes at least one real
deep-dive sibling. Move the shared content into the README, update links, and
materialize the deep dive atomically. A folder containing only README is a
defect.

## Durability

Write at the slowest-changing useful layer:

- behavior and boundaries instead of private symbols;
- file/module paths instead of line numbers;
- observable contracts instead of implementation trivia;
- decision rationale in append-only records;
- volatile values in reference documents.

A behavior-preserving refactor should not falsify prose.

## Depth brake

Add depth when it changes a reader decision, implementation, diagnosis, review,
or risk judgment. Do not create another file merely because a taxonomy slot
could exist. Prefer the fewest documents that each hold a complete subject in a
single primary mode.
