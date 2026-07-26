# Overlay — infrastructure as code

**Applies when:** the repo contains infrastructure definitions — declarative cloud resources, cluster manifests, configuration management, or deployment orchestration.

Infrastructure repos invert the usual risk profile: the code is often short and readable, but the consequences of a wrong change are immediate, shared, and sometimes irreversible. Documentation should concentrate on the two things the code cannot express — what state exists outside the repo, and what a change will actually do when applied.

## Additions to the tree

```
docs/
├── architecture/
│   ├── environments.md         what exists, where, and how environments differ
│   └── network.md              topology, boundaries, ingress and egress
├── operations/
│   ├── apply.md                how a change reaches an environment safely
│   ├── state.md                where state lives, locking, recovery
│   ├── disaster-recovery.md    backups, RTO/RPO, tested restore procedure
│   └── runbooks/
└── reference/
    ├── resources.md            resource inventory with ownership and cost
    └── access.md               who and what can change what
```

## `architecture/environments.md`

An inventory table (environment, purpose, region, who may apply changes, data classification) followed by an explicit statement of **how environments differ** — sizing, replica counts, feature toggles, data volume, retention. The differences are where staging stops predicting production, and they are almost never written down. If any environment is not reproducible from code, say so plainly and name what is manual; that gap is the most important fact in the document.

## `operations/apply.md`

The change procedure, in order: propose, review, plan, inspect the plan, apply, verify, roll back. State who may apply to each environment and what approval is required.

Include a section on **reading a plan** for this specific stack: which diff lines mean replacement rather than update, which resources cannot be modified in place, and which changes cause downtime. This is the knowledge that separates a safe operator from a dangerous one, and it lives entirely in people's heads by default.

Then the destructive-operation list: the changes that destroy data or cause outage, each with the safe procedure. A reviewer should be able to spot a dangerous plan by comparison with this list.

## `operations/state.md`

Where state is stored, how it is locked, who can access it, how it is backed up, and how to recover from corruption, a lost lock, or drift. Include the procedures for importing an existing resource and for removing a resource from state without destroying it — both are needed at moments when nobody wants to be reading documentation for the first time.

## `operations/disaster-recovery.md`

What is backed up, how often, where, and for how long; the recovery objectives (how much data loss is acceptable, how quickly service must return); the restore procedure step by step; and — the part that matters — **when the restore was last actually tested and what happened**. An untested backup is a hypothesis. Record the test date; its absence tells a reviewer everything.

## `reference/resources.md`

An inventory of what exists, with owner, purpose, environment, and rough cost. This becomes the basis for cost review, orphan cleanup and access audit. Flag resources that exist but are not managed by this repo — manually created resources are the most common source of surprise during a migration or an incident.

## `reference/access.md`

Human roles and their permissions per environment, machine identities and what each can do, how access is granted and revoked, how credentials are stored and rotated, and how privileged access is audited. Reference the identity system rather than duplicating its contents; the value here is the mapping from role to capability, which the identity system expresses in a form nobody reads.

## `reference/limitations.md` additions

Typical entries: provider quotas and limits that constrain scaling; resources that cannot be changed without replacement; regional or zonal constraints; version-upgrade paths that require downtime; manual steps not captured in code; and known drift between declared and actual state.

## Security note

Infrastructure repos attract secrets. State in `docs/security/README.md` how secrets are handled — the secret manager used, how values reach running workloads, and how the repo is scanned for accidental commits. If any credential has ever been committed, rotation is not optional, and the fact that a scanner is in place is worth documenting explicitly for reviewers.
