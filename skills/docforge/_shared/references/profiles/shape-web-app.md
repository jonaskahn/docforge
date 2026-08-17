# Shape — web application

**Applies when:** the repo builds a browser-delivered interface — a single-page app, a server-rendered application, or a static site with client-side behaviour.

Front-end repos have a characteristic documentation failure: the code is
highly legible (components are self-describing, the router shows the page
structure) while the things that actually cause problems are invisible —
where the rendering boundary sits, which state is authoritative, what
happens when the API is slow, and which browsers are actually supported.
Document the invisible things; do not narrate the component tree.

## Additions to the tree

```
docs/
├── architecture/
│   ├── rendering.md            server/client boundary, routing, caching
│   ├── state.md                what state exists, who owns it, how it syncs
│   └── ui-components.md        the shared component layer and its conventions
├── engineering/
│   └── styling.md              design tokens, theming, styling approach
└── reference/
    ├── configuration.md        every environment variable, and which are public
    └── browser-support.md      supported targets and performance budgets
```

## `architecture/rendering.md`

The single most valuable document for a web repo, because the rendering
model is the thing a newcomer gets wrong first.

Cover: which routes render where (server, client, statically at build time,
or incrementally), the exact rule for deciding whether new code goes
server-side or client-side, where data fetching happens for each case, what
is cached and for how long at each layer, how cache invalidation is
triggered, and what the user sees during loading and error states. Include a
route map — path, rendering strategy, data source, authentication
requirement — as a table.

State the boundary rules as invariants, since they are absences and
therefore invisible: "server components never import from `src/client/`",
"no component fetches directly; all data access goes through `src/data/`".

## `architecture/state.md`

Enumerate the categories of state and where each lives: server state
(fetched, cached, revalidated), client UI state (ephemeral), form state, URL
state (query parameters as shared truth), and persisted client state
(storage, cookies). For each, name the mechanism used and the rule for
choosing it.

The rule matters more than the inventory. Without one, every contributor
picks their favourite and the application ends up with four state systems
doing the same job.

## `architecture/ui-components.md`

Not a catalog of every component — that is what the code and, if present, a
component workbench are for. Document instead: the layering (primitives,
composites, feature components, layouts), which layer may import from which,
what belongs in the shared layer versus a feature folder, the props
conventions, and how variants and theming are expressed. If a component
workbench exists, link to it and stop.

## `reference/configuration.md`

Front-end configuration has a hazard the back end does not: **variables
exposed to the browser are public**. Anything embedded in the client bundle
is readable by anyone who opens developer tools. Make the exposure explicit
per variable:

| Variable | Purpose | Exposed to browser | Required | Default | Example |
|---|---|---|---|---|---|

Add a warning at the top of the file stating the exposure rule for this
framework's prefix convention, and never place a secret in a browser-exposed
variable. If one is currently there, that is a limitations entry and
probably an incident.

## `reference/browser-support.md`

Supported browsers and minimum versions, the basis for that list (analytics,
a support policy, or a guess — say which), what degrades versus what breaks
on unsupported targets, accessibility conformance target and known gaps, and
the performance budget with actual measured numbers. Reviewers and product
owners both ask for this and it is rarely written down.

## `reference/limitations.md` additions

Characteristic front-end entries: features unavailable without JavaScript;
known accessibility gaps with tracking references; behaviour on slow or
offline connections; upload size ceilings; list-rendering limits before
performance degrades; known layout issues on specific viewports; anything
that requires third-party cookies or storage that a strict browser
configuration blocks.

## Third-party front-end dependencies

Front ends accumulate services that execute in the user's browser —
analytics, error tracking, session replay, feature flags, chat widgets, tag
managers. Each is a data-protection consideration as much as a technical one,
so `architecture/dependencies.md` should record for each: what it collects,
whether it can capture personal data or form contents, whether it is loaded
before or after consent, where the data is processed, and what happens if
the script fails to load.

Session replay and error trackers deserve particular care: unless explicitly
configured otherwise, both may capture input contents. Document the masking
configuration and the fact that it exists.
