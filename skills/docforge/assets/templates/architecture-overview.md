# Architecture

_Last reviewed: {{YYYY-MM-DD}}_

{{One paragraph: the problem this repository solves, at the highest level.}}

## Bird's eye view

{{Two or three paragraphs tracing how data and control move from input to output.
A reader should be able to draw the box diagram from this section alone.}}

```mermaid
flowchart LR
  A[{{input}}] --> B[{{stage}}]
  B --> C[{{output}}]
```

## Code map

### `{{path/to/module}}/`

{{What it does, in one to three sentences.}} Key types: `{{Type}}`, `{{Type}}`.

- **Boundary:** {{what crosses in and out, if this is a trust or API boundary}}
- **Invariant:** {{what is deliberately absent or enforced — e.g. "performs no I/O"}}

### `{{path/to/module}}/`

{{...}}

## Cross-cutting concerns

| Concern | Where it lives | Notes |
|---|---|---|
| Configuration | `{{path}}` | See [../reference/configuration.md](../reference/configuration.md) |
| Error handling | `{{path}}` | |
| Logging | `{{path}}` | |
| Authentication | `{{path}}` | |
| Persistence | `{{path}}` | |

## Invariants

Rules that hold across the whole repository. Most are absences, which is why they
cannot be inferred from reading the code.

- {{e.g. `core/` imports nothing from `adapters/`}}
- {{e.g. no module outside `config/` reads environment variables}}

## What is deliberately not here

{{Scope boundaries — what this repo does not do, and which component does it instead.}}

## Why it is like this

Rationale lives in [decisions/](decisions/README.md), not here.
