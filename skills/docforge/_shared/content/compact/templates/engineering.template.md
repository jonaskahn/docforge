# {{TITLE}}

_Last reviewed: {{YYYY-MM-DD}}_

{{Two or three sentences introducing the compact engineering section: what
this file covers, why the engineering section exists, and who should read
it. A reader with no prior project knowledge should understand how this
repository is built and tested.}}

## At a glance

{{The engineering mental model: how a contributor gets from a fresh clone to
a working, tested change. Establish the shape; the setup and testing sections
below own the detail.}}

## Scope and boundaries

{{What belongs in the engineering section, and what is owned by an adjacent
section instead. Name the neighbouring sections so a reader who landed here
by mistake can route themselves away. Do not restate a fact another section
owns.}}

## Setup

{{How to get a working checkout: prerequisites, install steps, and how to
verify the environment is ready — grounded in repository manifests and
scripts.}}

## Testing

{{How to run the test suite and how tests are organized — grounded in
repository manifests and scripts.}}

## Conventions

_Diligence and higher only, and only when a conventions source exists —
omit this section entirely otherwise._

### {{Convention name}}

**Convention:** {{stated plainly}}

**Evidence:** {{lint rule, CI check, or repeated pattern recorded in provenance}}

**If not followed:** {{consequence — failing check, rejected review, or "no enforcement"}}

{{Repeat per convention, ordered by how often a contributor collides with it.
Cover style, structure, error handling, testing, and review conventions;
drop any dimension the repository doesn't evidence.}}

## Release

_Diligence and higher only — omit this section entirely at Spine._

**Version scheme:** {{SemVer or equivalent}}. Major: {{trigger}} · Minor:
{{trigger}} · Patch: {{trigger}}

1. Prerequisites: {{what must be true before starting — branch state,
   required checks, access}}
2. Build: `{{command}}` — verify: {{success signal}}
3. Verification: `{{command}}` — required gate owned by {{responsible role}}
4. Publication: `{{command}}` — verify: {{success signal}}
5. Rollback: triggered by {{release-health signal}}; {{rollback step}} —
   verify: {{success signal}}
