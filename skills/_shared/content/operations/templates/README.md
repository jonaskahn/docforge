# operations templates

Scaffold template files owned by the `operations` group.

## Contents

- `application-distribution.md` — Artifact, build, signing, packaging, channels, verification, update/rollback → [application-distribution.md](application-distribution.md)
- `deployment.md` — Environments, artifact path, rollout, rollback, verification → [deployment.md](deployment.md)
- `disaster-recovery.md` — Failure scenarios, recovery order, verification, data-loss boundary → [disaster-recovery.md](disaster-recovery.md)
- `flashing-recovery.md` — Prerequisites, artifact, connection, flashing, verification, rollback/recovery, safety → [flashing-recovery.md](flashing-recovery.md)
- `infrastructure-apply.md` — Plan/apply safety, external state, locking, ownership, resource inventory, drift, recovery → [infrastructure-apply.md](infrastructure-apply.md)
- `infrastructure-state.md` — Plan/apply safety, external state, locking, ownership, resource inventory, drift, recovery → [infrastructure-state.md](infrastructure-state.md)
- `job-reliability.md` — Retry, idempotency, timeout, backpressure, dead-letter, replay, observability → [job-reliability.md](job-reliability.md)
- `network-deployment.md` — Network configuration, keys/roles, deployment order, verification, upgrade/rollback → [network-deployment.md](network-deployment.md)
- `observability.md` — Signals, ownership, correlation, alert intent, blind spots → [observability.md](observability.md)
- `runbook.md` — Symptom, safety, diagnosis, remediation, verification, escalation → [runbook.md](runbook.md)

## Boundaries

Files here are referenced by exact path from catalog records (`.metadata/catalog/documents/operations/`); do not rename without updating the referencing record.
