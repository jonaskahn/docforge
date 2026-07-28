---
{"docforge_provenance":{"sections":[]}}
---
# Dependencies and integrations

_Last reviewed: {{YYYY-MM-DD}}_

## Runtime dependencies

| Package | Purpose | Licence | Version | Criticality | If it disappeared |
|---|---|---|---|---|---|
| {{name}} | {{why it is here}} | {{licence}} | {{range}} | {{high/medium/low}} | {{replacement path and effort}} |

## Development dependencies

{{Summary rather than enumeration. Note anything unusual or licence-encumbered.}}

## External services

### {{Service name}}

- **Purpose:** {{what it does for us}}
- **Criticality:** {{hard — we fail without it | soft — degraded | optional}}
- **Authentication:** {{mechanism; where credentials come from}}
- **Data exchanged:** {{what leaves and enters, including any personal data}}
- **Limits:** {{rate limits, quotas, payload ceilings}}
- **Failure handling:** {{timeout, retries, circuit breaker, fallback behaviour}}
- **Contract:** {{API version pinned, deprecation notice period, SLA}}
- **Region:** {{where data is processed, if it matters}}

## Dependency policy

- **Criteria for adding one:** {{maintenance signals, licence compatibility,
  security history, whether existing dependencies already cover it}}
- **Who approves:** {{role}}
- **Review cadence:** {{how often this inventory is checked}}
- **Update policy:** {{automated patches, manual majors, CVE triage}}

## Generated inventory

The full machine-readable inventory (SBOM) is produced by the pipeline and
published at {{location}}. This document carries the judgement a generated file
cannot: rationale, criticality and failure behaviour.
