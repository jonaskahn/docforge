# Triggers and jobs

_Last reviewed: {{YYYY-MM-DD}}_

_Repeat per job or trigger — the `##` block below._

## {{Job name}}

**Trigger:** {{schedule / event / manual}}

**Payload:** {{shape}}

**Concurrency:** {{overlapping instances allowed? what happens if so}}

**Downstream effect:** {{what happens once it completes}}

**Owner:** {{team or role}}

Reliability detail (retry, idempotency, dead-letter): see
[job-reliability.md](job-reliability.md).
