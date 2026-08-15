# Styling

_Last reviewed: {{YYYY-MM-DD}}_

## Component responsibilities

| Component | Owns (styling concern) | Consumes tokens from |
|---|---|---|
| {{component}} | {{e.g. spacing, color, elevation}} | {{token group}} |

General component hierarchy and composition: [../architecture/ui-components.md](../architecture/ui-components.md).

## Tokens

| Token | Value | Type |
|---|---|---|
| {{name}} | {{value}} | {{color / dimension / typography / other}} |

## Theming

**Mechanism:** {{CSS variables / theme provider / build-time generation}}

**On missing token:** {{degradation behavior}}

## Browser support

| Browser / engine | Minimum version | Evidenced by |
|---|---|---|
| {{browser}} | {{version}} | {{browserslist config / CI matrix / polyfill}} |

## Degradation

{{Fallback behavior when a browser or feature isn't supported — feature detection, polyfill, or graceful degradation. State only what is evidenced; never assert support that isn't tested.}}
