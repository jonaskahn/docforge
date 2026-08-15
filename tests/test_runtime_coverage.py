"""Runtime coverage: every CLI launcher is exercised on BOTH the Python and
Node runtimes — the real CLIs through fixture parity, and the library-mirror
launchers through API-surface parity (they exist for import compatibility
and are not runnable commands).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _support import ROOT, run

SHARED_ROOT = ROOT / "skills" / "docforge" / "_shared"
CLI_JS = SHARED_ROOT / "runtime" / "cli" / "js"


def js_exports(launcher: str) -> set[str]:
    result = subprocess.run(
        [
            "node", "-e",
            "const m = require(process.argv[1]); "
            "process.stdout.write(JSON.stringify(Object.keys(m).sort()));",
            str(CLI_JS / f"{launcher}.js"),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    return set(json.loads(result.stdout))


def python_exports(module_name: str) -> set[str]:
    module = __import__(module_name, fromlist=["*"])
    return {
        name for name in dir(module)
        if not name.startswith("_")
        and getattr(module, name, None) is not None
        and name not in {"annotations"}
    }


def normalized(names: set[str]) -> set[str]:
    return {re.sub(r"[^a-z0-9]", "", name.lower()) for name in names}


def normalize_text(text: str, repo: Path) -> str:
    return text.replace(str(repo.resolve()), "<REPO>").replace(str(repo), "<REPO>")


def seed_ua_graph(repo: Path) -> Path:
    graph = {
        "nodes": [
            {"id": "main", "name": "main", "path": "src/main.py", "type": "function"},
            {"id": "init", "name": "init", "path": "src/main.py", "type": "function"},
            {"id": "worker", "name": "worker", "path": "src/worker.py", "type": "function"},
        ],
        "edges": [
            {"source": "main", "target": "init", "type": "calls"},
            {"source": "init", "target": "worker", "type": "calls"},
        ],
    }
    path = repo / ".ua" / "knowledge-graph.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
    return path


class LibraryMirrorParityTests(unittest.TestCase):
    CASES = {
        "_util": ("runtime.common.python._util", ["fail", "read_json", "dump_json", "load_manifest"]),
        "provenance_frontmatter": ("runtime.common.python.provenance_frontmatter", ["parse_frontmatter", "emit_yaml", "scaffold_provenance"]),
        "manifest_deps": ("runtime.common.python.manifest_deps", ["extract_dependencies", "extract_package_identities"]),
        "graph_storage": ("runtime.graph.python.graph_storage", ["ensure_tmp_dir_gitignored", "KNOWN_GRAPH_DIRS"], {"writejson"}),
        "graph_source_registry": ("runtime.graph.python.graph_source_registry", ["SOURCES", "resolve_all_ready"]),
        "graph_source_understand_anything": ("runtime.graph.python.graph_source_understand_anything", ["detect", "read_mode"]),
        "discovery_gate": ("runtime.catalog.python.discovery_gate", ["apply_judgment", "validate_judgment", "needs_gate", "load_schema"]),
    }

    def test_library_mirrors_share_the_same_api_surface(self) -> None:
        for launcher, entry in self.CASES.items():
            module_name, sentinels, *rest = entry if isinstance(entry, tuple) else (entry, [])
            allowances = set(rest[0]) if rest else set()
            with self.subTest(launcher=launcher):
                py_names = normalized(python_exports(module_name))
                js_names = normalized(js_exports(launcher))
                # The JS export list must never expose anything Python lacks
                # beyond the documented allowances.
                self.assertEqual(js_names - py_names, allowances, f"{launcher}: js-only exports")
                # Every sentinel API name exists on both runtimes.
                for sentinel in sentinels:
                    key = re.sub(r"[^a-z0-9]", "", sentinel.lower())
                    self.assertIn(key, py_names, f"{launcher}: python missing {sentinel}")
                    self.assertIn(key, js_names, f"{launcher}: js missing {sentinel}")


class HashEvidenceCliParityTests(unittest.TestCase):
    def test_json_output_matches_across_runtimes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            target = repo / "src" / "main.py"
            target.parent.mkdir()
            target.write_text("def main():\n    pass\n", encoding="utf-8")
            outputs = {}
            for runtime in ("py", "js"):
                result = run(runtime, "hash_evidence", "--repo", str(repo), "--path", "src/main.py", "--json")
                self.assertEqual(result.returncode, 0, result.stderr)
                outputs[runtime] = json.loads(result.stdout)
            self.assertEqual(outputs["py"], outputs["js"])
            self.assertEqual(len(outputs["py"]["git_blob"]), 40)
            self.assertIsNotNone(outputs["py"].get("git_blob_normalized"))
            self.assertNotIn("evidence_range", outputs["py"])
            ranged = {}
            for runtime in ("py", "js"):
                result = run(runtime, "hash_evidence", "--repo", str(repo), "--path", "src/main.py", "--range", "1-2", "--json")
                self.assertEqual(result.returncode, 0, result.stderr)
                ranged[runtime] = json.loads(result.stdout)
                self.assertEqual(ranged[runtime]["evidence_range"], {"start": "1", "end": "2"})
                self.assertIsNotNone(ranged[runtime].get("range_blob"))
            self.assertEqual(ranged["py"], ranged["js"])

    def test_missing_file_exits_2_on_both_runtimes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for runtime in ("py", "js"):
                result = run(runtime, "hash_evidence", "--repo", str(repo), "--path", "nope.py", "--json")
                self.assertEqual(result.returncode, 2, result.stderr)


class ReadGraphCliParityTests(unittest.TestCase):
    def test_all_modes_match_across_runtimes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            graph = seed_ua_graph(repo)
            for flags in (("--probe",), ("--summary",), ("--modules",), ("--deps",), ()):
                outputs = {}
                for runtime in ("py", "js"):
                    result = run(runtime, "read_graph", "--graph", str(graph), *flags)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    outputs[runtime] = normalize_text(result.stdout, repo)
                self.assertEqual(outputs["py"], outputs["js"], flags)


class DiagnoseGraphsCliParityTests(unittest.TestCase):
    def test_empty_repo_reports_missing_on_both_runtimes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                result = run(runtime, "diagnose_graphs", "--repo", str(repo))
                self.assertEqual(result.returncode, 1)
                self.assertIn("No code graph found", result.stdout)

    def test_codegraph_artifact_reports_ready_on_both_runtimes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outputs = {}
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                (repo / ".codegraph").mkdir(parents=True)
                (repo / ".codegraph" / "codegraph.db").write_text("sqlite", encoding="utf-8")
                result = run(runtime, "diagnose_graphs", "--repo", str(repo))
                self.assertEqual(result.returncode, 0, result.stderr)
                outputs[runtime] = normalize_text(result.stdout, repo)
            self.assertEqual(outputs["py"], outputs["js"])

    def test_ua_graph_reports_ready_on_both_runtimes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outputs = {}
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                seed_ua_graph(repo)
                result = run(runtime, "diagnose_graphs", "--repo", str(repo))
                self.assertEqual(result.returncode, 0, result.stderr)
                outputs[runtime] = normalize_text(result.stdout, repo)
            self.assertEqual(outputs["py"], outputs["js"])


class DeriveFlowGraphCliParityTests(unittest.TestCase):
    def test_prepare_without_graph_fails_on_both_runtimes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                result = run(runtime, "derive_flow_graph", "prepare", "--repo", str(repo))
                self.assertEqual(result.returncode, 1)
                self.assertIn("PREPARE FAILED", result.stderr)
                self.assertIn("no code graph found", result.stderr)

    def test_prepare_and_write_match_across_runtimes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outputs = {}
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                seed_ua_graph(repo)
                prepare = run(runtime, "derive_flow_graph", "prepare", "--repo", str(repo))
                self.assertEqual(prepare.returncode, 0, prepare.stderr)
                self.assertIn("Strategy:", prepare.stdout)
                context = json.loads((repo / ".docforge" / "tmp" / "flow-context.json").read_text(encoding="utf-8"))

                def scrub(value):
                    if isinstance(value, dict):
                        return {k: scrub(v) for k, v in value.items()}
                    if isinstance(value, list):
                        return [scrub(item) for item in value]
                    if isinstance(value, str):
                        return normalize_text(value, repo)
                    return value

                context = scrub(context)
                if "repo" in context:
                    context["repo"] = "<NAME>"
                normalized_prepare = normalize_text(prepare.stdout, repo)
                normalized_prepare = re.sub(
                    r"(python runtime/cli/python/derive_flow_graph\.py|node runtime/cli/js/derive_flow_graph\.js) write",
                    "<RUNTIME> write",
                    normalized_prepare,
                )
                outputs[runtime] = {"prepare": normalized_prepare, "context": context}
            self.assertEqual(outputs["py"]["prepare"], outputs["js"]["prepare"])
            self.assertEqual(outputs["py"]["context"], outputs["js"]["context"])
            analysis = {
                "source": "fixture",
                "generatedFrom": "fixture",
                "flows": [
                    {"name": "startup", "steps": ["main", "init"]},
                    {"name": "worker", "steps": ["init", "worker"]},
                ],
            }
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                analysis_path = repo / "analysis.json"
                analysis_path.write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
                write = run(runtime, "derive_flow_graph", "write", "--repo", str(repo), "--analysis", str(analysis_path))
                self.assertEqual(write.returncode, 0, write.stderr)
                self.assertIn("Wrote", write.stdout)
                graph = json.loads((repo / ".docforge" / "tmp" / "flow-graph.json").read_text(encoding="utf-8"))
                self.assertEqual([flow["name"] for flow in graph["flows"]], ["startup", "worker"])
                self.assertIn("generatedAt", graph)
            # Empty flows are rejected on both runtimes.
            empty = {"flows": []}
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                empty_path = repo / "empty.json"
                empty_path.write_text(json.dumps(empty) + "\n", encoding="utf-8")
                write = run(runtime, "derive_flow_graph", "write", "--repo", str(repo), "--analysis", str(empty_path))
                self.assertEqual(write.returncode, 1)
                self.assertIn("WRITE FAILED", write.stderr)


class GraphSourceAdapterCliParityTests(unittest.TestCase):
    def test_codegraph_detect_parity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outputs = {}
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                result = run(runtime, "graph_source_codegraph", "detect", "--repo", str(repo))
                outputs[runtime] = (result.returncode, normalize_text(result.stdout, repo))
            self.assertEqual(outputs["py"], outputs["js"])

    def test_gitnexus_reader_without_db_fails_on_both_runtimes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                result = run(runtime, "graph_source_gitnexus_reader", "--repo", str(repo))
                self.assertEqual(result.returncode, 1)
                self.assertIn("No .gitnexus/lbug found", result.stderr)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
