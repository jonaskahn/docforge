# Quality bar

Run this before presenting anything. The failure mode this guards against is a tree that looks complete — right folders, right filenames, confident prose — while being unusable, unverified, or subtly invented.

## The four tests

Each targets one audience. A documentation set that fails any of them fails for that audience entirely, regardless of how good the rest is.

**1. The onboarding test.** A competent engineer who has never seen this repo starts at the root README and reaches a running local instance without asking a human a question. If any step requires tribal knowledge — an unlisted credential, an undocumented service, a version constraint discovered by failing — `engineering/setup.md` is incomplete.

**2. The location test.** Pick five things a maintainer does regularly: fix a bug in module X, add a configuration value, respond to an alert, add a dependency, change a public interface. For each, can a reader find the relevant document in under a minute starting from `docs/README.md`? If not, the index is decorative or the taxonomy is wrong.

**3. The reviewer test.** Someone assessing this repo for risk asks: what does it depend on, what are its known weaknesses, how is security handled, why is it built this way. Every one of those has an answer at a findable path. "It's in the code" is not an answer; neither is a document that exists but is empty.

**4. The stranger test.** A non-engineer reads `product/overview.md` and can explain what this repo does and why it exists. If they cannot, the document is written for people who already know.

## Verification checklist

### Accuracy — the non-negotiable category

- [ ] Every command shown has been run, or is explicitly marked unverified
- [ ] Version numbers match the manifest files, not memory
- [ ] Environment variables were found by searching for their accessor in code, not copied from an old example file
- [ ] File and module paths referenced in the code map exist
- [ ] External services listed are actually called by this code
- [ ] Nothing describes intended architecture as though it were shipped
- [ ] Every derivable fact is written in full — nothing retrievable from the graph/source/config/history was left for a human to author
- [ ] The only fill-markers remaining are typed `<UPPER_SNAKE>` tokens standing in for genuinely external values (contact, on-call, prod URL, org SLA, owner, roadmap date); no `{{…}}` scaffold markers and no punted `TODO` sections survive

### Grounding

- [ ] A knowledge graph was built or refreshed before writing, and the code map came from it
- [ ] Modules named in the code map exist as nodes in the graph
- [ ] Stated invariants are supported by absent edges, not by assumption
- [ ] Where the graph was unavailable, the response says so; content still came from direct inspection, and only genuinely external values fell back to typed tokens

### Structure

- [ ] Every folder has a `README.md`
- [ ] Every document is reachable from `docs/README.md` in at most two hops
- [ ] All internal links are relative and resolve
- [ ] No document sits in a folder whose audience it does not serve
- [ ] Root files are thin pointers with no content duplicated from `docs/`
- [ ] Naming follows the conventions in `docs-tree.md` — kebab-case, plural collections, no `misc/`

### Host neutrality

- [ ] No forge name appears in prose outside `docs/contributing/`
- [ ] Diagrams are Mermaid or committed images, each preceded by a prose description
- [ ] Callouts use portable blockquote syntax unless a platform commitment is documented
- [ ] Links are relative, not absolute URLs to the current host

### Completeness for the chosen tier

- [ ] Every file the tier requires exists and is filled, not templated
- [ ] Overlay documents for the repo's actual type are present
- [ ] `reference/limitations.md` is not empty — every real system has limitations, and an empty register means nobody looked
- [ ] Decision records cover the choices a reviewer would ask about
- [ ] Dependency inventory covers direct runtime dependencies and external services

### Maintainability

- [ ] Nothing hand-written duplicates a machine-readable source of truth
- [ ] Generated documentation is marked as generated, with the regeneration command
- [ ] Documents that go stale carry a `_Last reviewed: YYYY-MM-DD_` line
- [ ] No secret, credential, internal hostname or personal name-as-contact appears anywhere

### Durability and composition

