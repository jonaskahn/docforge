# Portfolio diligence

Portfolio is the cross-repository tier. It includes the full Diligence set for
member repositories plus this complete layer:

```text
docs-portfolio/
  README.md
  repo-inventory.md
  system-context.md
  decisions/README.md
  security-posture.md
  operations.md
  diligence-index.md
  glossary.md
```

Actual cross-repository decisions are dynamic documents under `decisions/`.

- `README.md` is the platform one-pager and routes to every portfolio artifact.
- `repo-inventory.md` records every mechanically discovered member, membership
  evidence, baseline status, and review disposition.
- `system-context.md` shows the platform boundary, deployable members, shared
  dependencies, protocols, and important cross-repository flows.
- `security-posture.md` summarizes cross-cutting identity, secrets, encryption,
  network, dependency, logging, incident, and disclosure controls, linking to
  member evidence.
- `operations.md` owns platform environments, operational coupling, shared
  signals, recovery order, and external owner/SLO tokens.
- `diligence-index.md` maps review questions to evidence and records gaps and
  confidence.
- `glossary.md` owns terms shared across repositories.

Under time pressure, sequence orientation/inventory, system context,
dependencies/security, limitations, member architecture, then decisions. Do
not overstate intended architecture or hide known gaps; record evidence,
uncertainty, and remediation separately.
