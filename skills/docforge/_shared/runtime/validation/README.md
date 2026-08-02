# Validation runtime

Cartridge-integrity tooling: deterministic catalog router generation and the
full release-time validator. Both are paired Python/JS public commands with
launchers in [`runtime/cli/`](../cli/README.md).

## Load this when

- Regenerating or checking the generated catalog READMEs/indexes →
  `generate_indexes` (`--write` / `--check`).
- Running the broad cartridge integrity gate after any change to metadata,
  schemas, templates, launchers, or contracts → `validate_metadata`.

## Scripts

| Script | js/py | Kind | Purpose |
|---|---|---|---|
| `generate_indexes` | both | CLI | Deterministically generate/check `.metadata/catalog` routers |
| `validate_metadata` | both | CLI | Full catalog/schema/template/peer/version validation |

## Details

### `generate_indexes`

```sh
python3 runtime/cli/python/generate_indexes.py --check
python3 runtime/cli/python/generate_indexes.py --write
```

Exactly one of `--check` / `--write` is required; no repo argument — inputs are
fixed to the cartridge (`.metadata/catalog/index.json` + referenced records).

- `--check` — read-only; prints each `STALE` target; exit `0` current, `1` stale.
- `--write` — writes only changed targets (catalog README, documents README +
  index, per-group README/index for groups with ≥ 6 records); does not delete
  obsolete generated targets; exit `2` on invalid/conflicting mode.

Internal API: `stale_targets()`, `write_targets()`, `targets()` (camelCase in
JS); `validate_metadata` imports the staleness pair.

### `validate_metadata`

```sh
python3 runtime/cli/python/validate_metadata.py   # node runtime/cli/js/validate_metadata.js
```

No options. Read-only. Checks catalog validity and version (2.12.0), generated
router freshness, schema versions (manifest 3.1, flow index 1.1, provenance
2.0), profile registry shape, discovery-gate schema, template provenance,
Python/JS launcher peer presence, public CLI contract tokens, release-version
agreement (plugin/marketplace/catalog), package descriptions, obsolete files,
nested-README policy, and duplicated legacy constants.

Each finding prints as `ERROR  ...`; exit `0` on `OK`, `1` on findings.
Python exposes `validate() -> list[str]`; the JS implementation is CLI-only.

## Where invoked

| Script | Documented callers | Programmatic callers |
|---|---|---|
| `generate_indexes` | [`workflows/tools.md`](../../workflows/tools.md) (cartridge-integrity inline check) | `validation/validate_metadata` (`stale_targets`) |
| `validate_metadata` | [`workflows/tools.md`](../../workflows/tools.md) | — (release-time gate; no workflow step invokes it) |

## Boundaries

`generate_indexes` writes only under `.metadata/catalog/`. The internal
`runtime/**/README.md` files are agent/operator documentation and are exempt
from the nested-README policy — generated repository documentation is not
affected.