- [ ] **Durability:** would a same-behaviour refactor (rename, extract, move) falsify this document? If yes, it is written too close to the code — rewrite at flow/behaviour level
- [ ] **No code:** no pasted code or code-like snippets in prose (except value *shape* in `errors.md`/`configuration.md`, and before/after snippets in a library `product/migration/vN-to-vM.md` guide); no line-number links; no claim anchored to an internal/private symbol
- [ ] **No duplication:** every fact stated once; the same sentence does not appear in two files; definitions live only in `glossary.md`
- [ ] **Completeness:** every aligned topic `README.md` stands alone — each subfile fact is summarized and linked from it, nothing dropped
- [ ] **Notices common:** every warning, critical constraint or irreversible behaviour appears in the topic `README.md`, not only in an audience subfile
- [ ] **Readable common layer:** each `README.md` is plain-language, jargon glossed or linked; internals pushed to subfiles
- [ ] **No empty audience subfile:** a `business-analyst.md` / `engineering.md` / `product-owner.md` exists only where real depth exists
- [ ] **Flat by default:** every `flows/<flow>` and `architecture/concepts/<subsystem>` is a flat file unless it currently carries at least one real subfile; no folder holds only a `README.md`
- [ ] **No dangling deep-dive:** no flat file or topic `README.md` links to a sibling subfile that does not exist on disk right now
- [ ] **Flows sourced from the domain graph:** `docs/flows/`, `product/overview.md`, `product/capabilities.md` and BA/PO content trace to `/understand-domain` output, confirmed present via `scripts/check_preconditions.py --need domain` — never hand-typed from route files or folder names
- [ ] **Diagrammed:** every flow with more than one step or a branch/error path carries a Mermaid diagram; prose still stands alone without it

## Automated checks worth adding to CI

Documentation decays silently unless something objects. The cheap wins, in rough order of value per effort:

1. **Link checking** on every change — catches the most common decay.
2. **Scaffold-marker detection** — fail on any `{{…}}` template marker or punted `TODO` in the default branch: those mean a section was left unwritten. Typed `<UPPER_SNAKE>` tokens are exempt (they are intentional human-fill slots); optionally warn if one survives past an agreed grace period so external facts do get filled in.
3. **Folder-only-readme detection** — fail if any `flows/<flow>/` or `architecture/concepts/<subsystem>/` directory contains a `README.md` and no other `.md` sibling; that shape means a promotion happened without a subfile. `docs_scaffold.py --audit` reports this as `folder-only-readme`.
4. **Forge-name grep** outside `docs/contributing/`.
5. **Spec validation** — if an API spec is generated, verify it regenerates identically to what is committed.
6. **Config drift** — compare documented environment variables against those the code reads.
7. **Setup verification** — periodically run the documented setup steps on a clean container. Expensive, and it catches the failure that matters most.

## Anti-patterns to check for explicitly

- **Templated husk**: correct headings, no content. Delete the section or fill it; an empty heading is a false promise.
- **Rationale in the code map**: opinions in `architecture/high-level.md` make it churn. Move them to a decision record.
- **The everything document**: a 2,000-line README nobody reads past line 40.
- **Aspirational documentation**: describing the target architecture as current.
- **Silent staleness**: no review dates anywhere, so a reader cannot judge what to trust.
- **Duplicated truth**: the same fact in the root README, the docs index and the product overview, already diverging.
- **Prose bound to code**: a claim anchored to a private symbol or a line number, so a routine rename falsifies the document. Write at the behaviour level instead.
- **Notice stranded in a subfile**: a warning that only the engineering deep-dive carries, invisible to a reader who stops at the topic README.
- **Folder-only-readme**: a `flows/<flow>/` or `architecture/concepts/<subsystem>/` containing nothing but `README.md`. Either a promotion happened with no subfile content (demote to a flat file) or a subfile is simply missing (write it).
- **Dangling deep-dive link**: "documented in the engineering deep-dive" pointing at a file that isn't there. Caught by `docs_scaffold.py --audit`'s broken-links check; treat any hit under `flows/` or `architecture/concepts/` as this specific defect, not a generic typo.
- **Hand-typed flow list**: flows enumerated from route files, screen names, or memory instead of `/understand-domain`'s output.
