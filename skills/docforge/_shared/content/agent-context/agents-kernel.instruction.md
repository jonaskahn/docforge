# Agent-context writing craft

Every generated agent-context output is permanently self-contained. It must
answer its own reader question without requiring any other documentation.
Facts may repeat across agent outputs when that makes each output independently
useful.

## Isolation

- Emit no Markdown links, URLs, `@` imports, peer-agent references,
  human-document references, or bare paths to generated documentation.
- Source and configuration paths are allowed when they are evidence for the
  stated fact. Verified commands are allowed.
- Never tell the reader to open, read, or consult another document.
- Generated non-agent documentation must not mention agent-context outputs.

## Evidence

Use terse, imperative language. State only facts supported by the selected
graph, manifests, source, configuration, CI, history, or explicit user input.
Do not infer a command from a script name, a convention from one occurrence, or
permission from tool defaults. Say that a command or rule is not evidenced
rather than inventing it.

Prefer durable module, source, and configuration paths over line numbers or
volatile symbol inventories. A compact ASCII layer stack is acceptable only
when bullets or a small table cannot express a dependency boundary clearly.

## Kernels

Use the same kernel template for both root kernel outputs. Each is a complete,
concise duplicate containing project purpose and stack, verified commands, a
durable repository map, precedence, hard boundaries, local conventions, and
validation expectations. Omit the optional conventions section when no
non-obvious convention is evidenced. Do not add a deeper-context section.

Preserve the kernel rubric's section order: Commands, Repository Map,
Precedence, Boundaries, optional Conventions, and Validation. The final line
states the observable working condition.

Keep each kernel within the `agents-kernel` audit-profile line budget and pass
the dedicated kernel rubric. Front-load commands and safety boundaries.

## Topic views

Each topic view directly states the minimum facts needed to answer its title:
architecture maps components and dependency direction; patterns gives repeated
shapes and exemplars; testing gives exact commands and suite behavior;
conventions gives evidenced directives; tech debt gives editing hazards and
safe handling; flows give trigger-to-effect sequences; glossary defines terms.
Keep the templates short and omit conditional views when their required
evidence is unavailable.

## Local configuration

The local-preferences output explains its local, uncommitted scope and contains
no shared project rules. Machine settings remain valid, stable JSON, preserve
existing user keys during merge, and add only portable, evidence-supported
permissions or hooks.
