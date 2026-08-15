# {{Epic title}}

_Last reviewed: {{YYYY-MM-DD}}_

## Outcome

{{What this cross-repo initiative delivers when done.}}

## Member repos

| Repo | Owning flow / feature | Component touched |
|---|---|---|
| {{repo}} | {{flow or feature link}} | {{component}} |

## Cross-repo sequence

```mermaid
sequenceDiagram
  participant A as {{repo_a}}
  participant B as {{repo_b}}
  participant C as {{repo_c}}
  A->>B: {{handoff}}
  B->>C: {{handoff}}
  C-->>A: {{outcome}}
```

## Open gaps

| Gap | Why it matters | Owner token |
|---|---|---|
| {{gap}} | {{impact}} | {{owner}} |
