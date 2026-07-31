# Shape — smart contract

**Applies when:** the repository deploys executable contracts or programs to a blockchain or distributed-ledger network.

Deployed contract behavior is public, stateful, and often irreversible. The documentation must make the external surface, authority model, economic invariants, trust assumptions, deployment parameters, and upgrade or incident limits reviewable before a transaction is signed.

## Additions to the tree

```
docs/
├── architecture/
│   └── contract-system.md        contracts, storage, calls, events, roles, upgrades
├── security/
│   └── economic-invariants.md    value flows, trust assumptions, invariant checks
└── operations/
    └── network-deployment.md     network config, keys, verification, pause/rollback
```

## `architecture/contract-system.md`

For every deployed contract, state its address per network once deployed, purpose, public and privileged entry points, persistent state, emitted events, external calls, and authority roles. Describe asset and value flows in domain terms, not only types. State whether the implementation is immutable, proxied, or otherwise upgradeable, who controls upgrades, the delay and approval path, and how storage compatibility is protected.

## `security/economic-invariants.md`

Express the properties that must remain true across every successful transaction: conservation or accounting of value, authorization boundaries, collateral or supply constraints, price/oracle assumptions, and emergency-stop behavior. For each invariant, identify enforcement location, tests or monitoring that exercise it, and the consequence if it fails. Also list trusted actors and external dependencies; an unstated multisig, oracle, sequencer, or admin key is a hidden security boundary.

## `operations/network-deployment.md`

Document chain/network identifiers, deployment order and constructor parameters, deterministic-address assumptions, compiler and optimizer settings, bytecode/source verification, signer custody, required confirmations, and post-deploy checks. Treat a deployment as incomplete until the expected code, roles, configuration, and event/asset balances are independently verified on the target network.

## Failure and incident limits

State what can be paused, upgraded, migrated, or recovered and what cannot. Include the response path for a compromised key, discovered vulnerability, oracle failure, and failed deployment. Do not promise rollback on a network where confirmed transactions are irreversible; name the compensating action instead.
