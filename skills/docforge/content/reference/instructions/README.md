# reference instructions

Writing-craft instruction files owned by the `reference` group.

## Contents

- `api-rate-limits.md` — Public surface, inputs/outputs, auth contract, limits, errors, compatibility source → [api-rate-limits.md](api-rate-limits.md)
- `api-reference.md` — Public surface, inputs/outputs, auth contract, limits, errors, compatibility source → [api-reference.md](api-reference.md)
- `browser-support.md` — Component responsibilities, composition, tokens/themes, browser matrix, degradation → [browser-support.md](browser-support.md)
- `command-reference.md` — Commands/subcommands, arguments, configuration, examples, side effects → [command-reference.md](command-reference.md)
- `compatibility.md` — Supported versions/platforms, tested matrix, deprecation behavior → [compatibility.md](compatibility.md)
- `configuration.md` — Every read setting, default, scope, sensitivity, validation → [configuration.md](configuration.md)
- `data-types.md` — Producers, transformations, contracts, checks, failure/recovery, schema ownership → [data-types.md](data-types.md)
- `limitations-register.md` — Known bounds, trigger, impact, workaround, source evidence → [limitations-register.md](limitations-register.md)
- `model-card.md` — Datasets, training/evaluation, artifact lineage, inference, limitations, drift, ownership → [model-card.md](model-card.md)
- `output-exit-contract.md` — Stdout/stderr ownership, formats, exit codes, stability, scripting behavior → [output-exit-contract.md](output-exit-contract.md)
- `performance-budgets.md` — Evidenced CPU/GPU/memory/storage/timing limits, measurement, degradation → [performance-budgets.md](performance-budgets.md)
- `platform-compatibility.md` — OS/device/architecture matrix, minimums, tested evidence, degradation, deprecation → [platform-compatibility.md](platform-compatibility.md)
- `resources.md` — Plan/apply safety, external state, locking, ownership, resource inventory, drift, recovery → [resources.md](resources.md)

## Boundaries

Files here are referenced by exact path from catalog records (`.metadata/catalog/documents/reference/`); do not rename without updating the referencing record.
