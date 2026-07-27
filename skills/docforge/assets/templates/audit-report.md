# Audit — {{docs/path/to/document.md}}

_Audited: {{YYYY-MM-DD}} · Auditor: independent subagent (did not write this document) · Type: {{doc-type}} · Primary mode: {{Explanation|Reference|How-to|Tutorial}}_

<!--
  The verdict an independent auditor returns for one document, per references/document-audit.md.
  It is what advances a document from `generated` to `complete` (on PASS) or to `needs_review`
  (on FAIL). Fill every row from the finished document + its document-catalog.md contract +
  its depth target; delete these comments. Order rows most-severe first.
-->

## Verdict: {{PASS | FAIL}}

{{One sentence: what blocks (if FAIL), or that the document is complete and grounded (if PASS).}}

## Must-present elements

| Element (from the contract) | Status | Gap type | Note |
|---|---|---|---|
| {{element}} | {{present \| missing \| shallow}} | {{— \| derivable \| external}} | {{what is thin/absent, or "—"}} |

- **present** — substantive, not a heading with a sentence under it.
- **shallow / missing** + **derivable** ⇒ hard FAIL: re-ground and rewrite, then re-audit. Never waived.
- **missing** + **external** ⇒ may PASS as a typed `<UPPER_SNAKE>` token or an explicit user waiver (name it below).

## Depth

- **Target:** {{L0 | L1 | L2 | L3}} (from `document-catalog.md` / `depth-and-audience.md`)
- **Achieved:** {{L0 | L1 | L2 | L3}}
- **Shortfall:** {{none | derivable — <what mechanism/edge-cases/failure-modes are missing>}}

A derivable depth shortfall (a subsystem a new engineer must understand left at summary depth) is a FAIL, not a nit.

## Primary mode & sectioning

- {{Kept to primary mode; any cross-mode material sectioned and cross-linked — PASS}}
- {{OR: modes blended — <where> — FAIL}}

_(A legitimately hybrid type — flow, `high-level.md` — is not a failure. Test the catalog's "one primary mode + section/cross-link" rule, not "single mode only".)_

## Grounding spot-check

| Claim | Cited source (frontmatter) | Matches source? |
|---|---|---|
| {{claim}} | {{src/path}} | {{yes \| no — <discrepancy> \| uncited}} |

## Fill-state & durability

- {{No `{{…}}` markers, no punted TODO; only typed `<UPPER_SNAKE>` tokens remain — or list what survives}}
- {{No pasted code / line-number links / private-symbol anchors — or list violations}}

## Waivers (external gaps only)

- {{`<TOKEN_NAME>` — the external value it stands for, and why it is unknowable from source. Or "none".}}
