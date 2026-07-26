# Tier 3 — multi-repo portfolio and diligence packaging

**Applies when:** several repositories are assessed as one system — technical due diligence for an investment or acquisition, a vendor security review, an architecture audit, or simply onboarding an engineer who must understand the whole platform rather than one service.

The problem at this tier is not that documentation is missing but that it is *distributed*. A reviewer with two weeks and five repositories cannot reconstruct the system from five separate READMEs, and what they cannot find, they record as absent. Since reviewer time is finite and adversarial-by-default, the objective is not to prove quality but to make evidence **findable**.

## The portfolio repository

One repository — or one directory in a monorepo — that sits above the others.

```
docs-portfolio/
├── README.md                   what this platform is; the repo map
├── system-context.md           the whole system in diagrams
├── decisions/                  cross-repo decisions, numbered as elsewhere
├── security-posture.md         organization-level security summary
├── operations.md               how the platform runs: environments, on-call, SLOs
├── diligence-index.md          the map from review question to evidence
└── glossary.md                 domain vocabulary shared across repos
```

### `README.md`

The one-pager: what the platform does, what business capability it delivers, and a table of every repository — name, purpose, language and runtime, team, maturity, and links to its README, architecture and security documents. A reviewer's first ten minutes are spent here; if it is missing, they build their own mental map and it will be wrong.

### `system-context.md`

Two diagrams, in this order:

1. **Context** — the platform as a single box, surrounded by the users and external systems it interacts with. Answers "what is this and what does it touch".
2. **Containers** — inside the box: each deployable unit, each data store, and the connections between them, with protocols labelled.

Precede each with prose describing the same thing, so the document survives a renderer that shows raw diagram source. Resist a third level of detail; component-level structure belongs in each repo's own architecture document.

Follow the diagrams with the **data flows that matter**: how a request traverses the system, where data enters and leaves, and where personal data crosses a boundary. The last is what a privacy reviewer is looking for.

### `decisions/`

Decisions that span repositories, and therefore have no natural home in any one of them: the authentication and tenancy model, service boundaries, data contracts between services, shared infrastructure choices, language and framework standards. Same format as repo-level records (see `decision-records.md`).

### `security-posture.md`

The organization-level summary a reviewer or enterprise customer asks for: how identity and access are managed, how secrets are handled, encryption in transit and at rest, network boundaries, dependency and vulnerability management, where the software bill of materials is published, logging and audit retention, the incident response process, the disclosure policy, and which compliance regimes apply with current status. Link to per-repo detail rather than restating it.

### `diligence-index.md` — the highest-value document at this tier

An explicit map from the questions a reviewer will ask to the artifacts that answer them. It converts a two-week scavenger hunt into a guided read, and it demonstrates that the team knows what it is being assessed on.

```markdown
# Where to find the evidence

| Review area | Question | Evidence |
|---|---|---|
| Architecture | How is the system structured? | `system-context.md`; each repo's `docs/architecture/high-level.md` |
| Architecture | Why is it structured that way? | `decisions/`; each repo's `docs/architecture/decisions/` |
| Code quality | What are the standards and are they enforced? | Each repo's `docs/engineering/conventions.md`; CI configuration |
| Testing | What is tested and how well? | Each repo's `docs/engineering/testing.md`; coverage reports at <location> |
| Security | What is the posture? | `security-posture.md`; each repo's `docs/security/` |
| Dependencies | What do we rely on and under what licences? | Each repo's `docs/architecture/dependencies.md`; SBOM at <location> |
| Operations | How does it run and who is on call? | `operations.md`; each repo's `docs/operations/` |
| Risk | What is known to be wrong or missing? | Each repo's `docs/reference/limitations.md` |
| Process | How does work get from proposal to production? | Each repo's `docs/contributing/` |
| Scale | What are the tested limits? | Each repo's limitations register, performance envelope section |
```

## Preparing under time pressure

If the review is imminent and the documentation is not ready, sequence by what carries the most weight and the least effort:

1. **Portfolio README and system context.** Without these a reviewer cannot orient, and everything they read afterwards is harder to interpret.
2. **Dependency inventories and SBOM.** The first artifact requested in almost every security review, and largely automatable.
3. **Security posture.** Second most requested. Mostly writing down what already happens.
4. **Limitations registers.** Cheap to write, and disproportionately effective — disclosed weaknesses are discounted, discovered ones are compounded.
5. **Architecture overviews per repo.** Expensive but unavoidable.
6. **Backfilled decision records.** Five to ten per repo, covering the choices most likely to be questioned.

Everything else can wait.

## Honesty under review

Two failure modes, both fatal, and one is not obvious:

**Overstating** — describing intended architecture as shipped, omitting known problems, implying process discipline that does not exist. Reviewers cross-check documents against the codebase and the commit history; a single discovered overstatement invalidates every other claim, including the true ones.

**Understating** — presenting a system as messier than it is because the documentation was written defensively. Under-documented strengths are simply not credited.

The correct posture is precise and unembarrassed. "We accepted a single-tenant schema model to reach market, documented in decision 0002; migrating to shared-schema multi-tenancy is scoped at roughly eight weeks and tracked in issue 341" is a sentence that increases confidence. Concealment of the same fact, once discovered, decreases it far more than the fact itself ever would.
