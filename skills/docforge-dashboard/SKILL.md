---
name: docforge-dashboard
description: Local Fumadocs dashboard for Docforge documentation — reconcile metadata, convert docs/ Markdown to MDX, and serve a generated site at /docs without touching the repository's package files.
---

# Docforge Dashboard

Slash command: `/docforge-dashboard`. Companion to `/docforge` and
`/docforge-revise`. Shared cartridge:
[`../docforge/_shared/`](../docforge/_shared/README.md).

## Load order

1. [`../docforge/_shared/rules.md`](../docforge/_shared/rules.md) — safety, graph precondition,
   provider sufficiency, completion.
2. [`../docforge/_shared/flags.md`](../docforge/_shared/flags.md) — `--plan-only`,
   `--auto-accept`.
3. [`../docforge/_shared/retrieval.md`](../docforge/_shared/retrieval.md) — catalog retrieval
   protocol.
4. Follow [`./workflows/dashboard.md`](workflows/dashboard.md)
   for the full dashboard lifecycle.
5. For metadata and manifest questions, use
   [`../docforge/_shared/workflows/validation.md`](../docforge/_shared/workflows/validation.md)
   and [`../docforge/_shared/workflows/tools.md`](../docforge/_shared/workflows/tools.md).

Dashboard-specific tools run from this skill root (`./runtime/cli/`); they
consume the shared cartridge's codec/util but live here because nothing else
uses them. Shared rules, flags, and retrieval are loaded from the cartridge.
Lock one session engine first; see
[`../docforge/_shared/workflows/tools.md`](../docforge/_shared/workflows/tools.md)
for execution rules and CLI syntax.

## `/docforge-dashboard`

| Flag | Effect |
|---|---|
| *(none)* | Full lifecycle: preflight → fingerprint → metadata reconcile → optional revise → route plan → MDX convert → navigation → validate → serve → open |
| `--plan-only` | Preflight, fingerprint, metadata dry-run, and route plan; no conversion, no writes, no server |
| `--auto-accept` | Skip the revise-vs-render prompt and routine pauses; never authorizes npm install of new packages without its own confirmation gate (see [`../docforge/_shared/flags.md`](../docforge/_shared/flags.md)) |

The dashboard lives in `<repo>/.docforge/dashboard/`:

- **Generated and disposable.** The directory is ignored via `.docforge/.gitignore`
  (rule `dashboard/`) but stays readable by agents and users when addressed
  explicitly.
- **Self-contained.** `package.json`, `package-lock.json`, and `node_modules`
  exist only inside the dashboard directory. Every npm command runs with
  `--prefix .docforge/dashboard`; the repository's own `package.json` and
  lockfiles are hashed before and after install and must not change.
- **Never hand-edited.** Content under `content/docs/` is converted from the
  repository's `docs/` Markdown plus manifest metadata.

## Lifecycle summary

```text
PREFLIGHT -> FINGERPRINT -> METADATA RECONCILE -> OPTIONAL REVISE
-> ROUTE PLAN -> MDX CONVERT -> NAVIGATION -> VALIDATE -> SERVE -> OPEN
```

- **Preflight:** repository, manifest 3.1, written `docs/` documents, and
  Node.js 22+ for the Fumadocs app.
- **Fingerprint:** HEAD, manifest, flow-index, every `docs/` file, template
  files, root package files, and settings. An unchanged fingerprint skips
  reconcile, convert, install, and cleanup — the dev server is reused or
  started and the dashboard opens.
- **Metadata reconcile:** ensures each written document's public `id` and
  `title` frontmatter match the manifest and that `docforge_provenance.doc_id`
  / `path` agree; bodies are preserved byte-for-byte.
- **Optional revise:** when documentation changed and the user chooses, run
  `/docforge-revise all` before conversion; otherwise render current
  documentation as a snapshot.
- **Route plan:** maps every included document to one Fumadocs URL and fails
  on duplicates before any write.
- **MDX convert:** structural conversion (code fences and inline code
  preserved; typed `<UPPER_SNAKE_CASE>` tokens and literal braces escaped
  outside code), internal link rewriting through the route ledger, and
  controlled asset copying.
- **Navigation:** one `meta.json` per folder with exact page coverage.
- **Validate:** duplicate URLs, meta coverage, internal links and heading
  anchors, assets, and the docs index.
- **Serve:** localhost-only dev server on a free port; PID and port are stored
  in `.docforge/dashboard/.docforge-dashboard.json` and reused while healthy.
  The command stays attached and stops the server on `Ctrl+C`, `Ctrl+Z`, or
  terminal closure.
- **Open:** the dashboard at `http://127.0.0.1:<port>/docs`.

## Isolation rules

- Never write outside `<repo>/.docforge/dashboard/` except the metadata
  reconciliation of `docs/` frontmatter (the dashboard's required input) and
  the `.docforge/.gitignore` rule.
- Never touch the repository's `package.json`, lockfiles, or workspace
  configuration.
- Never delete `node_modules`, `.next`, or the app shell for an ordinary
  content refresh; only `content/docs/` is replaced atomically (staged, then
  swapped).
- Re-running with an unchanged fingerprint performs no content writes.

## Not this command

- Fresh-start documentation plan → `/docforge`
  ([`../docforge/SKILL.md`](../docforge/SKILL.md)).
- Structural revise of the documentation itself → `/docforge-revise`
  ([`../docforge-revise/SKILL.md`](../docforge-revise/SKILL.md)).
- Read-only progress → plain language or `manage_manifest status` (no
  `--status` skill flag).
