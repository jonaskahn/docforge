# Model-native depth ladders

`target_depth` describes reader use; `model_depth` describes the minimum rigor
borrowed from a model. They are independent, catalog-owned requirements.

| Model | Rungs | Evidence and stop rule |
|---|---|---|
| C4 | context, container, component, component-evidence | Components state responsibility, technology, directional relationships, and public contracts. At component-evidence, material claims have heading-level provenance and distinguish supported from unknown boundaries. Never write C4 Level-4 prose or class diagrams. |
| arc42 | context, building-block-l1, building-block-l2, runtime-scenarios | Blackboxes state responsibility and interfaces; selected whiteboxes state why decomposition matters. Runtime scenarios map every activity to a named block and include an error path. Stop when another zoom changes no architectural judgment. |
| STRIDE | boundary-element, full-element, interaction-risk | Full-element covers every bounded DFD element. Interaction-risk is an evidence-gated reference register with a declared score rubric, disposition, controls, and residual uncertainty. |
| ADR | nygard, madr-min, madr-full | Do not invent history. MADR-min requires evidenced alternatives; otherwise label an honest Nygard reconstruction. MADR-full adds drivers, option tradeoffs, participants when known, and a concrete confirmation. |
| Mermaid | single-form, complementary, annotated | Choose the form matching the claim. Annotated diagrams label meaningful edges with active verbs and evidenced protocols. Complementary forms must answer different questions. |

Missing evidence lowers confidence or invokes the stated fallback; it never
licenses an invented relationship, alternative, score, owner, or control.
