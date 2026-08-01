# Dashboard runtime

Implementation behind the public `dashboard` launcher pair in
[`runtime/cli/`](../cli/README.md): builds and serves the local Fumadocs site
under `<repo>/.docforge/dashboard/`.

- `python/dashboard.py` / `js/dashboard.js` — Python and Node peers of the
  `scan` / `start` / `status` / `stop` CLI (see
  [`workflows/dashboard.md`](../../workflows/dashboard.md) for the lifecycle,
  flags, and isolation rules).
- `template/` — the static Fumadocs application shell (Next.js 16, Fumadocs
  UI/MDX, Tailwind 4) copied into the dashboard directory; its `README.md` is
  part of the scaffolded site, not repository documentation. `app/icon.png`
  (the Docforge logo) is served automatically by Next.js as the site
  favicon; replace that file to rebrand.

The runtime consumes the shared codec/util (`runtime.common.python.*` /
`runtime/common/js/*`) exactly like every other subsystem.
