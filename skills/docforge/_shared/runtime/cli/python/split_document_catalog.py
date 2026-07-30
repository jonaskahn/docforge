#!/usr/bin/env python3
"""Launcher: delegates to runtime.migrations.split_document_catalog."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from runtime.migrations.split_document_catalog import *  # noqa: F401,F403
from runtime.migrations import split_document_catalog as _impl

if __name__ == "__main__":
    raise SystemExit(_impl.main())
