#!/usr/bin/env python3
"""Launcher: delegates to runtime.documents.harvest_candidates."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from runtime.documents.python.harvest_candidates import *  # noqa: F401,F403
from runtime.documents.python import harvest_candidates as _impl

if __name__ == "__main__":
    raise SystemExit(_impl.main())
