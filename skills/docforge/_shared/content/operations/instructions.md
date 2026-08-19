# Operations writing craft

Writing-craft instructions for `operations` group documents. Routes:

- `distribution` → [Application-distribution](#application-distribution-writing-craft)
- `deployment` → [Deployment](#deployment-writing-craft)
- `infra_disaster_recovery` → [Disaster-recovery](#disaster-recovery-writing-craft)
- `flashing_recovery` → [Flashing-recovery](#flashing-recovery-writing-craft)
- `infra_apply`, `infra_state` → [Infrastructure-apply / infrastructure-state](#infrastructure-apply--infrastructure-state-writing-craft)
- `worker_reliability` → [Job-reliability](#job-reliability-writing-craft)
- `network_deployment` → [Network-deployment](#network-deployment-writing-craft)
- `observability` → [Observability](#observability-writing-craft)
- `runbook` → [Runbook](#runbook-writing-craft)

## Voice and linking craft

Voice for this group is owned by [`voice.md`](../../references/voice.md):
imperative and runnable, every step has an observable result. Name what a
linked document owns before the link ("recovery from a bad deploy is owned
there," never "see `disaster-recovery`"). What each side of a link owns,
and why it is linked rather than restated, is each contract's
`## Owns / links` table, not this section.

## Application-distribution writing craft

Derive build, signing mechanism, package format, channel eligibility, and update
behavior from manifests, CI, release configuration, or history. Name the role
authorized to publish, revoke, or roll back each channel; external store policy
and timing remain unknown unless evidenced.

One verified path from artifact to installed application: build, sign,
package, publish to channel, verify — in that order. Name every channel
in use (store, direct download, internal distribution) and what differs
about the procedure per channel, rather than one generic description that
quietly only covers one.

Give update and rollback the same rigor as initial publish. Never include
a signing key, secret, or unverified claim about store approval timelines
the repository doesn't evidence.

## Illustration

- **Form:** prose steps with command blocks.
- **Renders:** the verified path — build, sign, package, publish to channel,
  verify — per channel.
- **Trigger:** never — ordered steps and verification, not a diagram, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Deployment writing craft

Ground artifact source, environment commands, rollout behavior, and verification
in manifests, CI, deployment configuration, or source. For rollout and rollback,
name the authorized role and approval or escalation boundary; link incident
diagnosis to its runbook or disaster-recovery owner.

One verified path per environment: artifact source, rollout mechanism,
and rollback — in that order. State the rollout strategy plainly
(blue-green, canary, rolling). Follow every step with its verification
signal — the exact check a reader runs before calling the deploy done —
the same discipline `setup-guide` uses for local installs.

Keep incident procedures out; a deploy document tells you how to ship
safely, not how to recover from a bad one — that's
[Disaster-recovery](#disaster-recovery-writing-craft) or the relevant runbook. State
environment differences by reference to
`environments` rather than re-deriving them here.

## Illustration

- **Form:** prose and command blocks per environment; a Mermaid `flowchart`
  only if promotion order across three or more environments is otherwise
  ambiguous.
- **Renders:** artifact source, rollout mechanism, rollback, and the
  verification signal per environment.
- **Trigger:** only when promotion order across three or more environments
  cannot be read as prose, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Disaster-recovery writing craft

For each scenario, name recovery lead, escalation authority, and the role
authorized to approve failover, restore, or destructive action. Ground RTO, RPO,
recovery order, and data-loss boundary in backup, test, or incident evidence;
label untested paths and unknown objectives explicitly.

State RTO (how long recovery may take) and RPO (how much data loss is
acceptable) per scenario, as numbers, not aspirations. Give explicit stop
conditions: what state means "recovery is failing, escalate" versus "keep
going." Order recovery steps by dependency, not by convenience; a
downstream service brought up before its data store is not actually
recovered.

Every scenario ends the same way: a verification step that proves recovery
succeeded, not just that the commands ran. State the data-loss boundary
explicitly — the exact point in time data recovers to — rather than
implying "nothing was lost." Keep ordinary deploy steps out; this document
is for the day deployment already failed.

## Illustration

- **Form:** prose with an ordered command list.
- **Renders:** per scenario — RTO/RPO as numbers, recovery order, stop
  conditions, the closing verification step.
- **Trigger:** never — this is a runbook shape, not a diagram, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Flashing-recovery writing craft

Before flashing, identify the evidenced artifact version, target hardware or
revision, integrity or compatibility check, and source location. Put a
confirmation checkpoint immediately before erase, overwrite, or irreversible
actions, and name the recovery authority and escalation owner.

State prerequisites and required hardware/connection state before the
first command. Give one verified path: connect, flash, verify — with the
exact success signal after flashing, not just "wait for it to finish."
Give the recovery path (what to do if flashing fails mid-way) the same
rigor as the happy path.

Never include an unverified destructive command. Where a step is
irreversible or risks hardware damage, state that plainly immediately
before the command, not buried in a general safety note at the top.

## Illustration

- **Form:** prose steps with command blocks and inline warnings.
- **Renders:** prerequisites, the verified connect → flash → verify path, and
  the mid-flash recovery path.
- **Trigger:** never — ordered steps, explicit warnings, no diagram, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Infrastructure-apply / infrastructure-state writing craft

Covers `infra_apply` and `infra_state` — the plan/apply safety story and
the state-of-record story are two views of the same discipline and read
better together than duplicated.

State who or what may run apply, and what gate stands between plan and
apply (review, approval, CI check). For state: name where it lives, the
locking mechanism that prevents concurrent writers, and who owns it. State
drift explicitly: how it's detected, and what the recovery procedure is
when actual infrastructure diverges from recorded state.

Never include a credential or an unverified destructive command; every
apply-adjacent command shown here must be one a reader could safely run
against a real environment after reading the surrounding prose.

`infra_apply` owns the authorized actor, gate, preflight, approved artifact,
execution boundary, and abort condition. `infra_state` owns backend, locking,
state owner, drift detection, and recovery. Resource inventory and access grants
belong to their reference documents. Show a command only with its environment,
mutability, prerequisites, expected result, and safe failure behavior; otherwise
link to the authoritative tool procedure instead of inventing a runnable path.

## Illustration

- **Form:** Markdown tables for state ownership and locking; prose for drift
  and recovery.
- **Renders:** who may run apply, the plan→apply gate, where state lives, how
  drift is detected and recovered.
- **Trigger:** never — tables and prose, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Job-reliability writing craft

For every job class, identify failure, lag, or queue signals, their visibility,
alert owner, and correlation identifier; link shared inventories instead of
copying them. Ground retry, timeout, backpressure, dead-letter, and replay in
configuration or code, and require an authorized replay role plus integrity check.

State each reliability property as a concrete fact, not a category label:
retry count and backoff shape, not "retries"; the exact idempotency key or
mechanism, not "idempotent"; the timeout value and what happens on
timeout, not "times out." A job with no stated idempotency mechanism that
also retries is a duplicate-side-effect risk — say so plainly if that's the
actual state, rather than implying safety that isn't there.

State the dead-letter and replay path together: where failed jobs land,
and the actual procedure to replay them. Link job definitions
to `triggers-and-jobs` rather than restating
trigger/payload detail here; this document owns failure handling, not
job identity.

## Illustration

- **Form:** a Markdown table per job class.
- **Renders:** one row per job class — retry, idempotency, timeout,
  backpressure, dead-letter, replay — the table is the whole document.
- **Trigger:** never — the table is the whole document, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Network-deployment writing craft

Ground network identity, RPC/configuration source, deployed artifact and version,
address, and role assignment in deployment configuration, manifests, or verified
history. For deploy, upgrade, and rollback, state approving authority and the
confirmation boundary; never infer account or multisig control.

Write one verified path per target network (mainnet, testnet, or
equivalent), in order: network configuration, key and role setup, deploy
step, and post-deploy verification. State who holds which role (deployer,
admin, upgrader) and what each role can do, as a table; a deployment
procedure that doesn't name its own privileged roles is incomplete by the
same standard `contract-system` sets for upgrade
boundaries.

Give the upgrade and rollback path the same rigor as the initial deploy.
Never include a private key, seed phrase, or fabricated address; use an
obviously synthetic placeholder and say so.

## Illustration

- **Form:** numbered prose steps with a verification command.
- **Renders:** network configuration, key and role setup, deploy,
  post-deploy verification — per target network.
- **Trigger:** never — numbered steps and a verification command, not a
  diagram, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Observability writing craft

Ground signal names, sources, thresholds, routing, and ownership in
instrumentation, configuration, or operational evidence. Record absent telemetry
and unknown thresholds as blind spots; this document owns alert intent and links
each actionable alert to its runbook and escalation owner.

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

## Illustration

- **Form:** a Markdown table of signal → source → alert intent; prose for
  what is not covered.
- **Renders:** per signal — what emits it, where it is visible, who owns the
  alert, what the intent is.
- **Trigger:** never — the table is primary and blind spots are prose, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Runbook writing craft

Write for an operator under pressure. Start with the observable symptom, scope,
and safety boundaries, then give ordered diagnosis steps whose checks select the
next action. Make mitigations reversible where possible and place destructive or
high-impact actions behind explicit prerequisites. Each remediation ends with a
verification signal; state the escalation threshold, information to collect,
and prevention follow-up.

Do not substitute an architecture tutorial for incident action, assume access or
credentials, or present unverified commands as executable procedure. Link to
deployment or disaster recovery when those own the operation.

## Illustration

- **Form:** prose diagnosis steps; a Mermaid `flowchart` only when diagnosis
  has material branches.
- **Renders:** observable symptom, scope, safety boundaries, ordered checks,
  remediation, verification signal, escalation threshold.
- **Trigger:** only when diagnosis has material branches, per
  [`../../references/illustration.md`](../../references/illustration.md).
