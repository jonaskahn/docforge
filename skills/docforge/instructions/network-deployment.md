# Network-deployment writing craft

**Preferred illustration:** Follow
[`../references/illustration.md`](../references/illustration.md); this is a
how-to — numbered steps and a verification command, not a diagram.

Write one verified path per target network (mainnet, testnet, or
equivalent), in order: network configuration, key and role setup, deploy
step, and post-deploy verification — a reader should never have to guess
which network a step applies to. State who holds which role (deployer,
admin, upgrader) and what each role can do, as a table; a deployment
procedure that doesn't name its own privileged roles is incomplete by the
same standard [contract-system.md](contract-system.md) sets for upgrade
boundaries.

Give the upgrade and rollback path the same rigor as the initial deploy —
an unverified destructive command in either direction is worse here than
almost anywhere else in the document set. Never include a private key,
seed phrase, or fabricated address; use an obviously synthetic placeholder
and say so.
