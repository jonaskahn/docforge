# Shape — desktop application

**Applies when:** the repository ships a user-installed application for macOS, Windows, Linux, or multiple desktop platforms.

Desktop applications operate in a long-lived, user-controlled environment:
many windows and documents may coexist, files and paths are local, and
updates must preserve user data across versions. Document system integration,
storage boundaries, and update behavior rather than restating the view
hierarchy.

## Additions to the tree

```
docs/
├── architecture/
│   ├── application-lifecycle.md  startup, windows, documents, recovery, shutdown
│   ├── ui-and-state.md           window/session state and persisted user state
│   └── platform-integration.md   files, URLs, clipboard, notifications, OS services
├── security/
│   └── permissions.md            sandboxing, filesystem, automation, credentials
├── reference/
│   └── platform-compatibility.md supported OS/architecture targets and caveats
└── operations/
    └── distribution.md           signing, notarization, installers, updates, rollback
```

## `architecture/application-lifecycle.md`

Describe launch paths, single-instance or multi-instance behavior, window and
document restoration, background helpers, termination handling, and crash
recovery. Name each persistent location and its ownership. A reader must be
able to answer whether closing a window, quitting the app, or an OS update
can discard work.

## `architecture/ui-and-state.md`

Separate application-global state, per-window state, per-document state, and
user preferences. State where each persists, how concurrent windows avoid
overwriting one another, and how schema migrations or corrupted local data
are handled. Include the rules for external file changes when the app opens
user-owned files.

## `architecture/platform-integration.md`

Document every operating-system boundary: file associations, open-with and
URL handlers, drag and drop, clipboard, menu and keyboard shortcuts,
notifications, login/background items, and automation. For each, name the
registration location, platform limitations, and safe failure behavior.

## `security/permissions.md`

Record sandbox, filesystem, accessibility, automation, keychain/credential-
store, and network permissions by capability. Explain user consent, scope,
revocation, and the degraded experience. Do not treat installer privileges or
code-signing entitlement as proof that runtime access will succeed.

## `reference/platform-compatibility.md`

List supported OS releases, processor architectures, display/input
expectations, and dependencies such as runtimes or system services. State
upgrade and end-of-support policy, including whether older installations
receive security-only updates.

## `operations/distribution.md`

Describe packaging format, signing and notarization or equivalent trust
chain, installer/update ownership, release channels, and rollback procedure.
Call out migrations that make downgrades unsafe and the recovery path for a
broken update.
