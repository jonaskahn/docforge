# Discovery gate

The discovery gate interprets open-vocabulary cues after deterministic
`detect_profiles` and before the user confirms repository profiles.

## Authority

1. **Deterministic detect** emits strong confirms plus weak candidates and a cue
   bag (`match_strength`, `cues`, `ambiguous_with`).
2. **Agent gate** re-ranks or proposes catalog profile ids grounded in the pack.
3. **User confirm** remains the only authority that finalizes profiles.

Neither detect nor the gate confirms intake on the user's behalf. Scripts stay
offline: they emit packs and validate/apply judgment JSON; they never call a
model API.

## When to run

Run the gate during interactive intake when `needs_gate` is true in the pack
from `detect_profiles --repo <path> --emit-gate-pack`. That is true when any
detection is `candidate`, any row has `ambiguous_with`, or any cue lists two or
more candidate profiles.

Skip the gate only when every detection is strong-confirmed and the cue bag has
no multi-candidate groups. Fail open: invalid or missing judgment leaves
deterministic ranks unchanged.

## Bounded pack

Use only the pack. Hard caps are enforced by the emitter (excerpt count and
length). Do not crawl the repository beyond packed evidence paths. Allowed
profile ids are only those in `catalog_ids` or cue `candidate_profiles`.

## Judgment contract

Return JSON matching `.metadata/discovery-gate-schema.json` `#/definitions/judgment`:

- `action`: `promote` | `keep` | `demote` | `drop` | `propose`
- `propose` may lift a catalog id that appears only in cue candidates
- Ground every decision in pack cues, dependencies, or excerpts
- One cue may map to zero, one, or many aspects when evidence supports coexistence
- Do not invent profile ids; do not confirm the intake summary

Apply with `discovery_gate.apply_judgment` (Python) or
`discovery_gate.applyJudgment` (Node). Persist the judgment as
`discovery_gate` beside `discovery` in the manifest when initializing after
user confirmation.

## Intake presentation

Show **recommended** (post-gate) pre-checked and **also possible** unchecked,
each with a short evidence or gate reason. Let the user edit freely, then wait
for explicit confirmation.
