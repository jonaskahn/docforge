# Shape — command-line interface / terminal UI

**Applies when:** the repository exposes commands intended for a shell, scripts, CI, or an interactive terminal interface.

A command is both a human interface and an automation contract. Its most
consequential behavior is usually not the implementation but its argument
grammar, configuration precedence, streams, output stability, exit codes, and
behavior when no terminal is attached.

## Additions to the tree

```
docs/
├── reference/
│   ├── commands.md               command grammar, examples, side effects
│   └── output-and-exit-codes.md  streams, formats, schemas, exit-code contract
└── operations/
    └── distribution.md           install methods, shell completion, upgrades
```

## `reference/commands.md`

For every public command, state syntax, required inputs, defaults, side
effects, idempotency, confirmation behavior, and a successful example. Group
commands by user goal, not source module. Mark destructive or remote actions
prominently and document their dry-run, confirmation, and non-interactive
behavior.

## `reference/output-and-exit-codes.md`

Define the output contract once: which data goes to stdout, diagnostics to
stderr, stable machine-readable formats, color/progress behavior when output
is not a TTY, and any versioned JSON schema. Give every non-zero exit code a
stable meaning and recommended caller response. A script must never need to
parse decorative human output to determine success.

## Configuration and environment

Document the full precedence order across flags, environment variables,
configuration files, project-local files, and defaults. For every credential
input, state the secure mechanism and explicitly prohibit command-line
secrets if they would leak through process listings or shell history. Include
the command that reveals the effective configuration with secrets redacted.

## Shell integration

State supported shells, completion installation and versioning, stdin/file
conventions, and whether commands are safe in pipelines. If a TUI exists,
document terminal, color, Unicode, resize, and accessibility assumptions
separately from the batch command contract.

## `operations/distribution.md`

List supported installation channels, package names, binary integrity or
signing verification, supported platforms, upgrade path, and how users pin or
roll back a version. State whether configuration or on-disk state remains
compatible across upgrades.
