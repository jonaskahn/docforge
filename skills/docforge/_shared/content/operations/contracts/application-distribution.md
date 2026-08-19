# `application-distribution`

**Reader question** — "How does this application actually get built, signed, and published to each distribution channel?"

| Mode | Depth | Shape |
|---|---|---|
| How-to | deep-dive | entry-catalog |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Every channel in use (store, direct download, internal distribution), each its own entry | lead | one generic description that quietly only covers one channel |
| 2 | Per channel, in order: build, sign, package, publish, verify | per entry | a step given with no observable verification |
| 3 | Update and rollback given the same rigor as initial publish | per entry | rollback reduced to an afterthought |
| 4 | The role authorized to publish, revoke, or roll back each channel | per entry | an unverified claim about store approval timelines |

## Keep out

| Not here | Lives in |
|---|---|
| A signing key or secret | nowhere — name the mechanism, never the value |
| An unsupported store-policy claim | nowhere — external store policy and timing stay unknown unless evidenced |
| Deployment into runtime environments | `deployment` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Build, sign, package, publish, verify per channel; update and rollback | `deployment` | shipping into environments shares the same rigor and approval discipline |
