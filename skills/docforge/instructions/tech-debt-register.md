# Technical-debt writing craft

Name each debt item by the shortcut taken, not a vague quality label — "the retry loop has
no backoff," not "reliability issues." Use the same sequence for every entry: mechanism,
consequence, trigger for action, credible remediation direction.

Frame the "why" with Fowler's technical-debt quadrant: deliberate-and-prudent debt ("we
shipped before validating that backoff mattered") reads as competent judgment;
inadvertent debt ("we didn't know this would contend under load") reads as an honest
correction. Either framing beats a bare severity adjective. Order entries by the cost they
impose if left untouched, or by proximity to the next place someone will touch that code —
not alphabetically, not by discovery date.

Separate debt from hard constraints and from ordinary backlog work with one test each: if
undoing the shortcut requires redesigning intent rather than spending effort, it is a
constraint, not debt; if it is unstarted work with no shortcut currently in place, it is
backlog, not debt. Prefer evidence-backed specificity over severity adjectives.
