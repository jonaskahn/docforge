# Testing (agent view)

<!-- Standalone: this is the repository's only testing documentation. Own what
     the manifests and CI config state. Never invent a coverage policy or a test
     pyramid — those are judgment content with no mechanical source here. -->

## Runner

```
{{full-suite command}}
{{single-test command}}
```

## Layout

{{one line: where tests live, naming convention}}

{{one line: where fixtures and test configuration live, when the suite has them}}

## Mock stance

{{one line: what's mocked vs real in tests — use a typed <MOCK_STANCE> token only if genuinely not inferable from the test suite}}

## Before a PR

```
{{the exact ordered commands a change must pass, from manifest scripts and CI configuration}}
```
