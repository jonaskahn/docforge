# Technical-debt writing craft

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); use a table
for comparable register fields and prose for each item's judgment.

Name each debt item by the shortcut taken, not a vague quality label — "the retry loop has
no backoff," not "reliability issues." Use the same sequence for every entry: mechanism,
consequence, trigger for action, credible remediation direction.

Frame the "why" with Fowler's technical-debt quadrant: deliberate-and-prudent debt ("we
shipped before validating that backoff mattered") reads as competent judgment;
inadvertent debt ("we didn't know this would contend under load") reads as an honest
correction. Either framing beats a bare severity adjective. Order entries by the cost they
impose if left untouched, or by proximity to the next place someone will touch that code —
not alphabetically, not by discovery date.

Separate debt from hard constraints, limitations, and ordinary backlog with one litmus:
could we fix this with engineering effort? Yes → tech debt (a to-do with interest). No, it
is imposed from outside (physics, law, vendor) → constraint (nothing to pay down). It is a
deliberate user-visible boundary → limitation. Unstarted work with no shortcut in place is
backlog, not debt. Never cross-file them: a constraint in the debt register is noise a
reader cannot action, and debt dressed as a limitation hides a remediable cause. Prefer
evidence-backed specificity over severity adjectives.
