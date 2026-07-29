# Infrastructure-apply / infrastructure-state writing craft

Covers `infra_apply` and `infra_state` — the plan/apply safety story and
the state-of-record story are two views of the same discipline and read
better together than duplicated.

**Preferred illustration:** Follow
[`../references/illustration.md`](../references/illustration.md); tables
for state ownership and locking, prose for drift and recovery.

State who or what may run apply, and what gate stands between plan and
apply (review, approval, CI check) — plan/apply safety means naming the
thing that stops an unreviewed change, not just describing the happy path.
For state: name where it lives, the locking mechanism that prevents
concurrent writers, and who owns it. State drift explicitly: how it's
detected, and what the recovery procedure is when actual infrastructure
diverges from recorded state — drift left undetected is the failure mode
this document exists to prevent.

Never include a credential or an unverified destructive command; every
apply-adjacent command shown here must be one a reader could safely run
against a real environment after reading the surrounding prose.
