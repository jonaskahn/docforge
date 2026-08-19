# `application-lifecycle`

**Reader question** — "What state is this app in right now, and what happens if it's killed mid-transition?"

| Mode | Depth | Shape |
|---|---|---|
| Explanation | deep-dive | answer-first |

The lifecycle state machine is the governing structure — walked in the order the platform actually defines it, before any single transition's failure detail.

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | States walked in the platform's own order (launch, activation, background, termination) | L1 | states presented out of the platform's defined order |
| 2 | Per state: what triggers entry, what the app must do before leaving it, restoration behavior on relaunch | L1 | a state's accountable owner left uncited |
| 3 | Failure boundaries per transition: what happens if the app is killed mid-transition | L2 | only the clean path described, failure boundaries omitted |

## Keep out

| Not here | Lives in |
|---|---|
| The UI component inventory | `web_components` |
| Persisted state's storage mechanics | `persistence` or `web_state` |
| A platform-imposed lifecycle bound (e.g. background execution limits) | `platform_integration` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| Launch/activation/background/termination states, ownership, restoration, failure boundaries | `web_components` | the UI component inventory is owned there; this document only describes lifecycle states |
| Persisted state on backgrounding or restoration | `persistence` or `web_state` | what survives a lifecycle transition is owned by the state/persistence documents, linked not restated |
| A platform-imposed lifecycle bound | `platform_integration` | OS-imposed lifecycle constraints are owned there; this document describes the app's own state machine |
