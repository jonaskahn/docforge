#!/usr/bin/env python3
"""The shared entry-surface vocabulary: which names, paths, and graph layers
read as "a flow starts here". Not a public CLI.

flow_index.py and graph_source_understand_anything.py both need this and used
to carry byte-identical private copies, which drifted — the layer list in
particular was narrower on the flow_index side. One definition now, imported by
both.

ENTRY_LAYER_WORDS is deliberately broad: a layer named "Screens & Routes" is as
much an entry surface as one named "API", and a frontend repo has no layer
matching "service" or "api" at all. Matching is substring-on-lowercase, so
"routes", "Screens & Routes", and "Route Handlers" all hit "route".
"""

from __future__ import annotations

import re

# Verb prefixes that read as "this function starts something". ENTRY_WORDS is
# the permissive set (used with a path signal); CORE_ENTRY_WORDS is the strict
# subset (used when only layer membership backs the guess), so a bare `getFoo`
# in a service layer does not become a flow candidate on its own.
ENTRY_WORDS = re.compile(
    r"^(?:[Aa]ggregate|[Tt]rack|[Pp]ublish|[Dd]ispatch|[Ee]xecute|"
    r"[Rr]un|[Ss]tart|[Rr]eceive|[Pp]rocess|[Cc]onsume|[Hh]andle|"
    r"[Cc]reate|[Uu]pdate|[Dd]elete|[Ss]ave|[Gg]et|[Pp]ost|[Pp]ut|"
    r"[Pp]atch|[Ss]end)(?:[A-Z0-9_]|$)",
)
CORE_ENTRY_WORDS = re.compile(
    r"^(?:[Aa]ggregate|[Tt]rack|[Pp]ublish|[Dd]ispatch|[Ee]xecute|"
    r"[Rr]un|[Ss]tart|[Rr]eceive|[Pp]rocess|[Cc]onsume|[Hh]andle)"
    r"(?:[A-Z0-9_]|$)",
)
# Class/symbol suffixes that name an entry surface outright.
SURFACE_WORDS = re.compile(
    r"(controller|handler|processor|consumer|listener|worker|job|command|aggregator)$",
    re.IGNORECASE,
)
# Directory segments that put a file on an entry surface.
PATH_WORDS = re.compile(
    r"(controllers?|handlers?|processors?|consumers?|workers?|jobs?|commands?|"
    r"aggregators?|routes?|endpoints?)",
    re.IGNORECASE,
)

# Graph-layer name fragments that mark a layer as an entry/business surface.
# Backend vocabulary first, then the frontend surfaces a service-only list
# misses entirely — screens and routes are where a UI flow begins, and
# state/context layers are where it continues.
ENTRY_LAYER_WORDS = (
    "service", "business", "domain", "application", "presentation", "api",
    "screen", "route", "page", "view", "controller", "handler",
    "state", "context", "store",
)


def is_entry_layer(name: str | None) -> bool:
    """True when a graph layer's name reads as an entry/business surface."""
    lowered = str(name or "").lower()
    return any(word in lowered for word in ENTRY_LAYER_WORDS)


if __name__ == "__main__":
    raise SystemExit("error: entry_vocabulary.py is a shared module, not a CLI")
