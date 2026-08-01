# Dashboard runtime

Implementation behind the public `dashboard` launcher pair in
[`runtime/cli/`](../cli/README.md): builds and serves the local Fumadocs site
under `<repo>/.docforge/dashboard/`.

- `dashboard.py` / `dashboard.js` — Python and Node peers of the
  `start` / `status` / `stop` CLI (see
  [`workflows/dashboard.md`](../../workflows/dashboard.md) for the lifecycle,
  flags, and isolation rules).
- `template/` — the static Fumadocs application shell (Next.js 16, Fumadocs
  UI/MDX, Tailwind 4) copied into the dashboard directory; its `README.md` is
  part of the scaffolded site, not repository documentation.

The runtime consumes the shared codec/util (`runtime.common.*`) exactly like
every other subsystem.
