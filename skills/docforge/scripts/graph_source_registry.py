#!/usr/bin/env python3
"""Launcher: delegates to runtime.graph.graph_source_registry."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from runtime.graph.graph_source_registry import *  # noqa: F401,F403
