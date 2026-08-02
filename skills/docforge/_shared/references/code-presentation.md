# Code presentation

Fenced blocks are for material readers can run, copy, inspect as a contract, or
read as a diagram. They are never containers for explanatory prose, source
citations, or lists of implementation locations.

## Policy

- `contract-only` permits diagrams, literal output, schemas, configuration, and
  commands that the document contract requires.
- `task-focused` additionally permits the smallest verified example needed to
  complete or verify the reader's task.
- Never paste repository implementation as proof of a claim. Ground the claim
  in provenance and explain the behavior in prose instead.
- Introduce every fence with a sentence and use a language tag. Keep expected
  output in a separate `text docforge-role=output` fence.
- A document contract may require a command, payload, or diagram even for an
  audience whose default is `contract-only`.

## Fence roles

Use the language when it establishes the role: `bash`/`sh` for commands,
`mermaid` for diagrams, and a concrete source or configuration language for a
consumer-facing example. Use `docforge-role=` only when the language is
ambiguous:

| Role | Use for |
|---|---|
| `command` | executable shell or PowerShell steps |
| `code` | consumer-facing implementation examples |
| `config` | settings required for an action |
| `output` | captured or expected command output |
| `diagram` | Mermaid diagrams |
| `structure` | trees, timelines, and record layouts |
| `markup` | literal Markdown examples |

The linter treats prose-like content in a `command`, `code`, `diagram`, or
`structure` fence as a defect when it is clearly not literal output or markup.
