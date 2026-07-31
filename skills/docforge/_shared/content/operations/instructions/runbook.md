# Runbook writing craft

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md);
use a decision flowchart only when diagnosis has material branches.

Write for an operator under pressure. Start with the observable symptom, scope,
and safety boundaries, then give ordered diagnosis steps whose checks select the
next action. Make mitigations reversible where possible and place destructive or
high-impact actions behind explicit prerequisites. Each remediation ends with a
verification signal; state the escalation threshold, information to collect,
and prevention follow-up.

Do not substitute an architecture tutorial for incident action, assume access or
credentials, or present unverified commands as executable procedure. Link to
deployment or disaster recovery when those own the operation.
