# Dashboard

Owns: `/docforge-dashboard`, its flags (`--plan-only`, `--auto-accept`), the
generated Fumadocs application under `<repo>/.docforge/dashboard/`, metadata
reconciliation for public frontmatter, MDX conversion, route planning,
navigation generation, validation, and the localhost dev server.

Tool paths below are relative to this skill root
(`skills/docforge-dashboard/`, launchers under `runtime/cli/`). The runtime
consumes the shared cartridge's codec/util but lives here: nothing else uses
it, so it does not belong in `_shared`.

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

## Lifecycle

```text
PREFLIGHT -> FINGERPRINT -> METADATA RECONCILE -> OPTIONAL REVISE
-> ROUTE PLAN -> MDX CONVERT -> NAVIGATION -> VALIDATE -> SERVE -> OPEN
```

### 1. Preflight

- Repository is a git working tree; `.docforge/manifest.json` exists and is
  version 3.1.
- The session engine is locked (see
  [`../docforge/_shared/workflows/tools.md`](../docforge/_shared/workflows/tools.md));
  run every `dashboard` call with the same engine.
- For any install or serve step, Node.js 22+ must be available (`node
  --version`). The runtime checks this itself in `build`/`serve`.
- No `package.json` / `package-lock.json` at the repository root may be
  modified by this workflow; the runtime guards this.

### 2. Fingerprint

```sh
python3 runtime/cli/python/dashboard.py fingerprint --repo <repo> [--json]
node runtime/cli/js/dashboard.js fingerprint --repo <repo> [--json]
```

Inputs: git `HEAD`, `.docforge/manifest.json`, `.docforge/flow-index.json`
when present, every file under `docs/`, every dashboard template file,
root `package.json` / `package-lock.json` hashes, and a settings record
(base URL, template version, generator version, include pattern). Python and
JS peers produce identical fingerprints.

Compare against `fingerprint` in
`.docforge/dashboard/.docforge-dashboard.json`:

- **Match** → skip reconcile, convert, install, and cleanup. Start/reuse the
  dev server and open the dashboard. This is the fast path; it performs no
  content writes.
- **Mismatch** (or no state) → continue to metadata reconcile.

### 3. Metadata reconcile

```sh
python3 runtime/cli/python/dashboard.py metadata --repo <repo> [--dry-run] [--json]
node runtime/cli/js/dashboard.js metadata --repo <repo> [--dry-run] [--json]
```

For every non-skipped manifest document with an existing `docs/**/*.md` file:

- `id` must equal the manifest `documents[].id`;
- `title` must equal the manifest title (fallback: prettified id);
- `docforge_provenance.doc_id` must equal the manifest id;
- `docforge_provenance.path` must equal the manifest path.

Anything missing or mismatched is reported (`--dry-run` / `--plan-only`) or
rewritten, preserving the Markdown body byte-for-byte. `--dry-run` performs
no writes. Errors (unparseable frontmatter, provenance not schema 2.0) are
reported and, if any, the reconcile is not considered clean.

`build` runs this step automatically unless `--no-metadata` is passed.

### 4. Optional revise

If the fingerprint mismatch was caused by documentation content changes,
present the choice:

```text
Documentation changed since the last dashboard refresh.

Metadata reconciliation: <N> document(s)
Stale/updated content: <M> document(s)
New documents: <K>

Choose:
- Revise and render   (run /docforge-revise all, then render)
- Render current documentation
- Cancel
```

`/docforge-revise all` is a semantic, user-confirmed operation that can
re-ground and rewrite the source documentation; never run it silently.
`--auto-accept` chooses "Render current documentation" (snapshot) without the
prompt. An unchanged fingerprint skips this question entirely.

### 5. Route plan

```sh
python3 runtime/cli/python/dashboard.py plan --repo <repo> [--json]
node runtime/cli/js/dashboard.js plan --repo <repo> [--json]
```

Included documents: manifest documents with a written status and an existing
file under `docs/` ending in `.md` / `.mdx`. Everything else (root `README.md`,
`AGENTS.md`, machine JSON, planned/skipped docs, untracked Markdown) is
excluded.

| Source | Content output | URL |
|---|---|---|
| `docs/README.md` | `content/docs/index.mdx` | `/docs` |
| `docs/<dir>/README.md` | `content/docs/<dir>/index.mdx` | `/docs/<dir>` |
| `docs/<dir>/page.md` | `content/docs/<dir>/page.mdx` | `/docs/<dir>/page` |

The plan fails (exit 1) when two documents map to the same URL — including
the `docs/<dir>.md` vs `docs/<dir>/README.md` collision — or when
`docs/README.md` is not a written document. Show the ledger before building.

### 6. MDX convert

```sh
python3 runtime/cli/python/dashboard.py build --repo <repo> [--force] [--skip-install]
node runtime/cli/js/dashboard.js build --repo <repo> [--force] [--skip-install]
```

`build` runs metadata reconcile (unless `--no-metadata`), scaffold, convert,
navigation, assets, state, and (unless `--skip-install`) `npm install` /
`npm ci` inside the dashboard directory. With an unchanged fingerprint it
prints `fingerprint unchanged: no conversion needed` and performs no writes
(`--force` overrides).

Conversion rules (deterministic, code-fence aware):

