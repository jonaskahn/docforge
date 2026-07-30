#!/usr/bin/env python3
"""Launcher: delegates to runtime.portfolio.discover_child_repos."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from runtime.portfolio.discover_child_repos import *  # noqa: F401,F403
from runtime.portfolio import discover_child_repos as _impl

if __name__ == "__main__":
    raise SystemExit(_impl.main())
