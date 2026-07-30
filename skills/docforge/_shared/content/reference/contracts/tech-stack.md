# `tech-stack`

Content contract for document type `tech-stack`.

| Type | Must present | Keep out | Primary mode | Depth |
|---|---|---|---|---|
| tech-stack | detected languages/versions; runtimes/SDKs; primary frameworks per layer; datastores and messaging; build/package/dependency-management tooling; test and CI tooling; key runtime libraries with role | full lockfile dump, invented versions, marketing comparisons, operational-failure framing (owned by dependencies-inventory) | Reference | reference |

**Shape-conditional must-present:** for `infrastructure-platform`, replace the
row above with: IaC tool + version, cloud provider(s) targeted, orchestration
platform, environments defined, promotion/release tooling, secret-management
approach.

**Ownership:** `tech-stack` owns "what it is built with";
`dependencies-inventory` owns "what it depends on operationally and what
breaks."
