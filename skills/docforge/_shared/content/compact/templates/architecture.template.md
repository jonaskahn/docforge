# {{TITLE}}

_Last reviewed: {{YYYY-MM-DD}}_

**In one sentence:** {{the business capability this system owns, stated before any structure}}

{{Two or three sentences introducing the compact architecture section: what
this file covers, why the architecture section exists, and who should read
it. A reader with no prior project knowledge should understand how the system
is shaped and what question this file answers.}}

## At a glance

{{The system mental model: the handful of major components and how they fit
together, in one or two sentences or a short list. Establish the shape; the
high-level section below owns the detail.}}

## Scope and boundaries

{{What belongs in the architecture section, and what is owned by an adjacent
section instead. Name the neighbouring sections so a reader who landed here
by mistake can route themselves away. Do not restate a fact another section
owns.}}

## High-level architecture

{{Structure, boundaries, and integration surfaces — grounded in repository
evidence. Do not invent architecture the source does not show.}}

## Component design

_Diligence and higher only — omit this section entirely at Spine. Every field
of the `architecture-low-level` contract appears below; each repeated block
collapses to one line per instance, and nothing nests past `##`._

```text docforge-role=structure
{{repository}}/
├── {{source directory}}/    {{one-line responsibility}}
└── {{test directory}}/      {{one-line responsibility}}
```

{{One sentence: what the grouping reveals about ownership or runtime boundaries.}}

**Whiteboxes:** {{one line per high-level block worth a component-level zoom —
the block, why it is decomposed, and the dependency direction it permits. Not
every block earns one.}}

**{{Component name}}** — **Responsibility:** {{what it does and the boundary it
owns}} · **Contract:** `{{signature or protocol}}` · **Talks to:** {{component
— active verb and protocol when evidenced}} · **Invariant:** {{what is always
enforced or deliberately absent}} · **Failure boundary:** {{what it contains
when it fails, and what a caller must handle}}

{{Repeat the component line per component material to the decomposition above —
not an exhaustive file listing.}}

**Quality and change scenarios:** {{the evidenced load or latency ceiling this
design holds, or the modification it absorbs cheaply. Delete this line when the
repository evidences neither; never estimate a figure.}}

```mermaid
sequenceDiagram
  participant A as {{component}}
  participant B as {{component}}
  A->>B: {{specific action}}
  alt {{success condition}}
    B-->>A: {{outcome}}
  else {{material error}}
    B-->>A: {{safe failure behavior}}
  end
```

{{One architecturally relevant intra-block runtime scenario: why it matters,
its successful outcome, and its error path. Every message above maps to a
named component.}}

## Constraints

_Diligence and higher only — omit this section entirely at Spine._

| Constraint | Limit | Source | Why it exists | What lifting it would take |
|---|---|---|---|---|
| {{e.g. throughput}} | {{the ceiling}} | {{platform limit, regulation, contract, physics}} | {{the design choice behind it}} | {{the change required}} |

{{Boundaries this system assumes about its environment and inputs, and
non-goals — what it deliberately does not do, and which component does it
instead. Keep temporary shortcuts and user-visible limitations out; those
belong in Technical debt below and in `reference.md`, not here.}}

## Dependencies

_Diligence and higher only — omit this section entirely at Spine._

| Package | Purpose | Criticality | If it disappeared |
|---|---|---|---|
| {{name}} | {{why it is here}} | {{high/medium/low}} | {{replacement path and effort}} |

{{External services this system integrates with directly — purpose,
criticality, and failure handling for each. Summarize development
dependencies rather than enumerating them.}}

## Technical debt

_Diligence and higher only — omit this section entirely at Spine._

| Item | Shortcut taken | Cost it imposes | Remediation |
|---|---|---|---|
| {{name}} | {{the shortcut, in mechanism terms}} | {{who pays, how, when}} | {{what fixing it takes}} |

{{Describe each shortcut's cost in behavioral terms, with evidence — do not
paste the offending code. Keep hard constraints out; those belong in
Constraints above.}}
