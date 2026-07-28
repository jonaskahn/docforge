# Flow derivation

Use this procedure when a selected document requires `flow_graph` and the
chosen provider has a code graph but no native flow graph.

1. Run `derive_flow_graph prepare --repo <repo>`. It ranks externally visible
   entry points and emits a bounded analysis context.
2. Analyze the ranked entries in order. Record actors, trigger, ordered steps,
   branches, rules, failures, and outcome. Do not turn every graph node into a
   flow.
3. Run `derive_flow_graph write --repo <repo> --analysis <analysis.json>`.
4. Treat `.docforge/tmp/flow-graph.json` as provisional. Confirm business rules
   against source before asserting them.
5. Rerun `precheck_graph --repo <repo> --need flow`.

The derived file is temporary, git-ignored, and regenerated when needed. A
native provider result takes precedence.
