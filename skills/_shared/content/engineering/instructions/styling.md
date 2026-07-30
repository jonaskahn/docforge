# Styling writing craft

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); a table
for the token system, prose for the theming mechanism.

State the token system (spacing, color, typography scale) as data — name
and value — not prose description. State how theming actually works
(CSS variables, a theme provider, build-time generation) and the
degradation behavior when a token is missing. Keep this distinct from
[ui-components.md](ui-components.md): that document owns composition, this
one owns the token/theme system components consume.
