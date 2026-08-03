# Observability writing craft

Ground signal names, sources, thresholds, routing, and ownership in
instrumentation, configuration, or operational evidence. Record absent telemetry
and unknown thresholds as blind spots; this document owns alert intent and links
each actionable alert to its runbook and escalation owner.

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); a table
of signal → source → alert intent is primary, prose for what's not covered.

Organize around the four golden signals for user-facing services — latency,
traffic, errors, saturation — and RED (rate/errors/duration) or USE
(utilization/saturation/errors) as the underlying discipline for services
versus resources respectively. State, per signal: what emits it, where it's
visible (dashboard, log, trace), who owns the alert, and what the alert
intent actually is — "page someone" versus "log for later" are different
severities and must read as different.

Correlation matters as much as the raw signal: state how a reader moves
from an alert to the request/trace that caused it. Close with blind spots
named honestly: what this system cannot currently observe, not just what
it can.
