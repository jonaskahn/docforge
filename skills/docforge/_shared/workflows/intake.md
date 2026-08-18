# Intake

Owns: bare `/docforge`, safe discovery, profile detection, discovery gate,
discovery brief, two-turn scope questions, confirmation gate, graph-provider
choice.

## Bare `/docforge` invocation

Trigger: `/docforge` with no task, flags, tier, or typed profile document
request. Begin **interactive intake**. Never initialize a manifest, scaffold
a file, build/refresh a graph, install a provider, change configuration, or
archive/delete anything.

Safe discovery, in order:

1. Identify the repository root.
2. Check whether `.docforge/manifest.json` exists.
3. Run the read-only code-graph precheck.
4. Run `detect_profiles.{py,js}` inline for candidate shapes, platforms,
   frameworks, concerns
   ([`../runtime/catalog/README.md`](../runtime/catalog/README.md)).

Evidence strength (`detect_profiles.{py,js}`):

- **Strong**: declared dependencies, read structurally from
  project-definition manifests (`package.json`,
  `pyproject.toml`/`requirements.txt`, `pom.xml`, `build.gradle*`,
  `go.mod`, `Cargo.toml`, `Gemfile`, `composer.json`, `*.csproj`,
  `pubspec.yaml`) — never substring matching.
- **Weak**: path fragments, content keywords. Never confirm a profile on
  weak cues alone; the same noun or team term can mean different aspects
  across projects, stacks, domain language.

Discovery gate:

- `detect_profiles.{py,js} --emit-gate-pack` sets `needs_gate` → run the
  gate before the brief: follow
  [`../references/discovery-gate.md`](../references/discovery-gate.md),
  ground decisions only in the bounded pack, emit judgment JSON
  (`promote` / `keep` / `demote` / `drop` / `propose`).
- Apply the judgment with the `discovery_gate` library API
  (`runtime/catalog/{python/discovery_gate.py,js/discovery_gate.js}`; see
  [`../runtime/catalog/README.md`](../runtime/catalog/README.md)).
- Invalid judgment → fail open to deterministic ranks.
- Detection and the gate propose profiles; never confirm them.

Graph provider: one ready provider → it is the proposed default (provider
sufficiency rule below). Read-only selection: never permission to build,
refresh, install, or configure anything.

Nested repos:

- Root contains any nested `.git` directory (candidate multi-repo
  workspace) → also run the read-only `discover_child_repos.{py,js}`
  ([`../references/portfolio.md`](../references/portfolio.md)) to learn
  each detected member's tier.
- Discovery only: never decides inclusion, never offers Portfolio. Feeds
  the brief and the tier question.

Paired discovery — `detect_profiles` + nested-`.git` check = one step;
never refresh one alone:

- Material repo change after this pass, before Tier finalized (dir gains
  content, user confirms code arrived, anything altering profile evidence
  / member set) → re-run step + refresh brief before (re)asking Tier.
- Never finalize Tier from a brief the repo has outgrown.

## Discovery brief

Present after safe discovery (and the gate when `needs_gate`),
**before** any scope questions:

- Repository root + manifest existence (manifest exists: its tier, typed
  profiles, incomplete count).
- Code-graph readiness: name each ready provider, or none ready + setup
  offered only if graph source is unresolved. Never list absent providers
  as choices. Zero root profile evidence + nested repos detected → state
  the root has no source of its own to graph (expected for a pure
  collection root, not a setup gap); offer no graph setup for the root.
- **Recommended** vs **also possible** profile rows (shapes, platforms,
  frameworks, concerns), each with a one-line evidence or gate reason.
