# Product writing craft

Writing-craft instructions for `product` group documents. Routes:

- `accessibility` → [Accessibility](#accessibility-writing-craft)
- `api_versioning` → [Api-versioning](#api-versioning-writing-craft)
- `backlog_traceability` → [Backlog-traceability](#backlog-traceability-writing-craft)
- `ba_business_rules` → [Business-rules](#business-rules-writing-craft)
- `content_model` → [Content-model](#content-model-writing-craft)
- `po_features` → [Feature-catalog](#feature-catalog-writing-craft)
- `localization` → [Localization](#localization-writing-craft)
- `migration` → [Migration](#migration-writing-craft)
- `ba_process_flows` → [Process-flows](#process-flows-writing-craft)
- `product_overview` → [Product-overview](#product-overview-writing-craft)
- `quickstart` → [Quickstart](#quickstart-writing-craft)
- `po_release_notes` → [Release-notes](#release-notes-writing-craft)
- `ba_requirements` → [Requirements-traceability](#requirements-traceability-writing-craft)
- `po_metrics` → [Success-metrics](#success-metrics-writing-craft)

## Accessibility writing craft

For each supported interaction, state implemented semantic or resource behavior
and its fallback or degraded experience. Treat targets and verification results
as evidence-backed claims with dates; list unverified areas as limits and link
unresolved gaps to their feature or limitation owner.

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md); a table
for the conformance checklist, prose for verification method and gaps.

State the WCAG conformance level actually targeted (A, AA, or AAA) and per
which success criteria area (perceivable, operable, understandable,
robust). State the verification method per area: automated scan, manual
audit, or assistive-technology testing — name which, since they catch
different defects.

Close with known gaps stated as plainly as the covered areas; say whether
the document is complete or unaudited rather than leaving a nontrivial UI
with no gaps section. Never claim a compliance certification the
repository hasn't evidenced.

## Api-versioning writing craft

For every public deprecation, link the evidenced migration path or state that
none is published. Ground compatibility and removal claims in current public
contracts and history; never promise an unverified future version or date.

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md); a compact
table for the version/date/status facts, prose for the compatibility
promise itself.

State the versioning scheme first, in one sentence a caller can act on:
what changes without a version bump (additive fields, new optional
parameters) and what forces one (removed fields, changed types, changed
error semantics). Name how a caller pins a version (header, path segment,
or account default) before describing what changes between versions.

Give every deprecation the same three facts, in the same order: the version
it was deprecated in, the version (or date) it will stop working, and the
replacement to migrate to. State "not yet scheduled" plainly rather than
omitting the removal date. Order deprecations by how soon they bite, not
alphabetically. Link the operation-level detail to
`api-reference` rather than repeating request/response
shapes here — this document owns the compatibility promise, not the
surface.

## Backlog-traceability writing craft

**Preferred illustration:** Use a traceability table; no diagram is needed.

This dynamic document exists only when discovery finds ticket or connected
tracker evidence. For each evidenced item, map the immutable ticket identifier
to its feature, relevant flow or change, verification, and released or current
status. Preserve the tracker wording and link to the source when permitted so a
reader can distinguish repository evidence from external planning state.

Do not create a seed table, guess mappings from commit messages, or invent
backlog status. When ticket evidence disappears or is insufficient, omit the
document rather than leaving an empty artifact.

## Business-rules writing craft

**Preferred illustration:** This is a rule lookup; use a repeatable rule block
or table, not a diagram.

Make every rule independently reviewable. Give it a stable identifier and plain
language statement, then state its trigger, outcome, exceptions, owning process,
source-enforced condition, and executable verification when one exists. Separate
rules that happen to share a code path when their triggers or outcomes differ;
surface precedence when rules conflict or one overrides another.

Do not promote a method, field, or branch name into a rule without proving its
condition and effect. Link to the process and tests rather than duplicating
their ordered steps or test implementation.

## Content-model writing craft

Derive every field, transition, validation, visibility boundary, and authority
from schema, route, publishing configuration, or access evidence. Record
unsupported transitions as gaps and link data representation to its reference owner.

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md); a table
per content type for fields, prose for lifecycle and publishing boundary.

One section per content type: its fields (name, type, required/optional),
its lifecycle states (draft, review, published, archived — whatever the
system actually implements), and the validation applied at each
transition. State the publishing boundary plainly: what makes content
visible to an end reader, and what stays staged.

State ownership per content type — who can create, edit, or publish it —
as a fact, not editorial guidance. Keep editorial strategy (tone, voice,
content calendar) out entirely; that's unsupported by repository evidence
and belongs, if anywhere, outside this document set.

## Feature-catalog writing craft

**Preferred illustration:** Use a feature table ordered by reader value or
journey, not an implementation diagram.

Describe each externally reachable capability through the outcome it enables,
its intended audience, availability or delivery state, material constraints,
and links to its owning flow. Treat "shipped" as a claim requiring both a
reachable behavior and release or deployment evidence; distinguish implemented,
enabled, preview, and planned only when evidence supports the distinction.

Do not make this a module inventory or infer product intent from names alone.
Link to the product overview for shared positioning and to the flow for behavior
instead of duplicating either.

## Localization writing craft

For every locale or fallback behavior, state the resource-inventory source and
how coverage was verified. Add known limits for unsupported content, partial
coverage, formatting, or fallback behavior; file presence alone does not prove support.

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md); a
supported-locale table is the whole document.

One row per supported locale: coverage (fully translated, partial,
machine-translated — name which), and the fallback behavior when a string
or locale isn't available. State the resource format (the file type and
where translated strings actually live) so a contributor knows where to
add a locale, not just that localization exists. Never claim a locale is
"supported" if it's only partially translated; state the actual coverage.

## Migration writing craft

Create a migration guide only for an evidenced source-to-target transition, with
breaking changes grounded in public-surface comparison and history. Distinguish
verified mechanical steps from manual or unresolved work, and link rollback only
where an evidenced recovery path exists.

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md); this is a
how-to — ordered changes and verification, not a full compatibility
matrix.

State source and target versions in the opening line, then list breaking
changes in the order a reader must apply them, not internal changelog
sequence. For each breaking change, give the exact before/after and,
where mechanical, the search-and-replace or codemod that handles it.

End with a verification step that proves the migration succeeded, and a
rollback path if one exists; state plainly if it doesn't. Keep the full
version-support matrix out; that's `compatibility`,
this document is the path between two specific versions.

## Process-flows writing craft

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md);
use a flowchart only when the business decision path cannot be read as steps.

Write one business-recognizable narrative per canonical flow: identify the
actor and trigger, ordered business actions, decision points, exceptions, and
both successful and unsuccessful outcomes. Preserve the business consequence of
each branch, including what is rejected, deferred, or escalated. Link to the
canonical flow for the technical sequence and to the rule catalog for formal
logic.

Do not paste call chains, expose internal component names without reader value,
or restate a business rule's full definition here. A flow title or branch name
is a lead; confirm actors and outcomes against source and flow evidence.

## Product-overview writing craft

State users, problems, capabilities, and non-goals only where source, manifest,
or linked owning documentation supports them. Expose unresolved scope as a limit
and link behavior to its flow or feature-catalog owner rather than implementation detail.

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md); this
orientation page normally uses prose, with a table only for enumerable facts.

Shape the page like a compressed PR/FAQ (Amazon's "Working Backwards" frame), not a feature
list: a press-release-style opening, then FAQ-depth answers. Order matters:

1. Who the product is for and the problem it changes, stated as a job the reader hires the
   product to do (Jobs-to-be-Done phrasing: "when X happens, this lets you Y") rather than a
   persona bio.
2. The main capabilities as outcomes the reader gets, not modules the team built.
3. Boundaries and explicit non-goals, stated as plainly as the capabilities.
4. Links out: flows for behavior depth, capability and reference material for detail.

Avoid implementation vocabulary unless it is part of the product's contract with its users.
Keep the page short enough to orient in one read; a claim that needs a table or diagram to
land belongs in the linked document, not here.

## Quickstart writing craft

Derive prerequisites and commands from manifests and the reachable entry path,
then verify the stated first result where possible. When verification cannot run,
state the blocker and do not present a plausible command or output as verified;
link full setup and troubleshooting to their owners.

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md); commands
and prose only — no diagram at this depth.

This is the smallest useful slice of `setup-guide`'s how-to discipline
(Diataxis): the shortest verified path to one first useful result, not a
second copy of full setup. State prerequisites in one line, then one
command block, then the expected output — a reader deciding whether this
project is worth a deeper look should reach that result in under a minute
of reading.

Do not duplicate `setup-guide`'s configuration, troubleshooting, or
alternate-path content; link to it for anything beyond the first result.
End with one or two "what next" links (`setup-guide` for full install,
`product-overview` for what this does) — never end on a command with no
stated outcome.

## Release-notes writing craft

**Preferred illustration:** This is a release lookup; use consistent categories
and no illustration.

Correlate tags, release history, and the feature catalog into concise entries
that answer what changed for users, whether they must act, and which versions or
clients are affected. Make compatibility, migration, security, and availability
implications explicit, with a link to the owner document when a reader needs
more than a summary.

Include only released impact. Omit refactors, test-only changes, and dependency
noise unless the result materially changes user behavior, compatibility,
security, or operations; do not claim a commit is delivered without release
evidence.

## Requirements-traceability writing craft

**Preferred illustration:** Use a traceability table; no diagram is needed.

Keep the chain inspectable from evidenced requirement to owning rule or flow,
implementation area, verification, and current status. Retain stakeholder
wording and identifiers when supplied, and label whether each link is direct
source, test, history, or external evidence. Explain an incomplete chain as a
gap, not as proof that the requirement is satisfied.

Do not invent ticket identifiers, stakeholder intent, acceptance criteria, or
delivery status. Where an external requirement is known to exist but its
wording or identifier is unavailable, use a typed external token once and name
the evidence needed to resolve it.

## Success-metrics writing craft

**Preferred illustration:** Use a measure table; reserve diagrams for an
evidenced collection pipeline that cannot be understood from the fields.

For each outcome, separate the desired change from the measurable signal, its
instrumentation source and coverage, interpretation, cadence, and accountable
owner. State data quality or attribution limits that change how the measure can
be read. A recorded event proves collection exists, not that a target, baseline,
or product outcome has been achieved.

Never infer targets, owners, thresholds, or business intent from telemetry. Use
the typed external target token or explicitly state that no target is documented,
and link implementation detail to the owning analytics or configuration source.
