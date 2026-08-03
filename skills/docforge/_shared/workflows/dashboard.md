# Dashboard

Owns: the dashboard capability of the `docforge` skill — `dashboard.{py,js}
start` (serve or `--export`), `scan`,
`status`, and `stop`; the generated Fumadocs application under
`<repo>/.docforge/dashboard/`; metadata reconciliation for public frontmatter;
MDX conversion; route planning; navigation generation; validation; and the
localhost dev server. The optional `/docforge-dashboard` skill is only a thin
entrypoint into this file.

Tool paths below are relative to the cartridge root
(`skills/docforge/_shared/`, launchers under `runtime/cli/`).

## What the dashboard is

A local, generated Fumadocs site that renders the repository's written
Docforge documentation (`docs/`, status `generated` / `needs_review` /
`complete` in the manifest) as an interactive site. It is a **view**, never a
documentation source: the source of truth stays the `docs/` Markdown files
and `.docforge/manifest.json`.

The dashboard directory is fully self-contained:

- its own `package.json`, `package-lock.json`, and `node_modules`;
- npm commands always use `npm --prefix <repo>/.docforge/dashboard`;
- the repository's own package files are hashed before and after install and
  must not change (the runtime fails loudly otherwise);
- the directory is ignored through `.docforge/.gitignore` (rule `dashboard/`),
  added by the runtime's own `ensure_dashboard_ignored` (which also keeps the
  shared Docforge ignore rules via the cartridge's `ensure_docforge_gitignore`).

## Legacy manifest gate

`scan` and `start` require a manifest 3.1 (or 3.0, which
`migrate_metadata.{py,js}` — see
[`../runtime/manifest/README.md`](../runtime/manifest/README.md) —
upgrades in place). When the preflight fails because
`.docforge/manifest.json` carries an **older legacy manifest version** (1.1
`project_context` / `document_groups`, 2.0 flat `documents` with overlays, or
any other pre-3.0 shape), stop and present exactly these options before any
write:

1. **Revise all (recommended)** — run `/docforge-revise all`. Its
   `migrate_metadata.{py,js}` step re-registers the legacy manifest as 3.1
   (adopting
   written documents as `generated` with provenance 2.0, bodies preserved),
   then the revision re-grounds, lints, and audits the tree per
   [`workflows/revision.md`](revision.md). Run `dashboard.{py,js} start` again
   after
   the whole-tree gate passes.
2. **Update metadata only** — run
   `migrate_metadata.{py,js} --repo <repo> --report` to re-register the
   manifest
   without revising content, then re-run `dashboard.{py,js} scan` (or
   `start`). This
   path exists for **any** legacy version — nothing is hard-coded to one
   shape. The dashboard opens only if the migrated tree passes the route
   plan and validation; otherwise present every remaining finding and offer
   the revision path again.
3. **Stop** — make no changes; the dashboard is not opened and no previous
   build is presented as current.

`--plan-only` runs `migrate_metadata.{py,js} --dry-run` and shows the
migration
preview instead of writing. `--auto-accept` never bypasses this gate: the
manifest rewrite and frontmatter adoption are side effects with their own
approval, like every other safety gate in [`flags.md`](../flags.md).

A migrated tree is a **baseline**, not a certification: adopted documents
carry provenance 2.0 but were never independently audited, so `scan`'s
staleness checks and the `you should revise again` recommendation still
apply.

## Command

```sh
python3 runtime/cli/python/dashboard.py scan --repo <repo> [--json]
node runtime/cli/js/dashboard.js scan --repo <repo> [--json]

python3 runtime/cli/python/dashboard.py start --repo <repo> [--force] [--plan-only] [--no-open] [--skip-install] [--port N] [--export]
node runtime/cli/js/dashboard.js start --repo <repo> [--force] [--plan-only] [--no-open] [--skip-install] [--port N] [--export]

python3 runtime/cli/python/dashboard.py status --repo <repo> [--json]
node runtime/cli/js/dashboard.js status --repo <repo> [--json]

python3 runtime/cli/python/dashboard.py stop --repo <repo>
node runtime/cli/js/dashboard.js stop --repo <repo>
```

`start` is the single entrypoint. It is idempotent and performs this
lifecycle:

```text
PREFLIGHT -> SCAN -> METADATA RECONCILE -> SIGNATURE -> BUILD (if changed)
-> INSTALL (if missing) -> SERVE -> OPEN        (default)
-> INSTALL (if missing) -> EXPORT               (--export)
```

