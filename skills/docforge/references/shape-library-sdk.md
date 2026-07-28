# Shape — library / SDK

**Applies when:** the repo publishes a package that other codebases depend on — a language package, an internal shared module, or a client SDK.

A library's public surface is a contract with every consumer, and unlike a service it cannot be fixed forward: a breaking change propagates into other people's codebases on their schedule, not yours. Documentation therefore has one dominant job — making the boundary between public and internal unambiguous — and one recurring obligation: migration guides.

## Additions to the tree

```
docs/
├── product/
│   ├── quickstart.md           install to first working use
│   └── migration/              one guide per major version transition
│       ├── README.md
│       └── v1-to-v2.md
├── reference/
│   ├── api.md                  generated reference + the public/internal rule
│   └── compatibility.md        supported runtimes, peers, platforms
└── engineering/
    └── publishing.md           versioning, release, yanking
```

## The public surface rule

State it once, unmistakably, in `reference/api.md`:

> Everything exported from the package root is public API and covered by semantic
> versioning. Anything reachable only via a deeper import path, or prefixed with
> `_`, is internal and may change in any release, including a patch.

Then enforce it mechanically — an export barrel, an explicit `exports` map, visibility modifiers, whatever the language offers. A rule stated only in prose gets violated by consumers who then reasonably complain when it breaks, and you inherit a de facto commitment you never made.

## `product/quickstart.md`

Install command, minimal working example, and the three or four most common operations. The example must be complete and runnable — a fragment with elided imports fails the reader at exactly the moment they were about to succeed. Show the output.

## `reference/api.md`

Generate from doc comments in the source; hand-written API reference for a library drifts faster than for anything else because the surface is large and changes are small. Keep the hand-written part to: where the generated reference is published, the public/internal rule above, naming and argument conventions, the error model (what is thrown or returned, and what consumers may catch), and any global configuration.

## `reference/compatibility.md`

Supported language and runtime versions with the support policy behind them, peer dependency ranges and why they are bounded, supported platforms or architectures if relevant, and the end-of-life schedule for older majors. Consumers plan upgrades against this table; vagueness here becomes support tickets.

## `product/migration/vN-to-vM.md`

Write the migration guide *while* making the breaking changes, not after release. Reconstructing one from a diff months later misses the subtle behavioural changes, which are the ones that hurt.

```markdown
# Migrating from vN to vM

## Summary
What changed and why, in a paragraph. Estimated migration effort.

## Breaking changes
### <Change>
**Before / After** — code both ways.
**Why:** the reasoning.
**Automated:** whether a codemod or lint rule handles it.

## Behavioural changes
Same signature, different behaviour. The most dangerous category, because
nothing fails to compile. List these exhaustively even when the change is subtle.

## Deprecated but still working
What emits a warning now and will be removed when.

## New capabilities
Briefly — the reason to upgrade rather than pin.
```

## `engineering/publishing.md`

The version scheme and what each level means for this package specifically, how a release is cut, what gates it (tests, checks, approvals), where it is published, how a pre-release or release candidate is issued, and the procedure for a bad release — whether you unpublish, deprecate the version, or ship a patch. Decide that procedure before you need it.

## `reference/limitations.md` additions

Library-specific entries: platforms or runtimes not supported; thread-safety and concurrency guarantees (or their absence — this must be explicit); memory or performance characteristics at scale; known incompatibilities with common peer packages; bundle-size impact for client-side libraries; behaviours that differ between environments.

Concurrency guarantees deserve their own line. "This client is not safe for concurrent use; create one instance per worker" is the kind of sentence that prevents a class of production incident, and its absence is routinely read as a guarantee that was never made.
