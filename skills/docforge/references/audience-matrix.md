# Audience matrix — isolation, combination, ownership

Purpose: decide which folder a fact lives in when more than one audience could plausibly want it, and when to generate audiences together versus separately.

## Why BA and PO are separate overlays, not one

Business Analyst and Product Owner get conflated because both sit "between business and engineering," but they answer different questions and read documents in a different order:

| Question | BA | PO |
|---|---|---|
| What does the business rule precisely say? | Yes — primary artifact | No — cares that it exists, not its exact logic |
| Why does this requirement exist, with traceability to a stakeholder ask? | Yes | Only at epic level |
| Is this feature worth building, has it paid off? | No | Yes — primary question |
| What ships next, and in what order? | No | Yes |
| What can a customer expect right now, in plain language? | No (that's `product/overview.md`) | Yes, framed as release notes |

Treat them as genuinely separate readers with separate document sets. One "business" folder written for an average of both readers serves neither well.

## Isolated generation (default)

Whenever the request names one audience, produce only that overlay's folder. Do not create the other, do not stub it with placeholders, and reference it only in a single closing line of the produced folder's `README.md`: "If Product Owner documentation is also needed, see `../product-owner/`."

## Combined generation

Trigger only on an explicit multi-audience request — "docs for BA and PO," "align documentation for the whole product team." When combining:

1. Build both folders in full.
2. Assign single ownership for every fact both audiences need, using the table below, and cross-link the non-owning folder to it. Never paste the same paragraph into both.

| Fact | Owner | Cross-link from |
|---|---|---|
| Business rule definition (the exact logic — thresholds, eligibility conditions) | BA `business-rules.md` | PO `feature-catalog.md` links to the rule; does not restate it |
| Feature exists and what it is for | PO `feature-catalog.md` | BA `requirements-traceability.md` links to the feature it traces to |
| Domain term definition | `docs/reference/glossary.md` (spine) | Both BA and PO link here; neither restates a definition |
| Process/flow steps and decision points | BA `process-flows.md` | PO `feature-catalog.md` links for readers who want the mechanics |
| Success metric / KPI target | PO `success-metrics.md` | BA doesn't need this — omit, don't cross-link |
| Roadmap timing | `docs/product/roadmap.md` (spine) | PO `product-owner/README.md` links; does not duplicate the dated table |

3. Combined mode still produces two separate provenance manifest entries — combination governs prose cross-linking only, never provenance tracking. See `provenance-tracking.md`.

## Where the folders sit

```
docs/product/
├── overview.md              spine — unchanged by the audience overlays
├── capabilities.md          spine — unchanged by the audience overlays
├── roadmap.md               spine — unchanged by the audience overlays
├── business-analyst/        BA overlay
│   ├── README.md
│   ├── business-rules.md
│   ├── process-flows.md
│   └── requirements-traceability.md
└── product-owner/           PO overlay
    ├── README.md
    ├── feature-catalog.md
    ├── success-metrics.md
    └── release-notes.md
```

Both are subject-area folders — singular names, consistent with docforge's own naming rule: `business-analyst/`, not `business-analysts/` or the internal shorthand `ba/` a new reader won't recognize on sight.

## Deciding whether a repo needs these overlays at all

Build the **BA overlay** when the codebase encodes non-trivial business logic — validation rules, approval thresholds, eligibility conditions, pricing or discount logic — that a non-engineer would otherwise have to read source to find.

Build the **PO overlay** when the repo ships user-facing features with an independent release lifecycle (planned → building → shipped → deprecated) that someone actively plans against.

Skip either overlay, and say so explicitly, when the repo is pure infrastructure or a library with no embedded business logic and no independent release cadence — an unrequested, empty overlay is the same anti-pattern as an unfilled scaffold.
