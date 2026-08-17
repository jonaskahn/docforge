# {{project_name}}

{{One sentence: what this is.}} {{One sentence: primary languages/frameworks, from the manifests.}}

<!-- docforge-provenance v{{skill_version}} | graph {{graph_hash_short}} | {{graph_analyzed_date}} | regenerate: re-run the coding-agents audience -->

## Commands

```sh
{{verified install command}}
{{verified development or run command}}
{{verified focused test command}}
{{verified full validation command}}
```

Omit unavailable commands. Never invent an alternative.

## Repository Map

{{One bullet per durable source or configuration path: `- \`{{path}}\`: {{responsibility and boundary}}`}}
{{Up to five entry-point bullets: `- {{trigger or task}} starts at \`{{source path}}\`.`}}

Dependency direction: {{evidence-backed layer order and forbidden direction.}}

## Precedence

1. Preserve safety constraints and explicit approval requirements.
2. Follow the user's task requirements.
3. Follow the repository rules stated here.
4. If instructions conflict or evidence is missing, stop and ask.

## Boundaries

- Always: {{evidenced project directive.}}
- Ask first: {{operation requiring explicit approval.}}
- Never commit secrets, credentials, or local environment values.
- Never disable tests, validation, or checks to force success.
- Never run destructive commands without explicit approval.
{{One or two additional evidenced project-specific boundaries, if present.}}

## Conventions

{{Include only when non-obvious conventions are evidenced. State each as an imperative with a durable source path or repeated structural signal. Omit this heading and section when none qualify.}}

## Validation

- Minimum for a focused change: `{{verified command}}`
- Required before completion: `{{verified command}}`
- Success means: {{observable passing result.}}

Working if: commands are reproducible, boundaries hold, and changes pass the stated validation.
