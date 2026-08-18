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
- `test_agents_kernel.py` — `lint_agents_kernel` rubric: clean golden
  AGENTS.md guard, per-check dirty fixtures, and Python/Node parity.
- `test_generation.py` — deterministic router generation: `--check` passes on
  current output, repeated `--write` produces identical bytes, manual drift
  is detected without writing, no timestamps leak into generated files.
- `test_dashboard.py` — dashboard metadata reconciliation, signatures, staged
  build, serving, and stop.
- `test_dashboard_template.py` — dashboard app template contract: Fumadocs
  Glass layout wiring, theme CSS, and accessibility fallbacks.
- `test_structure.py` — SKILL.md content and (as the refactor below lands)
  router/link integrity and size budgets.

## Opt-in slow tier

`test_dashboard_mermaid_slow.py` is the one exception to "dependency-free":
it installs the dashboard template's real `mermaid`/`jsdom` via a real `npm
install` and runs a fixed diagram corpus through the real
`validate_mermaid.mjs`, to prove actual Mermaid syntax detection works (the
fast suite only fakes it, to stay network-free — see
`DashboardMermaidValidationTests` in `test_dashboard.py`). Skipped by
default; opt in with:

```sh
DOCFORGE_RUN_SLOW_TESTS=1 python3 -m pytest tests/test_dashboard_mermaid_slow.py
```

Not wired into CI — this repo's CI has never done a real `npm install`, and
this tier hits the real npm registry.

## Conventions

- Every test uses a `tempfile.TemporaryDirectory()` fixture repo; nothing
  under the tracked repository is modified.
- Cross-runtime assertions normalize repo-absolute paths, timestamps, and the
  `.py`/`.js` script suffix via `_support.normalized()` before comparing
  Python output to Node output.
