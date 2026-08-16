# `security_compact`

Content contract for compact document type `security_compact`.

The merged `docs/security.md` is the compact form of the security section:
the section-level orientation (assets, boundaries, and posture) followed by
the threat model and data handling, one `##` section per member below. Each
section follows its member's own content contract; the composed contract for
this document lists the members this project's manifest actually selected.

| Type | Must present | Keep out | Primary mode | Depth |
|---|---|---|---|---|
| security_compact | section introduction, at-a-glance security posture, scope and boundaries, bounded DFD with zones and element-by-STRIDE matrix, concrete threats with exactly one disposition each, data classes with lifecycle/access/retention/deletion; links to every selected, materialized document in this section's folder that this file does not merge | disclosure workflow, credentials, individual names as security contacts, invented compliance claims, guessed scores or owners, direct source-file navigation | Explanation | orientation |
