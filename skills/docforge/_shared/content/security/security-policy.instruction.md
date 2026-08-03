# Security-policy writing craft

Add a distinct Safe harbor and authorized testing section only when an accountable
policy decision establishes it, including good-faith limits and exclusions. Cite
policy, release, configuration, or maintainer evidence for scope, contact, and
response commitments; otherwise retain typed external unknowns.

**Preferred illustration:** Follow
[`../../references/illustration.md`](../../references/illustration.md); disclosure
policy is procedural prose, not a diagram, unless an evidenced lifecycle needs
three or more states.

Write disclosure instructions as a calm, unambiguous procedure — the human-readable
companion to a `security.txt` (RFC 9116): the same facts a machine-readable Contact and
Policy field point to, in prose a reporter can act on without guessing. Where the project
publishes `security.txt`, require at least Contact and Expires; Policy and Encryption are
optional pointers to this same page.

Put supported scope before reporting steps: state which versions or components are in
scope and, just as plainly, what testing is not authorized (no destructive testing, no
data exfiltration, no social engineering). Use
typed tokens only for external contact, response-time, and disclosure-window values; never
invent a number, an address, or a timeline that has not been confirmed. Commit only to an
acknowledgement window the project can actually meet;
ninety days is the common coordinated-disclosure default when no
confirmed window exists yet. State any safe-harbor commitment explicitly and
unconditionally where it applies, in the spirit of the DOJ's 2022 good-faith-research
guidance.
Distinguish what reporters should include (reproduction steps, impact, affected version)
from what they must not do, as two short, separate lists, not one merged paragraph. Keep
technical threat-model detail in the linked security documents; this page is a procedure,
not an analysis.
