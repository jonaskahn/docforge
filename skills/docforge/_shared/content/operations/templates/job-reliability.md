# Job reliability

_Last reviewed: {{YYYY-MM-DD}}_

| Job class | Retry | Idempotency | Timeout | Backpressure | Dead-letter | Replay |
|---|---|---|---|---|---|---|
| {{class}} | {{count + backoff}} | {{mechanism or "none"}} | {{value + on-timeout behavior}} | {{behavior}} | {{destination}} | {{procedure}} |

Job identity and triggers: see
[triggers-and-jobs.md](triggers-and-jobs.md).
