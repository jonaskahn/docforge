#!/usr/bin/env python3
"""Launcher: delegates to runtime.graph.read_graph."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from runtime.graph.read_graph import *  # noqa: F401,F403
from runtime.graph import read_graph as _impl

if __name__ == "__main__":
    raise SystemExit(_impl.main())
