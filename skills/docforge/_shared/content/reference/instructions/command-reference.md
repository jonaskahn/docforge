# Command-reference writing craft

Every entry cites its command definition, help output, or tested invocation and
records side effects only when observed. Link machine-output semantics to
`output-exit-contract`; do not present a plausible invocation as runnable.

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); a table
of flags is primary, one example block per command.

Follow POSIX/GNU convention: pair every short flag with its long-named
equivalent (`-v` / `--verbose`), and document them together, not as
separate entries. Give each command one runnable, copy-pasteable example
that needs no editing after paste. State side effects plainly (writes a
file, calls a network service, mutates state) as part of the command's
entry, not buried in prose elsewhere.

Group subcommands under their parent, not flattened alphabetically — a
reader exploring `repo sync` should find its subcommands together. Never show a call-graph or internal function name.
