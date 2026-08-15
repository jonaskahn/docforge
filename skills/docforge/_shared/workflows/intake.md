# Intake

Owns: bare `/docforge` invocation, safe discovery, profile detection, the
discovery gate, the discovery brief, scope questions, the confirmation gate,
and graph-provider choice.

## Bare `/docforge` invocation

When the user invokes `/docforge` with no task, flags, tier, or typed profile
document request, begin an **interactive intake**. Do not initialize a
manifest, scaffold a file, build/refresh a graph, install a provider, change
configuration, or archive/delete anything.

First perform only safe discovery: identify the repository root, check whether
`.docforge/manifest.json` exists, run the read-only code-graph precheck, and run
`detect_profiles.{py,js}` inline to identify candidate shapes, platforms,
frameworks, and concerns (see
[`../runtime/catalog/README.md`](../runtime/catalog/README.md)).
`detect_profiles.{py,js}` recognizes frameworks and shapes by reading
*declared dependencies* structurally from project-definition manifests
(`package.json`, `pyproject.toml`/`requirements.txt`, `pom.xml`,
`build.gradle*`, `go.mod`, `Cargo.toml`, `Gemfile`, `composer.json`,
`*.csproj`, `pubspec.yaml`), not by substring — so a declared dependency is
**strong** evidence. Path fragments and content keywords are **weak** cues:
they never alone confirm a profile. The same noun or team term can mean
different aspects across projects, stacks, and domain language.

When the pack from `detect_profiles.{py,js} --emit-gate-pack` sets
`needs_gate`, run the
**discovery gate** before the discovery brief: follow
[`../references/discovery-gate.md`](../references/discovery-gate.md), ground
decisions only in the bounded pack, and emit judgment JSON (`promote` / `keep`
/ `demote` / `drop` / `propose`). Apply it with the `discovery_gate` library
API (`runtime/catalog/{python/discovery_gate.py,js/discovery_gate.js}`, see
[`../runtime/catalog/README.md`](../runtime/catalog/README.md)); on
invalid judgment, fail open to deterministic ranks. Detection and the gate
propose profiles; they never confirm them on the user's behalf. When exactly
one readable code-graph provider is ready, use it as the proposed default and
do not ask the user to choose among absent providers. This read-only provider
selection is not permission to build, refresh, install, or configure
anything.

When the repository root contains any nested `.git` directory (a candidate
multi-repo workspace), also run the read-only `discover_child_repos.{py,js}`
(see [`../references/portfolio.md`](../references/portfolio.md)) to learn
each detected member's own tier. This is discovery only — it does not decide
inclusion or offer Portfolio by itself; it makes the fact available to the
discovery brief and the tier question below.

Treat `detect_profiles` and the nested-`.git` check as one paired discovery
step: never refresh one without the other. If repository state changes
materially after this pass but before the Tier question is finalized — a
directory that was empty gains real content, the user says code is coming
and later confirms it has arrived, or any other change that could alter
profile evidence or nested-repo membership — re-run this whole discovery
step and refresh the discovery brief before asking or re-asking Tier. Never
finalize Tier from a brief the repository has since outgrown.

## Discovery brief

After safe discovery (and the discovery gate when `needs_gate`), and **before**
asking any scope questions, present a short discovery brief:

- Repository root and whether a manifest exists (when a manifest exists,
  include its tier, typed profiles, and incomplete count).
- Code-graph readiness: name each ready provider, or state that none are ready
  and that setup will be offered only if graph source is unresolved — never a
  choice among absent providers. When the root itself shows zero profile
  evidence and nested repos were detected (see Portfolio readiness below),
  state plainly that the root has no source of its own to graph — this is
  expected for a pure collection root, not a setup gap — and do not offer
  graph setup for the root.
- **Recommended** vs **also possible** profile rows for shapes, platforms,
  frameworks, and concerns, each with a one-line evidence or gate reason.
