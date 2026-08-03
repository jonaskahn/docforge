# Migration writing craft

Create a migration guide only for an evidenced source-to-target transition, with
breaking changes grounded in public-surface comparison and history. Distinguish
verified mechanical steps from manual or unresolved work, and link rollback only
where an evidenced recovery path exists.

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); this is a
how-to — ordered changes and verification, not a full compatibility
matrix.

State source and target versions in the opening line, then list breaking
changes in the order a reader must apply them, not internal changelog
sequence. For each breaking change, give the exact before/after and,
where mechanical, the search-and-replace or codemod that handles it.

End with a verification step that proves the migration succeeded, and a
rollback path if one exists; state plainly if it doesn't. Keep the full
version-support matrix out; that's [compatibility.md](compatibility.md),
this document is the path between two specific versions.
