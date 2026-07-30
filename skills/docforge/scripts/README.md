# Scripts

Stable public launchers. Every file here is a thin re-export: it imports the
matching implementation from `../runtime/<subsystem>/` and, for CLI
commands, invokes its `main()`. None contain business logic.

## Load this when

- Running a command → use the launcher here exactly as documented in
  [`../workflows/tools.md`](../workflows/tools.md).
- Changing what a command does → edit the implementation in
  `../runtime/<subsystem>/`, not the launcher.
- Adding a new command → implement it in both Python and Node under the
  matching `../runtime/<subsystem>/`, then add a launcher pair here that
  imports it.

## Boundaries

- Launcher paths and flags are the stable public surface; internal
  `runtime/` paths are not.
- New behavior must land in both the Python and Node runtime peer before a
  launcher is added.
- Direct imports from a launcher file (rather than from `runtime/`) are
  unsupported — other code should import the runtime implementation
  directly if it needs to reuse logic.
