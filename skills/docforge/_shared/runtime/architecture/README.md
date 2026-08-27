# Architecture runtime

The adaptive deep-architecture ledger: prepare, import, decide, status,
validate, and audit the `.docforge/architecture-plan.json` coordination
record. `architecture_plan` is a paired Python/JS public command with
launchers in [`runtime/cli/`](../cli/README.md).

## Load this when

- Planning architecture documentation as an evidence-specific document pack →
  `architecture_plan prepare` (read-only; no web access).
- Writing the frozen evidence inventory and proposals to the ledger →
  `architecture_plan import --analysis <path>`.
- Recording the confirmed pack and research policy →
  `architecture_plan decide --select <id>... --decline <id>...
  --research-policy <mode>`.
- Reporting plan state → `architecture_plan status --repo <repo> [--json]`.
- Mechanically validating the ledger → `architecture_plan validate`.
- Recording the pack-audit result → `architecture_plan audit --repo <repo>
  --verdict <PASS|FAIL> --report <path>`.

## Scripts

| Script | js/py | Kind | Purpose |
|---|---|---|---|
| `architecture_plan` | both | CLI | Architecture-pack ledger lifecycle |

## Details

### `architecture_plan`

```sh
python3 runtime/cli/python/architecture_plan.py <subcommand> --repo <repo> ...
node   runtime/cli/js/architecture_plan.js    <subcommand> --repo <repo> ...
```

| Subcommand | Writes | Notes |
|---|---|---|
| `prepare --repo <repo> [--manifest <path>] [--json]` | stdout (or the requested output) | read-only evidence/planning pack: project scale/layout/tier/profiles/graph lock, empty system inventory, scale-aware worker counts. No web access. The agent fills the system inventory and document proposals from parallel evidence workers, then passes the result to `import` |
| `import --repo <repo> --analysis <path>` | `.docforge/architecture-plan.json` | validates the analysis against the schema-1.0 rules (duplicate ids, dangling edges, missing parent blocks, dependency cycles, invalid batch assignments, unresolved selected documents, invalid external-source metadata and dangling section references) and deterministically writes the ledger |
| `decide --repo <repo> --select <id>... --decline <id>... --research-policy <official-primary\|official-only\|off>` | `.docforge/architecture-plan.json` | records the confirmed pack and research policy. Remaining `proposed` documents become `declined`; only explicitly selected documents stay selected |
| `status --repo <repo> [--json]` | none | reports selected documents, unresolved gaps, research policy, and pack-audit state |
| `validate --repo <repo>` | none | mechanical schema and relationship validation; exits nonzero on any defect |
| `audit --repo <repo> --verdict <PASS\|FAIL> --report <path>` | `.docforge/architecture-plan.json` | records the semantic pack-audit result. A `FAIL` sets `audit.status: failed` |

Both runtimes emit byte-identical normalized JSON and equivalent
diagnostics. `prepare` never touches the repository; `import` / `decide` /
`audit` mutate only the ledger file.

## Boundaries

Consumes `common/` libraries (`_util`, `scale`), `catalog/query_catalog`,
and `catalog/detect_profiles`. The architecture-plan schema (1.0) lives at
`.metadata/architecture-plan-schema.json` and is enforced by
`validation/validate_metadata`.
