# System context

_Last reviewed: {{YYYY-MM-DD}}_

```mermaid
flowchart LR
  Member1["{{member repo}}"] -->|"{{coupling type}}"| Shared["{{shared service}}"]
  Member2["{{member repo}}"] -->|"{{coupling type}}"| Shared
  Shared --> External["{{external system}}"]
  Infra["{{infrastructure-platform member}}"] -->|"provisions-for / deploys-into"| Member1
```

{{One paragraph: what the portfolio borders and how members relate.}}

## Cross-repo flows

| Trigger | Repos involved | Outcome | Owning flow |
|---|---|---|---|
| {{trigger}} | {{repos}} | {{outcome}} | {{link to owning repo's flow doc}} |

## Dependency edges

| Repo | Depends on | Coupling type | Resolution |
|---|---|---|---|
| {{repo}} | {{sibling repo}} | {{shared library / API contract / event schema / provisions-for / deploys-into}} | {{mapping / heuristic}} |
