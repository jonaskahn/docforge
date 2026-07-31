# Tests

Dependency-free `unittest` suite for Docforge. Run with:

```sh
python3 tests/run.py
```

Fixtures shared across files live in `_support.py` (not collected as a test
module itself). Most tests invoke `skills/_shared/runtime/cli/python/*.py` and
`skills/_shared/runtime/cli/js/*.js` as subprocesses and assert Python/JS
parity directly.

## Layout

- `test_catalog.py` — catalog record integrity: every id resolves a type
  detail, template, and instruction file.
- `test_profiles.py` — profile detection, alias normalization, discovery-gate
  judgment.
- `test_manifest.py` — tier/profile selection, status/audit transitions,
  provenance defects, provenance codec, and metadata migration.
- `test_graph_and_flows.py` — graph-provider precheck/selection and
  flow-index harvest/revise/organize/render.
- `test_routing.py` — `--category`/`--route` resolution, unknown-id/group
  exit codes, and legacy-mode field-leak guards.
- `test_cli_parity.py` — same command, same fixture, across Python and Node;
  compares exit code, stdout, and produced files.
- `test_generation.py` — deterministic router generation: `--check` passes on
  current output, repeated `--write` produces identical bytes, manual drift
  is detected without writing, no timestamps leak into generated files.
- `test_structure.py` — SKILL.md content and (as the refactor below lands)
  router/link integrity and size budgets.

## Conventions

- Every test uses a `tempfile.TemporaryDirectory()` fixture repo; nothing
  under the tracked repository is modified.
- Cross-runtime assertions normalize repo-absolute paths, timestamps, and the
  `.py`/`.js` script suffix via `_support.normalized()` before comparing
  Python output to Node output.
