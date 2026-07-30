# Ui-components writing craft

One row per component: responsibility, how it composes with others
(slots, children, props contract), and the token/theme it consumes rather
than hardcodes. Never substitute a screenshot gallery for the composition
contract; a reader integrating a component needs the contract, not a
picture of it.

## Illustration

- **Form:** a table per component for responsibility and composition — this
  is Reference depth, not a screenshot catalog.
- **Renders:** nothing beyond the table; no relationship diagram unless
  composition cannot be expressed in a row.
- **Trigger:** never a diagram — reference depth stays tabular per
  [`illustration.md`](../../../references/illustration.md).

## Connections

| This document owns | Links to | Because |
|---|---|---|
| Component responsibilities, composition, tokens/themes, browser matrix, degradation | `application-lifecycle` and `rendering`/`state-management` | lifecycle and render/state mechanics are owned there; this document owns only the component contract |
| A navigation-driving component | `ui-navigation-state` | navigation ownership is owned there, linked not restated |
