# `setup-guide`

**Reader question** — "How do I get a working local checkout running, step by step?"

| Mode | Depth | Shape |
|---|---|---|
| How-to | deep-dive | executable-procedure |

## Must present

| # | Element | At | Done wrong |
|---|---|---|---|
| 1 | Prerequisites | L0 | a prerequisite discovered mid-procedure |
| 2 | One verified path from prerequisites to a running instance, one command per step, imperative present tense | L1 | "you could run X" instead of "Run X"; a menu of alternative paths |
| 3 | The observable success signal immediately after each command | L2 | a paragraph of explanation instead of the checkable output/state |
| 4 | Configuration introduced immediately before it is needed | L2 | a wall of settings dumped up front |
| 5 | Common recovery steps beside the failure they fix, keyed by symptom | L3 | recovery steps keyed by cause instead of the symptom the reader sees |
| 6 | A closing verification and a short "what next" | L3 | no verification step at the end |

## Keep out

| Not here | Lives in |
|---|---|
| An unverified command | nowhere — ground every command in manifests, CI, or local verification |
| Configuration semantics or the technology inventory, recreated | `configuration`, `tech_stack` |
| Running the test suite | `testing_guide` |

## Owns / links

| Owns | Links to | Because |
|---|---|---|
| The verified path from prerequisites to a running instance | `quickstart` | the under-a-minute first result is owned there |
| — | `configuration`, `tech_stack` | owned there, linked not recreated |
| Running the test suite after setup | `testing_guide` | owned there |
