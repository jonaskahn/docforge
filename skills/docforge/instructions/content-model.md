# Content-model writing craft

**Preferred illustration:** Follow
[`../references/illustration.md`](../references/illustration.md); a table
per content type for fields, prose for lifecycle and publishing boundary.

One section per content type: its fields (name, type, required/optional),
its lifecycle states (draft, review, published, archived — whatever the
system actually implements), and the validation applied at each
transition. State the publishing boundary plainly: what makes content
visible to an end reader, and what stays staged — a content model that
doesn't distinguish "saved" from "published" leaves a reader unable to
predict visibility.

State ownership per content type — who can create, edit, or publish it —
as a fact, not editorial guidance. Keep editorial strategy (tone, voice,
content calendar) out entirely; that's unsupported by repository evidence
and belongs, if anywhere, outside this document set.
