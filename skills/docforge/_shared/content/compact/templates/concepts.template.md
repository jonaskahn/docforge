# {{TITLE}}

_Last reviewed: {{YYYY-MM-DD}}_

{{Two or three sentences introducing the compact concepts section: the domain
vocabulary this system is built on, and why a reader should hold these
concepts before reading the architecture section.}}

## At a glance

{{How the concepts below relate to one another. Establish the shape; the
sections below own the detail.}}

## Scope and boundaries

{{What earns a concept section, and what belongs in the glossary or an
architecture section instead. Name the neighbouring sections so a reader who
landed here by mistake can route themselves away. Link any document in this
folder that this file does not merge.}}

## Concept register

| Concept | Defined in | Depended on by |
|---|---|---|
| [{{concept}}](#{{anchor}}) | {{path}} | {{documents}} |
| {{concept}} | {{path}} | {{documents}} |

{{One or two sentences on how to read the register and what a register-only
row means: the concept is named and located, and is not explained here.}}

## {{Concept name}}

_Repeat this section once per folded concept, in `compact_order`. Every field
of the `concept` contract appears below; each repeated block collapses to one
line per instance, and nothing nests past `##`._

**Models:** {{what this represents in the domain, in the repository's own vocabulary, and why the codebase needs the distinction}}

**Belongs to:** {{the high-level block this concept is the deep-dive of — link it}}

**Lifecycle:** {{the states it moves through, in order, and what moves it between them. "Created once, never transitions" when it has no lifecycle.}}

**Invariants:** {{one line per rule that must always hold, with what enforces it. State rules, not current behavior.}}

**Relates to:** {{what it depends on, what depends on it, and where a neighbouring concept takes over — link each. Never restate a neighbour's invariants.}}

**Failure boundary:** {{what it guarantees will not happen, and what it explicitly does not protect against}}

**Lives in:** {{the stable module or package paths that orient implementation work}}
