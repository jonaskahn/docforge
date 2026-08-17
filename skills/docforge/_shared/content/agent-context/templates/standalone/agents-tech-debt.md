# Tech debt (agent view)

<!-- Standalone: no human debt register exists to link. Own only what is
     mechanically observable in the source. If nothing qualifies, say so in two
     lines — an honest empty state beats an invented register. -->

## Editing hazards

{{one row per observed hazard; omit the table entirely when the repository has none}}

| Path | Hazard | Do not |
|---|---|---|
| `{{durable path}}` | {{marker or signal actually present: TODO / FIXME / HACK / DEPRECATED, a lint or format exclusion, a generated or vendored directory}} | {{what an agent must not "fix" incidentally}} |

## Complexity hotspots

{{when a code graph is available, the few highest-complexity modules an agent
  should read before editing; otherwise omit this heading}}
