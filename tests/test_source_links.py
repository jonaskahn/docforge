"""Source permalinks: declared base, pinned commit, validated targets, parity.

A reader who must open a file needs a link that works. A repo-relative link
cannot -- it 404s in the rendered site -- so the writer's readable authoring
form is expanded into an absolute permalink at the commit the document was
grounded against, with every target checked first. The previous output carried
1,064 hand-written `path:line` mentions, none checked, all pinned to a commit
that had already moved.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from _support import run

BASE = "https://gitlab.example.com/team/repo"
GITLAB = {
    "web_base": BASE,
    "forge": "gitlab",
    "blob_template": "{web_base}/-/blob/{commit}/{path}#L{start}-{end}",
}
COMMIT = "c" * 40


def seed(repo: Path, repository: dict | None = GITLAB) -> Path:
    (repo / "src").mkdir(parents=True)
    (repo / "config").mkdir()
    (repo / "src" / "worker.py").write_text(
        "\n".join(f"line {index}" for index in range(1, 121)) + "\n", encoding="utf-8"
    )
    (repo / "config" / "worker.yaml").write_text("key: value\n", encoding="utf-8")
    manifest = {
        "version": "3.10",
        "project": {"name": "fixture", "root": str(repo)},
        "documents": [{"id": "doc", "path": "docs/a.md", "group": "architecture"}],
    }
    if repository is not None:
        manifest["project"]["repository"] = repository
    (repo / ".docforge").mkdir(exist_ok=True)
    path = repo / ".docforge" / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def write_doc(repo: Path, body: str) -> Path:
    doc = repo / "docs" / "a.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(body, encoding="utf-8")
    return doc


class SourceLinkExpansionTests(unittest.TestCase):
    def test_authoring_form_becomes_a_pinned_permalink(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                manifest = seed(repo)
                doc = write_doc(
                    repo,
                    "# Doc\n\nThe scheduler claims items "
                    "([the crawl-job runner](src/worker.py#L97-L104)).\n"
                    "Add the key to [the worker config](config/worker.yaml).\n",
                )
                result = run(
                    runtime, "link_sources", "--repo", str(repo),
                    "--manifest", str(manifest), "--commit", COMMIT, "--write",
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                body = doc.read_text(encoding="utf-8")
                self.assertIn(
                    f"[the crawl-job runner]({BASE}/-/blob/{COMMIT}/src/worker.py#L97-104)",
                    body,
                )
                # No range means the file, not a line a refactor will move.
                self.assertIn(
                    f"[the worker config]({BASE}/-/blob/{COMMIT}/config/worker.yaml)",
                    body,
                )

    def test_backtick_wrapped_links_are_unwrapped(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                manifest = seed(repo)
                doc = write_doc(
                    repo,
                    "# Doc\n\nThe reset runs at startup "
                    "(`[the crawl-job runner](src/worker.py#L97-L104)`).\n",
                )
                result = run(
                    runtime, "link_sources", "--repo", str(repo),
                    "--manifest", str(manifest), "--commit", COMMIT, "--write",
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                body = doc.read_text(encoding="utf-8")
                self.assertIn(
                    f"[the crawl-job runner]({BASE}/-/blob/{COMMIT}/src/worker.py#L97-104)",
                    body,
                )
                self.assertNotIn(
                    f"`[the crawl-job runner]({BASE}/-/blob/{COMMIT}/src/worker.py#L97-104)`",
                    body,
                )

    def test_already_expanded_backtick_wrapped_links_are_unwrapped(self) -> None:
        # A link that was already expanded to a pinned permalink in an earlier
        # pass, but got wrapped in backticks by the writer -- e.g. a doc
        # written before this guard existed. Revise must still heal it.
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                manifest = seed(repo)
                pinned = f"{BASE}/-/blob/{COMMIT}/src/worker.py#L97-104"
                doc = write_doc(
                    repo,
                    f"# Doc\n\nThe reset runs at startup (`[the crawl-job runner]({pinned})`).\n",
                )
                result = run(
                    runtime, "link_sources", "--repo", str(repo),
                    "--manifest", str(manifest), "--commit", COMMIT, "--write",
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                body = doc.read_text(encoding="utf-8")
                self.assertIn(f"[the crawl-job runner]({pinned})", body)
                self.assertNotIn(f"`[the crawl-job runner]({pinned})`", body)

    def test_unresolvable_targets_fail_loudly_and_are_left_alone(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                manifest = seed(repo)
                doc = write_doc(
                    repo,
                    "# Doc\n\n"
                    "Missing: [the absent module](src/nope.py#L1-L2).\n"
                    "Past EOF: [the tail](src/worker.py#L900-L910).\n"
                    "Path label: [src/worker.py:97](src/worker.py#L97).\n",
                )
                result = run(
                    runtime, "link_sources", "--repo", str(repo),
                    "--manifest", str(manifest), "--commit", COMMIT, "--write", "--json",
                )
                self.assertEqual(result.returncode, 1)
                problems = json.loads(result.stdout)["problems"]
                self.assertTrue(any("no such file: src/nope.py" in p for p in problems))
                self.assertTrue(any("out of bounds" in p for p in problems))
                self.assertTrue(any("is a path; name the thing" in p for p in problems))
                # An unresolvable reference is never silently rewritten.
                self.assertIn("(src/nope.py#L1-L2)", doc.read_text(encoding="utf-8"))

    def test_fences_are_never_rewritten(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            manifest = seed(repo)
            doc = write_doc(
                repo,
                "# Doc\n\n```text\nexample: [x](src/worker.py#L1-L2)\n```\n",
            )
            result = run(
                "py", "link_sources", "--repo", str(repo),
                "--manifest", str(manifest), "--commit", COMMIT, "--write",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("[x](src/worker.py#L1-L2)", doc.read_text(encoding="utf-8"))

    def test_undeclared_repository_refuses_rather_than_guessing(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                manifest = seed(repo, repository=None)
                write_doc(repo, "# Doc\n\n[the runner](src/worker.py#L1-L2)\n")
                result = run(
                    runtime, "link_sources", "--repo", str(repo),
                    "--manifest", str(manifest), "--commit", COMMIT,
                )
                self.assertEqual(result.returncode, 2)
                self.assertIn("project.repository is not declared", result.stderr)

    def test_runtimes_agree_byte_for_byte(self) -> None:
        outputs = []
        bodies = []
        for runtime in ("py", "js"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                manifest = seed(repo)
                doc = write_doc(
                    repo,
                    "# Doc\n\nOne ([the runner](src/worker.py#L97-L104)), "
                    "two ([the config](config/worker.yaml)), "
                    "bad ([the absent](src/nope.py#L1-L2)).\n",
                )
                result = run(
                    runtime, "link_sources", "--repo", str(repo),
                    "--manifest", str(manifest), "--commit", COMMIT, "--write", "--json",
                )
                outputs.append(result.stdout)
                bodies.append(doc.read_text(encoding="utf-8"))
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(bodies[0], bodies[1])


class ForgeFlavorTests(unittest.TestCase):
    def test_each_flavor_uses_its_own_line_anchor_syntax(self) -> None:
        """The anchor differs per forge; a wrong guess highlights wrong lines."""
        import sys

        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "docforge" / "_shared"))
        from runtime.common.python.repo_identity import blob_url, normalize

        expected = {
            "github": "https://h/o/r/blob/" + COMMIT + "/src/a.py#L1-L2",
            "gitlab": "https://h/o/r/-/blob/" + COMMIT + "/src/a.py#L1-2",
            "gitea": "https://h/o/r/src/commit/" + COMMIT + "/src/a.py#L1-L2",
            "bitbucket": "https://h/o/r/src/" + COMMIT + "/src/a.py#lines-1:2",
        }
        for forge, url in expected.items():
            with self.subTest(forge=forge):
                identity = normalize({"web_base": "https://h/o/r", "forge": forge})
                self.assertEqual(blob_url(identity, COMMIT, "src/a.py", 1, 2), url)

    def test_self_hosted_flavor_is_asked_never_guessed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "a.txt").write_text("x\n", encoding="utf-8")
            for args in (
                ["init", "-q", "-b", "main"],
                ["config", "user.email", "a@b.c"],
                ["config", "user.name", "T"],
                ["add", "-A"],
                ["commit", "-q", "-m", "i"],
                ["remote", "add", "origin", "https://git.internal.example/team/repo.git"],
            ):
                subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)
            from _support import initialize

            self.assertEqual(initialize("py", repo, "spine").returncode, 0)
            refused = run("py", "manage_manifest", "set-repository", "--repo", str(repo))
            self.assertEqual(refused.returncode, 2)
            self.assertIn("cannot infer the forge flavor", refused.stderr)

            accepted = run(
                "py", "manage_manifest", "set-repository",
                "--repo", str(repo), "--forge", "gitea",
            )
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            manifest = json.loads(
                (repo / ".docforge" / "manifest.json").read_text(encoding="utf-8")
            )
            record = manifest["project"]["repository"]
            self.assertEqual(record["forge"], "gitea")
            self.assertEqual(record["declared_by"], "user")


if __name__ == "__main__":
    unittest.main()
