# Deployment

_Last reviewed: {{YYYY-MM-DD}}_

{{One paragraph: what gets deployed where, and what a reader is usually here to
do — ship, verify, or roll back.}}

```mermaid
%% Which infrastructure node runs which block, per environment. Nodes are
%% infrastructure; labels name the block that runs on them.
accTitle: Deployment view for {{environment}}
accDescr: {{One sentence: which nodes exist and which deployable block runs on each.}}
flowchart LR
  Registry["{{artifact source}}"] -->|"{{pulled by}}"| Node["{{compute node}} · {{runs: {{block}}}}"]
  Node -->|"{{connects over}}"| Managed["{{managed service}}"]
```

{{One or two sentences: which node is the single point of failure, and what
differs between environments. Per-environment detail lives in environments.md.}}

## {{Environment, e.g. Production}}

**Artifact source:** {{where the deployable artifact comes from}}

**Rollout strategy:** {{blue-green / canary / rolling}}

1. {{step}} — verify: {{observable success signal}}
2. {{step}} — verify: {{observable success signal}}

## Rollback

1. {{step}}

```bash
{{verification command}}
```

Environment differences: see [environments.md](environments.md). Incident
recovery: see [disaster-recovery.md](disaster-recovery.md).
