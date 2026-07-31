# Browser-support writing craft

Cite CI or manual-browser evidence and date for every support row. Link
component degradation behavior to `ui-components`; a browser absent from the
matrix is not implicitly supported or unsupported.

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); a
browser × minimum-version matrix table is the whole document.

State the tested matrix, not an aspiration; a browser listed as supported
should mean it's in the test matrix or verified manually — say which. State
degradation behavior per unsupported browser (polyfilled, reduced
functionality, blocked outright) rather than leaving it implicit.
