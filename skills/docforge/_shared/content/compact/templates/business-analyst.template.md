# {{TITLE}}

_Last reviewed: {{YYYY-MM-DD}}_

{{Two or three sentences introducing the compact business-analyst section:
which business processes this system automates, and what a business analyst
can answer from this file without reading code.}}

## At a glance

{{The business shape of the system: the processes it runs and where the rules
that govern them are enforced. Establish the shape; the sections below own
the detail.}}

## Scope and boundaries

{{What belongs in the business-analyst views, and what is owned by an
adjacent section instead. Name the neighbouring sections so a reader who
landed here by mistake can route themselves away. Link any document in this
folder that this file does not merge.}}

## Process flows

{{One subsection per business process: the actor, what triggers it, the steps
in business language, the decision points, the exceptions, and the outcome.
Link the owning technical flow rather than reproducing its call chain.}}

## Business rules

| Rule | Statement | Trigger | Outcome | Exceptions | Enforced in |
|---|---|---|---|---|---|
| {{BR-001}} | {{plain-language statement}} | {{when it applies}} | {{what it produces}} | {{carve-outs}} | {{evidence}} |

{{Each rule stated once here. A process flow that applies a rule links to its
row instead of restating it. Do not list a rule inferred only from a name.}}

## Requirements traceability

| Requirement | Owning rule / flow | Implementation | Test | Status |
|---|---|---|---|---|
| {{requirement, with its evidence}} | {{BR-001 / flow}} | {{evidence}} | {{evidence}} | {{met / partial / unmet}} |

{{Only requirements the repository evidences. Never invent a ticket
identifier to fill a row.}}
