# Voice

This file owns the per-section voice vocabulary: one voice per group, stated
as two or three concrete rules with a do/don't pair. Voice is a writing
constraint, not a heading checklist — the independent audit checks the
artifact against its group's voice the way it checks depth and mode.

## The vocabulary

| Group | Voice |
|---|---|
| root, product | plain and outcome-first; a non-specialist finishes the first paragraph |
| architecture | declarative present tense, strong active verbs, no hedging |
| flows | narrative and ordered; one idea per sentence; branch beside its step |
| engineering, operations | imperative and runnable; every step has an observable result |
| reference | terse and tabular; no narrative connective tissue |
| security | precise; hedge only where evidence is thin; never alarmist |
| portfolio | executive; value and risk before mechanism |
| contributing | welcoming imperative; assume competence, not context |
| agent-context | terse imperative; the output is read, not browsed |

## Do / don't per group

| Group | Do | Don't |
|---|---|---|
| root, product | Lead with the outcome a reader can act on; write the first paragraph for a stranger | Bury the point behind history, structure, or feature lists |
| architecture | "The gateway validates and routes." — active present tense, one job per sentence | "Handling and management of requests is performed by the gateway"; hedge ("generally", "mostly") |
| flows | "**3.** The pricing service revalidates the cart." — ordered, one idea per sentence, the branch right under the step that creates it. State the outcome in the opening, then the steps that reach it | Merge two ideas into one sentence; gather branches in a section away from their steps; make the reader reach the last section to learn what the flow guarantees |
| engineering, operations | "Run `make verify` — it prints one line per failing contract." — every step ends in an observable result | Narrate what a step does without a checkable outcome |
| reference | One row per fact; a sentence only when a table cannot carry the nuance | Connect entries with narrative glue ("Additionally", "It is worth noting") |
| security | "Evidence establishes rate limiting at the gateway; the app layer is unverified." — hedge exactly where evidence stops | Sound the alarm ("critical vulnerability") without evidence, or stay silent about thin evidence |
| portfolio | State the value or the risk before the mechanism that delivers it | Lead with architecture or inventory detail |
| contributing | "Set up by running `make dev`." — assume competence, explain the project, not the tool | Condescend ("simply", "just") or assume shared team context |
| agent-context | Facts, paths, and commands in short imperative lines | Links, narrative, or cross-references — outputs are self-contained and read as files |

## Adjacent authority

Depth and audience per reader are owned by
[`depth-and-audience.md`](depth-and-audience.md); this file owns only *how*
a document at a given depth is phrased, never *what* it contains. Writing
mechanics that touch phrasing but are not voice — provider neutrality,
presentation policy, evidence citation form — stay with
[`host-neutrality.md`](host-neutrality.md) and
[`evidence-presentation.md`](evidence-presentation.md).
