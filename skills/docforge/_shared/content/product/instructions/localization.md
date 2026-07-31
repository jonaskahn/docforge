# Localization writing craft

For every locale or fallback behavior, state the resource-inventory source and
how coverage was verified. Add known limits for unsupported content, partial
coverage, formatting, or fallback behavior; file presence alone does not prove support.

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); a
supported-locale table is the whole document.

One row per supported locale: coverage (fully translated, partial,
machine-translated — name which), and the fallback behavior when a string
or locale isn't available. State the resource format (the file type and
where translated strings actually live) so a contributor knows where to
add a locale, not just that localization exists. Never claim a locale is
"supported" if it's only partially translated; state the actual coverage.
