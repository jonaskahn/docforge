#!/usr/bin/env python3
"""Run the dependency-free Docforge fixture suite."""

import unittest

raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(
    unittest.defaultTestLoader.discover("tests", pattern="test_*.py")
).wasSuccessful())
