# `data-handling`

**Reader question** — "What data classes does this system hold, and how is each one collected, retained, and deleted?"

| Mode | Depth | Shape |
|---|---|---|
| Reference | deep-dive | entry-catalog |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Data classes the system actually distinguishes (public, internal, confidential, regulated/PII) — not a generic borrowed scheme | lead | a compliance-template tier list not grounded in this system's real distinctions |
| 2 | Per class, the full lifecycle in order: collected, used, retained (duration and why), deleted (mechanism, not policy language) | per class | a retention period with no deletion mechanism behind it |
| 3 | Access boundaries per class: who or what can read it | per class | "access is controlled" instead of naming who |

## Keep out

| Not here | Lives in |
|---|---|
| An invented compliance claim (GDPR, HIPAA, SOC 2) not evidenced | nowhere — no claim beats an invented one |
| An internal hostname, real credential, or individual's name as security contact | nowhere — use the role or channel from `security_root` |
| An unevidenced duration, processor, or outcome | nowhere — state it as a limit instead |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Data classes, lifecycle, access boundaries, deletion | `threat_model` | classifications are referenced there, never restated |
| The security contact role or channel | `security_root` | owned there, referenced not restated |
