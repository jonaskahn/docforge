# Docforge dashboard

This directory is a **generated, disposable** Fumadocs application owned by
the `/docforge-dashboard` skill.

- It is ignored by git (`.docforge/.gitignore` rule `dashboard/`).
- It never touches the repository's own `package.json` or lockfiles; all
  dependencies are installed inside this directory with
  `npm --prefix .docforge/dashboard`.
- Content under `content/docs/` is converted from the repository's
  `docs/` Markdown plus Docforge manifest metadata. Do not edit it by hand;
  re-run `/docforge-dashboard` to regenerate.
- The app shell (`app/`, `lib/`, `components/`, `package.json`,
  `next.config.mjs`, …) is copied from the Docforge skill template and only
  changes when the template version changes.
- Delete this directory to discard the dashboard; `/docforge-dashboard`
  rebuilds it from scratch.

State lives in `.docforge-dashboard.json` in this directory.
