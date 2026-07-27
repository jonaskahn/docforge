# Document audit — the independent per-document completion gate

A document is not `complete` because the writer believes it is. It is `complete` because a **separate agent that did not write it** checked it, cold, against its contract and its depth target and found no derivable gap. This file defines that check.

The failure it exists to stop is concrete and has already happened: a tree that *looks* finished — right folders, provenance frontmatter, confident prose — but is **shallow**, most docs 40–55 lines, flow docs stopping at L1 with no mechanism underneath. The old Step 6 could not catch it, because Step 6 fired once, over the whole tree, run by the same writer that produced it. A writer grading its own work in bulk at the end is not a gate. This is.

## Where it runs

Inside the Step 0 Gate-2 per-document write loop, after a document reaches `generated` and before it is presented as done:

```
in_progress → write + stamp provenance → generated → AUDIT (fresh subagent, cold) →
    PASS              ⇒ present the finished doc + its verdict → user accepts ⇒ complete
    FAIL (derivable)  ⇒ needs_review → rewrite that doc → re-audit  (never presented as done)
    FAIL (external)   ⇒ convert the atomic value to a typed <UPPER_SNAKE> token,
                         or record the user's explicit waiver ⇒ PASS
```

`--auto-accept` skips the user's *pause*, never the audit. There is no flag, and no user instruction, that marks a document `complete` without a passing audit — the same way no flag skips the plan-and-show or the re-ground step. The manifest's existing `needs_review` status carries the "failed audit, rewriting" state; no new status is introduced.

## The independence rule (why a fresh agent)

The auditor is a **separate subagent, spawned per document**. It must not be the agent that wrote the document, and it must not receive the writer's reasoning, notes, or justifications — only artifacts. A writer that explains *why* a section is thin has already told the auditor what to conclude; independence is exactly the property that a same-graph misreading gets caught instead of re-confirmed.

The auditor receives, and only receives:

- **the finished document** (its path — it reads the file itself)
- **the doc type's contract** from `references/document-catalog.md`: the must-present elements, the keep-out list, and the type's **primary** Diátaxis mode
- **the depth target** for that type (the L-level line in `document-catalog.md`, per the ladder in `depth-and-audience.md`)
- **the single-document subset of the quality bar** (below)
- **the provenance sources** listed in the document's own frontmatter — so it can open two or three of them and check that what the document claims is actually what the source does

It does **not** receive the plan, the other documents, or the writer's transcript. It judges the artifact on its own terms.

## The per-document checklist

The auditor runs the single-document subset of `references/quality-bar.md`'s verification checklist — every item that can be judged from one file — **plus** the type contract, **plus** the depth target:

1. **Must-present coverage.** Every element the type's `document-catalog.md` contract requires is present, and each is *substantive*, not a heading with a sentence under it. Mark each element `present | missing | shallow`.
2. **Keep-out.** Nothing the contract assigns to a *different* document has leaked in.
3. **Depth.** The document reaches its target L-level. A subsystem a new engineer must understand sitting at L1 summary when its target is L2/L3 is a **depth shortfall** — a FAIL, not a nit. This is the specific defect that let the shallow tree ship. "Detailed" means more useful signal (mechanism, edge cases, failure modes, what feeds it / what it feeds / what breaks it), never more words.
4. **Primary mode.** The document keeps to its declared primary mode; any genuinely cross-mode material is sectioned and cross-linked, not blended. This tests the *catalog's* rule ("one primary mode + section/cross-link"), **not** "single mode only" — a hybrid type like a flow (Explanation + a how-to spine) or `high-level.md` (Explanation/Reference) is correct and must not be failed for being hybrid.
5. **Grounding spot-check.** For two or three claims, open the frontmatter-cited source and confirm the claim matches the code's actual behaviour. A claim with no citation, or one the cited file does not support, is a gap.
6. **Fill-state.** No `{{…}}` scaffold markers and no punted `TODO` prose survive. The only fill-markers allowed are typed `<UPPER_SNAKE>` tokens standing for genuinely external values.
7. **Durability.** No pasted code, no line-number links, no claim anchored to a private symbol a rename would falsify (the `errors.md` / `configuration.md` value-shape exception aside).

## Every gap is either derivable or external — and that decides the outcome

For each gap the checklist surfaces, the auditor tags it:

- **derivable** — the answer lives in the graph, the source, config, or history, and was simply not retrieved or not written deep enough (a missing failure mode, an unwritten step, an L1 doc that should be L2). A derivable gap is a **hard FAIL**. The document goes to `needs_review`, the writer re-grounds and rewrites, and it is **re-audited**. It is never presented as done, and a derivable gap is never waived. "Query the graph again" is the fix, not "flag for the team."
- **external** — the answer lives in no source the agent can read (a disclosure contact, an on-call rotation, a production URL, an org-set SLA, an owner name, a roadmap date). The surrounding sentence must already be written in full with only the atomic value left as a typed `<UPPER_SNAKE>` token; or, if it is not a token yet, the writer converts it to one. An external gap — and only an external gap — may **PASS**, either as a typed token or under an explicit user waiver recorded in the verdict.

The single most common auditor error to guard against is **misclassifying a derivable gap as external to let it pass**. If the fix is "ask the graph a narrower question," the gap is derivable and blocks. When unsure, treat it as derivable.

## The verdict

The auditor returns a structured verdict (the artifact in `assets/templates/audit-report.md`), most-severe first:

- one row per must-present element: `present | missing | shallow`, each gap tagged `derivable | external`
- the depth level **achieved** vs. **target**
- the primary-mode + sectioning check: pass / fail
- an overall **`PASS` | `FAIL`**

`FAIL` if any element is `missing` or `shallow` with a derivable gap, or the depth target is not met with a derivable shortfall, or the primary-mode rule is broken, or a fill-state / grounding / durability check fails on derivable content. `PASS` only when every remaining gap is external and represented by a typed token or an explicit waiver.

## Optional mechanical pre-audit

`scripts/check_document.{py,js}` (if present) runs *before* the agent on one doc path and flags the purely mechanical defects — `{{…}}` markers, empty headings, dead relative links, unlinked file mentions (another real document named in backticks but never actually linked to), missing must-present headings for that type — so the agent spends its judgement on depth, grounding, and mode rather than on things a regex catches. It never replaces the agent; a clean mechanical pass is necessary, not sufficient.

For `AGENTS.md` specifically (`agent-context` overlay), also run `scripts/check_agents_kernel.{py,js}` before the agent — it checks the format-specific rubric (100-line cap, tagline/test-sentence shape, negation ratio, dangling `@docs/agents/…` links) that `check_document.py`'s generic checks have no concept of.

## What this changes about Step 6

Step 6 is no longer the per-document gate — this file is. Step 6 becomes the **final whole-tree consistency pass**: the checks that are only meaningful across the full set — cross-document dead links, unlinked file mentions across the whole tree, duplication across documents, index reachability, forge-name leakage (all via `docs_scaffold.py --audit`). Per-document completeness, depth, mode, and grounding are settled here, one document at a time, before each is ever marked `complete`.