- The public frontmatter (`id`, `title`, `docforge_provenance`) is re-emitted
  from the manifest; the body is otherwise untouched except for the rules
  below.
- Inside fenced code blocks and inline code, text is preserved verbatim.
- Outside code, `<` `>` `{` `}` are escaped to HTML entities so typed
  `<UPPER_SNAKE_CASE>` tokens and literal braces can never be parsed as JSX
  or expressions.
- `import` / `export` statements outside code fences are rejected by the
  validation gate (the production build must pass).
- Internal Markdown links are rewritten through the route ledger:
  `[x](../README.md#anchor)` → `[x](/docs#anchor)`; directory links
  (`[reference/](reference/README.md)`) resolve to the folder URL.
- Image/asset links (png, jpg, jpeg, gif, svg, webp, avif, ico, bmp; cap
  10 MB) are copied to `public/docs-assets/` and rewritten to
  `/docs-assets/<path>`.
- Anchors are derived from headings (`[#custom-id]` suffixes honored) and
  validated later.

Staging: converted content and `meta.json` files are written under
`content/.staging/`, then swapped into `content/docs/` atomically. A failed
conversion leaves the last good dashboard untouched and removes the staging
directory.

### 7. Navigation

One `meta.json` per folder:

```json
{
  "title": "Architecture",
  "pages": ["index", "concepts", "constraints", "data-flow"]
}
```

- `index` first when the folder has an index page;
- child folders, then pages, deterministically ordered (write order, then
  source path);
- folder titles come from the folder's index document title, then the
  `docs_index` manifest title for the root folder, then a prettified folder
  name;
- exact coverage: every generated page appears in exactly one `meta.json`
  (validated, no `...` wildcard reliance).

### 8. Validate

```sh
python3 runtime/cli/python/dashboard.py validate --repo <repo> [--json]
node runtime/cli/js/dashboard.js validate --repo <repo> [--json]
```

Exit 0 only when all of the following hold:

1. No duplicate URLs (case-folded).
2. Every ledger output file exists, including `content/docs/index.mdx`.
3. Every `meta.json` lists exactly its expected children.
4. Every internal `/docs/...` link resolves and, when it carries a fragment,
   the heading anchor exists in the target document.
5. Every `/docs-assets/...` reference points at a copied asset.
6. Unresolved targets are reported as warnings (exit stays 0 only if there
   are no errors).

The skill runs this gate after every build and, for a production check, may
additionally run `npm --prefix .docforge/dashboard run build` (a `next
build`) before serving. If the production build fails, do not serve; report
the compiler output and leave the previous dashboard in place.

### 9. Serve

```sh
python3 runtime/cli/python/dashboard.py serve --repo <repo> [--port N]
node runtime/cli/js/dashboard.js serve --repo <repo> [--port N]
```

- Reuses a healthy running server whose stored PID and dashboard path match;
- otherwise binds `127.0.0.1` to a free port and starts
  `npm --prefix <dashboard> run dev -- -H 127.0.0.1 -p <port>`;
- writes `pid` / `port` / `url` / `started_at` into
  `.docforge/dashboard/.docforge-dashboard.json`, logs to
  `.docforge/dashboard/dev.log`;
- polls `/docs` until it responds (timeout 180 s; on timeout, prints the log
  tail and fails);
- ordinary content refreshes hot-reload; the server is restarted only when
  the app shell or dependencies changed.

```sh
python3 runtime/cli/python/dashboard.py stop --repo <repo>
node runtime/cli/js/dashboard.js stop --repo <repo>
```

Stops the recorded server process and clears the PID/port state.

### 10. Open

Open `http://127.0.0.1:<port>/docs` in the default browser (host `open` /
`xdg-open`, or ask the user). Confirm the page rendered (status 200) before
declaring the run complete.

## Status

```sh
python3 runtime/cli/python/dashboard.py status --repo <repo> [--json]
node runtime/cli/js/dashboard.js status --repo <repo> [--json]
```

Reports dashboard existence, fingerprint match, server state, and included
document count — the read-only way to check whether `/docforge-dashboard` is
up to date.

## Shell and branding

The Fumadocs application shell is copied from the skill template
(`runtime/template/`) only when the template hash changes:

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
  H1; the frontmatter title drives navigation and browser metadata only.

## Flags

Same flags as `/docforge` (see
[`../../docforge/_shared/flags.md`](../../docforge/_shared/flags.md)):

- `--plan-only`: preflight, fingerprint, metadata dry-run, and route plan
  only; no conversion, no install, no server.
- `--auto-accept`: skips the revise-vs-render prompt (renders current
  documentation) and routine pauses; never authorizes installing Node.js,
  changing package files, or deleting the dashboard directory.

## Not this workflow

- Fresh-start documentation plan →
  [`../docforge/_shared/workflows/intake.md`](../docforge/_shared/workflows/intake.md)
  + [`../docforge/_shared/workflows/planning.md`](../docforge/_shared/workflows/planning.md).
- Structural revise of the documentation →
  [`../docforge/_shared/workflows/revision.md`](../docforge/_shared/workflows/revision.md).
- Staleness / migration / whole-tree audit →
  [`../docforge/_shared/workflows/validation.md`](../docforge/_shared/workflows/validation.md).
