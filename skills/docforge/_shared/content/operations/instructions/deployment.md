# Deployment writing craft

Ground artifact source, environment commands, rollout behavior, and verification
in manifests, CI, deployment configuration, or source. For rollout and rollback,
name the authorized role and approval or escalation boundary; link incident
diagnosis to its runbook or disaster-recovery owner.

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); prose and
commands per environment, a flowchart only if promotion order across three
or more environments is otherwise ambiguous.

One verified path per environment: artifact source, rollout mechanism,
and rollback — in that order, since rollback is not optional detail. State
the rollout strategy plainly (blue-green, canary, rolling) because it
determines what "in progress" looks like to an on-call reader. Follow every
step with its verification signal — the exact check a reader runs before
calling the deploy done — the same discipline setup-guide.md uses for local
installs.

Keep incident procedures out; a deploy document tells you how to ship
safely, not how to recover from a bad one — that's
[disaster-recovery.md](disaster-recovery.md) or the relevant runbook. State
environment differences by reference to
[environments.md](environments.md) rather than re-deriving them here.
