# Risk documents — limitations, dependencies, security, debt and constraints

These documents carry the risk surface of a repository. They are the ones most often missing, and the ones a technical reviewer opens first. Their shared property: they are uncomfortable to write, which is precisely why their presence is read as a competence signal and their absence as either naivety or concealment.

`document-catalog.md` states the crisp content contract (must-present / keep-out) for each of these; this file holds the deep template and the writing craft. Section 4 draws the line between the three registers that readers most often blur — limitations, technical debt, and constraints.

---

## 1. `docs/reference/limitations.md`

Undocumented limitations do not disappear; they get discovered by a customer at an inconvenient moment, or by a reviewer who then wonders what else went unmentioned. A frank register converts a discovered surprise into a disclosed constraint.

### Structure

```markdown
# Limitations and known issues

_Last reviewed: YYYY-MM-DD_

## Known limitations
Design constraints and deliberate trade-offs. These are not defects; they are
the shape of the system.

| Area | Limitation | Impact | Workaround | Tracking |
|---|---|---|---|---|
| Ingestion | Single-threaded per source | ~500 rows/s ceiling per source | Shard by source | #142 |
| Auth | Sessions do not survive a restart | Users re-authenticate after deploy | Deploy off-peak | #201 |

## Known issues
Defects under investigation. Each links to the tracker; the tracker holds the
detail, this table holds the summary so a reader sees the shape without leaving
the repo.

| Issue | Symptom | Affected versions | Status |
|---|---|---|---|

## Not supported
Things a reasonable person expects and will not find. Be blunt.

- No support for <X>. <One line on whether this is planned.>

## Scale and performance envelope
The tested limits: request rate, dataset size, concurrent users, payload size.
State what has actually been measured and what is extrapolated — a reviewer will
ask, and "we have not tested beyond this" is a respectable answer.

## Deployment-specific caveats
Constraints that only apply to certain versions, platforms or configurations —
minimum versions of external systems, resource requirements that surprise people,
combinations known not to work.
```

### Writing them well

- **Impact in the reader's terms**, not the implementation's: "imports over 2 GB fail" rather than "the buffer is bounded at 2 GB".
- **Always give the workaround** where one exists. A limitation with a workaround is an inconvenience; without one it reads as a wall.
- **Distinguish deliberate from accidental.** A trade-off with stated reasoning reads as engineering judgement; the same constraint unexplained reads as an oversight.
- **Date the review.** A limitations register with no review date cannot be trusted, because a reader cannot tell whether the absence of an entry means "no such limitation" or "nobody has looked since 2023".

---

## 2. `docs/architecture/dependencies.md`

Every third-party dependency is a piece of the system that someone else controls: its security posture, its licence, its release cadence, its continued existence. This document is typically the first artifact requested in a security review or acquisition, and assembling it under time pressure is miserable.

### Structure

```markdown
# Dependencies and integrations

## Runtime dependencies
Direct dependencies the shipped system requires.

| Package | Purpose | Licence | Version | Criticality | If it disappeared |
|---|---|---|---|---|---|
| <name> | <why it is here> | MIT | ^4.2 | high | <replacement path, effort> |

## Development dependencies
Summarize rather than enumerate; note anything unusual or licence-encumbered.

## External services
Systems this repo calls that it does not own.

### <Service name>
- **Purpose:** what it does for us
- **Criticality:** hard dependency (we fail without it) | soft (degraded) | optional
- **Authentication:** mechanism; where credentials come from
- **Data exchanged:** what leaves and enters, including any personal data
- **Limits:** rate limits, quotas, payload ceilings
- **Failure handling:** timeout, retry policy, circuit breaker, fallback behaviour
- **Contract:** API version pinned, deprecation notice period, SLA
- **Region:** where data is processed, if it matters for compliance

## Dependency policy
- Criteria for adding one: <maintenance signals, licence compatibility,
  security history, whether the standard library or an existing dependency covers it>
- Who approves: <role>
- Review cadence: <how often the inventory is checked>
- Update policy: <automated patch updates, manual majors, how CVEs are triaged>

## Generated inventory
The machine-readable inventory (SBOM) is produced by the CI pipeline and
published at <location>. This document is the human layer: rationale, criticality
and failure behaviour, none of which a generated file can supply.
```

### Notes

- **The "if it disappeared" column** is the one that changes conversations. It forces an assessment of concentration risk that a plain package list hides, and it is the question a reviewer will ask anyway.
- **Licence column, always.** A copyleft dependency in a proprietary product is the kind of finding that stops a transaction. Better found by you.
- **Generate the exhaustive list, hand-write the judgement.** Enumerating hundreds of transitive dependencies by hand produces a document that is stale on commit. Automate the SBOM; keep this file to the direct dependencies and the assessment.
- **The generated SBOM carries the NTIA minimum fields.** For every component, top-level and transitive: supplier/author, component name, version, a unique identifier (PURL, CPE, or hash), the dependency relationship, the author of the SBOM data, and a timestamp — emitted in a standard machine-readable format (SPDX or CycloneDX). CycloneDX additionally carries vulnerability and VEX status where relevant. This is the exhaustive layer; the hand-written table above is the judgement layer (criticality, failure handling, "if it disappeared") that no generated file supplies.

