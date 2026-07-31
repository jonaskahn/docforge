# Error-catalog writing craft

**Preferred illustration:** Use an error-envelope table followed by a catalog
and status summary; no diagram is needed.

Document the stable response envelope once, emphasizing which fields clients may
branch on and which are human-facing or additive. Give every machine-readable
code a stable anchor, trigger, observable status or category, safe client
behavior, retry conditions, and correlation or observability guidance. Close
with a status-level summary so consumers can survey the complete failure surface.

Never expose stack traces, internal exception names, secrets, or a retryable
claim unsupported by the actual behavior. Treat a renamed code or changed error
meaning as a compatibility change, not prose cleanup.
