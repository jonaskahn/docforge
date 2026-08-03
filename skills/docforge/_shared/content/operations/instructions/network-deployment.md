# Network-deployment writing craft

Ground network identity, RPC/configuration source, deployed artifact and version,
address, and role assignment in deployment configuration, manifests, or verified
history. For deploy, upgrade, and rollback, state approving authority and the
confirmation boundary; never infer account or multisig control.

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); this is a
how-to — numbered steps and a verification command, not a diagram.

Write one verified path per target network (mainnet, testnet, or
equivalent), in order: network configuration, key and role setup, deploy
step, and post-deploy verification. State who holds which role (deployer,
admin, upgrader) and what each role can do, as a table; a deployment
procedure that doesn't name its own privileged roles is incomplete by the
same standard [contract-system.md](contract-system.md) sets for upgrade
boundaries.

Give the upgrade and rollback path the same rigor as the initial deploy.
Never include a private key, seed phrase, or fabricated address; use an
obviously synthetic placeholder and say so.
