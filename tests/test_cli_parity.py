"""Python/Node runtime parity: same fixture, same exit code/stdout/files."""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from _support import blob_hash, initialize, load_manifest, markdown_with_provenance, normalized, normalized_blob_hash, provenance, run, write_flow_index
from test_graph_and_flows import _two_provider_repo


class RuntimeParityTests(unittest.TestCase):
    def test_manifest_dry_run_and_filesystem_parity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            py_repo, js_repo = Path(tmp) / "py", Path(tmp) / "js"
            py_repo.mkdir()
            js_repo.mkdir()
            kwargs = {
                "shapes": ("api-service", "library-sdk"),
                "audiences": ("coding-agents",),
            }
            py_result = initialize("py", py_repo, "portfolio", **kwargs)
            js_result = initialize("js", js_repo, "portfolio", **kwargs)
            self.assertEqual(py_result.returncode, js_result.returncode)
            py_manifest, js_manifest = load_manifest(py_repo), load_manifest(js_repo)
            for manifest in (py_manifest, js_manifest):
                manifest["generated_at"] = "<TIME>"
                manifest["metadata"]["last_updated"] = "<TIME>"
                manifest["project"]["scale"]["decided_at"] = "<TIME>"
                manifest["project"]["root"] = "<REPO>"
                manifest["project"]["name"] = "<NAME>"
            self.assertEqual(py_manifest, js_manifest)

            py_tree = run("py", "scaffold_docs", "--repo", str(py_repo), "--manifest",
                          str(py_repo / ".docforge/manifest.json"), "--dry-run")
            js_tree = run("js", "scaffold_docs", "--repo", str(js_repo), "--manifest",
                          str(js_repo / ".docforge/manifest.json"), "--dry-run")
            self.assertEqual(py_tree.returncode, 0, py_tree.stderr)
            self.assertEqual(py_tree.stdout, js_tree.stdout)
            self.assertIn("Generation plan — tier: portfolio", py_tree.stdout)
            self.assertIn("depth:", py_tree.stdout)
            self.assertIn("requires:", py_tree.stdout)
            self.assertIn("selected by:", py_tree.stdout)
            self.assertRegex(
                py_tree.stdout,
                r"\d+ manifest documents; \d+ require a flow graph\.",
            )
            listed = {
                match.group(1)
                for line in py_tree.stdout.splitlines()
                if (match := re.match(r"^\d{3}\s+\S+\s+(\S+)$", line))
            }
            self.assertEqual(listed, {doc["path"] for doc in py_manifest["documents"]})

            for runtime, repo in (("py", py_repo), ("js", js_repo)):
                write_flow_index(repo)
                add = run(runtime, "manage_manifest", "add", "--repo", str(repo), "--type", "flow",
                          "--id", "flow-checkout", "--path", "docs/flows/checkout.md")
                self.assertEqual(add.returncode, 0, add.stderr)
                create = run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest",
                             str(repo / ".docforge/manifest.json"), "--document", "flow-checkout")
                self.assertEqual(create.returncode, 0, create.stderr)
            py_files = sorted(str(item.relative_to(py_repo)) for item in py_repo.rglob("*") if item.is_file())
            js_files = sorted(str(item.relative_to(js_repo)) for item in js_repo.rglob("*") if item.is_file())
            self.assertEqual(py_files, js_files)
            for rel in py_files:
                if rel != ".docforge/manifest.json":
                    py_bytes = (py_repo / rel).read_text(encoding="utf-8")
                    js_bytes = (js_repo / rel).read_text(encoding="utf-8")
                    timestamp = r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\+00:00"
                    self.assertEqual(re.sub(timestamp, "<TIME>", py_bytes), re.sub(timestamp, "<TIME>", js_bytes))

    def test_unknown_flags_exit_two(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                result = run(runtime, "scaffold_docs", "--repo", tmp, "--manifest", "missing", "--wat")
                self.assertEqual(result.returncode, 2)
                result = run(runtime, "precheck_graph", "--repo", tmp, "--need", "domain")
                self.assertEqual(result.returncode, 2)
                result = run(runtime, "manage_manifest", "set-graph", "--repo", tmp, "--wat")
                self.assertEqual(result.returncode, 2)

    def test_set_graph_and_init_graph_provider_parity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            py_repo, js_repo = Path(tmp) / "py", Path(tmp) / "js"
            for repo in (py_repo, js_repo):
                repo.mkdir()
                (repo / ".gitnexus").mkdir()
                (repo / ".gitnexus" / "lbug").write_bytes(b"fixture")
            manifests = {}
            for runtime, repo in (("py", py_repo), ("js", js_repo)):
                result = initialize(runtime, repo, "spine")
                self.assertEqual(result.returncode, 0, result.stderr)
                manifest = load_manifest(repo)
                manifest["generated_at"] = "<TIME>"
                manifest["metadata"]["last_updated"] = "<TIME>"
                manifest["graph"]["locked_at"] = "<TIME>"
                manifest["project"]["scale"]["decided_at"] = "<TIME>"
                manifest["project"]["root"] = "<REPO>"
                manifest["project"]["name"] = "<NAME>"
                manifests[runtime] = manifest
            self.assertEqual(manifests["py"], manifests["js"])
            for runtime, repo in (("py", py_repo), ("js", js_repo)):
                result = run(
                    runtime, "manage_manifest", "set-graph", "--repo", str(repo),
                    "--provider", "bogus",
                )
                self.assertEqual(result.returncode, 2)
                self.assertIn("unknown graph provider", result.stderr)

    def test_locked_provider_prepare_parity(self) -> None:
        """Honoring the session lock must produce identical stdout and an identical
        flow-context on both runtimes — the lock's read side is parity surface now,
        including the `[session lock]` label and `sourceOrigin`."""
        with tempfile.TemporaryDirectory() as tmp:
            # Same basename under different parents, so the embedded repo name is
            # identical on both sides and only the parent path has to normalize.
            repos = {"py": Path(tmp) / "py" / "repo", "js": Path(tmp) / "js" / "repo"}
            stdouts, contexts = {}, {}
            for runtime, repo in repos.items():
                repo.mkdir(parents=True)
                _two_provider_repo(repo)
                self.assertEqual(
                    initialize(runtime, repo, "spine", graph_provider="codegraph").returncode, 0
                )
                result = run(runtime, "derive_flow_graph", "prepare", "--repo", str(repo))
                self.assertEqual(result.returncode, 0, result.stderr)
                # resolve() too: on macOS the tmp dir is reached through a
                # /private symlink, so the printed path differs from `repo`.
                text = normalized(result.stdout, [repo.resolve(), repo])
                # The trailing "then run:" hint names each runtime's own launcher
                # (python .../python/... vs node .../js/...) and is meant to differ.
                stdouts[runtime] = "\n".join(
                    line for line in text.splitlines() if "runtime/cli/" not in line
                )
                context = json.loads(
                    (repo / ".docforge" / "tmp" / "flow-context.json").read_text(encoding="utf-8")
                )
                context["generatedFrom"] = "<PATH>"
                context["repo"] = "<NAME>"
                contexts[runtime] = context
            self.assertEqual(stdouts["py"], stdouts["js"])
            self.assertEqual(contexts["py"], contexts["js"])
            self.assertEqual(contexts["py"]["source"], "codegraph")
            self.assertEqual(contexts["py"]["sourceOrigin"], "lock")

    def test_agent_settings_merge_and_local_ignore_are_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            results = []
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                (repo / ".claude").mkdir(parents=True)
                (repo / ".claude" / "settings.json").write_text(
                    json.dumps({
                        "permissions": {"deny": ["Bash(custom-danger*)"]},
                        "env": {"KEEP_ME": "yes"},
                    }) + "\n",
                    encoding="utf-8",
                )
                (repo / ".gitignore").write_text("build/\n", encoding="utf-8")
                init = initialize(
                    runtime, repo, "spine", audiences=("coding-agents",),
                )
                self.assertEqual(init.returncode, 0, init.stderr)
                for doc_id in ("claude_settings", "claude_local"):
                    created = run(
                        runtime, "scaffold_docs",
                        "--repo", str(repo),
                        "--manifest", str(repo / ".docforge" / "manifest.json"),
                        "--document", doc_id,
                    )
                    self.assertEqual(created.returncode, 0, created.stderr)
                settings = json.loads(
                    (repo / ".claude" / "settings.json").read_text(encoding="utf-8")
                )
                self.assertEqual(settings["env"], {"KEEP_ME": "yes"})
                self.assertIn(
                    "Bash(custom-danger*)", settings["permissions"]["deny"],
                )
                self.assertIn(
                    "Bash(git reset --hard*)", settings["permissions"]["deny"],
                )
                ignore = (repo / ".gitignore").read_text(encoding="utf-8")
                self.assertEqual(ignore.count("CLAUDE.local.md"), 1)
                self.assertIn("build/\n", ignore)
                results.append((settings, ignore))
            self.assertEqual(results[0], results[1])

    def test_check_staleness_cosmetic_status_output_parity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "source.txt"
            source.write_text("one\ntwo\n", encoding="utf-8")
            raw_blob = blob_hash(source.read_bytes())
            norm_blob = normalized_blob_hash(source.read_bytes())
            doc = repo / "README.md"
            value = provenance(
                doc_id="root_readme", path="README.md", tier="spine",
                target_depth="overview", section_id="readme",
                source_path="source.txt", source_blob=raw_blob,
                normalized_blob=norm_blob,
            )
            doc.write_text(markdown_with_provenance(value, "# Readme\n"), encoding="utf-8")
            manifest = {
                "version": "3.1", "project": {"root": str(repo)},
                "documents": [{
                    "id": "root_readme", "type": "root-readme", "path": "README.md",
                    "status": "complete", "provenance_mode": "sections", "provenance": value,
                }],
            }
            manifest_path = repo / ".docforge" / "manifest.json"
            manifest_path.parent.mkdir()
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            source.write_text("one\r\ntwo  \r\n", encoding="utf-8")
            outputs = {}
            for runtime in ("py", "js"):
                plain = run(runtime, "check_staleness", "--manifest", str(manifest_path))
                self.assertEqual(plain.returncode, 0, plain.stderr)
                as_json = run(runtime, "check_staleness", "--manifest", str(manifest_path), "--json")
                self.assertEqual(as_json.returncode, 0, as_json.stderr)
                outputs[runtime] = (
                    normalized(plain.stdout, [repo]),
                    normalized(as_json.stdout, [repo]),
                )
            self.assertEqual(outputs["py"], outputs["js"])
            self.assertIn("COSMETIC", outputs["py"][0])

    def test_docforge_finish_parity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            results = {}
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                init = initialize(runtime, repo, "spine")
                self.assertEqual(init.returncode, 0, init.stderr)
                (repo / ".docforge" / "tmp" / "scratch.json").write_text("{}", encoding="utf-8")
                finish = run(runtime, "manage_manifest", "finish", "--repo", str(repo))
                self.assertEqual(finish.returncode, 0, finish.stderr)
                results[runtime] = {
                    "tmp_exists": (repo / ".docforge" / "tmp" / "scratch.json").exists(),
                    "gitignore_exists": (repo / ".docforge" / ".gitignore").is_file(),
                    "manifest_exists": (repo / ".docforge" / "manifest.json").is_file(),
                }
            self.assertEqual(results["py"], results["js"])
            self.assertFalse(results["py"]["tmp_exists"])
            self.assertTrue(results["py"]["gitignore_exists"])
            self.assertTrue(results["py"]["manifest_exists"])

    def test_preview_parity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src").mkdir()
            (repo / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
            scope = [
                "--tier", "diligence", "--layout", "compact",
                "--shape", "library-sdk", "--audience", "engineers",
                "--audience", "beginners", "--audience", "coding-agents", "--json",
            ]
            py_result = run("py", "manage_manifest", "preview", "--repo", str(repo), *scope)
            js_result = run("js", "manage_manifest", "preview", "--repo", str(repo), *scope)
            self.assertEqual(py_result.returncode, 0, py_result.stderr)
            self.assertEqual(js_result.returncode, 0, js_result.stderr)
            self.assertEqual(json.loads(py_result.stdout), json.loads(js_result.stdout))
            # Read-only: no manifest, no directories, nothing written by either runtime.
            self.assertFalse((repo / ".docforge").exists())


if __name__ == "__main__":
    unittest.main()
