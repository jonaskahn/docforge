# Writing the compact coding-agent reference

Write one `##` section per topic member selected by the manifest, in this
order:

1. `## Architecture`: components, entry points, dependency direction, and
   boundaries.
2. `## Patterns`: repeated implementation shapes, representative source paths,
   hotspots, and applicable checks.
3. `## Testing`: exact commands, suite layout, selection, fixtures, isolation,
   and success signals.
4. `## Conventions`: evidenced safety, naming, structural, and workflow rules.
5. `## Tech debt`: observed limitations, editing risks, and safe handling.
6. `## Flows`: evidenced triggers, entry paths, durable sequences, results, and
   failure behavior.
7. `## Terms`: concise definitions, code context, and important distinctions.

Omit Conventions when its source condition is false. Omit Flows and Terms when
flow evidence is unavailable. Do not emit empty conditional sections.

Each selected section must answer its reader question without relying on any
other documentation. Facts may repeat between sections. Emit no Markdown
links, URLs, imports, references to peer outputs or human documentation, bare
generated-document paths, reader directions, or attribution language. Source
and configuration paths and verified commands are allowed.

Keep each selected section to roughly 25 lines. Prefer durable paths and stable
behavior over volatile symbols. Ground every heading in its own provenance
section, and never invent detail to fill the budget.
