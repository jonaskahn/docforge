<!-- Prune every row below that points at a document this repo does not have.
     A router with dead links is worse than a short one. -->

# Documentation

{{One line: what this repository is.}}

## By audience

| You are | Read |
|---|---|
| New to the project | [product/overview.md](product/overview.md) |
| A new engineer | [architecture/high-level.md](architecture/high-level.md) → [engineering/setup.md](engineering/setup.md) |
| Consuming this service | [product/quickstart.md](product/quickstart.md) → [reference/](reference/README.md) |
| On call | [operations/](operations/README.md) |
| Reviewing risk | [security/](security/README.md) · [architecture/dependencies.md](architecture/dependencies.md) · [reference/limitations.md](reference/limitations.md) |
| Contributing | [contributing/](contributing/README.md) |

## By folder

| Folder | Contents |
|---|---|
| [product/](product/) | What this does and why it exists — business language |
| [architecture/](architecture/) | How it is built, and why — code map, flows, decisions, dependencies |
| [engineering/](engineering/) | Setup, testing, conventions, release |
| [operations/](operations/) | Deployment, observability, runbooks |
| [reference/](reference/) | Configuration, limitations, errors, glossary |
| [security/](security/) | Threat model, data handling, disclosure |
| [contributing/](contributing/) | How changes get proposed, reviewed and merged |

## Conventions

- Documents that go stale carry a `_Last reviewed:_` line.
- Reference material is generated where a machine-readable source exists; generated
  files say so and name the regeneration command.
- Documentation is host-neutral: forge-specific detail lives only in
  [contributing/README.md](contributing/README.md).