- Scale (gate pack `scale`, see
  [`../runtime/catalog/README.md`](../runtime/catalog/README.md)):
  `<source_files>` src, `<declared_dependencies>` deps,
  `<flow_candidates>` flow candidates, `<confirmed_profiles>` confirmed →
  `small` | `medium` | `large`; suggested layout `<compact|standard>`
  ([`../references/docs-tree.md`](../references/docs-tree.md) "Compact
  layout"). small = <50 source files; dep breadth 40+ or flow breadth
  10+ indexed flow candidates → medium. Many tracked config/docs files,
  little source → still small (file-count signal, not coverage judgment).
- Existing documentation note when `docs/` (or equivalent) exists, with
  brief evidence (API schema, web framework manifest, library package
  manifest, pipeline configuration, infrastructure files). Foreign
  `.md` / `.mdx` files (no manifest entry) → include their count.
  Unmanaged-doc triage (keep self-managed / archive,
  [`../references/docs-tree.md`](../references/docs-tree.md)) is a
  planning-time tree decision, not a scope dimension: no intake control.
- Portfolio readiness, only when nested repos detected: name each member
  + tier; state whether every member is already at Diligence or higher.

Brief rules:

- Never initialize a manifest, scaffold files, or ask for side-effect
  approval in the brief.
- Open Turn 1 in the same message as the brief when the host allows it;
  else brief first, Turn 1 next. Never present scope questions without
  this brief.
- Never silent-confirm detections or gate judgments.

## Turn structure

Intake asks its scope questions in exactly two turns.

| Turn | Asks | Why it is separate |
|---|---|---|
| 1 — Direction | Goal or action (Scope, on revise), Documentation layout, Target readers (fresh start only), and Flow mode (revise, flow-touching scopes only) | Layout fixes the shape of the tree that every later answer describes; the reader pick decides whether the agent-context group is generated at all; flow mode decides how much of the flow index is re-derived before anything is sized |
| 2 — Scope | Tier, repository profiles, output audience, graph source, execution mode | These describe the content *inside* the tree Turn 1 fixed |

Pack rules:

- Never present layout in the same turn as tier, profiles, audiences, or
  execution mode.
- Open Turn 2 only after Turn 1 is answered.
- Turn 2 never re-presents Goal or Layout as controls; only as confirmed
  baseline facts.
- Confirmation summary: last step of Turn 2's pack (the host's `Confirm`
  control) or a separate message after it. Never merge it into Turn 1.
- A turn whose questions are all already resolved is skipped, never shown
  empty.

## Scope intake

- Ask only unresolved questions, in order below; present one turn's
  unresolved questions together.
- Explain why each question matters; give every choice a short
  consequence. One answer per question; multiple where explicitly
  allowed.
- Native single-select / multi-select controls when the host provides
  them; else a numbered question set with lettered options. Never
  prescribe an exact screen or a combined answer syntax.
- Collect each turn's applicable answers as one response.
- Original request already supplied choices → retain them; present only
  unresolved questions.
- Resume or Status: omit tier, audience, profile questions the manifest
  already resolves.

### Revise selection changes

When a dimension is re-asked because it has a delta or a requested change:

- Show the current manifest value(s) above each control as the baseline.
- Never present a `Keep` choice. Never make the user re-select values
  that are already selected. Controls represent only requested changes.
- **Scale / layout:** re-derive scale from the same detect run.
  Detection disagrees → show `Current: <class> / <layout>`.
  `decided_by: "detected"` → offer `Change to <detected class/layout>`
  as a recommended change. `decided_by: "user"` or `"migration"` →
  state the drift as a fact, offer the change without recommendation. A
  user or migration decision is
  never silently re-derived; no change → manifest values stand unchanged
  ([`revision.md`](revision.md) "Applying the answers to the manifest").
  Layout belongs to Turn 1 and is the first control in that pack.
- **Tier:** show `Current tier: <tier>`; offer `Change to <other tier>`
  per alternative tier.
- **Profiles and output audiences:** show `Currently selected: <values>`;
  offer `Add <value>` for unselected values, `Remove <value>` for
  selected values. Freshly detected profiles and suitable missing
  audiences are recommended `Add` actions with evidence or unlock
  reason. Exception: coding agents appears only as a `Remove` action (or
  through the `/docforge-revise agents` repair), never as an `Add` in
  this control.

An empty change set preserves the displayed manifest values but is not
silent acceptance: include the unchanged values in the final confirmation
and wait for explicit confirmation before reconciling the manifest.

### Turn 1 — Direction

