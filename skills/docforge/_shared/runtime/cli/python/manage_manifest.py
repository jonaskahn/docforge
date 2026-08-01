#!/usr/bin/env python3
"""Launcher: delegates to runtime.manifest.manage_manifest."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from runtime.manifest.python.manage_manifest import *  # noqa: F401,F403
from runtime.manifest.python import manage_manifest as _impl

if __name__ == "__main__":
    raise SystemExit(_impl.main())
