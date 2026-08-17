# Agent-context writing craft — standalone mode

Applies when `project.agent_context.mode` is `standalone`: the agent-context
group is the only documentation this repository has. There is no human-facing
document to link, so these views **own** the facts they state instead of
routing to an owner. Everything in
[`agents-kernel.instruction.md`](agents-kernel.instruction.md) still applies
except its linking rules, which are replaced below.

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md); prefer a
compact ASCII layer stack only when bullets cannot express the module map.

## Own the fact, do not route to it

Never link a human-facing document in this mode. Those documents were not
generated, so a link to `../architecture/high-level.md` is a dead link and a
fact with no owner — the audit fails it. State the fact instead, at the depth
this document's declared capability supports.

Cross-links **within** the agent-context group stay normal: views may link
`AGENTS.md` and each other, and in compact layout they are `##` sections of one
file, so a link becomes an anchor.

## Agent-sufficient, not a human documentation set

Standalone raises what these views own; it does not raise how much they say.
They remain token-budgeted retrieval views, and the depth ceiling is unchanged:

- **Own:** durable paths, boundaries, entry points, verified commands,
  observable hazards, and the vocabulary an agent needs to navigate the code.
- **Do not own:** design rationale ("why we chose X"), business context,
  operational procedure, roadmap, or narrative history. None of those is
  derivable from a code graph or a package manifest, and inventing them
  violates the first safety boundary in [`../../rules.md`](../../rules.md).

When a reader question falls outside that line, say plainly that this
repository has no document covering it. An honest gap is correct; a plausible
invention is a failure.

## Evidence ceiling is unchanged

Each record's `requires` still bounds what its view may claim. A view whose
capability is absent is `skipped`, exactly as in linked mode — standalone never
licenses a claim the evidence does not carry. Derive boundaries from graph edge
direction, entry points from graph roots and in-degree, commands from manifest
scripts and CI configuration, and hazards from markers actually present in the
source.

## Later runs may convert these views

A run that adds human-facing documentation asks whether to convert these views
into linked stubs or keep them self-contained. Write each fact where it belongs
now; do not hedge or pre-write links against a tree that does not exist.
