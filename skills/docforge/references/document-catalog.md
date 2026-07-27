# Document catalog — what each kind of document must present

This is the content contract for every document the skill produces: its job, the one
Diátaxis mode it stays in, the elements it must present, and the material that belongs in a
*different* document. It is grounded in the frameworks each doc type descends from — Diátaxis,
the C4 model, arc42, MADR, Keep a Changelog, RFC 9457, OWASP/STRIDE, the NTIA SBOM minimum
elements, the Data Contract Specification, and the Business Rules Manifesto — so a generated
document matches what a reader who knows the field expects to find.

Use it two ways: when the plan-first cadence (`SKILL.md` Step 0) enumerates the parts, this is
what each part promises to cover; when you write a part (Step 5), this is the checklist of
what "complete" means for that document. Depth within each element follows the deep-by-default
rule in `depth-and-audience.md`; provenance is stamped per `provenance-tracking.md`.

**Each type carries a target depth (an L-level from the ladder in `depth-and-audience.md`).**
It is the concrete bar the independent per-document audit (`document-audit.md`) checks against:
a document that lands below its target with a *derivable* shortfall FAILs the completion gate.
The `Target depth` line on the types below is explicit where depth is the usual failure mode
(architecture, flows, concepts); for every other type the target is its ladder cell — orientation
and lookup types sit at L0/L1, and **any subsystem a new engineer must understand to be
productive defaults to L2/L3**, not a summary.

---

## The one rule that governs the whole tree: one document, one mode

Diátaxis sorts all technical documentation into four modes by what the reader is doing:

| Mode | Reader is… | Answers | Voice |
|---|---|---|---|
| **Tutorial** | learning by doing | "walk me from zero to a working result" | a guaranteed single happy path, no choices |
| **How-to** | accomplishing a task | "how do I do X" | ordered actions for a goal, adaptable |
| **Reference** | looking a fact up | "what is the exact value/signature/key" | austere, neutral, exhaustive, mirrors the product |
| **Explanation** | building understanding | "why is it like this" | discussion, context, trade-offs, alternatives |

**A document declares one primary mode and stays in it.** Mixing modes is the most common way a
document becomes hard to use: explanation bloats a tutorial, how-to steps clutter a reference,
theory buries the commands. When source material genuinely spans modes (a testing doc has both
runnable commands and strategy), **section it explicitly and cross-link** — commands under a
how-to heading, rationale under an explanation heading — rather than blending the prose. Two
document classes are the sanctioned exception: **orientation documents** (root `README.md`,
`product/overview.md`, folder `README.md` indexes) may summarize across modes, but only as a
landing page that delegates depth to the dedicated documents. Everything else picks a lane.

This rule composes with the ones already in force: state each fact once and link (`document-composition.md`),
describe behaviour not code (non-negotiable 6), and go deep by default, cutting only filler
(`depth-and-audience.md`).

---

## Product — for readers who will never open the code

### `product/overview.md` — what this is and why it exists
- **Mode:** Explanation.
- **Target depth:** L0 (orientation for a non-engineer — the stranger test in `quality-bar.md`). Depth here means clarity and completeness of the *why/what/for-whom*, not mechanism; a doc a non-engineer can't use to explain the product is a shortfall even at L0.
- **Must present:** the problem it solves; who it is for (and implicitly who it is not); the value/outcome that makes it distinct; a one-paragraph plain definition (category + capability); where it sits in the wider system (upstream/downstream neighbours, responsibility boundary); 2–5 representative use cases in business terms; links onward to getting-started, capabilities, architecture.
- **Keep out:** install/setup steps, CLI, config keys, API signatures, procedures (→ engineering/reference); an exhaustive feature list (→ `capabilities.md`).

### `product/capabilities.md` — the feature catalog in business language
- **Mode:** Reference (business-language, not technical).
- **Target depth:** L0–L1 (one substantive entry per capability; the bar is *coverage* — every domain capability present with its outcome and role — not per-entry mechanism).
- **Must present:** one entry per capability named in domain language, not code symbols; for each — what it does, the user/business outcome it enables, who uses it (role), the scenario it supports, status where relevant (GA/beta/deprecated) and any edition gating; grouped by domain or user journey with a consistent per-entry shape; cross-links to the how-to and flow docs.
- **Keep out:** implementation, code structure, API signatures, step-by-step how-to (link out), marketing narrative, roadmap promises. Sourced from `/understand-domain`, never hand-typed — see the hard gate in `SKILL.md`.

