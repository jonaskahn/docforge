# {{TITLE}}

_Last reviewed: {{YYYY-MM-DD}}_

{{Two or three sentences introducing the compact operations section: what
this file covers, why the operations section exists, and who should read
it. A reader with no prior project knowledge should understand how this
system is deployed and observed.}}

## At a glance

{{The operational mental model: how a change reaches production and how its
health is watched. Establish the shape; the deployment and observability
sections below own the detail.}}

## Scope and boundaries

{{What belongs in the operations section, and what is owned by an adjacent
section instead. Name the neighbouring sections so a reader who landed here
by mistake can route themselves away. Link any document in this folder that
this file does not merge.}}

## Deployment

{{Environments, artifact source, rollout strategy, and verification for each
— grounded in repository evidence. Keep incident procedures out.}}

## Rollback

{{Rollback trigger and steps, with a verification command. Environment
differences and incident recovery live in adjacent documents; link, don't
restate.}}

## Observability

| Signal | Source | Visible in | Owner | Alert intent |
|---|---|---|---|---|
| Latency | {{source}} | {{dashboard/log/trace}} | {{owner}} | {{page / log-only}} |
| Traffic | {{source}} | {{...}} | {{owner}} | {{...}} |
| Errors | {{source}} | {{...}} | {{owner}} | {{...}} |
| Saturation | {{source}} | {{...}} | {{owner}} | {{...}} |

{{How a reader moves from an alert to the request or trace that caused it,
and what this system cannot currently observe. Keep provider marketing out.}}

## Runbook index

| Runbook | Recovers | Trigger | Status |
|---|---|---|---|
| [{{runbook}}](#{{anchor}}) | {{what it restores}} | {{alert or symptom}} | documented below |
| {{runbook}} | {{what it restores}} | {{alert or symptom}} | register only |

{{One or two sentences on what a register-only row means: the runbook is
named and evidenced, and its procedure is not written out here.}}

## {{Runbook name}}

_Repeat this section once per folded runbook._

**Trigger.** {{The alert or symptom that sends a reader here.}}

{{The ordered, verified steps, the decision points, and the outcome that ends
the procedure — each grounded in cited repository evidence. Never write a step
the repository does not evidence.}}
