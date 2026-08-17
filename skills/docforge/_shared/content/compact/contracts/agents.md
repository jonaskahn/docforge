# `agents_compact`

Content contract for compact document type `agents_compact`.

The compact form contains exactly the selected topic members, in this order:
architecture, patterns, testing, conditional conventions, tech debt,
conditional flows, and conditional terms. Each section is a self-contained
answer to its own reader question and may repeat facts needed for that answer.
Budget each selected section to roughly 25 lines.

No section refers to any documentation. Source and configuration paths and
verified commands are allowed. Omit conventions when no conventions source is
evidenced. Omit flows and terms when flow evidence is unavailable.

| Type | Must present | Keep out | Primary mode | Depth |
|---|---|---|---|---|
| agents_compact | concise purpose plus seven ordered, independently useful topic sections selected by evidence; direct facts, durable source/configuration paths, constraints, and verified commands; roughly 25 lines maximum per selected section | Markdown links, URLs, imports, documentation paths or references, reader routing, attribution language, volatile symbol dumps, sections not selected by evidence | Reference | deep-dive |
