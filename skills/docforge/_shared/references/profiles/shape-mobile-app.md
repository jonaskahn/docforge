# Shape — mobile application

**Applies when:** the repository ships an iOS, Android, or cross-platform application installed and used on a phone or tablet.

Mobile applications do not control their runtime: the operating system can
suspend or terminate them, devices vary sharply, and permissions, network
access, and distribution are mediated by the platform. Document the
lifecycle boundaries and platform commitments that source code alone cannot
make clear.

## Additions to the tree

```
docs/
├── architecture/
│   ├── application-lifecycle.md  foreground, background, restoration, recovery
│   ├── ui-and-state.md           navigation, state ownership, offline behavior
│   └── platform-integration.md   OS services and their failure modes
├── security/
│   └── permissions.md            requested capability, purpose, denial behavior
├── reference/
│   └── platform-compatibility.md supported OS/device targets and degradation
└── operations/
    └── distribution.md           signing, store release, staged rollout, rollback
```

## `architecture/application-lifecycle.md`

State what survives process death and what does not. Cover launch inputs
(notification, deep link, restored state), foreground/background
transitions, background work eligibility and limits, interruption recovery,
and the exact point at which unsaved work is persisted. Separate an OS
guarantee from best effort; a task that "continues in the background" is
misleading unless its platform grant, time limit, and recovery behavior are
named.

## `architecture/ui-and-state.md`

Map the principal user journeys to navigation state, persisted data, and
network-dependent state. Name the source of truth for each and describe the
offline, slow-network, conflict, and sign-out cases. Do not inventory
screens; record the rules that keep restored or resumed screens from showing
stale, unauthorized, or impossible state.

## `architecture/platform-integration.md`

For each platform capability used (notifications, camera, location, files,
background execution, authentication, share sheets), state the initiating
user action, permission or entitlement, data exchanged, supported platforms,
and behavior when unavailable or denied. This makes a platform-policy change
diagnosable without reading platform-specific code.

## `security/permissions.md`

One row per permission: platform name, user-facing purpose, feature blocked
when denied, fallback, data retention, and revocation behavior. Never imply
a permission is guaranteed merely because it was requested. Link any
capability that is required for a store declaration or privacy disclosure.

## `reference/platform-compatibility.md`

List minimum supported OS versions, device and form-factor support, required
hardware and services, and each known degraded path. Give the support policy
and test basis, not just a platform matrix. Distinguish unsupported from
supported-with-reduced-functionality.

## `operations/distribution.md`

Document the signing identity or service, release channels, store metadata
owners, review gates, rollout controls, and how a harmful release is halted.
State which changes cannot be rolled back after users install them,
especially persisted-data migrations and backend contract changes.
