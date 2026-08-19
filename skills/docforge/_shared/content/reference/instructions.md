# Reference writing craft

Writing-craft instructions for `reference` group documents. Routes:

- `api_rate_limits` → [Api-rate-limits](#api-rate-limits-writing-craft)
- `api_reference` → [Api-reference](#api-reference-writing-craft)
- `browser_support` → [Browser-support](#browser-support-writing-craft)
- `cli_commands` → [Command-reference](#command-reference-writing-craft)
- `library_compatibility` → [Compatibility](#compatibility-writing-craft)
- `configuration` → [Configuration](#configuration-writing-craft)
- `data_types` → [Data-types](#data-types-writing-craft)
- `api_errors` → [Error-catalog](#error-catalog-writing-craft)
- `limitations` → [Limitations-register](#limitations-register-writing-craft)
- `model_card` → [Model-card](#model-card-writing-craft)
- `cli_output` → [Output-exit-contract](#output-exit-contract-writing-craft)
- `performance_budgets` → [Performance-budgets](#performance-budgets-writing-craft)
- `platform_compatibility` → [Platform-compatibility](#platform-compatibility-writing-craft)
- `infra_resources`, `infra_access` → [Resources / access](#resources--access-writing-craft)
- `tech_stack` → [Tech-stack](#tech-stack-writing-craft)

## Voice and linking craft

Voice for this group is owned by [`voice.md`](../../references/voice.md):
terse and tabular, no narrative connective tissue. Name what a linked
document owns before the link ("the shared response envelope is restated
once there," never "see `api-errors`"). What each side of a link owns, and
why it is linked rather than restated, is each contract's `## Owns / links`
table, not this section.

## Api-rate-limits writing craft

Cite gateway, configuration, or specification evidence for every limit, header,
and 429 behavior. Link endpoint-specific authentication to `api-authentication`;
an absent documented limit is an unknown, not an unlimited contract.

State the limiting dimension first — per API key, per IP, per endpoint, per
account tier. Distinguish sustained rate from burst allowance where both
exist. Give the exact response
contract a caller can code against: status code, and every header the
caller reads (`Retry-After`, remaining-quota headers, reset timestamp) —
name the literal header, not "the appropriate header."

State what to do on a 429 as an imperative, not a description: back off for
the stated duration, then retry — not "clients should implement backoff."
If limits differ by plan or tier, give one table with tier as a column
rather than one prose paragraph per tier.

## Illustration

- **Form:** Markdown table for limit values by dimension; prose only for the
  429 retry contract.
- **Renders:** the limit table itself — one row per limit × dimension, tier as
  a column — and the retry contract as imperative prose.
- **Trigger:** the table by default; a diagram only when a limit relationship
  cannot be read from the table, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Api-reference writing craft

For every operation, cite the authoritative schema, export, or generator. Link
authentication, limits, errors, compatibility, and version policy to their
respective owners instead of maintaining parallel copies of those contracts.

Derive the surface from the repository's spec, schema, or exported interface
— never hand-transcribe route handlers into a parallel list. Open with the
compatibility source named plainly: the file or generator a
reader can diff against (`openapi.yaml`, generated client types, a GraphQL
schema) so "authoritative" has a concrete referent, not just this page.

Group operations by resource or domain, not by HTTP verb or source file — a
reader looking up "orders" should find every order operation in one place.
Within a group, give every operation the same field order: method and path,
purpose in one clause, request shape, response shape, one realistic example.
Reuse the response envelope owned by [Error-catalog](#error-catalog-writing-craft);
restate its field table once, there, and link to it per endpoint rather than
repeating it. State auth requirement and rate-limit class as table columns,
not a repeated paragraph.

Mark deprecated operations inline with the version that deprecated them and
the replacement, following the policy in `api-versioning`.

## Illustration

- **Form:** Markdown tables for endpoint and field lookups; prose only to
  explain a contract nuance a table cannot carry.
- **Renders:** the lookup tables themselves — one row per operation with
  method/path, purpose, request, response, auth, and rate-limit class.
- **Trigger:** a diagram only when a contract nuance cannot be expressed in a
  table row — a reference document stays tabular, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Browser-support writing craft

Cite CI or manual-browser evidence and date for every support row. Link
component degradation behavior to `ui-components`; a browser absent from the
matrix is not implicitly supported or unsupported.

State the tested matrix, not an aspiration; a browser listed as supported
should mean it's in the test matrix or verified manually — say which. State
degradation behavior per unsupported browser (polyfilled, reduced
functionality, blocked outright) rather than leaving it implicit.

## Illustration

- **Form:** a Markdown matrix table.
- **Renders:** browser × minimum version × degradation behavior — the matrix
  table is the whole document.
- **Trigger:** never — the matrix table is the whole document, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Command-reference writing craft

Every entry cites its command definition, help output, or tested invocation and
records side effects only when observed. Link machine-output semantics to
`output-exit-contract`; do not present a plausible invocation as runnable.

Follow POSIX/GNU convention: pair every short flag with its long-named
equivalent (`-v` / `--verbose`), and document them together, not as
separate entries. Give each command one runnable, copy-pasteable example
that needs no editing after paste. State side effects plainly (writes a
file, calls a network service, mutates state) as part of the command's
entry, not buried in prose elsewhere.

Group subcommands under their parent, not flattened alphabetically — a
reader exploring `repo sync` should find its subcommands together. Never show a call-graph or internal function name.

## Illustration

- **Form:** a Markdown table of flags; one code-fence example block per
  command.
- **Renders:** the flag table — short/long pairs documented together — and
  each command's copy-pasteable example.
- **Trigger:** never — no call-graph or internal structure diagram, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Compatibility writing craft

Every supported row cites CI, manual, or community evidence with its date. Link
migration procedures to their owner rather than embedding upgrade steps, and
mark an untested version or platform as unknown rather than compatible by default.

State the supported-version matrix as tested evidence, not aspiration — a
version marked supported should mean "we run CI against it," not "it
probably works." Include the deprecation column: when support for each older version ends,
and what happens after (still works, unsupported but functional, actively
broken).

Order rows newest-version-first. State the actual test evidence (CI
matrix, manual verification, community report) per row where confidence
varies.

## Illustration

- **Form:** a Markdown matrix table.
- **Renders:** version/platform × test evidence × deprecation horizon — the
  matrix table is the whole document.
- **Trigger:** never — the matrix table is the whole document, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Configuration writing craft

For every setting, cite its exact configuration source and consuming code, and
state scope and sensitivity only when evidenced. Link environment-specific
differences to `environments`; do not infer defaults from one deployment file.

Apply the 12-factor discipline: every setting the application actually
reads from its environment, with name, default, scope (which
environment/service reads it), and sensitivity (is this safe to log or
does it need a secret store) — as table columns, not prose repeated per
setting. State the source of truth precisely (an env var name, a config
file path and key) so a reader can find where to actually set it, not just
that it exists.

Never invent an aspirational setting the code doesn't read, and never print
a real secret value — show the variable name and note where the value
lives instead. Order by how often a reader tunes the setting, not
alphabetically; the setting everyone changes in local dev belongs above the
one nobody has touched since launch.

## Illustration

- **Form:** a Markdown table.
- **Renders:** one row per setting — name, default, scope, sensitivity — the
  table is the whole document.
- **Trigger:** never — the table is the whole document, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Data-types writing craft

Cite the authoritative schema or export for every type, constraint, and
representation change. Link business semantics to their glossary or rule owner;
do not reconstruct field meaning from a sample payload.

One row per type: name, wire representation (not the internal language
type), constraints (range, length, pattern), and nullability. State the
wire representation precisely enough to implement against — "timestamp"
is not a wire representation, "ISO 8601 string, UTC" is. Where a type has been renamed or its representation changed, note the
prior representation and the version it changed in.

Order types by how often a reader looks them up — the types used across
the most operations first — not alphabetically and not by internal module.
Do not restate business meaning already owned by
`business-rules` or `glossary`.

## Illustration

- **Form:** a single Markdown table.
- **Renders:** one row per type — name, wire representation, constraints,
  nullability — the lookup itself.
- **Trigger:** almost never — a diagram only when a type relationship cannot
  be read from the lookup table; this document is a lookup, not an
  explanation, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Error-catalog writing craft

Document the stable response envelope once, emphasizing which fields clients may
branch on and which are human-facing or additive. Give every machine-readable
code a stable anchor, trigger, observable status or category, safe client
behavior, retry conditions, and correlation or observability guidance. Close
with a status-level summary so consumers can survey the complete failure surface.

Never expose stack traces, internal exception names, secrets, or a retryable
claim unsupported by the actual behavior. Treat a renamed code or changed error
meaning as a compatibility change, not prose cleanup.

## Illustration

- **Form:** an error-envelope table, then a per-code catalog table, then a
  status-level summary table.
- **Renders:** the envelope fields clients may branch on; one row per
  machine-readable code; the complete failure surface survey.
- **Trigger:** never — no diagram is needed.

## Limitations-register writing craft

Each limitation cites implementation, test, issue, or incident evidence and
names a review owner when established. Route remediable engineering debt to
`tech-debt-register`; preserve an unowned or unresolved limitation without
softening it into a roadmap promise.

Use one entry per observable limitation, and place it in exactly one of the register's
sections — a boundary test decides which, not a judgment call:

- **Known limitations** — built this way on purpose; a design trade-off, not a defect.
- **Known issues** — a defect under investigation, plausibly fixed later.
- **Not supported** — a capability a reasonable reader expects and will not find, with no
  fix in flight.
- **Scale and performance envelope** — a tested numeric boundary, not a behavior.

Within an entry, state trigger, impact, workaround, and evidence in that consistent order.
State impact in the reader's terms — "imports over 2 GB fail," not "the buffer is bounded
at 2 GB." Always give the workaround where one exists. Distinguish deliberate trade-offs from accidental gaps: a bound with stated reasoning
reads as judgment; the same bound unexplained reads as an oversight. Use frank language; do
not soften impact, and do not turn a remediation hope into a current fact — "not currently
planned" is honest, "coming soon" is a promise this document cannot keep. Date the review:
without a review date a reader cannot tell whether a missing entry means "no such
limitation" or "nobody has looked." Order entries by how often a reader will hit them, not
by discovery date or file location.

## Illustration

- **Form:** Markdown tables for comparable limits; prose for each entry's
  trigger, impact, workaround, and evidence.
- **Renders:** the register's sections with one entry per row; prose carries
  the entry's chain of facts.
- **Trigger:** never — tables and prose carry the whole register, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Model-card writing craft

Cite dataset, run or artifact, and evaluation evidence for every metric, and
name the model owner when established. Link lifecycle mechanics to
`model-lifecycle`; do not infer model quality from a declared architecture.

Follow the Model Cards for Model Reporting shape (Mitchell et al., 2019):
model details, intended use, training data summary, evaluation results,
limitations, and out-of-scope uses, in that order. State out-of-scope uses
as plainly as intended ones.

Give evaluation results with their measurement context (dataset, metric,
date) — a bare accuracy number with no dataset named is not evidence.
Never claim a fairness or safety property the repository hasn't actually
evaluated; state what was measured and what wasn't. Link training-data
lineage to `model-lifecycle` rather than repeating
it here.

## Illustration

- **Form:** prose sections per Mitchell et al.'s standard shape; a Markdown
  table only for evaluation metrics.
- **Renders:** model details, intended use, training data summary, evaluation
  results, limitations, out-of-scope uses — the metrics table with dataset,
  metric, and date.
- **Trigger:** never — prose sections and the metrics table carry the card,
  per [`../../references/illustration.md`](../../references/illustration.md).

## Output-exit-contract writing craft

For each captured example, cite the command and version that produced its exit
status and streams. Link command-specific side effects back to
`command-reference`; this contract owns stable output semantics, not usage prose.

State the exit-code table first: code, meaning, and whether it's stable
enough to script against. State which stream
owns which content (stdout for machine-parseable output, stderr for
human-facing diagnostics, or whatever the actual split is) and the output
format's stability guarantee — is this JSON schema versioned, or can a
field disappear in a minor release?

Give one real, captured output example per format, not a hand-typed
approximation — including whitespace and field order if those are part of
the contract.

## Illustration

- **Form:** Markdown tables for exit codes and stream ownership; one captured
  code-fence example per format.
- **Renders:** the exit-code table — code, meaning, scripting stability — and
  the stream-ownership table.
- **Trigger:** never — this document exists so a script can be written against
  it, not read for prose, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Performance-budgets writing craft

Every budget cites its measurement artifact and date, then names the owner and
remediation or limit when breached. Link user-visible constraints and detailed
remediation to their owning register rather than hiding them in a threshold row.

One row per budget: the evidenced limit (CPU, GPU, memory, storage,
timing), how it was measured (load test, profiler, production
observation — name which), and what degrades when the budget is
approached or exceeded — an SRE error-budget framing applied to resource
limits rather than availability. Never state a target that hasn't been measured.

Order by how often a reader hits the budget in practice, not by resource
type alphabetically. State the measurement's recency; date it the way `limitations-register`
dates its review.

## Illustration

- **Form:** a Markdown table of budget × measurement × degradation.
- **Renders:** one row per budget — evidenced limit, how it was measured, what
  degrades — the table is the whole document.
- **Trigger:** never — the table is the whole document, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Platform-compatibility writing craft

Cite device or test-matrix evidence for every platform row. Link permission and
lifecycle behavior to their owning documents, and mark unverified target support
or degradation as unknown rather than inferring it from a build artifact.

State minimums as tested evidence, not aspiration — the same discipline
[Compatibility](#compatibility-writing-craft) applies to library versions, applied
here to OS/device/architecture. State degradation behavior below the
minimum (refuses to run, runs with reduced features) and the deprecation
horizon for older supported platforms.

## Illustration

- **Form:** a Markdown matrix table (OS/device/architecture × minimum
  version).
- **Renders:** tested minimums, degradation below the minimum, and the
  deprecation horizon — the matrix table is the whole document.
- **Trigger:** never — the matrix table is the whole document, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Resources / access writing craft

Covers `infra_resources` and `infra_access` — both are lookup inventories;
the craft is keeping them that way rather than letting narrative creep in.

Resources: one row per managed resource — name, type, owner, criticality.
Order by criticality, the same principle `dependencies-inventory` uses,
not alphabetically. Access: one row per grant — principal, scope, how the
grant was made (path, not just "IAM"), and review cadence if one exists. A
grant with no review cadence stated reads as permanent by default; say so
if that's true rather than leaving it silent.

Never include a credential, secret, or literal access key — name the
mechanism (a role, a policy, a secret manager reference), never the
value.

For each resource, include a stable locator or context (such as account,
environment, region, or canonical address) and a source-of-truth link; do not
copy mutable state or apply procedure. For access, distinguish an evidenced
review cadence from `unknown` rather than treating silence as permanence. Keep
resource inventory and grants separate: a resource does not prove who can use
it, and a grant does not prove current resource state.

## Illustration

- **Form:** Markdown tables only.
- **Renders:** one row per managed resource — name, type, owner, criticality;
  one row per grant — principal, scope, mechanism, review cadence.
- **Trigger:** never — this is Reference depth, not Explanation, per
  [`../../references/illustration.md`](../../references/illustration.md).

## Tech-stack writing craft

Make this a stable lookup of what the repository is built with: language and
runtime versions, frameworks, build and package tools, datastores or messaging,
test and CI tooling, and key runtime libraries with their role and manifest
source. Prefer declared versions; mark a version unavailable rather than
deriving it from a lockfile or an import. Group rows by the layer a maintainer
would change together, not alphabetically.

Keep operational dependency failure behavior in `architecture/dependencies.md`.
Do not dump lockfiles, present transitive packages as primary choices, invent
versions, or turn the table into a marketing comparison.

## Illustration

- **Form:** one evidence-backed Markdown table grouped by layer.
- **Renders:** the layered table itself — language/runtime, frameworks, build
  tools, datastores, test/CI tooling, key libraries with role and manifest
  source.
- **Trigger:** never — no architecture diagram is needed.
