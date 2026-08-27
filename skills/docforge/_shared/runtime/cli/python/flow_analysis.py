#!/usr/bin/env python3
"""Launcher: delegates to runtime.flows.python.flow_analysis."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from runtime.flows.python.flow_analysis import *  # noqa: F401,F403
from runtime.flows.python import flow_analysis as _impl

if __name__ == "__main__":
    raise SystemExit(_impl.main())