---

## 3. `docs/security/` and root `SECURITY.md`

Two distinct audiences: a researcher who has found something and needs a private channel, and a reviewer assessing whether security is taken seriously.

### Root `SECURITY.md` (thin)

```markdown
# Security policy

## Supported versions
| Version | Supported |
|---|---|
| 2.x | yes |
| 1.x | security fixes until YYYY-MM-DD |

## Reporting a vulnerability
Report privately to <address>. Do not open a public issue.

We acknowledge reports within <N> business days and aim to provide an assessment
within <N> days. We follow a <N>-day coordinated disclosure timeline and will
credit reporters who wish to be named.

Full posture: `docs/security/README.md`.
```

Commit to an acknowledgement window you can actually meet; a missed SLA in a public policy is worse than a vaguer one honestly stated. Ninety days is the common coordinated-disclosure default. Where the project publishes a `security.txt` (RFC 9116), it carries at minimum a **Contact** and an **Expires** field, and optionally Encryption, Acknowledgments, Preferred-Languages, Canonical, and Policy — the machine-discoverable pointer to this same policy.

### `docs/security/threat-model.md`

Keep it proportionate. A workable short form: what is worth protecting (data, credentials, availability, integrity), who might want it (external attacker, malicious user, compromised dependency, insider), where trust boundaries sit (network edge, authentication layer, tenant separation, the boundary between your code and third-party code), what mitigates each risk, and what is explicitly accepted or out of scope. The accepted-risk section is the one reviewers read most carefully — it demonstrates that the analysis was performed rather than assumed.

For repos that warrant more rigour, follow the OWASP four-question frame (*what are we building, what can go wrong, what are we doing about it, did we do a good enough job*) and give it structure: a **data-flow diagram** with the trust boundaries drawn on the flows, then threats enumerated per element with **STRIDE** — Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation of privilege — and one response per threat (mitigate / eliminate / transfer / accept) tied to a testable control. Reference the data classifications from `data-handling.md`; do not restate the inventory here.

### `docs/security/data-handling.md`

What data is collected and why, classification (public / internal / confidential / personal), where it is stored and for how long, who and what can access it, whether it crosses jurisdictions, how deletion requests are honoured, and what is encrypted in transit and at rest. Where a regulatory regime applies, say which and cite the specific obligation rather than gesturing at compliance generally.

**Never place in these files:** credentials or key material, internal hostnames or network topology, unremediated vulnerability details, or the names of individuals as security contacts (use a role address that survives departures).

---

## 4. `architecture/tech-debt.md`, `architecture/constraints.md`, and the line to `reference/limitations.md`

These three registers are constantly conflated, and the conflation is expensive: a constraint logged as debt implies a repayment that can never come; fixable debt logged as a limitation hides a remediable cause behind a "that's just how it is". Keep them distinct by *who can change the thing and whether it is user-visible*.

### `architecture/tech-debt.md` — internal, fixable with effort

A backlog of shortcuts the team took and can pay down. Per item: the shortcut or deferred improvement and **why** it was taken (the deadline, the unknown, the dependency), the area it affects, its **impact × likelihood**, the **interest** it accrues (what not fixing it costs over time), a suggested remedy and rough effort, plus owner and status. This is an engineering to-do list with a cost of delay attached — RAID-register in spirit.

### `architecture/constraints.md` — external, immovable

The fixed boundaries the team **cannot** change and must design within: physical or protocol limits (latency floors, packet sizes), platform or vendor ceilings, regulatory mandates, a mandated technology stack, hard budget or staffing limits. Per constraint: the boundary, its **source**, and its **design implication**. Not a to-do list — there is nothing to pay down, only to respect.

### The litmus

| The thing is… | Register | Is it a to-do? |
|---|---|---|
| Fixable by us later | `architecture/tech-debt.md` | Yes — with interest |
| Unfixable by anyone (physics, law, vendor) | `architecture/constraints.md` | No |
| Won't/needn't fix, and user-visible | `reference/limitations.md` | Not necessarily |

One question resolves almost every case: *could we fix this with engineering effort?* Yes → tech debt. No, it's imposed from outside → constraint. It's a deliberate boundary a user would bump into → limitation. Never cross-file them: a constraint in the debt register is noise a reader can't action, and debt dressed as a limitation is a defect hidden as a design choice.
