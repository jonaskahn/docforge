# Architecture (agent view)

<!-- Standalone: this is the repository's only architecture documentation.
     Own the facts a code graph supports — paths, boundaries, entry points.
     Never rationale ("why we chose X"); that is not derivable from a graph. -->

{{One sentence: the stack — primary languages/frameworks.}}

## Quick start

```
{{install and dev commands, from the manifests}}
```

## Layer map

{{one bullet per layer, name + one-line responsibility}}

## Boundaries

{{one bullet per rule, from graph edge direction: which layer may import which,
  and which direction is never observed. State the rule, not its history.}}

## Entry points

{{at most five rows, from graph roots and in-degree}}

| Entry | Path | Handles |
|---|---|---|
| {{name}} | `{{durable path}}` | {{one line}} |

## Where to add X

{{three to five rows mapping a change kind to the directory that owns it}}

| To change | Work in |
|---|---|
| {{change kind}} | `{{directory}}` |
