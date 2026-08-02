# Profiles

Audience and repository-shape guides: what each profile changes about
selection, terminology, and reader expectations.

## Load this when

- Writing for a Business Analyst reader → [audience-business-analysts.md](audience-business-analysts.md)
- Writing for a Product Owner reader → [audience-product-owners.md](audience-product-owners.md)
- Writing for a coding-agent reader → [audience-coding-agents.md](audience-coding-agents.md)
- Writing for an operator → [audience-operators.md](audience-operators.md)
- Writing for a security reviewer → [audience-security-reviewers.md](audience-security-reviewers.md)
- Documenting an HTTP/gRPC/GraphQL service → [shape-api-service.md](shape-api-service.md)
- Documenting a browser-delivered application → [shape-web-app.md](shape-web-app.md)
- Documenting a published package or SDK → [shape-library-sdk.md](shape-library-sdk.md)
- Documenting a scheduled/ETL/streaming pipeline → [shape-data-pipeline.md](shape-data-pipeline.md)
- Documenting infrastructure-as-code or deployment orchestration → [shape-infrastructure-platform.md](shape-infrastructure-platform.md)
- Documenting a phone or tablet application → [shape-mobile-app.md](shape-mobile-app.md)
- Documenting a desktop application → [shape-desktop-app.md](shape-desktop-app.md)
- Documenting a command-line interface or terminal UI → [shape-cli-tui.md](shape-cli-tui.md)
- Documenting a game → [shape-game.md](shape-game.md)
- Documenting embedded or IoT firmware → [shape-embedded-iot.md](shape-embedded-iot.md)
- Documenting a blockchain smart-contract system → [shape-smart-contract.md](shape-smart-contract.md)

## Contents

- [audience-business-analysts.md](audience-business-analysts.md)
- [audience-product-owners.md](audience-product-owners.md)
- [audience-coding-agents.md](audience-coding-agents.md)
- [audience-operators.md](audience-operators.md)
- [audience-security-reviewers.md](audience-security-reviewers.md)
- [shape-api-service.md](shape-api-service.md)
- [shape-web-app.md](shape-web-app.md)
- [shape-library-sdk.md](shape-library-sdk.md)
- [shape-data-pipeline.md](shape-data-pipeline.md)
- [shape-infrastructure-platform.md](shape-infrastructure-platform.md)
- [shape-mobile-app.md](shape-mobile-app.md)
- [shape-desktop-app.md](shape-desktop-app.md)
- [shape-cli-tui.md](shape-cli-tui.md)
- [shape-game.md](shape-game.md)
- [shape-embedded-iot.md](shape-embedded-iot.md)
- [shape-smart-contract.md](shape-smart-contract.md)

## Boundaries

Canonical profile IDs, aliases, and detection signals live in
`.metadata/catalog/profiles/` (query via `query_catalog.{py,js} --profile`,
see [`../../runtime/catalog/README.md`](../../runtime/catalog/README.md)), not
here. These files own reader-facing guidance for a profile already selected;
they do not select documents themselves.

`engineers` and `beginners` intentionally use the default tier, depth, and
document contracts rather than dedicated packs: their catalog entries define
general questions but select no specialist document surface. Add a profile only
when a distinct audience owns a stable set of documents or evidence rules.
