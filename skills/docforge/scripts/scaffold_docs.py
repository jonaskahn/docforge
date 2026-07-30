#!/usr/bin/env python3
"""Launcher: delegates to runtime.documents.scaffold_docs."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from runtime.documents.scaffold_docs import *  # noqa: F401,F403
from runtime.documents import scaffold_docs as _impl

if __name__ == "__main__":
    raise SystemExit(_impl.main())
