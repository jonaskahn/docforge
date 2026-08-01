---
docforge_provenance:
  schema: "2.0"
  doc_id: "<DOC_ID>"
  path: "<DOCUMENT_PATH>"
  generated_at: "<GENERATED_AT>"
  generator:
    name: "docforge"
    version: "2.7.0"
  tier: "<TIER>"
  target_depth: "<TARGET_DEPTH>"
  graph:
    provider: "<GRAPH_PROVIDER>"
    flow: "<FLOW_CAPABILITY>"
  sections: []
---
# {{repo_name}}

> {{one_sentence_what_this_does_and_the_capability_it_delivers}}

**Status:** {{production|beta|experimental}} · **Owner:** <TEAM_OWNER> · **Support:** <SUPPORT_CHANNEL>

## What this is

{{Two or three sentences a non-engineer understands: the problem, the value, and
where this sits relative to the rest of the system.}}

## Quickstart

```bash
{{shortest path to a running instance}}
```

Full instructions: [docs/engineering/setup.md](docs/engineering/setup.md)

## Documentation

Everything lives in [`docs/`](docs/README.md). Start where you fit:

<!-- Prune any row pointing at a document this repo does not have. -->

| You are | Start here |
|---|---|
| New to the project | [docs/product/overview.md](docs/product/overview.md) |
| A new engineer | [docs/architecture/high-level.md](docs/architecture/high-level.md) |
| Using this as a consumer | [docs/product/quickstart.md](docs/product/quickstart.md) |
| Reviewing risk or security | [docs/security/](docs/security/README.md) · [docs/architecture/dependencies.md](docs/architecture/dependencies.md) |

## Known limitations

See [docs/reference/limitations.md](docs/reference/limitations.md). Read it before
building on this.

## Licence

{{licence}} — see [LICENSE](LICENSE).
