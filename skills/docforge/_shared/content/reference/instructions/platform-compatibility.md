# Platform-compatibility writing craft

Cite device or test-matrix evidence for every platform row. Link permission and
lifecycle behavior to their owning documents, and mark unverified target support
or degradation as unknown rather than inferring it from a build artifact.

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); a matrix
table (OS/device/architecture × minimum version) is the whole document.

State minimums as tested evidence, not aspiration — the same discipline
[compatibility.md](compatibility.md) applies to library versions, applied
here to OS/device/architecture. State degradation behavior below the
minimum (refuses to run, runs with reduced features) and the deprecation
horizon for older supported platforms.
