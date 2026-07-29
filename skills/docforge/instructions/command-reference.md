# Command-reference writing craft

**Preferred illustration:** Follow
[`../references/illustration.md`](../references/illustration.md); a table
of flags is primary, one example block per command.

Follow POSIX/GNU convention: pair every short flag with its long-named
equivalent (`-v` / `--verbose`), and document them together, not as
separate entries — a reader scripting against this CLI needs the stable
long name. Give each command one runnable, copy-pasteable example that
needs no editing after paste — a placeholder left in a "copy-paste" example
is a broken example. State side effects plainly (writes a file, calls a
network service, mutates state) as part of the command's entry, not
buried in prose elsewhere; a reader deciding whether a command is safe to
run should not have to hunt for that fact.

Group subcommands under their parent, not flattened alphabetically — a
reader exploring `repo sync` should find its subcommands together. Never
show a call-graph or internal function name; this document is the
command's public contract, not its implementation.
