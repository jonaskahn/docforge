# {{TITLE}}

_Last reviewed: {{YYYY-MM-DD}}_

{{Two or three sentences introducing the compact product-owner section: what
this product delivers, for whom, and what a product owner can answer from
this file.}}

## At a glance

{{The product shape: the outcomes this system delivers and how their value is
measured. Establish the shape; the sections below own the detail.}}

## Scope and boundaries

{{What belongs in the product-owner views, and what is owned by an adjacent
section instead. Name the neighbouring sections so a reader who landed here
by mistake can route themselves away. Link any document in this folder that
this file does not merge.}}

## Feature catalog

| Feature | User outcome | Audience | Availability | Owning flow |
|---|---|---|---|---|
| {{feature}} | {{what the user can now do}} | {{who}} | {{released / behind a flag / planned}} | {{link}} |

{{Outcomes, not an implementation inventory. A feature belongs here only when
the repository evidences it.}}

## Success metrics

| Outcome | Measure | Instrumented? | How to interpret it |
|---|---|---|---|
| {{outcome}} | {{measure}} | {{yes / partially / no}} | {{what a change means}} |

{{State the instrumentation honestly. Where a target exists outside the
repository, name the token that carries it rather than supplying a number.}}

## Release notes

| Version | Date | User impact | Compatibility |
|---|---|---|---|
| {{version}} | {{YYYY-MM-DD}} | {{what changed for a user}} | {{breaking / additive / none}} |

{{Released user impact only. Keep internal refactors and dependency bumps
out.}}

## Backlog traceability

_Only when the repository carries ticket evidence — otherwise omit this
heading entirely._

| Ticket | Feature | Flow or change | Release / status |
|---|---|---|---|
| {{evidenced ticket id}} | {{feature}} | {{link}} | {{link}} |
