# Dataset writing craft

- Open with the dataset's identity: what real-world or system entity it
  represents and the guarantee it exists to provide.
- Name every producer and every consumer explicitly.
- State schema ownership (which document or schema file is the source of
  truth for fields, so this document links rather than repeats them),
  freshness and retention (how current the data is guaranteed to be and how
  long it is kept), and failure/recovery (what happens on a bad write, a
  missed refresh, or a consumer reading stale data).
- Evidence every lineage claim — a table, a pipeline config, a schema file
  this document can point to.
- Never present a sample or a one-off observation as if it were a guarantee;
  a reference document's value is that every row can be trusted without
  re-verification.

## Illustration

- **Form:** a Markdown table for identity/producers/consumers/freshness; a
  Mermaid `erDiagram` only when durable relationships between this and other
  datasets need to be shown, not for the dataset's own field list.
- **Renders:** producer-to-dataset-to-consumer as a lookup row, or entity
  relationships when more than one dataset is involved.
- **Trigger:** an `erDiagram` only past two or more related datasets with a
  durable relationship — per
  [`illustration.md`](../../../references/illustration.md)'s reference-depth
  guidance.

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Dataset identity, producers, consumers, freshness, retention, failure/recovery | `data-flow` | data-flow traces movement and transformation; this document owns the dataset's own contract at rest |
| Schema fields | the owning schema/reference document | never repeat field definitions inline; name the owner and link |
| A known gap in lineage evidence | `tech-debt-register` | an unevidenced claim is a defect to fix, not a fact to assert here |

## Voice

- **Voice:** declarative present tense, strong active verbs, no hedging.
