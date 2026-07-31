# Configuration writing craft

For every setting, cite its exact configuration source and consuming code, and
state scope and sensitivity only when evidenced. Link environment-specific
differences to `environments`; do not infer defaults from one deployment file.

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); a table
is the whole document — one row per setting.

Apply the 12-factor discipline: every setting the application actually
reads from its environment, with name, default, scope (which
environment/service reads it), and sensitivity (is this safe to log or
does it need a secret store) — as table columns, not prose repeated per
setting. State the source of truth precisely (an env var name, a config
file path and key) so a reader can find where to actually set it, not just
that it exists.

Never invent an aspirational setting the code doesn't read, and never print
a real secret value — show the variable name and note where the value
lives instead. Order by how often a reader tunes the setting, not
alphabetically; the setting everyone changes in local dev belongs above the
one nobody has touched since launch.
