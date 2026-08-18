# Observability

_Last reviewed: {{YYYY-MM-DD}}_

## Signals

| Signal | Source | Visible in | Owner | Alert intent |
|---|---|---|---|---|
| Latency | {{source}} | {{dashboard/log/trace}} | {{owner}} | {{page / log-only}} |
| Traffic | {{source}} | {{...}} | {{owner}} | {{...}} |
| Errors | {{source}} | {{...}} | {{owner}} | {{...}} |
| Saturation | {{source}} | {{...}} | {{owner}} | {{...}} |

## Correlation

{{How a reader moves from an alert to the request or trace that caused it.}}

```mermaid
%% The path an on-call engineer actually walks, in order. Name the tool or field
%% that carries each hop -- a correlation id, a trace id, a log query.
accTitle: From alert to root cause
accDescr: {{One sentence: which signal fires first, and which identifier links each hop to the next.}}
flowchart LR
  Alert["{{alert · source}}"] -->|"{{carries: {{identifier}}}}"| Dashboard["{{dashboard or query}}"]
  Dashboard -->|"{{carries: {{identifier}}}}"| Trace["{{trace or request}}"]
  Trace -->|"{{carries: {{identifier}}}}"| Logs["{{service logs}}"]
```

{{One or two sentences: which identifier survives every hop, and where the chain
breaks today. A hop with no shared identifier is a blind spot — record it below.}}

## Blind spots

{{What this system cannot currently observe.}}
