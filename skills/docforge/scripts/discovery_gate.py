#!/usr/bin/env python3
"""Launcher: delegates to runtime.catalog.discovery_gate."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from runtime.catalog.discovery_gate import *  # noqa: F401,F403

if __name__ == "__main__":
    raise SystemExit("discovery_gate is a library module")
