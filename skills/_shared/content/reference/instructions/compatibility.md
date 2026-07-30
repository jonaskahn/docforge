# Compatibility writing craft

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); a
version/platform matrix table is the whole document.

State the supported-version matrix as tested evidence, not aspiration — a
version marked supported should mean "we run CI against it," not "it
probably works." Include the deprecation column: when support for each
older version ends, and what happens after (still works, unsupported but
functional, actively broken) — a compatibility document with no
deprecation horizon leaves a reader unable to plan an upgrade.

Order rows newest-version-first; a reader almost always wants "does the
current version work with X" before historical detail. State the actual
test evidence (CI matrix, manual verification, community report) per row
where confidence varies — not every row deserves the same confidence, and
saying so is more honest than a uniform checkmark.
