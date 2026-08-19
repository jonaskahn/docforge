# `security-policy`

**Reader question** — "What's in scope for a security report, how do I report one, and what should I expect back?"

| Mode | Depth | Shape |
|---|---|---|
| Orientation | orientation | answer-first |

The governing claim — what's in scope and how to report — comes before the procedure; this page is a procedure, not a threat analysis.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Supported scope: which versions or components are in scope | L0 | reporting steps given before scope is stated |
| 2 | What testing is not authorized (no destructive testing, no data exfiltration, no social engineering) | L1 | authorized and unauthorized testing merged into one paragraph |
| 3 | The reporting procedure: what to include, as a separate list from what not to do | L1 | disclosure instructions vague enough that a reporter must guess the next step |
| 4 | Response commitments: acknowledgement window, using typed tokens for any unconfirmed value | L2 | an invented timeline, address, or number with no confirmed source |
| 5 | A safe-harbor commitment, only when an accountable policy decision establishes it, stated explicitly and unconditionally where it applies | L3 | technical threat-model detail folded into this page |

## Keep out

| Not here | Lives in |
|---|---|
| Threat-model detail | `threat_model` |
| Scored threats and exhaustive interactions | `threat_register` |
| An invented number, address, or timeline | nowhere — use a typed external unknown until confirmed |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Scope, reporting procedure, response commitments, safe harbor | `threat_model` | technical analysis is owned there; this page is procedure, not analysis |
| — | `threat_register` | scored threats and exhaustive interactions are owned there, never restated on this page |
