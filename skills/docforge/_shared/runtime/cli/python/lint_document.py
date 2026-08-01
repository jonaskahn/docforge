#!/usr/bin/env python3
"""Launcher: delegates to runtime.documents.lint_document."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from runtime.documents.python.lint_document import *  # noqa: F401,F403
from runtime.documents.python import lint_document as _impl

if __name__ == "__main__":
    raise SystemExit(_impl.main())