1. **Goal or action.** Base only on the repository root's own manifest
   state (the brief's first bullet) — never on a detected member's
   manifest or tier from the Portfolio-readiness bullet; those describe
   collection members, not this session's target.

   - No manifest: offer a new documentation plan, or planning without
     writing.
   - Manifest exists: also offer resume (plain language / intake goal →
     [`writing.md`](writing.md)), status or staleness check (read-only;
     plain language or `manage_manifest.{py,js} status`, see
     [`../runtime/manifest/README.md`](../runtime/manifest/README.md)),
     update/refresh of a named document, revise via `/docforge-revise`
     (`flow` / `<area>` / `all`, same `--plan-only` / `--auto-accept` /
     `--no-dashboard` flags), or replace the plan.
   - Briefly distinguish inspection, planning, writing, read-only
     reporting.
   - Natural-language **update** / **refresh** of a named document
     routes to [`revision.md`](revision.md) (staleness-first), never a
     full rewrite.

2. **Documentation layout.** Turn 1 resolves layout — never silently
   defaulted, never deferred to Turn 2. Ask per table:

   | Repository / invocation state | Layout in Turn 1 |
   |---|---|
   | No manifest | **Asked.** Both layouts; detected one marked `(suggested — …)`, never pre-selected |
   | Manifest exists and the goal may replace the plan | **Asked**, with the qualifier line below |
   | Manifest exists and detection drifted from `project.scale` | **Asked** as a `Change to <detected layout>` control (see Revise selection changes) |
   | Manifest exists, no drift, goal is Resume / Status / single-document update | **Not asked.** Stated as a baseline fact in the confirmation summary |
   | Goal is Portfolio, or the invocation names the `portfolio` tier | **Not asked.** `standard` is stated as a fixed consequence of the tier |
   | `/docforge-revise all`, or any invocation that names a tier | **Not forced by the tier naming.** That exception adds a control only for Tier in Turn 2; layout still follows the drift / requested-change rule above — asked on a drift or a requested change, stated as unchanged otherwise |

   Options (single-select; each carries the detected evidence from the
   brief's scale line):

   - **Compact** — fewer, denser files; same subjects as Standard
     (`docs/product.md` instead of `docs/product/README.md` + overview).
     Covers Spine and Diligence only. File count = f(layout, tier):
     roughly 8 files at Spine, 15 at Diligence; a confirmed shape or
     more flows adds sections, not files.
   - **Standard** — one file per subject; tree grows with every
     confirmed profile. Flow documents are confirmed at the write-start
     flow gate, not at intake: their count is not part of this turn's
     math. The only layout Portfolio supports.

   **Compact excludes Portfolio.** Compact cannot hold Portfolio — see
   [`../references/docs-tree.md`](../references/docs-tree.md) "Compact
   layout" (rule) and
   [`../references/portfolio.md`](../references/portfolio.md) "Layout"
   (why). Nested repos detected (brief's Portfolio-readiness bullet) →
   say so here: choosing Portfolio in Turn 2 switches layout to
   standard; the confirmation summary carries that change (see tier
   question below).

   Layout rules:

   - Mark the detected layout `(suggested — <source_files> source files,
     <declared_dependencies> declared dependencies, <flow_candidates>
     flow candidates, <confirmed_profiles> confirmed profiles)`; never
     pre-select it. Reply omits layout → one layout-only follow-up
     before Turn 2.
   - Goal still open in the same pack → add qualifier: "Layout applies
     only if you create or replace a plan; Resume and Status use the
     layout already recorded in the manifest." Chosen goal turns out not
     to use layout → discard the layout answer, report the manifest
     value as a baseline fact, never silently apply the discarded
     answer.
   - Carry the confirmed pick into `init` ([`planning.md`](planning.md)):
     matches detection → no flag (`decided_by: "detected"`); differs →
     `--layout <compact|standard>` (plus `--scale-class` when the class
     also changed) (`decided_by: "user"`).

3. **Target readers.** Fresh starts only. Ask once, in Turn 1: the pick
   decides whether the agent-context group is generated; Turn 2 never
   re-asks it. Single-select:

   - **Both** (recommended) — human-facing documentation + coding-agent
     context: `AGENTS.md`, `CLAUDE.md`, `CLAUDE.local.md`,
     `.claude/settings.json`, seven topic views under `docs/agents/`
     (compact: one seven-section `docs/agents.md`).
   - **AI coding agents** — coding-agent context only. Write no
     human-facing documentation. Every agent-context output is
     self-contained and contains zero documentation references,
     regardless of whether human documentation exists now or is added
     later.
   - **Human readers** — human-facing documentation only; generate no
     coding-agent context.

   Consequences:

   - Never re-ask the pick. Turn 2's Output audience control lists the
     six reader audiences only and reports the pick as a baseline fact —
     `Coding agents: included (from your reader choice)` or
     `Coding agents: not generated` (see Output audience below).
   - **Tier is reported as a fact when the pick is `AI coding agents`.**
     Run `manage_manifest.{py,js} preview` for the agent scope at
     `spine` and `diligence`; equal counts → report instead of asking:
     `Tier: spine — every agent-context document is Spine-tier; a higher
     tier adds nothing inside this scope`. Still record the tier (a
     later widened run may use it). Turn 2 then asks only graph source
     and execution mode; tier, profiles, audiences are baseline facts,
     never controls — nothing in them changes the agent-only projection.
   - **The pick maps to init flags exactly** — single canonical mapping:
     [`planning.md`](planning.md) "Target readers → init flags"; never
     invent another flag combination for agent-context documents.
   - Confirmation summary gains one line: `Target readers: Both — AI
     coding agent context included` | `Target readers: AI coding agents
     — agent-context scope only` | `Target readers: Human readers — no
     agent context generated`.

### Turn 2 — Scope

Open only after Turn 1 is answered. Restate confirmed goal and layout as
baseline facts at the top of the pack, never as controls.

4. **Documentation tier.** New or plan-only scope: always offer Spine
   (essential repository documentation) and Diligence (Spine + flows,
   risks, security, operations, dependencies, and decision records where
   history evidences them), marking one as the grounded recommendation
   Docforge will explain after inspection. Decision records are conditional
   by nature — `harvest_candidates` proposes them from history and the user
   selects; a repository whose history evidences none gets no decisions
   folder, which the tier description must not over-promise.
   Offer Portfolio (Diligence + `docs-portfolio/` diligence views) only
   when nested repos detected: every included member at Diligence or
   higher → offer it normally and say why it qualifies; else name the
   lagging member(s) and state each needs its own separate Diligence run
   first — never list Portfolio as a normal choice
   ([`../references/portfolio.md`](../references/portfolio.md) "Readiness
   gate").

   Turn 1 confirmed **compact**: still list Portfolio whenever the
   readiness gate passes — never hide a tier the repository qualifies
   for — labeled `Portfolio (requires standard layout — selecting it changes
   your layout from compact to standard)`. Portfolio is standard-only;
   compact covers Spine and Diligence. User selects it → the
   confirmation summary carries the layout change and requires explicit
   confirmation.

5. **Repository profiles.** One multi-select per applicable dimension.
   Each dimension is a separate control with its own label, question
   text, and first clause stating its axis; internal catalog ids and CLI
   flags are unchanged. Two dimensions must never share question text or
   an option set. A confirmed `framework` tailors evidence queries; it
   never adds a framework-specific tree.

   | Control label | Catalog dimension | Question text | Axis |
   |---|---|---|---|
   | **Delivers** | `shape` | What does this repository deliver? | The artifact it ships |
   | **Runs on** | `platform` | Where does it run? | Execution environment |
   | **Built with** | `framework` | What is it built with? | Declared frameworks and toolkits |
   | **Behaviors** | `concern` | What cross-cutting behavior does it have? | Evidenced cross-cutting concerns |

   Control rules:

   - **Recommended** options pre-checked, **also possible** unchecked;
     each carries its evidence or gate reason from the brief.
   - Omit a dimension only when detection produced no candidates and no
     weak cues for it.
   - Permit multiple values per dimension; one overloaded cue may map to
     several aspects when evidence supports it.
   - Exactly one candidate, no alternative → state `only candidate —
     confirm it or add your own`; never present a one-item choice that
     reads as a decision.
   - Weak-cues-only dimension → keep the "these are weak candidates"
     framing.
   - Detection and the gate never finalize profiles; never silent-confirm
     them.

6. **Output audience.** Always present a native multi-select with the
   six reader audiences as visible options — never drop BA/PO from the
   control, and never add Coding agents to it (the Turn-1 reader pick
   decides coding agents; see Target readers):

   - Engineers
   - Beginners
   - Business analysts (BA)
   - Product owners (PO)
   - Operators
   - Security reviewers

   BA, PO, operators, security reviewers add their catalog-owned views.
   A yes/no "add more?" without the option list is not enough; unchecked
   audiences must appear in the same multi-select.

   - **Coding agents baseline.** State the Turn-1 reader outcome here,
     never as a control: `Coding agents: included (from your reader
     choice)` for `Both` / `AI coding agents`, or `Coding agents: not
     generated` for `Human readers` (see Target readers). Revise whose
     manifest stores coding-agents → baseline; drop only via `Remove`
     (consequence: `removes AGENTS.md, CLAUDE.md, and the agent views`).
     Repair: `/docforge-revise agents` ([`revision.md`](revision.md)),
     never `Add` here.
   - **New or plan-only** (audience unresolved): required, unless the
     reader pick is `AI coding agents` — then skip this question and
     state tier, profiles, audiences as baseline facts (see Target
     readers). Pre-select Engineers + Beginners (matches the CLI default
     when no audience flag is supplied); never apply that default
     silently — the user must confirm or edit. Leave BA, PO, Operators,
     Security reviewers unchecked but visible. Reply omits audience →
     one audience-only follow-up listing all six options.
   - **Any revise that rediscovers docs** (`/docforge-revise all`,
     `/docforge-revise <area>`, `/docforge-revise flow`, or
     natural-language revise detecting missing / updated / new
     documents): after analysis, compute **suitable missing audiences**
     — catalog `selection.audiences` required by newly selected,
     missing, or updated documents not already in the manifest. Show
     current manifest audiences separately as the baseline. Mark
     suitable-missing and brief-evidenced audiences as recommended `Add`
     actions with a one-line reason (which new/missing doc types they
     unlock, e.g. BA → `ba_*`, PO → `po_*`). Show all six: `Remove` for
     current, `Add` for every other audience. Manifest has no audiences
     → use the new/plan-only path. Never keep defaults silently;
     preserve an unchanged set only after the full delta control and
     explicit confirmation.
   - **Resume or Status:** omit audience when the manifest resolves it;
     else use the new/plan-only path. Single-document update/refresh:
     never re-prompt audience unless the named document's catalog
     audiences are missing from the manifest — then offer only those
     suitable-missing audiences plus the current set (still list all
     six).

7. **Graph source, only when unresolved.** Follow the provider
   sufficiency rule (below). Several ready providers → offer only those.
   None ready → explain setup paths and their approval requirements.
   Exactly one ready → record it as the proposed source, skip this
   question, and include it in the final confirmation so the user can
   still ask to compare or change it. User picks among several ready
   providers → carry that id into `planning.md`'s `init` call as
   `--graph-provider`, locked into the manifest for the whole session —
   not narrated only
   ([`../references/graph/graph-sources.md`](../references/graph/graph-sources.md)
   "Session persistence"). Exactly one ready provider → omit the flag;
   `init` locks it automatically.

8. **Execution mode.** Required whenever the action will plan or write
   (new plan, plan-only, resume writing). May be omitted only on Status,
   staleness-only, or revise-flow inventory paths when no further tree
   pauses will occur. Single-select, exact labels:

   - **Review** — pause after every new or changed tree for confirmation
   - **Auto-accept (permissionless)** — display trees and updates, then
     continue without routine conversational pauses; maps to
     `--auto-accept`
   - **Plan only** — stop after the completed tree and document cards;
     maps to `--plan-only`

   Rules:

   - State that Auto-accept never approves installation, configuration,
     indexing, refreshes, archive/delete, or other separately approved
     side effects.
   - Goal's "planning without writing" is not a substitute for Execution
     mode.
   - Never apply execution mode on silent defaults. Reply omits mode →
     one mode-only follow-up.

### Revise: which dimensions each turn actually asks

For `/docforge-revise flow` / `<area>` / `all`, or any revise that
rediscovers docs: stop and ask before any scope decision, detection, or
writing (the idempotent `migrate_metadata` run precedes the brief — see
[`revision.md`](revision.md) "Questions revise asks"). Scale each turn to
what is unresolved or changed — never a reflexive full re-ask. Turn 1
carries Scope, Layout, and Flow mode; Turn 2 carries the rest.

- **Scope** (Turn 1): asked when the invocation is ambiguous.
- **Layout** (Turn 1): asked only when scale detection disagrees with
  the manifest or the user requested a change; first control in that
  pack when asked (see Revise selection changes). No delta → state
  current layout as unchanged.
- **Flow mode** (Turn 1): asked whenever the scope re-harvests flows —
  `/docforge-revise flow`, `/docforge-revise all`, or a natural-language
  revise that touches flows. `<area>` never re-harvests and never asks.
  Single-select, never defaulted silently; option text and consequences
  are owned by [`revision.md`](revision.md) "Questions revise asks".
- **Execution mode** (Turn 2): always asked, unless the invocation
  supplies `--plan-only` or `--auto-accept` — these govern this run,
  never read off the manifest.
- **Tier** (Turn 2): asked only on a tier-change request, a manifest
  with no tier, or detection evidence the current tier no longer fits
  (e.g. newly evidenced profiles unlocking a higher tier). No such
  reason → state current tier as unchanged. **Exception:**
  `/docforge-revise all` and any invocation that names a tier (`spine` /
  `diligence` / `portfolio`) always present the tier control and always
  show the selection-change preview ([`revision.md`](revision.md)
  "Annotated plan tree") — even with no delta — so a tier-naming run can
  never change which documents belong silently. `<area>` and `flow`
  keep the delta-aware behavior; a bare `/docforge-revise` still asks
  nothing.
- **Profiles** (Turn 2 — Delivers / Runs on / Built with / Behaviors):
  asked only for dimensions with a delta — a fresh detection not
  already selected, or a user-requested change. No new candidates and no
  requested change → report unchanged, never re-present.
- **Output audience** (Turn 2): asked only when there are suitable
  missing audiences or a user-requested change. No delta → state
  current audiences as unchanged.

Resolve:

- Layout, Tier, Profiles, Output audience all resolve with no delta and
  no requested change → skip their controls; show one confirmation
  summary with that unchanged baseline plus Scope (if ambiguous) and
  Execution mode. Still an explicit confirmation, never a silent
  default.
- Any delta or requested change → use the change-only controls in
  **Revise selection changes** (`Change to` for layout and tier; `Add` /
  `Remove` for profiles and output audience) for those dimensions only;
  show the rest as plain baseline facts in the same summary, with the
  manifest's current values displayed as the baseline throughout.
- Never proceed on silent defaults. Collect each turn's requested
  changes in one response, show the confirmation summary, wait for
  explicit confirmation. Reply leaves a material choice missing or
  ambiguous (including Layout, Output audience, or Execution mode when
  required) → one concise follow-up with only the unresolved choices,
  in the turn that owns them.

## Confirmation summary

Pre-step: run `manage_manifest.{py,js} preview` with the confirmed scope
([`../runtime/manifest/README.md`](../runtime/manifest/README.md)).
Read-only — writes no manifest, no directories, nothing — inside intake's
no-side-effect boundary.

For a **revise** confirmation (`/docforge-revise` with a scope, or a
natural-language revise), skip the projection, ablation, and density
lines below — those size a *new* scope. Show instead: the changed
dimensions (baseline → requested change), the annotated plan tree
([`revision.md`](revision.md) "Annotated plan tree"), and the
unmanaged-doc triage when found; unchanged dimensions as baseline facts.

Lines:

1. **Projected tree size**, from `preview`:

   `Projected tree size: 15 documents (compact) / 34 (standard)`

   **Flow documents are never inside this projection.** They are dynamic
   and confirmed at the write-start flow gate
   ([`planning.md`](planning.md) "Flow gate (write-start)"), not at
   intake. State that on the summary itself, using the brief's flow
   breadth when the discovery pass already saw a flow index or a native
   flow source:

   `Flow documents: pending write-start selection — 3 candidates at discovery (main deep-dives capped at 15).`

   or, when no flow evidence existed at intake:

   `Flow documents: not yet counted — harvested and confirmed at the write-start flow gate.`

   The corrected count arrives at the gate's structure update, never
   silently.

2. **Ablation.** Name any single selection responsible for **25% or
   more** of the projected documents, using `preview`'s ablation count —
   how many documents disappear if that value is dropped. Reader pick
   `Both` → always include the coding-agents ablation line, computed
   against the `Human readers` projection, even below 25% — the cost of
   agent context must be visible on the summary itself:

   `Coding agents adds 5 of the 34 documents (15%).`

   Reader pick `AI coding agents` → the whole projection is the agent
   context; state that once instead of an ablation line.

3. **Density** (compact layout only): add `preview`'s density line for
   the three densest merged files — a file count alone hides how much
   each file carries:

   `Densest: docs/reference.md — 8 sections; docs/agents.md — 7; docs/architecture.md — 6.`

4. **Spilled groups.** Report every group `preview` marks as **spilled**:
   it reached `COMPACT_SECTION_CAP` and keeps its overflow at standard
   paths — the one case where compact stops being bounded. The user
   hears it before confirming, not discovers it in the tree:

   `docs/architecture.md reached COMPACT_SECTION_CAP; the overflow keeps its own standard paths.`

Summary rules:

- The ablation section is a report, never a gate: never blocks
  confirmation, never drops a selection, never argues the user out of a
  choice. It exists because the dimensions are not equally expensive — a
  platform, a framework, or most concerns often add zero documents and
  only shift narrative emphasis, while one audience can carry a third of
  the tree — and the user cannot see that from the question pack alone.
  Flow documents are excluded from ablation math: they are not selected
  yet, and their cost is reported by the flow gate's own selection
  prompt.
- Display one confirmation summary containing: action, confirmed layout,
  confirmed target readers, tier, every selected profile dimension,
  every selected audience, selected graph provider and its code/flow
  capabilities, execution mode (include "permissionless" in the label
  when Auto-accept was selected). Restate the layout with its detected
  evidence: `Layout: compact (confirmed — 34 source files, 28 declared
  dependencies, 3 flow candidates, 2 confirmed profiles)`.
- Turn 1 confirmed compact and Turn 2 selected Portfolio → state the
  override instead: `Layout: standard (required by Portfolio tier —
the compact pick from Turn 1 does not apply)`. Never silently apply the
  discarded compact answer, and never silently drop it without saying
  so. The manifest records this as `decided_by: "tier-constraint"`.
- Pick differs from detection → `init --scale-class` / `--layout`
  records `decided_by: "user"` on the manifest
  ([`planning.md`](planning.md)); pick matches → `decided_by:
  "detected"`, no flags. Never a silent re-derivation either way.
- Ask whether to continue, edit a choice, or cancel. Always wait for
  explicit confirmation of this summary, including when Auto-accept was
  selected. Only after confirmation: initialize or replace the manifest,
  begin deeper planning. Later plan-tree pauses follow the selected
  execution mode.
- Show only currently valid choices. Never offer Resume,
  status/staleness check, or `/docforge-revise` when no manifest exists;
  never present a provider that needs setup as ready. No ready code
  graph → explain that global installation/MCP wiring is user-run and
  that an agent-run repository index build or refresh needs separate
  explicit approval; selecting a setup path is not that approval.

## Provider sufficiency rule, in detail

One readable `code_graph` is required — not one index from every
supported provider. Understand Anything, GitNexus, CodeGraph are equally
trusted when READY. Missing competitors are normal; never list them in
the standard intake, plan summary, or readiness table. Never invent a
combined "Understand Anything + GitNexus" (or similar) readiness line
unless both were READY and the user selected a primary.

- One ready provider: state it once; it is the proposed default.
- Several ready providers: list only those; ask which is primary.
- No ready provider: explain the available setup paths; ask the user to
  choose one.
- Selected flow-dependent documents: use the chosen provider's native
  flow capability first; derive provisionally only when it has none.
  CodeGraph has no native `flow_graph` — CodeGraph-only → schedule
  Docforge-derived flows and state so explicitly.

Examples:

- `.gitnexus/lbug` with indexed Process nodes satisfies both `code_graph`
  and native `flow_graph`. Never mention absent Understand Anything or
  CodeGraph indexes unless the user asks to compare or switch.
- A READY CodeGraph index alone is sufficient for `code_graph`; never
  mention absent Understand Anything or GitNexus.
- The all-provider output of `diagnose_graphs.{py,js}` is
  troubleshooting detail
  ([`../runtime/graph/README.md`](../runtime/graph/README.md)); never the
  default `/docforge` intake.

Explicit requests such as "create diligence API documentation" skip
answered questions; present any materially missing scope questions in
their own turn. The final intake confirmation and all side-effect
approvals remain mandatory under `--auto-accept`
([`../flags.md`](../flags.md)).

## Invocation flags relevant to intake

Shared flag definitions: [`../flags.md`](../flags.md). Intake-specific
effects:

- `--plan-only`: on `/docforge`, the dry-run tree shows no placeholder
  documents; on `/docforge-revise`, the structure update / dry-run tree
  is shown.
- `--auto-accept` and `--no-dashboard`: no intake-specific effect beyond
  [`../flags.md`](../flags.md).

Structural revise uses `/docforge-revise` (never `/docforge --revise`).

Routing:

- Single-document **update** / **refresh** → Update one document path in
  [`revision.md`](revision.md) (blob-first, no rediscovery).
- **Revise** (`/docforge-revise` all / area / flow) → the full revise
  meaning there.
- Brand-new single-document write → graph precheck + the full
  [`writing.md`](writing.md) path.

Next: once scope is confirmed, proceed to
[`planning.md`](planning.md).
