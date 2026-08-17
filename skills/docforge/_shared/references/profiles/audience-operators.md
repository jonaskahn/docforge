# Operator audience profile

Select the `operators` audience when readers must deploy, observe, diagnose,
recover, or safely change a running system. This is an operational view over
repository and environment evidence; it does not turn unverified run commands
or assumed ownership into facts.

## Generated structure

```text
docs/operations/
├── README.md
├── deployment.md                         # selected when deployment evidence exists
├── observability.md                      # selected when signals or alerts exist
├── runbooks/
│   ├── README.md
│   └── {incident-or-task}.md             # dynamic; evidenced scenarios only
└── <shape-specific operations documents> # selected by catalog conditions
```

Shape-specific documents cover distribution, worker reliability,
infrastructure apply/state/disaster recovery, device flashing and recovery,
or network deployment. Select only the documents supported by the repository
shape and evidence; an empty operational taxonomy is not a useful
deliverable.

## Content ownership

### `README.md`

Route an operator from routine delivery to observability and
scenario-specific runbooks. State the system boundary and link to the
security posture for access and credential constraints; do not duplicate
either child document.

### Deployment and distribution

Document the evidenced artifact path, prerequisite access, rollout sequence,
verification signal, rollback boundary, and responsible role. Separate a
verified command from a placeholder or an external approval. Deployment facts
belong here; architecture explains why the components exist.

### Observability and runbooks

For each signal, identify what it indicates, its owner, correlation context,
alert intent, and known blind spots. Each runbook owns one symptom or task:
safety gate, diagnosis, bounded remediation, success check, escalation point,
and data-loss or customer-impact boundary. Do not write a runbook from a log
name or exception string alone.

## Evidence recipe

Follow the evidence loop in [`source-analysis.md`](../source-analysis.md):

1. Use the selected code graph to locate deployable units, entry points,
   configuration reads, operational dependencies, and tests.
2. Confirm artifacts, environments, commands, signals, and recovery behavior
   in configuration, automation, source, and executable verification.
3. Use history only to explain an evidenced operational decision or incident
   response.
4. Treat account roles, dashboards, on-call rotations, service objectives,
   and production procedures as external evidence unless recorded in the
   repo.
