# `decisions_compact`

Content contract for compact document type `decisions_compact`.

The merged `docs/decisions.md` is the compact form of the decision record
section. It holds the decision register followed by one `##` section per
recorded architectural decision the manifest folded into it. Every known
decision appears in the register whether or not it has a section, so the
record of what was decided stays complete; the section budget bounds how many
are written up in full here. Each decision section follows the `adr` content
contract.

| Type | Must present | Keep out | Primary mode | Depth |
|---|---|---|---|---|
| decisions_compact | section introduction, the decision register (identifier, title, status, date, superseded-by), one section per folded decision carrying context, decision, alternatives considered, consequences, and status; links to every selected, materialized document in this section's folder that this file does not merge | decisions with no evidence in history or code, retroactive justification of a decision the repository does not record, implementation detail owned by an architecture section, direct source-file navigation | Explanation | reference |
