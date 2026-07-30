#!/usr/bin/env python3
"""Launcher: delegates to runtime.graph.graph_source_understand_anything."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from runtime.graph.graph_source_understand_anything import *  # noqa: F401,F403
