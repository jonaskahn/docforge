# Agent-context overlay

Select this overlay explicitly when agent-facing context is wanted. It writes
last because its views link to finished human-facing documents.

The catalog defines:

- `AGENTS.md`: compact root kernel, exempt from frontmatter and capped by the
  agent-kernel lint profile;
- `CLAUDE.md` and `CLAUDE.local.md`: fixed shims, with provenance in manifest;
- `.claude/settings.json`: safely merged machine configuration;
- `docs/agents/`: brief linking views.

`CLAUDE.local.md` is added to the target repository’s ignore rules.

Architecture and patterns require the code graph. Testing uses manifests.
Conventions is selected only with an existing conventions source. Only the flow
view and flow-derived glossary view require the flow graph. Other agent files
must not be hard-gated on it.

Agent views link to the human document that owns a fact. Patterns may contain
agent-specific exemplars when no human document owns them. Cross-vendor mirrors
are produced only when requested or when existing target configuration makes
them applicable.
