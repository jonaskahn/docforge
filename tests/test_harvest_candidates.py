"""Decision and concept candidate harvest: real git signals, no invention,
byte-identical across runtimes.

`concept` and `adr` are gated on `discovered_concept` / `discovered_decision`,
conditions no code evaluates. Before this harvest existed nothing ever looked,
so every Diligence run produced a `decisions/` and `concepts/` folder holding
only an index explaining its own emptiness.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from _support import run


def git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True, capture_output=True, text=True,
    )


def seed_repo(repo: Path) -> None:
    """A repository with an initial import plus two later subsystems."""
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "docforge@example.com")
    git(repo, "config", "user.name", "Docforge Test")

    imported = repo / "src" / "legacy"
    imported.mkdir(parents=True)
    for index in range(4):
        (imported / f"module{index}.py").write_text("value = 1\n", encoding="utf-8")
    (repo / "package.json").write_text('{"dependencies": {}}\n', encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "Migrate code from existing solution")

    kafka = repo / "src" / "kafka"
    kafka.mkdir(parents=True)
    for index in range(5):
        (kafka / f"consumer{index}.py").write_text("value = 2\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "Add the kafka event pipeline")

    templates = repo / "src" / "templates" / "reports"
    templates.mkdir(parents=True)
    for index in range(6):
        (templates / f"report{index}.js").write_text("module.exports = {};\n", encoding="utf-8")
    (repo / "package.json").write_text('{"dependencies": {"kafkajs": "^2"}}\n', encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "Add report templates and kafkajs")


class HarvestCandidatesTests(unittest.TestCase):
    def _payload(self, runtime: str, repo: Path) -> dict:
        result = run(runtime, "harvest_candidates", "--repo", str(repo), "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_git_signals_become_candidates_with_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            payload = self._payload("py", repo)

            titles = [row["title"] for row in payload["decisions"]]
            self.assertIn("Introduce the kafka subsystem", titles)
            self.assertIn(
                "Dependency and toolchain choices recorded in package.json", titles
            )
            # Arrived with the initial import, so no decision was made here.
            self.assertNotIn("Introduce the legacy subsystem", titles)

            for row in payload["decisions"]:
                self.assertEqual(row["status"], "candidate")
            kafka = next(
                row for row in payload["decisions"]
                if row["title"] == "Introduce the kafka subsystem"
            )
            self.assertEqual(kafka["paths"], ["src/kafka"])
            self.assertEqual(len(kafka["evidence"]), 1)
            self.assertEqual(kafka["evidence"][0]["subject"], "Add the kafka event pipeline")
            self.assertRegex(kafka["evidence"][0]["commit"], r"^[0-9a-f]{40}$")

    def test_template_trees_are_never_concepts(self) -> None:
        """A template tree carries no mechanism at any depth.

        Emitting one is the decorative documentation the coherence principle
        penalizes, and it is how email-template subfolders once surfaced as
        architecture concepts.
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            payload = self._payload("py", repo)
            paths = [path for row in payload["concepts"] for path in row["paths"]]
            self.assertIn("src/kafka", paths)
            for path in paths:
                self.assertNotIn("templates", path)

    def test_no_git_repository_yields_no_invented_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src").mkdir()
            payload = self._payload("py", repo)
            self.assertEqual(payload["decisions"], [])
            self.assertEqual(payload["summary"]["decision_candidates"], 0)

    def test_limits_are_honored_and_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            result = run(
                "py", "harvest_candidates", "--repo", str(repo),
                "--decision-limit", "1", "--json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(json.loads(result.stdout)["decisions"]), 1)

            rejected = run(
                "py", "harvest_candidates", "--repo", str(repo), "--decision-limit", "0",
            )
            self.assertEqual(rejected.returncode, 2)

    def test_writes_candidates_file_without_json_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            result = run("py", "harvest_candidates", "--repo", str(repo))
            self.assertEqual(result.returncode, 0, result.stderr)
            target = repo / ".docforge" / "candidates.json"
            self.assertTrue(target.is_file())
            self.assertIn("candidate", target.read_text(encoding="utf-8"))
            self.assertIn("none is selected until the write-start gate", result.stdout)

    def test_runtimes_agree_byte_for_byte(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            python = run("py", "harvest_candidates", "--repo", str(repo), "--json")
            node = run("js", "harvest_candidates", "--repo", str(repo), "--json")
            self.assertEqual(python.returncode, 0, python.stderr)
            self.assertEqual(node.returncode, 0, node.stderr)
            self.assertEqual(python.stdout, node.stdout)


if __name__ == "__main__":
    unittest.main()
