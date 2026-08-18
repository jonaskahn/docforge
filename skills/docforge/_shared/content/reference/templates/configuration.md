# Configuration

_Last reviewed: {{YYYY-MM-DD}}_

## Sources and precedence

{{Where configuration comes from, and what happens when two sources set the
same key.}}

```mermaid
%% Precedence only -- not an inventory of settings. Left loses, right wins.
accTitle: Configuration source precedence
accDescr: {{One sentence: which sources exist and which one wins a conflict.}}
flowchart LR
  Default["{{built-in default}}"] -->|"{{overridden by}}"| File["{{config file}}"]
  File -->|"{{overridden by}}"| Env["{{environment variable}}"]
  Env -->|"{{overridden by}}"| Secret["{{secret store}}"]
```

{{One or two sentences: which source wins, which values are required with no
default, and where a missing value fails — at boot or at first use. A reader
debugging "my setting had no effect" needs this before the table.}}

## Settings

Ordered by how often a reader tunes each setting.

| Setting | Source | Default | Scope | Sensitive |
|---|---|---|---|---|
| {{name}} | {{env var / config key}} | {{default}} | {{env/service}} | {{yes/no}} |
