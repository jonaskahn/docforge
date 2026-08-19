# `environments`

**Reader question** — "What actually differs between staging and production, and who controls each one's config?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | coverage-matrix |

Full coverage means every dimension that differs across environments has a row, environments as columns, so a reader can spot every difference in one scan.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Every dimension that differs (config, scale, data realism, service stubs), environments as columns | the matrix | an environment difference asserted with no configuration or CI-policy evidence |
| 2 | The promotion boundary: what must be true before a change moves to the next environment, and who owns the gate | the matrix | a promotion gate left unstated |
| 3 | Configuration ownership per environment: which team or system controls it | the matrix | unverified parity or gate behavior presented as fact instead of unknown |

## Keep out

| Not here | Lives in |
|---|---|
| Deployment procedure | the relevant `deployment` document |
| Configuration values themselves | `configuration` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Environment differences, promotion boundaries, configuration ownership | the relevant `deployment`/`runbook` documents | this document says what differs; deployment procedure is owned there |
| Configuration values themselves | `configuration` | this document owns which team controls config per environment, not the values or their schema |
