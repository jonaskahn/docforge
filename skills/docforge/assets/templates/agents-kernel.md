# {{project_name}}

{{One sentence: what this is.}} {{One sentence: primary languages/frameworks, from the manifests.}}

<!-- docforge-provenance v{{skill_version}} | graph {{graph_hash_short}} | {{graph_analyzed_date}} | regenerate: re-run the agent-context overlay -->

## 1. Commands

**One way to run things. Don't invent alternatives.**

```
{{install command}}
{{dev command}}
{{test command}}
{{lint command}}
{{build command}}
```

The test: a fresh clone runs green after pasting the commands above.

## 2. Boundaries

**Three tiers. No exceptions, no shortcuts.**

Always: {{directive from CONVENTIONS.md, or a safe default}}
Ask first: {{directive}}
Never: commit secrets, `.env` files, or credentials.
Never: edit or delete applied migrations.
Never: run destructive commands without explicit approval.
Never: push `--force` to `main`.
{{one or two project-specific Never lines, only if CONVENTIONS.md adds one not already covered}}

## 3. Module Map

**Layers are disjoint. Don't blur them.**

{{one bullet per layer: `- {{layer name}} ({{node count}}) — {{one-line responsibility}}`}}

The test: every file under `{{primary source dir}}/` maps to exactly one layer above.

## 4. Architectural Altitude

**{{one-line tagline naming the main layer and, if any, the backstage layer}}**

{{one bullet per guided-tour entry point, max 5: `- To understand {{step}}, start at \`{{file path}}\`.`}}

The test: open this file cold, name the top two entry points without scrolling.

## 5. Non-Obvious Conventions

**Match existing shape. Don't normalise the outliers.**

{{one bullet per topology-derived surprise the graph actually surfaced. Omit this whole section — heading included — if nothing surprising was found; an empty section is worse than none.}}

The test: grep for the convention in two more places before assuming it holds.

## 6. Absolute Rules

**Read and follow. No exceptions, no workarounds.**

### Safety
- MUST NOT commit secrets, `.env` files, or credentials.
- MUST NOT edit migrations after they have been applied.
- MUST NOT disable tests to make them pass.
- MUST NOT run destructive commands without explicit human approval.
- When a hook blocks a command, stop and ask — never work around it.

### While coding
- MUST NOT add abstractions beyond what is planned.
- MUST NOT improve or refactor adjacent unrelated code.
- MUST state assumptions explicitly; if uncertain, ask before proceeding.

{{### Project-specific — only if CONVENTIONS.md has a safety/pattern directive not already covered above. Omit heading and block entirely otherwise.}}

## 7. Deeper Context

**This file is the kernel. Below it, read on demand.**

- @docs/agents/architecture.md — stack, quick start, layer map
{{- @docs/agents/flow.md — domain flows with entry points and triggers (omit if no domain graph or no flows)}}
- @docs/agents/patterns.md — recurring patterns and exemplars
{{- @docs/agents/glossary.md — canonical vocabulary (omit unless domain quality is high or mixed)}}
{{- @docs/agents/conventions.md — AI-targeted coding directives (only if CONVENTIONS.md exists)}}
- @docs/agents/testing.md — runner, layout, mock stance
- @docs/agents/tech-debt.md — known gotchas

The test: if the answer is here, don't open `docs/agents/`.

---

Working if: agents stop asking "where does X live?", hook denials are respected, and PRs match the conventions above without being told.
