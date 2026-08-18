# Triggers and jobs

_Last reviewed: {{YYYY-MM-DD}}_

{{One paragraph: what kinds of work run in the background here, and what a
reader is usually trying to find out — why work did or did not run.}}

```mermaid
%% Group by trigger family (schedule, event, queue drain), not one node per job.
%% Split into a second diagram per family rather than growing this one.
flowchart LR
  accTitle:Trigger to job to downstream effect
  accDescr: {{One sentence: which trigger kinds start which job families, and what each produces.}}
  Schedule["{{trigger · schedule}}"] -->|"{{starts}}"| JobA["{{job family}}"]
  Event["{{trigger · event}}"] -->|"{{starts}}"| JobB["{{job family}}"]
  JobA -->|"{{writes}}"| Effect["{{downstream effect}}"]
  JobB -->|"{{writes}}"| Effect
```

{{One or two sentences: which trigger fires most often, and which job's failure
is most visible. The per-job detail below is the reference; this view is the map.}}

_Repeat per job or trigger — the `##` block below._

## {{Job name}}

**Trigger:** {{schedule / event / manual}}

**Payload:** {{shape}}

**Concurrency:** {{overlapping instances allowed? what happens if so}}

**Downstream effect:** {{what happens once it completes}}

**Owner:** {{team or role}}

Reliability detail (retry, idempotency, dead-letter): see
[job-reliability.md](job-reliability.md).
