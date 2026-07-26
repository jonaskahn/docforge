# Local setup

_Last reviewed: {{YYYY-MM-DD}}_ · Expect roughly **{{N}} minutes** for a first run.

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| {{runtime}} | {{exact version or range}} | {{how to install}} |
| {{tool}} | {{version}} | |

Access you will need, and who grants it: {{credential or system}} — {{role/team}}.

## Steps

1. Clone the repository and enter it.
2. `{{install command}}`
3. Copy the example configuration: `cp {{.env.example}} {{.env}}` and fill in the
   values described in [../reference/configuration.md](../reference/configuration.md).
4. `{{start dependencies — database, queue, etc.}}`
5. `{{run the application}}`

## Verify

```bash
{{verification command}}
```

Expected output:

```
{{what success looks like}}
```

## Common problems

**{{Symptom}}** — {{cause and fix}}.

**{{Symptom}}** — {{cause and fix}}.

## Next

- Understand the codebase: [../architecture/overview.md](../architecture/overview.md)
- Run the tests: [testing.md](testing.md)
- Make a change: [../contributing/README.md](../contributing/README.md)