- Project scale, from the gate pack's `scale` field (see
  [`../runtime/catalog/README.md`](../runtime/catalog/README.md)):
  `<source_files>` source files, `<declared_dependencies>` declared
  dependencies, `<flow_candidates>` flow candidates, `<confirmed_profiles>`
  confirmed profiles → `small` | `medium` | `large`;
  `<compact|standard>` layout suggested (see
  [`../references/docs-tree.md`](../references/docs-tree.md) "Compact
  layout"). Small is under 50 source files; dependency breadth (40+) and
  flow breadth (10+ indexed flow candidates) promote a small repo to
  medium. A small repo with many tracked config/docs files but little
  source is still small; this is a file-count signal, not a coverage
  judgment.
- Existing documentation note when `docs/` (or equivalent) is already present,
  with a brief evidence note such as an API schema, web framework manifest,
  library package manifest, pipeline configuration, or infrastructure files.
  When the tree holds foreign `.md` / `.mdx` files (no manifest entry),
  include their count — the unmanaged-document triage (keep self-managed /
  archive, see [`../references/docs-tree.md`](../references/docs-tree.md))
  is a planning-time tree decision, not a scope dimension: no extra intake
  control here.
- Portfolio readiness, only when nested repos were detected: name each
  detected member and its tier, and state plainly whether every member is
  already at Diligence or higher.

Do not initialize a manifest, scaffold files, or ask for side-effect approval
in the brief. Open the scope question pack in the same turn when the host
allows (brief + questions together), or brief first then questions if the host
needs a separate message — but never present scope questions without this
brief. Never silent-confirm detections or gate judgments.

## Scope intake

Present all applicable unresolved questions together in one intake. Explain in
plain language why each question matters, then give every choice a short
consequence so the user can select one answer per question (or multiple answers
where explicitly allowed). Use native single-select and multi-select controls
when the host provides them; otherwise use a concise numbered question set with
lettered options. Do not prescribe an exact screen or require a particular
combined answer syntax.

### Revise selection changes

For a dimension being re-asked because it has a delta or a requested change,
show the current manifest value or values above each control as the baseline.
Do not present a `Keep`
choice, and do not make the user re-select values that are already selected.
Instead, controls represent only requested changes:

- **Scale / layout:** re-derive scale from the same detect run and show
  `Current: <class> / <layout>` when detection disagrees with the manifest.
  When `decided_by` is `detected`, offer `Change to <detected class/layout>`
  as a recommended change; when `decided_by` is `user`, state the detected
  drift as a fact and offer the change without a recommendation — a user
  decision is never silently re-derived, and no change means the manifest
  values stand unchanged (see [`revision.md`](revision.md) "Applying the
  answers to the manifest"). Layout is the first control in the pack — it
  shapes the plan tree every later answer describes.
- **Tier:** show `Current tier: <tier>` and offer `Change to <other tier>` for
  each alternative tier.
- **Profiles and output audiences:** show `Currently selected: <values>` and
  offer `Add <value>` for unselected values and `Remove <value>` for selected
  values. Freshly detected profiles and suitable missing audiences are
  recommended `Add` actions with their evidence or unlock reason.

An empty set of changes preserves the displayed manifest values, but it is not
silent acceptance: include those unchanged values in the final confirmation and
wait for the user's explicit confirmation before reconciling the manifest.

Ask only what remains unresolved, in this order:

1. **Goal or action.** Base this only on the repository root's own manifest
   state — the discovery brief's first bullet — never on a detected member's
   manifest or tier from the Portfolio-readiness bullet; those describe
   collection members, not this session's target. For a repository without a
   manifest, offer creating a new documentation plan or planning without
   writing. When a manifest exists,
   also offer resuming it (plain language / intake goal →
   [`writing.md`](writing.md); no `--resume` flag), checking status or
   staleness (read-only; no `--status` flag — use plain language or
   `manage_manifest.{py,js} status`, see
   [`../runtime/manifest/README.md`](../runtime/manifest/README.md)), updating
   or refreshing a named document,
   revising via `/docforge-revise` (`flow` / `<area>` / `all`, with the same
   `--plan-only` / `--auto-accept` / `--no-dashboard` flags), or replacing the plan. Briefly
   distinguish inspection, planning, writing, and read-only reporting.
   Natural-language **update** / **refresh** of a named document routes to
   [`revision.md`](revision.md) (staleness-first), not a full rewrite.
2. **Documentation layout.** Always asked for a new or plan-only scope —
   never silently defaulted, even when detection suggests one — and always
   before tier, profiles, and audiences, because the layout shapes the plan
   tree every later answer describes. Present a native single-select with
   both layouts, each carrying the detected evidence from the discovery
   brief's scale line:
   - **Compact** — fewer, denser files; the same subjects as Standard at the
     same depth (`docs/product.md` instead of `docs/product/README.md` +
     overview, and so on).
   - **Standard** — one file per subject.
   Mark the detected layout `(suggested — <source_files> source files,
   <declared_dependencies> declared dependencies, <flow_candidates> flow
   candidates, <confirmed_profiles> confirmed profiles)` but never pre-select
   it on the user's behalf. If the reply omits layout, ask one layout-only
   follow-up. The confirmed pick is carried into `init`
   ([`planning.md`](planning.md)): no flag when it matches detection
   (`decided_by: "detected"`), `--layout <compact|standard>` (with
   `--scale-class` when the user also changed the class) when it differs
   (`decided_by: "user"`). Resume or Status omits layout — the manifest
   already resolves it.
3. **Documentation tier.** For a new or plan-only scope, offer Spine
   (essential repository documentation) and Diligence (Spine plus flows,
   risks, security, operations, dependencies, and ADRs) always, or a grounded
   recommendation that Docforge will explain after inspection. Offer
   Portfolio (Diligence plus `docs-portfolio/` diligence views) only when
   nested repos were detected during discovery: if every included member is
   already at Diligence or higher, offer it normally and say why it
   qualifies; otherwise name the lagging member(s) and explain that each
   needs its own separate Diligence run first, rather than listing Portfolio
   as a normal choice (see [`../references/portfolio.md`](../references/portfolio.md)
   "Readiness gate").
4. **Repository profiles.** Require one multi-select per applicable dimension
   (shapes, platforms, frameworks, concerns): a native multi-select or lettered
   multi-select with **recommended** options pre-checked and **also possible**
   options unchecked, each with its evidence or gate reason from the discovery
   brief. Omit a dimension only when detection produced no candidates and no
   weak cues for it. Permit multiple values in every dimension — one overloaded
   cue may map to several aspects when evidence supports it. Shapes describe
   what the repository delivers; platforms describe where it runs; frameworks
   describe how it is built and tailor evidence queries without adding
   framework-specific trees; concerns describe evidenced cross-cutting
   behavior. Detection and the gate never finalize profiles; do not
   silent-confirm them on the user's behalf.
5. **Output audience.** Always present a native multi-select that lists
   **every** catalog audience as a visible option — never drop BA/PO/agents
   from the control:
   - Engineers
   - Beginners
   - Business analysts (BA)
   - Product owners (PO)
   - Coding agents
   - Operators
   - Security reviewers
   BA, PO, coding agents, operators, and security reviewers add their
   catalog-owned views. A yes/no “add more?” with no option list is not
   enough; the unchecked audiences must appear in the same multi-select.
   - **New or plan-only** (audience unresolved): required. Pre-select
     Engineers + beginners as the suggested starting point (matching the
     manifest CLI default when no audience flag is supplied), but never apply
     that default silently — the user must confirm or edit. Leave BA, PO,
     Coding agents, Operators, and Security reviewers unchecked but visible.
     If the reply omits audience, ask one audience-only follow-up that again
     lists all seven options.
   - **Any revise that rediscovers docs** (`/docforge-revise all`,
     `/docforge-revise <area>`, `/docforge-revise flow`, or natural-language
     revise that detects missing / updated / new documents): after analysis,
     compute **suitable missing audiences** — catalog `selection.audiences`
     required by newly selected, missing, or updated documents that are not
     already in the manifest.
      Show the current manifest audiences separately as the baseline. Mark
      suitable missing and discovery-brief evidenced audiences as recommended
      `Add` actions with a one-line reason (which new/missing doc types they
      unlock, e.g. BA → `ba_*`, PO → `po_*`, Coding agents → `agents_*`). Show
      **all seven** actions: `Remove` for current audiences and `Add` for every
      other audience. If the manifest has no audiences, use the new/plan-only
      path above. Never keep defaults silently; preserve an unchanged audience
      set only after the full delta control and explicit confirmation.
   - **Resume or Status**: omit audience when the manifest already resolves
     it; otherwise use the new/plan-only path. Single-document update/refresh
     does not re-prompt audience unless the named document's catalog
   audiences are missing from the manifest — then offer only those suitable
   missing audiences plus the current set (still list all seven).
6. **Graph source, only when unresolved.** With several ready providers, offer
   only those providers. With no ready provider, explain setup paths and their
   approval requirements. With exactly one ready provider, record it as the
   proposed source and skip this question; include it in the final confirmation
   so the user can still ask to compare or change it. When the user picks among
   several ready providers here, carry that id into `planning.md`'s `init` call
   as `--graph-provider`, so it is locked into the manifest for the whole
   session — not narrated only (see
   [`../references/graph/graph-sources.md`](../references/graph/graph-sources.md)
   "Session persistence"). With exactly one ready provider, omit the flag; `init`
   locks it automatically.
7. **Execution mode.** Required whenever the action will plan or write (new
   plan, plan-only, or resume writing). Only Status, staleness-only, or
   revise-flow inventory paths may omit it when no further tree pauses will
   occur. Present a native single-select with these exact labels:
   - **Review** — pause after every new or changed tree for confirmation
   - **Auto-accept (permissionless)** — always display trees and updates, then
     continue without routine conversational pauses; maps to `--auto-accept`
   - **Plan only** — stop after the completed tree and document cards; maps to
     `--plan-only`
   Explain that Auto-accept never approves installation, configuration,
   indexing, refreshes, archive/delete, or other separately approved side
   effects. Do not treat Goal's “planning without writing” as a substitute for
   Execution mode, and never apply execution mode on silent defaults. If the reply
   omits mode, ask one mode-only follow-up.

Collect the applicable answers as one response. If the user supplied one or
more choices in the original request, retain them and include only unresolved
questions in the intake. For Resume or Status, omit tier, audience, and shape
questions that the existing manifest already resolves.

For `/docforge-revise flow`, `/docforge-revise <area>`, `/docforge-revise all`,
or any revise that rediscovers docs, always stop and ask before migration,
detection, or writing — but scale the pack to what is actually unresolved or
changed, never a reflexive full re-ask of every dimension on every run:

- **Execution mode** (and **Scope**, when the invocation is ambiguous) is
  always asked, unless the invocation already supplies `--plan-only` or
  `--auto-accept` — these govern this run and are never read off the
  manifest.
- **Layout** is asked only when scale detection disagrees with the manifest
  or the user requested a change; it is the first control in the pack when
  asked (see Revise selection changes). No delta means state the current
  layout as unchanged instead.
- **Tier** is asked only when the invocation requests a tier change, the
  manifest has no tier, or detection surfaces evidence the current tier no
  longer fits (for example, newly evidenced profiles that unlock a higher
  tier). No such reason means state the current tier as unchanged instead of
  presenting a control. **Exception:** `/docforge-revise all` and any
  invocation that names a tier (`spine` / `diligence` / `portfolio`) always
  present the tier control and always show the selection-change preview
  ([`revision.md`](revision.md) "Annotated plan tree") — even with no delta —
  so a tier-naming run can never change which documents belong silently.
  `<area>` and `flow` keep the delta-aware behavior above; a bare
  `/docforge-revise` still asks nothing.
- **Profiles** (shape / platform / framework / concern) are asked only for
  dimensions with an actual delta: a fresh detection not already selected, or
  a change the user requested. A dimension with no new candidates and no
  requested change is reported unchanged, not re-presented.
- **Output audience** is asked only when there are suitable missing
  audiences or the user requested a change. No delta means state the current
  audiences as unchanged instead.

When Layout, Tier, Profiles, and Output audience all resolve with no delta
and no requested change, skip their controls and show one confirmation summary
with that unchanged baseline plus Scope (if it was ambiguous) and Execution
mode — still an explicit confirmation, not a silent default, just scoped to
what is actually in question. When any of them does have a delta or a
requested change, use the change-only controls in **Revise selection changes**
(`Change to` for layout and tier, `Add` / `Remove` for profiles and output
audience) for those dimensions only, and show the rest as plain baseline
facts in the same confirmation summary — with the manifest's current values
displayed as the baseline throughout. Never proceed on silent defaults;
collect the requested changes in one response, show the confirmation summary,
and wait for explicit confirmation before continuing. If the reply leaves a
material choice missing or ambiguous — including Layout, Output audience, or
Execution mode when required — ask one concise follow-up containing only
those unresolved choices.

After resolving the answers, display one confirmation summary containing the
action, the confirmed layout, tier, every selected profile dimension, and
every selected audience, selected graph provider and its code/flow
capabilities, and execution mode (include “permissionless” in the label when
Auto-accept was selected). The summary restates the confirmed layout with its
detected evidence: `Layout: compact (confirmed — 34 source files, 28 declared
dependencies, 3 flow candidates, 2 confirmed profiles)`. A pick that differed
from detection records `decided_by: "user"` on the manifest via
`init --scale-class` / `--layout` ([`planning.md`](planning.md)); a pick
matching detection records `decided_by: "detected"` with no flags — never a
silent re-derivation either way. Ask
whether to continue, edit a choice, or cancel. Always wait for explicit confirmation
of this intake summary, including when Auto-accept was selected. Only after
confirmation may Docforge initialize or replace a manifest or begin deeper
planning. Later plan-tree pauses follow the selected execution mode.

Show only currently valid choices. Do not offer Resume, status/staleness
check, or `/docforge-revise` when no manifest exists, and do not present a
provider that needs setup as ready. If no code graph is ready, explain that
global installation/MCP wiring is user-run and that an agent-run repository
index build or refresh needs separate explicit approval; selecting a setup
path is not that approval.

## Provider sufficiency rule, in detail

Docforge needs one readable `code_graph`, not one index from every supported
provider. Understand Anything, GitNexus, and CodeGraph are equally trusted
when READY. Missing competitors are normal and must not appear in the standard
intake, plan summary, or readiness table. Never invent a combined
“Understand Anything + GitNexus” (or similar) readiness line unless both were
actually READY and the user selected a primary.

- One ready provider: state it once and proceed with it as the proposed
  default.
- Several ready providers: list only those ready providers and ask which should
  be primary.
- No ready provider: explain the available setup paths and ask the user to
  choose one.
- Selected flow-dependent documents: first use the chosen provider's native
  flow capability; derive provisionally only when it has none. CodeGraph has
  no native `flow_graph` — when it is the only ready code graph, schedule
  Docforge-derived flows and say so explicitly.

For example, `.gitnexus/lbug` with indexed Process nodes satisfies both
`code_graph` and native `flow_graph`. Do not mention absent Understand Anything
or CodeGraph indexes in that case unless the user asks to compare or switch.
Likewise, a READY CodeGraph index alone is sufficient for `code_graph`; do not
mention absent Understand Anything or GitNexus. The all-provider output of
`diagnose_graphs.{py,js}` is troubleshooting detail (see
[`../runtime/graph/README.md`](../runtime/graph/README.md)) and is never the
default
`/docforge` intake.

Explicit requests such as "create diligence API documentation" skip answered
questions; present any materially missing scope questions together. The final
intake confirmation and all side-effect approvals remain mandatory under
`--auto-accept` (see [`../flags.md`](../flags.md)).

## Invocation flags relevant to intake

Shared flag definitions:
[`../flags.md`](../flags.md). Intake-specific effects:

- `--plan-only`: analyze and show the plan / dry-run tree; do not write or
  re-ground document bodies. On `/docforge`, precheck, analyze, initialize the
  complete static manifest, add discovered dynamic documents, and display the
  dry-run tree (no placeholder documents). On `/docforge-revise`, run revise
  analysis and show the structure update / dry-run tree.
- `--auto-accept`: display plans, trees, and results, then continue without
  routine conversational pauses; see [`../flags.md`](../flags.md) for the
  explicit list of excluded side effects.

Structural revise uses `/docforge-revise` (not `/docforge --revise`). There is
no `--resume` or `--status` skill flag.

An explicit single-document **update** or **refresh** follows the Update one
document path in [`revision.md`](revision.md): blob-first, no rediscovery.
**Revise** (`/docforge-revise` all / area / flow) is broader: obsolete docs via
`git_blob`, new docs from detect/catalog, missing files from new instructions,
big-picture and connection updates, and — for revise flow — the full harvest →
organize → derive → write pipeline. `FRESH` blobs do not skip work when new
flows or connections change a document's role. A brand-new single-document
write still requires graph precheck and the full [`writing.md`](writing.md)
path.

Next: once scope is confirmed, proceed to
[`planning.md`](planning.md).
