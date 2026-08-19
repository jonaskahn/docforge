# Document shapes

This file owns **shape**: the spine a document's body is built around, and
the order in which a reader travels it. [`progressive-disclosure.md`](progressive-disclosure.md)
owns the altitude vocabulary (L0–L3) every shape instantiates;
[`depth-and-audience.md`](depth-and-audience.md) owns how much detail;
[`illustration.md`](illustration.md) owns the form of one figure;
[`document-composition.md`](document-composition.md) owns which *document*
holds a fact. Nothing else owns the form of the *whole* document — that gap is
this file.

## Choosing a shape

Walk this list in order; the first question that fires names the shape.

1. Is the section order fixed by a named standard, spec, or schema outside
   docforge (MADR, a model-card format, a data-contract schema, the
   AGENTS.md kernel spec)? → **`fixed-frame`**.
2. Does the whole document return the value behind a key the reader already
   holds, with no argument to make? → **`lookup`**.
3. Does the document own no fact of its own and exist only to route the
   reader to the document that does? → **`router`**.
4. Does it fold other documents' own content into `##` sections of one
   merged file? → **`merged-section-spine`**.
5. Is the row set itself the claim — a closed, discovered population,
   including what was excluded? → **`coverage-matrix`**.
6. Is it one repeated, addressable block per member of a named set, each
   complete alone? → **`entry-catalog`**.
7. Does the reader travel forward through time? If a check along the way
   selects the next branch → **`diagnostic-path`**; if the reader's own hands
   drive each step to a checkable result → **`executable-procedure`**;
   otherwise → **`ordered-narrative`**.
8. Otherwise: state the governing claim, then the structure that makes it
   true → **`answer-first`**.

## The vocabulary

| Shape | Spine | Complete when |
|---|---|---|
| `answer-first` | a governing claim, then the structure that makes it true | every part named at L1 has L2 depth, or a stated reason it needs none |
| `ordered-narrative` | time — the reader travels forward through something the system does | every step, branch condition, categorized failure, and the outcome are present |
| `executable-procedure` | the reader's hands — each step ends in a checkable result | a stranger reaches the verified end state without asking a human |
| `diagnostic-path` | symptom → cause → resolution, a check selects the branch | every branch the diagnosis offers has a resolution and a verify |
| `lookup` | a key the reader already holds | the key space is closed and stated |
| `entry-catalog` | one addressable block per member of a named set | every entry carries every declared field, `n/a` stated rather than omitted |
| `coverage-matrix` | the row set is itself the claim | every discovered member has a row, including excluded ones |
| `router` | the reader's destination | every selected, materialized non-agent child is linked with the reader question it answers |
| `merged-section-spine` | a host file ordering member documents | every folded member keeps every field of its own contract, condensed never summarized |
| `fixed-frame` | an authority outside docforge | the external standard's sections are present, in its order |

### `answer-first`

**Travel:** L0 the claim → L1 the whole map named → L2 per-part mechanism →
L3 the boundary. **Stop test:** the standard stop test in
[`progressive-disclosure.md`](progressive-disclosure.md), used literally.
**Illustration tendency:** `flowchart`, `stateDiagram-v2`, or `erDiagram`, at
L1. **Done wrong:** mechanism stated before the claim; an "overview" that is
a table of contents; one part explained in full while its siblings are still
unnamed. **Pairs with:** Explanation / deep-dive, and Orientation /
orientation for the documents that front one. **Examples:** `concept`,
`arch_high_level`, `arch_low_level`, `system_overview`, `threat_model`,
`root_readme`.

### `ordered-narrative`

**Travel:** L0 the guarantee → L1 every step named → L2 branch, failure, and
timing detail per step → L3 who owns recovery. **Stop test:** a reader who
stops after the step list can narrate the sequence end to end and state the
guarantee. **Illustration tendency:** `sequenceDiagram` primary; `flowchart`
for branch fan-out. **Done wrong:** mechanism before the guarantee; branches
gathered away from the step that creates them; a technical retry the caller
never observes, written up as a failure mode. **Pairs with:** Explanation /
deep-dive. **Examples:** `flow`, `data_flow`, `app_lifecycle`,
`model_lifecycle`.

### `executable-procedure`

**Travel:** L0 outcome and prerequisites → L1 the numbered path → L2
command, expected output, and verify per step → L3 rollback, escalation,
what's next. **Stop test:** a reader who stops mid-procedure is left in a
known state, not an undefined one. **Illustration tendency:** usually none;
a `text` fence for expected output; `flowchart` only for a real gate. **Done
wrong:** narration in place of imperatives; no verify step; a destructive
command with no stated stop condition. **Pairs with:** How-to / deep-dive.
**Examples:** `setup_guide`, `release_guide`, `library_publishing`,
`migration`, `quickstart`.

### `diagnostic-path`

**Travel:** L0 impact and immediate mitigation, before the cause is known →
L1 the branch map, every cause named, none resolved yet → L2 one resolution
per cause plus its verify → L3 escalation and prevention. **Stop test:** a
reader who stops after mitigation has reduced harm and knows they have not
fixed the cause. **Illustration tendency:** `flowchart TD` as a decision
path. **Done wrong:** diagnosis stated before mitigation; a branch with no
resolution; a taxonomy of causes where a decision path was owed. **Pairs
with:** How-to / deep-dive. **Examples:** `runbook`,
`infra_disaster_recovery`, `flashing_recovery`.

### `lookup`