- **Preflight:** repository, manifest 3.1 (or 3.0), and a readable `docs/` tree.
  When the manifest is a legacy pre-3.0 version (or any other unsupported
  version), apply the [Legacy manifest gate](#legacy-manifest-gate)
  before continuing. The
  session engine is locked (see
  [`workflows/tools.md`](tools.md)); run every `dashboard.{py,js}` call with
  the same engine (scripts and README:
  [`../runtime/dashboard/README.md`](../runtime/dashboard/README.md)). Node.js
  22+ is required only for install/serve steps.
- **Scan:** a read-only diagnostic pass over the manifest and tree (see
  [Scan: you should revise again](#scan-you-should-revise-again) below). `start`
  prints the findings and the recommendation up front; it does not hide them.
- **Metadata reconcile:** ensures each written document's public `id` and
  `title` frontmatter match the manifest and that `docforge_provenance.doc_id`
  / `path` agree; bodies are preserved byte-for-byte. Idempotent and always
  run (it is the dashboard's required input).
- **Signature:** two working-tree signatures decide what to rebuild:
  - `render_sig` — `docs/**/*.md[x]` paths and bytes (including images),
    included root-document bytes, and a manifest projection (`id`, `title`,
    `path`, `status`, `write_order`, `nav_order`). Git `HEAD`, the flow
    index, and the repository's package files are **not** part of it: they do
    not affect the rendered site, and unrelated changes must not trigger a
    rebuild.
  - `shell_sig` — dashboard template file bytes, the per-project app name and
    repository URL (the `lib/shared.ts` inputs), and the template version.
  Both are computed from the working tree, never from committed Git blobs, so
  freshly generated or dirty documentation invalidates immediately.
- **Build (when changed or `--force`):** route plan → scaffold the app shell
  (when the shell signature changed) → convert `docs/` Markdown to MDX into
  `content/.staging/` → write navigation `meta.json` → copy image assets →
  validate the staged output (links, anchors, coverage, assets) → atomically
  swap it into place. A failed conversion or validation removes the staging
  directory and leaves the previous dashboard untouched. `--force` ignores
  both signatures and always regenerates generated output (`content/docs`,
  `public/docs-assets`, navigation, app shell, `.next`) but keeps
  `node_modules`.
- **Install (when missing):** `npm install` runs only when the dashboard has
  no `node_modules` / lockfile yet. Later runs reuse the installed
  dependencies (`--skip-install` disables this step).
- **Serve:** binds `127.0.0.1` to a free port (or `--port N`) and starts
  `npm --prefix <dashboard> run dev -- -H 127.0.0.1 -p <port>` as a
  **detached background server**, records `pid` / `port` / `url` in
  `.docforge/dashboard/.docforge-dashboard.json`, and polls `/docs` until it
  responds (timeout 180 s; on timeout prints the log tail and fails). A
  healthy recorded server is reused.
- **Open:** opens `http://127.0.0.1:<port>/docs` in the default browser
  (`open` / `xdg-open`; never fails the run). `--no-open` skips this.
- `start` exits after the server is healthy; the server keeps running in the
  background until `dashboard.{py,js} stop`.
- **Export (`--export`):** instead of SERVE -> OPEN, the runtime runs
  `npm --prefix <dashboard> run build`. The generated app is a static-export
  Next.js site (`output: 'export'`; search uses the statically pre-rendered
  `staticGET` index), so `next build` emits **plain `.html` files** under
  `<dashboard>/out/` — hostable at a domain root on GitHub Pages, S3, or any
  static file server. No server is started and no browser is opened. The
  export is skipped when the stored `export_sig` (render + shell signatures)
  matches and `out/` already contains HTML; the printed `<dashboard>/out`
  path is the deployable artifact. `--export` cannot be combined with
  `--port`.

`--plan-only` performs the preflight, metadata reconcile **dry-run**, both
signatures, and the route plan only: no writes, no install, no server. It
exits `1` when the route plan has problems or reconcile would report errors.
The `render_sig:` / `shell_sig:` lines it prints are the parity-checkable
signatures.

`scan` is the read-only "should I revise again?" check: it reports every
finding without building or serving anything, exits `1` when anything is
found, and `--json` prints the machine-readable report.

`status` reports dashboard existence, whether the current render signature
matches the stored one, the server state, and the included-document count —
the read-only way to check whether the dashboard is up to date.

`stop` stops the recorded dev server (whole process group, forced after a
short grace period) and clears the PID/port state.

## When the build fails: revise before the dashboard

A `start` that cannot build is a **docs problem, not a view problem**: route
plan problems, conversion failures, and validation errors (links, anchors,
coverage, assets) exit `1` before install/serve/open, the previous dashboard
is left untouched, and the dev server is never started.

When `start` fails, the agent must:

1. Present every error exactly as printed (route plan problems, conversion
   errors, validation errors). Never summarize away a failing check.
2. **Never open the dashboard and never present the previous build as
   current** — the served site must reflect the documentation, and it does
   not yet.
3. Ask the user to **revise the documentation first** — recommend
   [`workflows/revision.md`](revision.md) (`/docforge-revise`, scoped to the
   area owning the failing documents, or `all`) — and ask whether to run it
   now.
4. Only after the revision passes the whole-tree gate
   ([`validation.md`](validation.md)) and the next `dashboard.{py,js} start`
   succeeds,
   serve and open the dashboard.

`--auto-accept` does not waive this: a failed build is never opened, and the
revise request is still asked (like other mandatory safety gates in
[`flags.md`](../flags.md)).

## Scan: you should revise again

`scan` (and the `start` lifecycle) runs a read-only diagnostic pass over the
manifest and tree before anything is built or served. It reports:

- **metadata** — documents under `docs/` whose frontmatter is missing,
  unparseable, or not schema 2.0 (reconcile would skip or error);
- **incomplete** — manifest documents that are not `generated` /
  `needs_review` / `complete` (planned, `in_progress`, ...), which the
  dashboard cannot render;
- **missing_file** — written documents whose file no longer exists;
- **drift** — provenance sources whose current bytes no longer match the
  recorded `git_blob` (the document is stale);
- **broken_link** — internal Markdown links that resolve neither to a ledger
  page nor to an asset;
- **untracked** — `.md` / `.mdx` files under `docs/` with no manifest entry.

`scan` exits `1` when anything is found, so it is the read-only answer to
"should I revise again?" before opening the dashboard.

When `start` (or `scan`) reports problems, the agent must:

1. Present the full list — kind, document, and detail — never a summary that
   hides a finding.
2. Tell the user **you should revise again** and recommend
   [`workflows/revision.md`](revision.md) (`/docforge-revise`, scoped to the
   failing documents or `all`); ask whether to run the revision now.
3. Under `--auto-accept`, still print the findings and the recommendation
   before proceeding — the suggestion is never silent.
4. Only when the scan is clean is the documentation ready to render; then
   proceed to serve/open as usual.

## What the dashboard is not

- Never write outside `<repo>/.docforge/dashboard/` except the metadata
  reconciliation of `docs/` frontmatter (the dashboard's required input) and
  the `.docforge/.gitignore` rule.
- Never touch the repository's `package.json`, lockfiles, or workspace
  configuration.
- Never delete `node_modules` or the app shell for an ordinary content
  refresh; only generated content is replaced atomically (staged, validated,
  then swapped).
- Re-running with an unchanged signature performs no content writes.

## Conversion rules (deterministic, code-fence aware)

- The public frontmatter (`id`, `docforge_provenance`) is re-emitted from the
  manifest; the body is otherwise untouched except for the rules below.
- The frontmatter `title` is the document's **first H1 heading** (markers
  like `[!toc]` / `[#custom-id]` and link/formatting syntax stripped) so
  titles are fully meaningful ("Documentation", not "Docs Index"); it falls
  back to the manifest title when a document has no H1. `meta.json` folder
  titles inherit the same value.
- Inside fenced code blocks and inline code, text is preserved verbatim.
- Outside code, `<` `>` `{` `}` are escaped to HTML entities so typed
  `<UPPER_SNAKE_CASE>` tokens and literal braces can never be parsed as JSX
  or expressions.
- HTML comments outside code are removed: management markers such as
  `<!-- docforge-children:start -->` never reach the rendered site, while the
  content between the markers (for example the child table) is kept, and
  comment text inside fenced or inline code is preserved verbatim.
- GFM stays enabled: the app shell extends the Fumadocs default preset with
  `applyMdxPreset(...)` instead of replacing it, so Markdown tables render.
- `import` / `export` statements outside code fences are rejected by the
  validation gate (the production build must pass).
- Internal Markdown links are rewritten through the route ledger:
  `[x](../README.md#anchor)` → `[x](/docs#anchor)`; directory links
  (`[reference/](reference/README.md)`) resolve to the folder URL.
- Image/asset links (png, jpg, jpeg, gif, svg, webp, avif, ico, bmp; cap
  10 MB) are copied to `public/docs-assets/` and rewritten to
  `/docs-assets/<path>`.
- Anchors are derived from headings (`[#custom-id]` suffixes honored) and
  validated before the staged content is swapped in.
- Unresolved internal Markdown links — targets that normalize inside `docs/`
  or to a repository-root `.md` / `.mdx` file with no ledger entry — fail the
  build; other unresolved targets (external trees such as `docs-portfolio/`)
  are warnings.

## Route plan

Included documents: manifest documents with a written status and an existing
file ending in `.md` / `.mdx` that live under `docs/` **or at the repository
root** (a path with no `/`). Root-level documents (for example `README.md`,
`CHANGELOG.md`, `CONTRIBUTING.md`, `AGENTS.md`, `SECURITY.md`) become pages
under `/docs/root/<slug>` so `docs/` pages can link to them and resolve. Root
files are only included when they carry docforge provenance (schema 2.0) — in
file frontmatter for section-provenance documents, or in the manifest for
`provenance_mode: manifest` documents such as `AGENTS.md`. `CLAUDE.local.md`
is **always excluded**: it is gitignored, machine-local preferences, and must
never become a shared page even when it carries provenance.
Machine JSON, planned/skipped docs, subdirectory-rooted docs outside `docs/`,
and untracked Markdown are excluded.

| Source | Content output | URL |
|---|---|---|
| `docs/README.md` | `content/docs/index.mdx` | `/docs` |
| `docs/<dir>/README.md` | `content/docs/<dir>/index.mdx` | `/docs/<dir>` |
| `docs/<dir>/page.md` | `content/docs/<dir>/page.mdx` | `/docs/<dir>/page` |
| `README.md` (root) | `content/docs/root/readme.mdx` | `/docs/root/readme` |
| `CHANGELOG.md` (root) | `content/docs/root/changelog.mdx` | `/docs/root/changelog` |

The plan fails (exit 1) when two documents map to the same URL — including
the `docs/<dir>.md` vs `docs/<dir>/README.md` collision — or when
`docs/README.md` is not a written document. `start` shows the ledger and
stops before any write when the plan has problems.

## Navigation

One `meta.json` per folder:

```json
{
  "title": "Architecture",
  "pages": ["index", "concepts", "constraints", "data-flow"]
}
```

- `index` first when the folder has an index page;
- then folders and pages **interleaved by the manifest `nav_order`** (a
  curated, reader-first navigation order independent of the generation
  `write_order`), falling back to `write_order` when `nav_order` is absent —
  so the sidebar reads the way a reader moves through the material (product
  before architecture before reference), never alphabetically and never by
  generation order. A folder is ordered by its index document's `nav_order`
  (or `write_order`), or by the smallest order among its pages when it has no
  index; the name breaks ties deterministically;
- folder titles come from the folder's index document title, then the
  `docs_index` manifest title for the root folder, then a prettified folder
  name; the `root` folder (repository-root files such as `README.md` and
  `CHANGELOG.md`) always sorts last and is titled **Project**;
- exact coverage: every generated page appears in exactly one `meta.json`
  (validated, no `...` wildcard reliance).

## Shell and branding

The Fumadocs application shell is copied from the cartridge template
(`runtime/dashboard/template/`) only when the shell signature changes:

- Next.js 16 + Fumadocs UI / MDX (pinned versions), Tailwind 4, local search;
- `lib/shared.ts` is generated per project: `appName` from
  `manifest.project.name`, `gitUrl` from `git remote get-url origin` (when a
  remote exists), docs route `/docs`;
- navbar title and GitHub link come from those values; each page's metadata
  title is `<Page title> | <App name>`;
- Mermaid code blocks render via `remarkMdxMermaid` and a client renderer
  (`mermaid`, `next-themes`);
- the Fumadocs prev/next footer is kept; a Docforge attribution line
  (`Documentation generated by Docforge`, linking to
  `https://github.com/jonaskahn/docforge`) is rendered beneath each article;
- no extra `DocsTitle` is rendered: Docforge documents already contain their
  H1; the frontmatter title (H1-derived, see above) drives navigation and
  browser metadata only.

## Flags

Same flags as `/docforge` (see [`flags.md`](../flags.md)):

- `--plan-only`: preflight, metadata dry-run, signatures, and route plan
  only; no conversion, no install, no server. On a legacy manifest, the
  metadata dry-run is the `migrate_metadata.{py,js} --dry-run` preview (see
  the
  [Legacy manifest gate](#legacy-manifest-gate)).
- `--auto-accept`: skips the revise-vs-render prompt (renders current
  documentation) and routine pauses; never authorizes installing Node.js,
  changing package files, or deleting the dashboard directory.

## Not this workflow

- Fresh-start documentation plan →
  [`workflows/intake.md`](intake.md)
  + [`workflows/planning.md`](planning.md).
- Structural revise of the documentation →
  [`workflows/revision.md`](revision.md).
- Staleness / migration / whole-tree audit →
  [`workflows/validation.md`](validation.md).
