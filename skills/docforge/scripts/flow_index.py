#!/usr/bin/env python3
"""Launcher: delegates to runtime.flows.flow_index."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from runtime.flows.flow_index import *  # noqa: F401,F403
from runtime.flows import flow_index as _impl

if __name__ == "__main__":
    raise SystemExit(_impl.main())
