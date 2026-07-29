# Security-policy writing craft

**Preferred illustration:** Follow
[`../references/illustration.md`](../references/illustration.md); disclosure
policy is procedural prose, not a diagram, unless an evidenced lifecycle needs
three or more states.

Write disclosure instructions as a calm, unambiguous procedure — the human-readable
companion to a `security.txt` (RFC 9116): the same facts a machine-readable Contact and
Policy field point to, in prose a reporter can act on without guessing.

Put supported scope before reporting steps: state which versions or components are in
scope and, just as plainly, what testing is not authorized (no destructive testing, no
data exfiltration, no social engineering) — scope silence reads as scope permission. Use
typed tokens only for external contact, response-time, and disclosure-window values; never
invent a number, an address, or a timeline that has not been confirmed. State any
safe-harbor commitment explicitly and unconditionally where it applies, in the spirit of
the DOJ's 2022 good-faith-research guidance — a safe harbor implied only by tone is not one
a cautious reporter will rely on. Distinguish what reporters should include (reproduction
steps, impact, affected version) from what they must not do, as two short, separate lists,
not one merged paragraph. Keep technical threat-model detail in the linked security
documents; this page is a procedure, not an analysis.
