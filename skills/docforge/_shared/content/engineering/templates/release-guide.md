# Release guide

_Last reviewed: {{YYYY-MM-DD}}_

## Prerequisites

{{What must be true before starting a release — branch state, required checks green, access.}}

## Version

**Scheme:** {{SemVer or equivalent}}. Major: {{trigger}} · Minor: {{trigger}} · Patch: {{trigger}}

## Build

1. `{{command}}` — verify: {{success signal}}

## Verification

**Required gate:** {{evidenced check or approval}} — owned by {{responsible role}}.

1. `{{command}}` — verify: {{success signal}}

## Publication

1. `{{command}}` — verify: {{success signal}}

## Rollback

**Trigger:** {{release-health signal that forces a rollback, e.g. an error-rate threshold, and who escalates it}}.

1. {{step}} — verify: {{success signal}}

Released changes: record in [changelog.md](changelog.md).
