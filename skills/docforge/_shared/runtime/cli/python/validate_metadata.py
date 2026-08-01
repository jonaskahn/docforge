#!/usr/bin/env python3
"""Launcher: delegates to runtime.validation.validate_metadata."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from runtime.validation.python.validate_metadata import *  # noqa: F401,F403
from runtime.validation.python import validate_metadata as _impl

if __name__ == "__main__":
    raise SystemExit(_impl.main())
