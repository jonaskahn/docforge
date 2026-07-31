# Tech-stack writing craft

**Preferred illustration:** Use one evidence-backed table grouped by layer; no
architecture diagram is needed.

Make this a stable lookup of what the repository is built with: language and
runtime versions, frameworks, build and package tools, datastores or messaging,
test and CI tooling, and key runtime libraries with their role and manifest
source. Prefer declared versions; mark a version unavailable rather than
deriving it from a lockfile or an import. Group rows by the layer a maintainer
would change together, not alphabetically.

Keep operational dependency failure behavior in `architecture/dependencies.md`.
Do not dump lockfiles, present transitive packages as primary choices, invent
versions, or turn the table into a marketing comparison.