**Travel:** L0 collapses to a read-rule — the key, the ordering that serves
it, any precedence or scope that changes an answer; the table's own columns
are the L1; no true L2 or L3. **Stop test:** a reader who reads exactly one
row gets a correct value — no row's meaning depends on prose they skipped.
**Illustration tendency:** `table`; a diagram only for the read-rule itself,
never re-rendering rows (`Trigger: never` for most). **Done wrong:**
alphabetical order where frequency-of-use would serve; narrative glue
between rows; a row that is wrong without the precedence block above it.
**Pairs with:** Reference / reference. **Examples:** `glossary`,
`configuration`, `tech_stack`, `api_rate_limits`, `infra_access`, `dataset`.

### `entry-catalog`

**Travel:** L0 the set plus the envelope every entry shares → L1 an index,
one line per entry → L2 the entry blocks, fixed field order → L3 what is not
catalogued here. **Stop test:** a reader arriving at one entry by anchor
gets a complete answer without reading a sibling. **Illustration tendency:**
`table` for the index; rarely more. **Done wrong:** field order drifting
between entries; the shared envelope repeated inside every entry; an entry
with no index line above it. **Pairs with:** Reference / reference, or
Explanation / reference for narrative entries. **Examples:**
`ba_business_rules`, `api_reference`, `limitations`, `ba_process_flows`.

### `coverage-matrix`

**Travel:** L0 the population and how it was enumerated → L1 the matrix →
L2 per-row notes and exceptions → L3 what sits outside the population and
why. **Stop test:** a reader who counts the rows learns the true size of the
population. **Illustration tendency:** `table`, always; a companion diagram
usually just restates the same rows and should be dropped. **Done wrong:**
silently omitting a member instead of recording it as excluded; a row with
no evidence; a partial sweep presented as the whole population. **Pairs
with:** Reference / deep-dive. **Examples:** `threat_register`,
`portfolio_repo_inventory`, `browser_support`, `backlog_traceability`.

### `router`

**Travel:** the six-step sequence already stated in
[`../content/shared/folder-index.instruction.md`](../content/shared/folder-index.instruction.md)
`## Top-down shape` — introduction, at-a-glance, scope and boundaries,
start-here reading paths, the child map, related sections. That file governs
routers; this entry only names the shape. **Stop test:** a reader who stops
at the at-a-glance knows whether their answer lives in this section at all.
**Illustration tendency:** prose and links only. **Done wrong:** carrying a
child-owned fact; linking an unselected or unwritten child; alphabetical
child order instead of most-orienting-first. **Pairs with:**
Orientation/Routing, target depth `orientation` or `router`. **Examples:**
`docs_index`, `flows_index`, `decisions_index`, every `folder-index`-aliased
section README.

### `merged-section-spine`

**Travel:** L0 section introduction and at-a-glance → L1 scope and what is
merged versus linked → L2 one `##` per folded member, each keeping its own
shape's ladder inside its section → L3 links to unmerged siblings. **Stop
test:** a reader who reads one folded section gets what the standalone
document would have given them, minus depth, never minus correctness.
**Illustration tendency:** inherited from each member; the host adds none of
its own. **Done wrong:** a merged narrative replacing named sections; the
host restating a member's fact instead of hosting it. **Pairs with:** the
range its members span — see each compact contract's facets row. **Examples:**
the 13 documents under `content/compact/`.

### `fixed-frame`

**Travel:** none of ours — follow the external order exactly. **Stop test:**
does not apply; the acceptance test is conformance to the cited standard,
not progressive disclosure. **Illustration tendency:** whatever the standard
itself calls for; none owed beyond that. **Done wrong:** reordering sections
to put a governing claim first, which breaks the conformance this shape
exists to protect. **Pairs with:** varies — this shape is defined by its
authority, not by mode or depth. **Examples:** `adr` (MADR), `model_card`
(Mitchell et al., 2019), `agents_kernel`, `claude_shim`, `claude_local` (the
AGENTS.md kernel spec).

## Shape and the altitude ladder

The L0–L3 altitude meanings are fixed for every document regardless of
shape; only the travel order and which altitudes are load-bearing vary, and
that variation is stated per shape above and in
[`progressive-disclosure.md`](progressive-disclosure.md) `## Scope`. A
contract's `Must present` table assigns every element an altitude in its `At`
column using this same vocabulary — never a shape-local rename.

## One shape per document

A document holds exactly one shape, declared once in its contract and its
catalog record. Nesting is expressed *inside* a shape, never by combining
two: `ba_process_flows` is `entry-catalog` whose entries each happen to read
as a narrative internally — that is still one shape, not
`entry-catalog`-plus-`ordered-narrative`. A `merged-section-spine` host's
folded sections keep their members' own shapes inside those sections; the
host's own shape stays `merged-section-spine`. If a document type seems to
need two shapes, it is two document types.

## Declaring it

The catalog field `answer_shape` holds one of the ten values above, enum-
validated by `query_catalog --validate`, and returned by `--route` next to
`target_depth`. A contract's facets row (`| Mode | Depth | Shape |`) must
match the record's `answer_shape` exactly; a mismatch is a linter defect (see
`quality-bar.md`).

## What this file does not decide

It does not set word counts, section lengths, illustration form beyond a
tendency (`illustration.md` decides the figure itself), how much detail a
section carries (`depth-and-audience.md`), or how a sentence sounds
(`voice.md`). It decides only the spine and the order a reader travels it.
