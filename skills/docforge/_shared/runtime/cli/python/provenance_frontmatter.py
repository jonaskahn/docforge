#!/usr/bin/env python3
"""Launcher: delegates to runtime.common.provenance_frontmatter."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from runtime.common.provenance_frontmatter import *  # noqa: F401,F403
