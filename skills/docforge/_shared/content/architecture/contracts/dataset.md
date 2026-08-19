# `dataset`

**Reader question** — "What is this dataset, who produces and consumes it, and how fresh is it guaranteed to be?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | reference | lookup |

Identity is the key a reader looks this document up by; every other field reads as a fact about that one dataset.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Dataset identity: what real-world or system entity it represents, the guarantee it exists to provide | lead | a sample or one-off observation presented as a guarantee |
| 2 | Every producer and every consumer, named explicitly | L2 | a lineage claim with no table, pipeline config, or schema file evidencing it |
| 3 | Schema ownership: which document is the source of truth for fields | L2 | fields repeated instead of linked to the owning schema |
| 4 | Freshness and retention: how current the data is guaranteed to be, how long it's kept | L2 | freshness left unstated |
| 5 | Failure/recovery: bad write, missed refresh, consumer reading stale data | L2 | recovery behavior omitted |

## Keep out

| Not here | Lives in |
|---|---|
| A sample presented as a guarantee | nowhere |
| Movement and transformation detail | `data_flow` |
| Schema field definitions | the owning schema/reference document |
| A known lineage-evidence gap | `tech_debt` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Dataset identity, producers, consumers, freshness, retention, failure/recovery | `data_flow` | data-flow traces movement and transformation; this document owns the dataset's own contract at rest |
| Schema fields | the owning schema/reference document | never repeat field definitions inline; name the owner and link |
| A known gap in lineage evidence | `tech_debt` | an unevidenced claim is a defect to fix, not a fact to assert here |
