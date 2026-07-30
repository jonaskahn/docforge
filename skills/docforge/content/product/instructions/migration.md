# Migration writing craft

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); this is a
how-to — ordered changes and verification, not a full compatibility
matrix.

State source and target versions in the opening line, then list breaking
changes in the order a reader must apply them — a migration guide ordered
by internal changelog sequence rather than dependency order will break a
reader who follows it literally. For each breaking change, give the exact
before/after and, where mechanical, the search-and-replace or codemod that
handles it — Keep-a-Changelog's discipline of naming the user-facing change
precisely, applied to migration steps rather than release notes.

End with a verification step that proves the migration succeeded, and a
rollback path if one exists — state plainly if it doesn't. Keep the full
version-support matrix out; that's [compatibility.md](compatibility.md),
this document is the path between two specific versions.
