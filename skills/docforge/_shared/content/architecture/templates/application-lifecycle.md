# Application lifecycle

_Last reviewed: {{YYYY-MM-DD}}_

```mermaid
stateDiagram-v2
  [*] --> Launch
  Launch --> Active
  Active --> Background
  Background --> Active
  Background --> Terminated
  Terminated --> [*]
```

_Repeat per state — Launch, Active, Background, Terminated above._

## {{State}}

**Owner:** {{accountable component or team for this state's behavior}}

**Trigger:** {{what enters this state}}

**Must do before leaving:** {{cleanup/save}}

**Restoration on relaunch:** {{behavior}}

**On kill mid-transition:** {{failure boundary}}
