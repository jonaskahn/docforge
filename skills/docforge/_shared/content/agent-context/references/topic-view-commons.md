# Topic view shared rubric

Every `agent-context` topic view inherits this rubric. A topic contract may
add topic-specific requirements but never relaxes these rules.

## Isolation

- No Markdown links, URLs, or `@` imports.
- No references to any peer-agent output or human-facing document.
- No bare paths naming generated documentation.
- Source and configuration paths are allowed when they are evidence for a
  stated fact. Verified commands are allowed.

## Shape

- Exactly one level-1 heading naming the topic.
- At most one fenced code block per file.
- Provenance HTML comment within the first 10 lines.
- Durable source and configuration paths only; no volatile line numbers and no
  raw graph schemas.

## Evidence discipline

- Omit any section whose required evidence is unavailable; never scaffold an
  empty section.
- State only facts supported by the selected graph, manifests, source,
  configuration, CI, history, or explicit user input.
- When evidence cannot establish a required fact, state the bounded
  uncertainty or skip the affected output.
