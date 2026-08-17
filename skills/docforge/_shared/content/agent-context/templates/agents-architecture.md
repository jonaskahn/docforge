# Architecture

{{One sentence: the stack — primary languages/frameworks.}}

## Components

| Source path | Responsibility | Depends on | Must not depend on |
|---|---|---|---|
| `{{durable path}}` | {{one-line responsibility}} | {{lower-level component or external boundary}} | {{forbidden dependency}} |

## Entry points

{{One bullet per material trigger: `- {{trigger}} enters at \`{{source path}}\` and hands off to {{component}}.`}}

## Invariants

- Dependency direction: {{evidence-backed direction.}}
- Data boundary: {{where state enters, changes, and leaves.}}
- Change constraint: {{material rule an edit must preserve.}}
