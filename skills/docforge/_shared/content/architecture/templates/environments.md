# Environments

_Last reviewed: {{YYYY-MM-DD}}_

| Dimension | {{Dev}} | {{Staging}} | {{Production}} |
|---|---|---|---|
| Configuration | {{value/source}} | {{...}} | {{...}} |
| Scale | {{...}} | {{...}} | {{...}} |
| Data realism | {{...}} | {{...}} | {{...}} |
| External services | {{stub/real}} | {{...}} | {{...}} |
| Config owner | {{team/system}} | {{...}} | {{...}} |

Configuration values themselves live in
[reference/configuration.md](../reference/configuration.md) — this table states
who owns each environment's settings, not the values.

## Promotion boundary

{{What must be true before a change moves to the next environment, and who
owns that gate.}}
