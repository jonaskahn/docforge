# Migrations runtime

Historical, **one-shot** metadata migration tools with Python and Node peers.
They exist to reconstruct or reproduce past migrations — not for current
catalog or document maintenance. No long-term support commitment.

## Load this when

- Reproducing the old monolith → split-catalog migration → `split_catalog`.
- Reproducing the old `references/document-catalog.md` contract split →
  `split_document_catalog`.

For anything else: use the current tools (`query_catalog`, `generate_indexes`,
`validate_metadata`, `manage_manifest`).

## Scripts

| Script | js/py | Kind | Purpose |
|---|---|---|---|
| `split_catalog` | both | CLI | Historical `.metadata/catalog.json` → split index/types/profiles migration |
| `split_document_catalog` | both | CLI | Historical document-catalog table → per-type contract files |

## Details

### `split_catalog`

```sh
python3 runtime/cli/python/split_catalog.py [--dry-run] [--root <skill-root>]
node   runtime/cli/js/split_catalog.js    [--dry-run] [--root <skill-root>]
```

Rewrites `.metadata/catalog/index.json`, `types/*.json`, and `profiles/*.json`
with a hard-coded catalog version **2.17.0**. The current catalog requires
**2.18.0** — running it against the current tree would regress the catalog
version and shape. Use only to reproduce the original migration. `--root`
overrides the skill root (used by the parity tests).

### `split_document_catalog`

```sh
python3 runtime/cli/python/split_document_catalog.py [--dry-run] [--root <skill-root>]
node   runtime/cli/js/split_document_catalog.js    [--dry-run] [--root <skill-root>]
```

Creates `references/catalog-contracts/`, **deletes every existing `*.md`
there**, writes a README and per-type contracts, and replaces the source
monolith with a stub. Highly destructive outside its intended one-shot
context. `--root` overrides the skill root (used by the parity tests).

## Where invoked

Nowhere. Neither migration is referenced by any workflow, reference, or
SKILL.md — no specific file calls them. They are manual, historical, one-shot
tools; the current workflows deliberately never invoke them.

## Boundaries

Both tools ship paired Python/JS peers and are included in the validator's
Python/JS peer check. Always inspect `--dry-run` output before running either
migration.