### `product/roadmap.md` — direction, not commitment
- **Mode:** Explanation.
- **Must present:** a **Now / Next / Later** structure (Now = in development, specced; Next = confident but timing looser; Later = directional/exploratory); framing around customer problems and outcomes, not a feature list; explicit certainty labels so Later items don't read as promises; an explicit not-yet-supported / out-of-scope stance.
- **Keep out:** firm dates beyond Now, guarantees on Later items, a dumped backlog, detailed specs (→ the feature/requirements docs). Roadmap is aspiration and must be labelled as future (non-negotiable: document what runs, not what's planned, except where clearly marked here or in an ADR).

---

## Flows — one business flow per file

### `flows/<flow>.md` (or, once promoted, `<flow>/README.md`)
- **Mode:** Explanation + a how-to spine (the flow's steps), kept in the aligned-topic shape of `document-composition.md`.
- **Target depth:** L1 at the flat-file level (a reader follows the whole flow in plain language). The mechanism (L2) and rules (L1–L2) live in the `engineering.md` / `business-analyst.md` subfiles once promoted — the flat file is *complete* at L1, not shallow, so long as every step and every critical notice is present.
- **Must present:** L0 (what the flow is and why it matters); L1 (how it runs, in plain language, with a Mermaid diagram once there's more than one step or a branch); every critical notice, inline, visible to a reader who never opens a subfile. Standalone.
- **Promotion & per-reader depth:** promote to a `<flow>/` folder with `business-analyst.md` / `engineering.md` / `product-owner.md` subfiles only in the same pass their real content is written (`document-composition.md`). Each subfile's contract is the BA / engineering / PO row below.
- **Keep out:** a folder or "go deeper" link with no subfile behind it; hand-enumerated flows (gated on `/understand-domain` — `SKILL.md`).

---

## Architecture — the system as built, at two altitudes

### `architecture/high-level.md` — the stable map (C4 Context + Container, arc42 §1–4,8)
- **Mode:** Explanation/Reference (the durable structure).
- **Target depth:** L1 (the map — context, containers, boundaries, invariants). Deep mechanism is *out* (it belongs in `low-level.md` / `concepts/`), but L1 here still means every container's responsibility and the cross-cutting invariants are stated — a 46-line "what it is" summary that names boxes without their responsibilities or boundaries is a derivable shortfall, not a complete map.
- **Must present:** system purpose and top 3–5 quality goals; the significant constraints that bound the design; **system context** — the system as one box, the people/roles who use it, the external systems it depends on, and the boundary between them; the **container view** — the deployable/runnable units (services, SPA, databases, queues), each with its responsibility and principal technology, and how they communicate; the solution strategy (top-level approach, not full ADRs); cross-cutting concepts (persistence, security, logging conventions); the **invariants** a reader can't recover from code because they are absences ("nothing under `core/` performs I/O", "handlers never touch the database directly").
- **Techniques:** reference by file/module path, never by private symbol or line number; a reader should be able to draw the box diagram from the prose; restrict to what changes once or twice a year.
- **Keep out:** internal component/class decomposition (→ `low-level.md`); request-by-request sequences (→ `data-flow.md`); the full argument for one choice (→ `decisions/`); deep mechanism, algorithms, failure modes (→ `low-level.md` / `concepts/`).

### `architecture/low-level.md` — component decomposition (C4 Component, arc42 §5)
- **Mode:** Reference/Explanation.
- **Target depth:** L1–L2 (components, their interfaces, the data model described; deeper mechanism per subsystem is delegated to `concepts/`).
- **Must present:** the components inside each building block and their responsibilities, as a whitebox-of-blackboxes hierarchy taken to the depth that helps; provided/required interfaces and contracts of each; the data model *described* (key entities, relationships, ownership) — not dumped from schema; an index into `concepts/<subsystem>/` for subsystems that earn a full deep-dive.
- **Keep out:** external actors and system-wide context (→ high-level); why a technology was chosen (→ ADR); end-to-end runtime flows (→ data-flow); pasted code.

### `architecture/data-flow.md` — the runtime view (C4 Dynamic, arc42 §6)
- **Mode:** Explanation.
- **Target depth:** L1–L2 (ordered interactions per scenario, with error/operational behaviour along the path).
- **Must present:** the important behavioural scenarios as **ordered/numbered interactions** — which container or component handles each step from entry point to result; interactions at critical external interfaces; error, exception, and operational behaviour along the path.
- **Keep out:** a static catalogue of every component (→ low-level); rationale (→ ADR). Cover the interesting and recurring paths, not every possible call.

### `architecture/concepts/<subsystem>.md` (promoted: `<subsystem>/engineering.md`) — deep mechanism
- **Mode:** Explanation (L2–L3).
- **Target depth:** L2–L3 — the deepest bar in the tree. This is where the "orientation masquerading as documentation" failure hits hardest: a concept doc that says what a subsystem *is* without algorithm, invariants and why they hold, concurrency, and failure modes is a derivable shortfall and FAILs the audit.
- **Must present:** how the subsystem actually works — algorithm, the invariants and *why they hold*, concurrency assumptions, failure modes, trade-offs. This is the default depth for any subsystem a new engineer must understand (`depth-and-audience.md`); `/understand-explain <module>` is the required source, not optional.
- **Keep out:** whole-system context; pasted code or symbol/line anchors; rationale that belongs in an ADR.

### `architecture/decisions/NNNN-<slug>.md` — ADRs
- **Mode:** Explanation. **Full treatment in `decision-records.md`** — do not restate it here.
- **Must present (the contract):** title as an outcome; status (proposed/accepted/superseded-by/deprecated) with date and deciders; context and problem statement (the forces, value-neutral); considered options; the decision ("We will…") and the reasoning that was decisive; consequences (positive, negative *named*, neutral); "revisit if". One decision per record, immutable once accepted.
- **Keep out:** system structure/diagrams (link them); how-to; project background beyond the forces on this one decision. An ADR records a decision already made — it is not a forward design proposal, and the skill documents what runs, so it produces ADRs, not RFC/design docs.

### `architecture/dependencies.md`
- **Mode:** Reference + a thin Explanation layer. **Full template in `risk-docs.md`.**
- **Must present (the contract):** per direct runtime dependency — name, purpose (what feature it backs), licence (SPDX), version constraint, criticality, and "if it disappeared"; per external service — auth, data exchanged, limits, **failure handling** (timeout/retry/circuit-breaker/fallback), contract (pinned version, deprecation notice, SLA), region; a dependency policy; a pointer to the generated SBOM (the exhaustive machine list) so this file stays the human judgement layer.
- **Keep out:** hand-enumerated transitive trees (generate the SBOM); supply-chain threat mitigation (→ threat-model). See `risk-docs.md` for the NTIA minimum fields the generated SBOM must carry.

### `architecture/tech-debt.md` and `architecture/constraints.md`
- **Mode:** Reference. **Full treatment and the three-way litmus in `risk-docs.md`.**
- **`tech-debt.md` must present:** per item — the shortcut taken and why, the affected area, impact × likelihood, the interest it accrues, a remedy/effort estimate, owner and status. Internal, fixable-with-effort.
- **`constraints.md` must present:** per constraint — the fixed boundary the team cannot change (physics/protocol, platform/vendor, regulatory, mandated stack), its source, and its design implication. Not a to-do list.
- **Keep out / the litmus:** *fixable by us later* → tech-debt; *unfixable by anyone* → constraint; *won't/needn't fix and user-visible* → `reference/limitations.md`. Never log a constraint as debt (nothing to pay down) or fixable debt as a limitation (it hides a remediable cause).

---

## Engineering — for contributors before their first merge

### `engineering/setup.md` — zero to running
- **Mode:** Tutorial (getting-started) — one guaranteed happy path.
- **Must present:** prerequisites with exact versions, tools, accounts, credentials up front; a wall-clock time-to-run estimate; a single ordered, copy-pasteable command sequence with **no forks**; a visible expected result after the meaningful steps; an explicit end-to-end verification ("you should see X"); a bounded troubleshooting list of failures that actually happened; next steps. If a step needs access someone must grant, name who grants it. Verify every command by running it.
- **Keep out:** why/architecture (link out), alternative paths and optional configs, exhaustive flag reference (→ `configuration.md`), edge cases beyond the common failures. Don't make the learner choose anything.

### `engineering/testing.md`
- **Mode:** Split — how-to for running, explanation for strategy; section the two, don't blend.
- **Must present:** exact commands (full suite, single test, watch) with prerequisites and how to read pass/fail; where tests live, naming, how to add one; the test categories/pyramid and when each runs (local vs CI); what coverage means here — how it's measured, the threshold, and its limits (coverage ≠ correctness); fixtures/mocks/test-data conventions; what gates a merge.
- **Keep out:** product feature descriptions; test-runner config (→ `configuration.md`); letting strategy prose bury the commands.

### `engineering/conventions.md`
- **Mode:** Reference with a thin how-to (how to auto-fix).
- **Must present:** the rules as clear directives (naming, formatting, layout, imports, error handling, commit/branch format, review expectations); correct-vs-incorrect examples for the non-obvious ones; the formatter/linter that enforces each rule and the command to run it; the scope each rule applies to; brief rationale only where a rule is surprising.
- **Keep out:** design-philosophy essays (→ explanation), product/setup content, and restating what the linter config already enforces — point to it as the source of truth.

### `engineering/release.md`
- **Mode:** How-to.
- **Must present:** how a change moves from merge to production — the branch/tag/version step, the promotion path, approvals, and the link to the operational deployment mechanics.
- **Keep out:** environment topology and rollback mechanics (→ `operations/deployment.md` — link, don't duplicate); user-facing release framing (→ release notes).

---

## Operations — for whoever is on call

### `operations/deployment.md`
- **Mode:** Reference/How-to.
- **Must present:** the environments (dev/staging/canary/prod), each one's purpose, parity gaps, and the promotion path; production topology (services, regions, data stores, load balancers, external deps, traffic flow); the rollout strategy (blue-green/canary/rolling) and the gates that advance or halt it; a tested rollback strategy — triggers, who decides, expected recovery time, migration-reversibility caveats; the release procedure (pre-flight checklist, artifact/version, config & secrets handling, DB-migration ordering, feature-flag coordination); post-deploy verification signals; ownership, approvals, freeze windows.
- **Keep out:** incident remediation (→ runbooks); CI internals; IaC source (link, don't inline).

### `operations/observability.md`
- **Mode:** Reference/Explanation.
- **Must present:** the three pillars for this service — metrics (the golden signals: latency, traffic, errors, saturation), logs (structure, destination, retention), traces (request paths across components); the SLIs measured and how each is computed; SLOs, their measurement window, and the error-budget policy that gates releases; the dashboard catalogue (what each shows, its audience, where it lives); the alert catalogue — condition, threshold, severity, the SLO it protects, and the runbook each alert links to; the instrumentation/labeling conventions.
- **Keep out:** step-by-step remediation (→ runbooks); infra provisioning (→ deployment); vendor tool tutorials.

### `operations/runbooks/<symptom>.md`
- **Mode:** How-to, written for someone under pressure at an inconvenient hour.
- **Must present:** a **symptom-first entry** keyed to the alert the pager fired, not the internal fault name; a severity/impact statement; preconditions (access, tools, flags, safety checks); **numbered imperative steps** to diagnose → mitigate → resolve, with exact commands, decision branches, and expected output per step; verification of each step and the overall fix (what "healthy" looks like); the escalation path (who to page next, when, how); a rollback/mitigation-before-root-cause path; communication/status-update wording; metadata (owner, last-reviewed, links to dashboards and related runbooks).
- **Keep out:** root-cause narrative and lessons learned (→ postmortem); architecture rationale; anything not directly actionable. Terse and executable.

---

## Reference — lookup, not narrative

### `reference/configuration.md`
- **Mode:** Reference — exhaustive, structure mirrors the actual config surface.
- **Must present:** a table, one row per key the code actually reads (verify by grepping the accessor, not by copying an old `.env`): name (exact case), type, default, required (and under what condition), allowed values/range/format, one-sentence description, scope/where-set (env/file/flag, runtime vs build-time), and where useful example value, since-version, and secret-sensitivity. Every key that exists is listed; none that doesn't. Show secret *shape* (`sk_live_<32 hex>`), never a real value.
- **Keep out:** setup narrative, "why this default" discussion (→ explanation), task walkthroughs.

### `reference/limitations.md`
- **Mode:** Reference. **Full template in `risk-docs.md`.**
- **Must present (the contract):** three labelled sections — **known limitations** (by-design boundaries: area, limitation, impact in the reader's terms, workaround, tracking), **known issues** (present defects with symptom, affected versions, status, tracker link), and **not supported** (things a reasonable person expects and won't find); plus the tested scale/performance envelope and deployment-specific caveats; a review date.
- **Keep out:** internal code shortcuts and refactor plans (→ `tech-debt.md`); unfixable external boundaries (→ `constraints.md`). Limitations are externally observable facts for users. Keep the three sub-categories distinct.

### `reference/glossary.md`
- **Mode:** Reference.
- **Must present:** one entry per domain term, alphabetical; a concise neutral definition in domain language; context/scope and "not to be confused with" disambiguation; the canonical spelling/casing (the ubiquitous language the codebase and team share); cross-links to related terms and the docs that use them; a consistent one-line format.
- **Keep out:** how-to steps, tutorials, and long essays on a concept (link to an explanation doc); opinion or rationale inside the definition.

### `reference/errors.md` — API error catalog *(API overlay)*
- **Mode:** Reference. See `overlay-api-service.md` for the surrounding API docs.
- **Must present (RFC 9457 Problem Details):** per problem type — a stable **`type`** URI that dereferences to docs (the catalog key), a constant human-readable **`title`**, the advisory HTTP **`status`**, an occurrence-specific **`detail`** oriented to helping the client fix it, and an **`instance`** identifier; plus a stable machine-readable **error code** distinct from the HTTP status (e.g. `USER_NOT_FOUND`), a consistent message format, a resolution/`documentation_url` per code, and any structured extension members. Served as `application/problem+json`.
- **Keep out:** overloading HTTP status as the only signal; parse-dependent data in `detail` (use extensions); stack traces or internal detail; titles/codes that drift per occurrence — they must be stable.

---

## Security — external reporter + posture reviewer

### `security/README.md` (posture) and root `SECURITY.md` (disclosure)
- **Mode:** Reference/Explanation. **Full templates in `risk-docs.md`.**
- **Root `SECURITY.md` must present:** how to report privately (a role address, never a public issue), supported versions, the coordinated-disclosure policy and timeframe, and a response SLA you can actually meet. A `security.txt` (RFC 9116) carries at least **Contact** and **Expires**.
- **Keep out:** internal threat analysis (→ threat-model); credentials, internal hostnames, unremediated vulnerability detail; individuals' names as contacts (use a role address).

### `security/threat-model.md`
- **Mode:** Explanation. **Full treatment in `risk-docs.md`.**
- **Must present (OWASP four-question / STRIDE):** the assets worth protecting; the actors including adversaries; the entry points/attack surface; the **trust boundaries** where trust level changes; a data-flow diagram with those boundaries drawn on it; threats enumerated per element (STRIDE: spoofing, tampering, repudiation, information disclosure, denial of service, elevation of privilege); a mitigation per threat (mitigate/eliminate/transfer/accept) with a testable control; and the explicitly accepted/out-of-scope risks — the section reviewers read most closely.
- **Keep out:** disclosure logistics (→ SECURITY.md); the full data inventory (→ data-handling — reference its classifications, don't duplicate them).

### `security/data-handling.md`
- **Mode:** Reference. **Full treatment in `risk-docs.md`.**
- **Must present:** data classification tiers and what falls in each; an inventory of data categories, especially PII/PHI/financial, and where each lives; data flow/lineage from origin through processing, storage, to deletion; retention and deletion procedures (including subject-deletion requests); residency/sovereignty and per-region constraints; access controls and encryption in transit and at rest; the compliance regimes that apply, citing the specific obligation.
- **Keep out:** adversarial threat enumeration (→ threat-model); deployment topology; report intake (→ SECURITY.md). This is the authoritative record of what data exists and its rules; the threat model consumes it.

---

## Contributing — process

### `contributing/README.md`, `ownership.md`, `templates/`
- **Mode:** How-to.
- **Must present:** the change workflow (branch → review → merge → release); who owns which paths and decisions (`ownership.md`); host-neutral issue/change templates. This is the one area where a single forge-specific pointer is permitted — confined per `host-neutrality.md`.
- **Keep out:** architecture, product, and reference content — link to it.

---

## Root pointers and the index

### Root `README.md` — the audience router
- **Mode:** Orientation (blends a short explanation with minimal how-to fragments).
- **Must present:** the title matching the repo/package; a one-line description (<120 chars, matching the registry/repo description); optional badges; a short background (what problem, provenance, key dependencies); a runnable install block with prerequisites; a usage example with expected output; where to contribute; the licence (SPDX) last; and explicit links into `docs/`. A table of contents once it exceeds ~100 lines.
- **Keep out:** full tutorials, exhaustive reference, deep architecture essays, long troubleshooting — link to the dedicated docs. Written after the front-door set because it summarizes them (`SKILL.md` Step 5). Stays a thin router; never duplicates its `docs/` counterpart.

### `docs/README.md` — the index and audience router
- **Mode:** Orientation.
- **Must present:** a one-line repo description; a table mapping audience → starting document; the folder map with one line each. Routing, not content — if a reader has to guess which folder to open, it has failed.

### Root `CHANGELOG.md` — the technical, exhaustive history
- **Mode:** Reference. Follows **Keep a Changelog** + **SemVer**.
- **Must present:** one entry per version, newest first, each with its release date; changes grouped under **Added / Changed / Deprecated / Removed / Fixed / Security**; an **Unreleased** section at the top; linkable versions; a statement of whether the project follows SemVer (MAJOR breaking / MINOR compatible feature / PATCH fix). Curated for humans — notable changes, not a commit dump.
- **Keep out:** raw commit logs, marketing prose, screenshots, and "why it matters" framing — that's release notes. Never merge the two.

---

## Overlay documents

The repo-type and audience overlays add further documents; each overlay reference (`overlay-*.md`)
owns the detail. The content contracts research surfaced for the ones most often confused:

### Data contract *(data-pipeline overlay)* — `overlay-data-pipeline.md`
- **Mode:** Reference.
- **Must present**, per dataset — owner and physical location; update cadence and freshness SLA; grain (one row per what, per what period); schema (column, type, nullable, description, PII); semantics (definitions of anything ambiguous — status values, currency, timezone, late-data handling); quality guarantees (what is enforced, and the negative case stated explicitly); change policy (notice period and channel for breaking changes); known consumers and what breaks for each if the contract changes.
- **Keep out:** pipeline/transformation code beyond what a consumer needs; undocumented ad-hoc fields; SLAs stated as aspirations without targets; implicit ownership. `overlay-api-service.md` has no equivalent document — an API's own response shapes are the API reference (`reference/api.md`), not a separate data contract.

### Business rules *(BA overlay)* — `overlay-business-analyst.md`
- **Mode:** Reference (declarative, business-owned). Follows the Business Rules Manifesto.
- **Must present**, per rule — a plain-language rule name (the entry's identifier); a declarative statement in business vocabulary a stakeholder would recognize; where it's enforced (module, by path — behaviour, never a private symbol or line number); which flow/entity it applies to; its exceptions (state "none found" rather than omitting the field); and its source (the `/understand-chat` query and date that verified it). Kept separate from process so one rule spans many flows.
- **Keep out:** feature descriptions, KPIs, product value (→ PO feature catalog); system-enforcement/implementation detail (→ requirements); rules stated as a solution ("the system shall…") — state the business constraint. Sourced from `/understand-domain` / `/understand-chat`, gated on the domain graph.

### Requirements traceability matrix *(BA overlay)* — `overlay-business-analyst.md`
- **Mode:** Reference (links + status, not prose).
- **Must present:** one row per requirement — the requirement in the stakeholder's own wording where recoverable (else inferred from code, with only the unrecoverable phrasing marked by a typed token); the business rule(s) in `business-rules.md` implementing it; the code location; test coverage (file/name, or "none — flag"); and status (implemented / partial / not started).
- **Keep out:** narrative rationale (→ requirements/rules docs); design discussion; anything not linkable to a rule or code location. The orphan rows it surfaces (untested requirement, unimplemented requirement) are the defects it exists to catch.

### Feature catalog & success metrics *(PO overlay)* — `overlay-product-owner.md`
- **Mode:** Reference/Explanation.
- **Must present:** per feature — name and user/business value (problem solved, outcome), framed for the customer; success metrics/KPIs each with a target, a metric owner, and a review cadence; the acceptance criteria / definition-of-done (functional + non-functional conditions); status/adoption.
- **Keep out:** business-rule constraints, thresholds, policy logic (→ BA rules); implementation; traceability plumbing. Focus is value + measurable success. Don't confuse acceptance criteria (this feature's done-ness) with business rules (org-wide constraints).

### Release notes *(PO overlay)* — `overlay-product-owner.md`
- **Mode:** Explanation, user-facing.
- **Must present:** benefit-framed, audience-appropriate prose for end-users/stakeholders; only the key features, improvements, and resolved UX issues; what's new and *how it helps*, with screenshots/links to feature pages where useful; optionally split technical vs non-technical.
- **Keep out:** every small fix and internal change, exhaustive version history, raw category lists — that's the changelog. Changelog is complete-technical-for-devs; release notes are curated-benefit-for-users. Never collapse the two.
