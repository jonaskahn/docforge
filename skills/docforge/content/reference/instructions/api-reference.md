# Api-reference writing craft

**Preferred illustration:** Follow
[`../../../references/illustration.md`](../../../references/illustration.md); this is a
reference document — tables for endpoint and field lookups, prose only to
explain a contract nuance a table cannot carry.

Derive the surface from the repository's spec, schema, or exported interface
— never hand-transcribe route handlers into a parallel list; the two will
drift, and the hand-written one is wrong by definition the moment they do.
Open with the compatibility source named plainly: the file or generator a
reader can diff against (`openapi.yaml`, generated client types, a GraphQL
schema) so "authoritative" has a concrete referent, not just this page.

Group operations by resource or domain, not by HTTP verb or source file — a
reader looking up "orders" should find every order operation in one place.
Within a group, give every operation the same field order: method and path,
purpose in one clause, request shape, response shape, one realistic example.
Reuse the response envelope owned by [error-catalog.md](error-catalog.md);
restate its field table once, there, and link to it per endpoint rather than
repeating it. State auth requirement and rate-limit class as table columns,
not a repeated paragraph — a reader scanning ten operations should not
re-read the same sentence ten times.

Mark deprecated operations inline with the version that deprecated them and
the replacement, following the policy in api-versioning.md; a removed
operation that lingers silently in the reference is a worse defect than an
absent one.
