# Job reliability

_Last reviewed: {{YYYY-MM-DD}}_

| Job class | Retry | Idempotency | Timeout | Backpressure | Dead-letter | Replay |
|---|---|---|---|---|---|---|
| {{class}} | {{count + backoff}} | {{mechanism or "none"}} | {{value + on-timeout behavior}} | {{behavior}} | {{destination}} | {{procedure}} |

The table above is the per-class reference; the diagram below answers the
different question a reader has at 3am — where does a failing unit of work end
up, and can it come back?

```mermaid
%% States a unit of work occupies, not the steps of any one job. A terminal
%% state with no exit is the one to name explicitly in prose.
stateDiagram-v2
  accTitle:Retry and recovery states for a unit of work
  accDescr: {{One sentence: which states a failing job moves through and which state it cannot leave without intervention.}}
  [*] --> Queued
  Queued --> Running: {{claimed}}
  Running --> Done: {{success}}
  Running --> Retrying: {{retryable failure}}
  Retrying --> Running: {{within retry budget}}
  Retrying --> DeadLetter: {{budget exhausted}}
  DeadLetter --> Queued: {{operator replay}}
  Done --> [*]
```

{{One or two sentences: which state a stuck item actually rests in, what moves
it out, and whether anything is left partially applied on the way. If a claimed
item can never be reclaimed, say so here — that is the failure operators hit.}}

Job identity and triggers: see
[triggers-and-jobs.md](triggers-and-jobs.md).
