# Flashing-recovery writing craft

**Preferred illustration:** Follow
[`../references/illustration.md`](../references/illustration.md); this is a
safety-gated how-to — ordered steps, explicit warnings, no diagram.

State prerequisites and required hardware/connection state before the
first command — a reader who starts flashing without the right connection
state risks bricking the device. Give one verified path: connect, flash,
verify — with the exact success signal after flashing, not just "wait for
it to finish." Give the recovery path (what to do if flashing fails
mid-way) the same rigor as the happy path; this document is read under
stress, when a device is already in a bad state.

Never include an unverified destructive command. Where a step is
irreversible or risks hardware damage, state that plainly immediately
before the command, not buried in a general safety note at the top.
