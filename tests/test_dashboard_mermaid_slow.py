"""Opt-in slow tier: real Mermaid detection.

Every other dashboard test fakes `npm`/`mermaid` entirely (see
`fake_npm_env()`/`prepare_fake_mermaid_dashboard()` in `test_dashboard.py`),
which proves the gate's plumbing (subprocess/JSON contract, abort behavior)
but cannot prove real Mermaid syntax detection actually works -- for that,
`mermaid.parse()` has to run for real, against a real `npm install` of the
dashboard template's `mermaid`/`jsdom`.

This is the only place in the suite that installs real npm dependencies, so
it is opt-in: set `DOCFORGE_RUN_SLOW_TESTS=1` to run it. Not wired into CI.

    DOCFORGE_RUN_SLOW_TESTS=1 python3 -m pytest tests/test_dashboard_mermaid_slow.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "skills" / "docforge" / "_shared" / "runtime" / "dashboard" / "template"

RUN_SLOW = os.environ.get("DOCFORGE_RUN_SLOW_TESTS") == "1"

# A small fixed corpus, not live-generated doc content: this is the tripwire
# for a `mermaid`/`jsdom` version bump changing `.parse()` behavior
# (mermaid-js/mermaid#6370 documents at least one known false-negative case
# in a headless/jsdom context), so it must stay stable across runs.
VALID_DIAGRAMS = {
    "flowchart": "flowchart TD\n  A[Start] --> B{Decision}\n  B -->|Yes| C[End]\n  B -->|No| A\n",
    "sequence": "sequenceDiagram\n  Alice->>Bob: Hello Bob\n  Bob-->>Alice: Hi Alice\n",
    "class": "classDiagram\n  class Animal\n  Animal : +String name\n",
    "state": "stateDiagram-v2\n  [*] --> Still\n  Still --> [*]\n",
    "gantt": "gantt\n  title A Gantt Diagram\n  section Section\n  A task :a1, 2024-01-01, 30d\n",
    "pie": 'pie title Pets\n  "Dogs" : 40\n  "Cats" : 30\n',
    "er": "erDiagram\n  CUSTOMER ||--o{ ORDER : places\n",
}

INVALID_DIAGRAMS = {
    "unclosed_subgraph": "flowchart TD\n  subgraph one\n  A --> B\n",
    "garbage_text": "this is not a diagram at all just prose\n",
    "misspelled_keyword": "flowcart TD\n  A --> B\n",
}


@unittest.skipUnless(RUN_SLOW, "set DOCFORGE_RUN_SLOW_TESTS=1 to run the real npm/mermaid tier")
class RealMermaidDetectionTests(unittest.TestCase):
    """Installs the template's real `mermaid`/`jsdom` once, then runs the
    fixed corpus through the real, unmodified `validate_mermaid.mjs`."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = Path(tempfile.mkdtemp(prefix="docforge-real-mermaid-"))
        instance = cls.tmp / "dashboard"
        instance.mkdir()
        for name in ("package.json", "package-lock.json"):
            source = TEMPLATE / name
            if source.is_file():
                shutil.copy2(source, instance / name)
        shutil.copytree(TEMPLATE / "scripts", instance / "scripts")
        install = subprocess.run(
            ["npm", "--prefix", str(instance), "install", "--no-audit", "--no-fund"],
            capture_output=True, text=True, timeout=300,
        )
        if install.returncode != 0:
            raise RuntimeError(f"npm install failed: {install.stderr}")
        cls.instance = instance

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _verdicts(self, charts: list[str]) -> list[dict]:
        script = self.instance / "scripts" / "validate_mermaid.mjs"
        result = subprocess.run(
            ["node", str(script)],
            input=json.dumps([{"chart": chart} for chart in charts]),
            cwd=str(self.instance),
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_valid_diagrams_across_common_types_all_parse(self) -> None:
        names = list(VALID_DIAGRAMS)
        verdicts = self._verdicts([VALID_DIAGRAMS[name] for name in names])
        for name, verdict in zip(names, verdicts):
            self.assertTrue(verdict["ok"], f"{name}: expected valid, got {verdict}")
            self.assertIsNone(verdict["error"])

    def test_invalid_diagrams_are_all_rejected(self) -> None:
        names = list(INVALID_DIAGRAMS)
        verdicts = self._verdicts([INVALID_DIAGRAMS[name] for name in names])
        for name, verdict in zip(names, verdicts):
            self.assertFalse(verdict["ok"], f"{name}: expected invalid, got {verdict}")
            self.assertTrue(verdict["error"])

    def test_verdicts_do_not_leak_state_across_sequential_calls(self) -> None:
        # A single validator process handles every fence in a document set,
        # in order -- a bad diagram must never poison the ones after it.
        interleaved = [
            VALID_DIAGRAMS["flowchart"],
            INVALID_DIAGRAMS["garbage_text"],
            VALID_DIAGRAMS["sequence"],
            INVALID_DIAGRAMS["misspelled_keyword"],
            VALID_DIAGRAMS["pie"],
        ]
        verdicts = self._verdicts(interleaved)
        self.assertEqual([v["ok"] for v in verdicts], [True, False, True, False, True])


if __name__ == "__main__":
    unittest.main()
