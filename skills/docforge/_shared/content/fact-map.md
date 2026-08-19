# Fact ownership map

This file arbitrates contested ownership *between document types* — cases
where two or more catalog document types could each plausibly claim the same
fact, and each type's own `## Owns / links` table looks correct read alone.
It does not enumerate every fact every document owns; that would restate the
141 per-document contracts and rot on the first sweep that misses one. A row
is admitted only when at least two named types could each claim the fact
class. This file is capped at 40 rows; if a genuine dispute would push past
that, the fix is a sharper fact-class boundary, not a longer table.

[`document-composition.md`](../references/document-composition.md) owns the
general no-duplication policy (one owner per fact, link don't restate) and
the class-level rules that apply to every document regardless of type. This
file owns only the named, contested cases.

| Fact class | Owner | Contested with | How the non-owner refers to it |
|---|---|---|---|
| What the repository is built with | `tech_stack` | `dependencies` | links to `tech_stack` for language/framework identity; states only what breaks operationally |
| What it depends on operationally and what breaks | `dependencies` | `tech_stack` | `tech_stack` omits failure framing and links to `dependencies` |
| A shortcut we could fix later | `tech_debt` | `limitations`, `architecture_constraints` | both link to `tech_debt` rather than restate the remediation direction |
| A bound imposed from outside, immovable | `architecture_constraints` | `tech_debt`, `limitations` | neither describes an immovable external bound as a fixable shortcut |
| A deliberate or accepted user-visible gap | `limitations` | `tech_debt`, `architecture_constraints` | both link to `limitations` for the user-visible framing |
| The STRIDE analysis and top-threat summary | `threat_model` | `threat_register` | `threat_register` carries only the per-threat register and links back for narrative analysis |
| Per-interaction threat rows with disposition and evidence | `threat_register` | `threat_model` | `threat_model` summarizes; it does not restate every row |
| Data classification and handling rules | `data_handling` | `threat_model` | `threat_model` links to `data_handling` classifications rather than restating them |
| The operation surface: methods, request/response shapes | `api_reference` | `api_errors`, `api_authentication`, `api_rate_limits` | each of the three is linked per operation, never inlined |
| The shared error envelope and per-code catalog | `api_errors` | `api_reference` | `api_reference` links per endpoint rather than restating the envelope |
| Auth contract per operation | `api_authentication` | `api_reference` | `api_reference` carries only the auth class as a column |
| Rate or quota limits per operation | `api_rate_limits` | `api_reference` | `api_reference` carries only the limit class as a column |
| Every read setting: default, scope, sensitivity, validation | `configuration` | `infra_environments`, `setup_guide` | both link to `configuration` rather than re-listing settings |
| Per-environment values and promotion path | `infra_environments` | `configuration` | `configuration` owns the setting; `infra_environments` owns which environment sets it to what |
| The one-time steps to reach a first verified run | `setup_guide` | `configuration` | `configuration` is not a walkthrough; `setup_guide` sequences the settings a first run needs |
| A domain term's precise definition | `glossary` | any document that names the term | every document links to the glossary entry rather than defining the term inline |
| Ordered steps, branches, and technical failure modes | `flow` | `ba_process_flows`, `po_features` | `ba_process_flows` links to the canonical flow for step-by-step depth |
| The business-recognizable narrative of the same work | `ba_process_flows` | `flow` | `flow` does not restate the business narrative, only the technical steps |
| That a feature exists and what it is for | `po_features` | `flow` | `flow` does not restate feature value or status; `po_features` links back for mechanism |
| A domain concept's meaning, invariants, lifecycle | `concept` | `arch_low_level` | `arch_low_level` references a concept by name, never redefines it |
| System context and container boundaries | `arch_high_level` | `arch_low_level` | `arch_low_level` does not restate the high-level map |
| Component decomposition and intra-block runtime scenario | `arch_low_level` | `arch_high_level` | `arch_high_level` keeps component detail out entirely |
| Signals, correlation path, alert intent | `observability` | `runbook` | `runbook` links to `observability` rather than re-describing signals |
| Symptom-to-resolution diagnosis for an incident | `runbook` | `observability` | `observability` does not walk a diagnosis path |
| Retry, backoff, and job-specific reliability guarantees | `worker_reliability` | `runbook` | a worker's own retry contract lives there, not duplicated per runbook |
| Component inventory | `web_components` | `browser_support` | `browser_support` carries only the compatibility matrix and links back |
| Styling approach and tokens | `web_styling` | `browser_support` | `browser_support` carries only the compatibility matrix and links back |
| Per-browser or per-version compatibility matrix | `browser_support` | `web_components`, `web_styling` | neither carries a compatibility matrix of its own |
| Section introduction, at-a-glance, scope, and the group's own matrix | each `*_compact` host | its own `compact_members` | the host owns nothing a member owns; every member fact is hosted, never restated |

## Agreement

`query_catalog --validate-fact-map` checks this table against the contracts
it describes: for every row above, every id in `Contested with` must carry
a `## Keep out` row whose `Lives in` cell names the `Owner`. A row that
fails is a drift defect — fix whichever side is stale, the map or the
contract.
