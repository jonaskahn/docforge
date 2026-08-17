# Flows

| Flow | Trigger | Entry source path | Durable sequence | Result | Failure behavior |
|---|---|---|---|---|---|
| {{name}} | {{event or request}} | `{{path}}` | {{three to six component steps}} | {{terminal effect}} | {{evidenced containment or surfaced error}} |

Include only flows present in declared flow evidence. Preserve asynchronous and
transaction boundaries when they affect safe changes.
