# Output-exit-contract writing craft

For each captured example, cite the command and version that produced its exit
status and streams. Link command-specific side effects back to
`command-reference`; this contract owns stable output semantics, not usage prose.

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); tables
for exit codes and stream ownership — this document exists so a script can
be written against it, not read for prose.

State the exit-code table first: code, meaning, and whether it's stable
enough to script against — a reader automating around this CLI needs to
know which codes are contract and which are incidental. State which stream
owns which content (stdout for machine-parseable output, stderr for
human-facing diagnostics, or whatever the actual split is) and the output
format's stability guarantee — is this JSON schema versioned, or can a
field disappear in a minor release?

Give one real, captured output example per format, not a hand-typed
approximation; a scripting reader needs to see the actual shape, including
whitespace and field order if those are part of the contract.
