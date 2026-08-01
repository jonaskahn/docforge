#!/usr/bin/env python3
"""Launcher: delegates to the docforge-dashboard runtime.

The dashboard runtime lives with its skill (`skills/docforge-dashboard/`),
not in the shared cartridge. It still consumes the cartridge's shared
codec/util (`runtime.common.*`), so both the shared root and the dashboard
runtime directory are placed on sys.path.
"""

from __future__ import annotations

import sys
from pathlib import Path

LAUNCHER = Path(__file__).resolve()
DASH_RUNTIME = LAUNCHER.parents[2]                       # skills/docforge-dashboard/runtime
SHARED_ROOT = LAUNCHER.parents[4] / "docforge" / "_shared"  # skills/docforge/_shared
sys.path.insert(0, str(SHARED_ROOT))
sys.path.insert(0, str(DASH_RUNTIME))
from dashboard import *  # noqa: F401,F403
from dashboard import main as _main

if __name__ == "__main__":
    raise SystemExit(_main())
