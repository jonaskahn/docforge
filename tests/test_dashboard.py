"""Dashboard: metadata reconciliation, route planning, MDX conversion, validation, fingerprinting."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path

from _support import (
    ROOT,
    blob_hash,
    load_manifest,
    markdown_with_provenance,
    normalized,
    provenance,
)

DASH_CLI_PY = ROOT / "skills" / "docforge-dashboard" / "runtime" / "cli" / "python"
DASH_CLI_JS = ROOT / "skills" / "docforge-dashboard" / "runtime" / "cli" / "js"


def run_dashboard(runtime: str, *args: str) -> subprocess.CompletedProcess:
    command = (
        ["python3", str(DASH_CLI_PY / "dashboard.py")]
        if runtime == "py"
        else ["node", str(DASH_CLI_JS / "dashboard.js")]
    )
    return subprocess.run(command + list(args), cwd=ROOT, text=True, capture_output=True)


def wait_until(predicate, timeout: float = 10) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.05)
    return False


def url_responds(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=0.2):
            return True
    except Exception:  # noqa: BLE001 - refusal and HTTP errors both mean unavailable
        return False

INDEX_BODY = """# Documentation

## Introduction

See [architecture/](architecture/README.md) and [product/overview.md](product/overview.md).

| Section | Description |
| --- | --- |
| Architecture | How it is built |
| Product | What it does |
"""

CONSTRAINTS_BODY = """# Constraints

Owner is <TEAM_OWNER>. Literal braces {stay} safe.

```js
const x = '<TEAM_OWNER> {not escaped}';
```

See [the index](../README.md#documentation).

| Area | Limit |
| --- | --- |
| Latency | <100 ms |

```mermaid
graph TD;
  A-->B;
```
"""


def written_doc(doc_id: str, path: str, body: str, write_order: int = 10) -> dict:
    value = provenance(
        doc_id=doc_id,
        path=path,
        tier="spine",
        target_depth="orientation",
        section_id="main",
        source_path="src/main.ts",
        source_blob=blob_hash(b"evidence"),
    )
    return {
        "id": doc_id,
        "title": doc_id.replace("_", " ").title(),
        "type": "generic",
        "path": path,
        "group": "architecture",
        "selection": {"origins": [{"kind": "dynamic", "id": "generic"}], "evidence": []},
        "status": "generated",
        "requires": [],
        "scaffold_template": "unused",
        "target_depth": "orientation",
        "write_order": write_order,
        "provenance_mode": "sections",
        "audit_profile": "standard",
        "provenance": value,
        "audit": None,
    }


def seed_repo(repo: Path) -> None:
    bodies = {
        "docs_index": INDEX_BODY,
        "architecture_constraints": CONSTRAINTS_BODY,
        "product_overview": "# Overview\n\nBody.\n",
    }
    docs = [
        written_doc("docs_index", "docs/README.md", INDEX_BODY, write_order=30),
        written_doc("architecture_constraints", "docs/architecture/constraints.md", CONSTRAINTS_BODY, write_order=9),
        written_doc("product_overview", "docs/product/overview.md", bodies["product_overview"], write_order=19),
    ]
    manifest = {
        "version": "3.1",
        "generated_at": "2026-08-01T00:00:00Z",
        "project": {"name": "fixture", "root": str(repo), "tier": "spine", "profiles": {}},
        "discovery": [],
        "documents": docs,
        "metadata": {},
    }
    manifest_path = repo / ".docforge" / "manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    for doc in docs:
        target = repo / doc["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(markdown_with_provenance(doc["provenance"], bodies[doc["id"]]), encoding="utf-8")


class DashboardMetadataTests(unittest.TestCase):
    def test_reconcile_adds_id_title_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outputs = []
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                seed_repo(repo)
                result = run_dashboard(runtime, "metadata", "--repo", str(repo))
                self.assertEqual(result.returncode, 0, result.stderr)
                text = (repo / "docs" / "product" / "overview.md").read_text(encoding="utf-8")
                self.assertTrue(text.startswith('---\nid: "product_overview"\n'))
                self.assertIn('title: "Product Overview"', text)
                self.assertIn('# Overview\n\nBody.\n', text)
                second = run_dashboard(runtime, "metadata", "--repo", str(repo))
                self.assertEqual(second.returncode, 0, second.stderr)
                self.assertIn("reconciled: 0", second.stdout)
                outputs.append(normalized(result.stdout, [repo]))
            self.assertEqual(outputs[0], outputs[1])

    def test_reconcile_fixes_provenance_doc_id_and_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            target = repo / "docs" / "architecture" / "constraints.md"
            text = target.read_text(encoding="utf-8")
            text = text.replace('doc_id: "architecture_constraints"', 'doc_id: "stale_id"')
            text = text.replace('path: "docs/architecture/constraints.md"', 'path: "docs/architecture/stale.md"')
            target.write_text(text, encoding="utf-8")
            result = run_dashboard("py", "metadata", "--repo", str(repo), "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            fixed = [row for row in json.loads(result.stdout)["reconciled"] if row["doc"] == "architecture_constraints"]
            self.assertEqual(fixed[0]["fixed"], ["id", "title", "provenance.doc_id", "provenance.path"])
            fresh = target.read_text(encoding="utf-8")
            self.assertIn('doc_id: "architecture_constraints"', fresh)
            self.assertIn('path: "docs/architecture/constraints.md"', fresh)


class DashboardPlanTests(unittest.TestCase):
    def test_route_plan_readme_becomes_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            for runtime in ("py", "js"):
                result = run_dashboard(runtime, "plan", "--repo", str(repo), "--json")
                self.assertEqual(result.returncode, 0, result.stderr)
                plan = json.loads(result.stdout)
                by_path = {page["source_path"]: page for page in plan["pages"]}
                self.assertEqual(by_path["docs/README.md"]["url"], "/docs")
                self.assertEqual(by_path["docs/README.md"]["output_path"], "index.mdx")
                self.assertEqual(by_path["docs/architecture/constraints.md"]["url"], "/docs/architecture/constraints")
                self.assertEqual(by_path["docs/architecture/constraints.md"]["output_path"], "architecture/constraints.mdx")
                self.assertEqual(plan["problems"], [])

    def test_duplicate_url_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            manifest = load_manifest(repo)
            manifest["documents"].append(written_doc("collision_a", "docs/architecture.md", "# Architecture\n"))
            manifest["documents"].append(written_doc("collision_b", "docs/architecture/README.md", "# Architecture\n"))
            (repo / "docs" / "architecture.md").write_text(
                markdown_with_provenance(manifest["documents"][-2]["provenance"], "# Architecture\n"),
                encoding="utf-8",
            )
            (repo / "docs" / "architecture" / "README.md").write_text(
                markdown_with_provenance(manifest["documents"][-1]["provenance"], "# Architecture\n"),
                encoding="utf-8",
            )
            (repo / ".docforge" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            for runtime in ("py", "js"):
                result = run_dashboard(runtime, "plan", "--repo", str(repo), "--json")
                self.assertEqual(result.returncode, 1)
                plan = json.loads(result.stdout)
                self.assertTrue(any("duplicate url" in problem for problem in plan["problems"]))

    def test_root_level_documents_route_under_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            manifest = load_manifest(repo)
            manifest["documents"].append(written_doc("changelog", "CHANGELOG.md", "# Changelog\n", write_order=5))
            manifest["documents"].append(written_doc("root_readme", "README.md", "# Root Readme\n", write_order=6))
            (repo / ".docforge" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            (repo / "CHANGELOG.md").write_text(
                markdown_with_provenance(manifest["documents"][-2]["provenance"], "# Changelog\n"),
                encoding="utf-8",
            )
            (repo / "README.md").write_text(
                markdown_with_provenance(manifest["documents"][-1]["provenance"], "# Root Readme\n"),
                encoding="utf-8",
            )
            for runtime in ("py", "js"):
                result = run_dashboard(runtime, "plan", "--repo", str(repo), "--json")
                self.assertEqual(result.returncode, 0, result.stderr)
                plan = json.loads(result.stdout)
                by_path = {page["source_path"]: page for page in plan["pages"]}
                self.assertEqual(by_path["CHANGELOG.md"]["url"], "/docs/root/changelog")
                self.assertEqual(by_path["CHANGELOG.md"]["output_path"], "root/changelog.mdx")
                self.assertEqual(by_path["README.md"]["url"], "/docs/root/readme")
                self.assertEqual(by_path["README.md"]["output_path"], "root/readme.mdx")
                self.assertEqual(plan["problems"], [])

    def test_root_level_documents_without_provenance_are_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            manifest = load_manifest(repo)
            local_shim = written_doc("claude_local", "CLAUDE.local.md", "# Local\n", write_order=7)
            manifest["documents"].append(local_shim)
            (repo / ".docforge" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            (repo / "CLAUDE.local.md").write_text("# Local preferences\n", encoding="utf-8")
            for runtime in ("py", "js"):
                result = run_dashboard(runtime, "plan", "--repo", str(repo), "--json")
                self.assertEqual(result.returncode, 0, result.stderr)
                plan = json.loads(result.stdout)
                by_path = {page["source_path"]: page for page in plan["pages"]}
                self.assertNotIn("CLAUDE.local.md", by_path)
                build = run_dashboard(runtime, "build", "--repo", str(repo), "--skip-install")
                self.assertEqual(build.returncode, 0, build.stderr)
                self.assertFalse((repo / ".docforge" / "dashboard" / "content" / "docs" / "root" / "claude.local.mdx").exists())


class DashboardFingerprintTests(unittest.TestCase):
    def test_fingerprint_parity_and_sensitivity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            manifest = load_manifest(repo)
            changelog = written_doc("changelog", "CHANGELOG.md", "# Changelog\n", write_order=5)
            manifest["documents"].append(changelog)
            (repo / ".docforge" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            (repo / "CHANGELOG.md").write_text(
                markdown_with_provenance(changelog["provenance"], "# Changelog\n"),
                encoding="utf-8",
            )
            py = run_dashboard("py", "fingerprint", "--repo", str(repo)).stdout.strip()
            js = run_dashboard("js", "fingerprint", "--repo", str(repo)).stdout.strip()
            self.assertEqual(py, js)
            before = py
            (repo / "CHANGELOG.md").write_text(
                markdown_with_provenance(changelog["provenance"], "# Changelog\n\nNew entry.\n"),
                encoding="utf-8",
            )
            py_after = run_dashboard("py", "fingerprint", "--repo", str(repo)).stdout.strip()
            self.assertNotEqual(before, py_after)


class DashboardServerTests(unittest.TestCase):
    def test_serve_stays_attached_and_signals_stop_server(self) -> None:
        fake_npm = """#!/usr/bin/env python3
import http.server
import sys

port = int(sys.argv[sys.argv.index("-p") + 1])

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, _format, *_args):
        pass

http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            npm = bin_dir / "npm"
            npm.write_text(fake_npm, encoding="utf-8")
            npm.chmod(0o755)
            env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ.get("PATH", ""))

            for runtime in ("py", "js"):
                for stop_signal in (signal.SIGINT, signal.SIGTSTP):
                    with self.subTest(runtime=runtime, signal=stop_signal):
                        dashboard = root / f"dashboard-{runtime}-{stop_signal}"
                        dashboard.mkdir()
                        command = (
                            [sys.executable, str(DASH_CLI_PY / "dashboard.py")]
                            if runtime == "py"
                            else ["node", str(DASH_CLI_JS / "dashboard.js")]
                        )
                        proc = subprocess.Popen(
                            command + ["serve", "--dashboard", str(dashboard)],
                            cwd=ROOT,
                            text=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            env=env,
                        )
                        state_path = dashboard / ".docforge-dashboard.json"

                        def running() -> bool:
                            if not state_path.is_file():
                                return False
                            state = json.loads(state_path.read_text(encoding="utf-8"))
                            return isinstance(state.get("url"), str) and url_responds(state["url"])

                        self.assertTrue(wait_until(running), "dashboard server did not start")
                        state = json.loads(state_path.read_text(encoding="utf-8"))
                        url = state["url"]
                        self.assertIsNone(proc.poll(), "serve command exited instead of staying attached")
                        os.kill(proc.pid, stop_signal)
                        stdout, stderr = proc.communicate(timeout=10)
                        self.assertEqual(proc.returncode, 128 + stop_signal, stderr)
                        self.assertIn("dashboard server stopped", stdout)
                        stopped_state = json.loads(state_path.read_text(encoding="utf-8"))
                        self.assertNotIn("pid", stopped_state)
                        self.assertNotIn("port", stopped_state)
                        self.assertNotIn("url", stopped_state)
                        self.assertTrue(wait_until(lambda: not url_responds(url)), "server port remained open")


class DashboardBuildTests(unittest.TestCase):
    def test_build_converts_escapes_and_rewrites_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            for runtime in ("py", "js"):
                result = run_dashboard(runtime, "build", "--repo", str(repo), "--skip-install")
                self.assertEqual(result.returncode, 0, result.stderr)
                output = repo / ".docforge" / "dashboard" / "content" / "docs" / "architecture" / "constraints.mdx"
                text = output.read_text(encoding="utf-8")
                self.assertTrue(text.startswith('---\nid: "architecture_constraints"\n'))
                self.assertIn('title: "Constraints"', text)
                self.assertIn("Owner is &lt;TEAM_OWNER&gt;", text)
                self.assertIn("&#123;stay&#125;", text)
                self.assertIn("const x = '<TEAM_OWNER> {not escaped}';", text)
                self.assertIn("[the index](/docs#documentation)", text)
                self.assertIn("```mermaid", text)
                self.assertIn("| Area | Limit |", text)
                self.assertIn("| Latency | &lt;100 ms |", text)
                index = repo / ".docforge" / "dashboard" / "content" / "docs" / "index.mdx"
                self.assertIn('title: "Documentation"', index.read_text(encoding="utf-8"))
                root_meta = json.loads((repo / ".docforge" / "dashboard" / "content" / "docs" / "meta.json").read_text(encoding="utf-8"))
                self.assertEqual(root_meta["title"], "Documentation")
                validate = run_dashboard(runtime, "validate", "--repo", str(repo))
                self.assertEqual(validate.returncode, 0, validate.stdout)

    def test_build_rewrites_links_to_root_level_documents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            manifest = load_manifest(repo)
            changelog = written_doc("changelog", "CHANGELOG.md", "# Changelog\n", write_order=5)
            root_readme = written_doc("root_readme", "README.md", "# Root Readme\n", write_order=6)
            manifest["documents"].extend([changelog, root_readme])
            (repo / ".docforge" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            (repo / "CHANGELOG.md").write_text(
                markdown_with_provenance(changelog["provenance"], "# Changelog\n\nSee [docs](docs/README.md).\n"),
                encoding="utf-8",
            )
            (repo / "README.md").write_text(
                markdown_with_provenance(root_readme["provenance"], "# Root Readme\n\n## Documentation\n\nSee [changelog](CHANGELOG.md).\n"),
                encoding="utf-8",
            )
            index = repo / "docs" / "README.md"
            index.write_text(
                index.read_text(encoding="utf-8").replace(
                    "See [architecture/](architecture/README.md) and [product/overview.md](product/overview.md).",
                    "See [architecture/](architecture/README.md), [CHANGELOG.md](../CHANGELOG.md) and [docs](../README.md#documentation).",
                ),
                encoding="utf-8",
            )
            for runtime in ("py", "js"):
                result = run_dashboard(runtime, "build", "--repo", str(repo), "--skip-install")
                self.assertEqual(result.returncode, 0, result.stderr)
                index_mdx = repo / ".docforge" / "dashboard" / "content" / "docs" / "index.mdx"
                text = index_mdx.read_text(encoding="utf-8")
                self.assertIn("[CHANGELOG.md](/docs/root/changelog)", text)
                self.assertIn("[docs](/docs/root/readme#documentation)", text)
                changelog_mdx = repo / ".docforge" / "dashboard" / "content" / "docs" / "root" / "changelog.mdx"
                self.assertTrue(changelog_mdx.is_file())
                self.assertIn("[docs](/docs)", changelog_mdx.read_text(encoding="utf-8"))
                readme_mdx = repo / ".docforge" / "dashboard" / "content" / "docs" / "root" / "readme.mdx"
                self.assertTrue(readme_mdx.is_file())
                self.assertIn("[changelog](/docs/root/changelog)", readme_mdx.read_text(encoding="utf-8"))
                validate = run_dashboard(runtime, "validate", "--repo", str(repo))
                self.assertEqual(validate.returncode, 0, validate.stdout)

    def test_meta_order_follows_write_order_not_alphabet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            manifest = load_manifest(repo)
            additions = [
                written_doc("zeta_index", "docs/zeta/README.md", "# Zeta\n", write_order=5),
                written_doc("alpha_index", "docs/alpha/README.md", "# Alpha\n", write_order=90),
                written_doc("mm_one", "docs/mm-one.md", "# Mm\n", write_order=40),
                written_doc("aa_two", "docs/aa-two.md", "# Aa\n", write_order=70),
            ]
            manifest["documents"].extend(additions)
            (repo / ".docforge" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            for doc in additions:
                target = repo / doc["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(markdown_with_provenance(doc["provenance"], "# Title\n"), encoding="utf-8")
            for runtime in ("py", "js"):
                result = run_dashboard(runtime, "build", "--repo", str(repo), "--skip-install")
                self.assertEqual(result.returncode, 0, result.stderr)
                meta = json.loads((repo / ".docforge" / "dashboard" / "content" / "docs" / "meta.json").read_text(encoding="utf-8"))
                self.assertEqual(
                    meta["pages"],
                    ["index", "zeta", "architecture", "product", "mm-one", "aa-two", "alpha"],
                )

    def test_root_folder_is_named_others_and_sorts_last(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            manifest = load_manifest(repo)
            changelog = written_doc("changelog", "CHANGELOG.md", "# Changelog\n", write_order=5)
            root_readme = written_doc("root_readme", "README.md", "# Root Readme\n", write_order=6)
            manifest["documents"].extend([changelog, root_readme])
            (repo / ".docforge" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            for doc in (changelog, root_readme):
                (repo / doc["path"]).write_text(
                    markdown_with_provenance(doc["provenance"], f"# {doc['id']}\n"),
                    encoding="utf-8",
                )
            for runtime in ("py", "js"):
                result = run_dashboard(runtime, "build", "--repo", str(repo), "--skip-install")
                self.assertEqual(result.returncode, 0, result.stderr)
                root_meta = json.loads(
                    (repo / ".docforge" / "dashboard" / "content" / "docs" / "root" / "meta.json").read_text(encoding="utf-8")
                )
                self.assertEqual(root_meta["title"], "Others")
                top_meta = json.loads(
                    (repo / ".docforge" / "dashboard" / "content" / "docs" / "meta.json").read_text(encoding="utf-8")
                )
                self.assertEqual(top_meta["pages"][-1], "root")

    def test_build_fast_path_does_not_rewrite_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            first = run_dashboard("py", "build", "--repo", str(repo), "--skip-install")
            self.assertEqual(first.returncode, 0, first.stderr)
            output = repo / ".docforge" / "dashboard" / "content" / "docs" / "index.mdx"
            before = output.read_text(encoding="utf-8")
            second = run_dashboard("py", "build", "--repo", str(repo), "--skip-install")
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn("fingerprint unchanged", second.stdout)
            self.assertEqual(output.read_text(encoding="utf-8"), before)

    def test_template_signature_credits_docforge_and_fumadocs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            run_dashboard("py", "build", "--repo", str(repo), "--skip-install")
            layout = (repo / ".docforge" / "dashboard" / "app" / "docs" / "layout.tsx").read_text(encoding="utf-8")
            self.assertIn("Documentation generated by", layout)
            self.assertIn("https://github.com/jonaskahn/docforge", layout)
            self.assertIn("UI by", layout)
            self.assertIn("https://www.fumadocs.dev/", layout)

    def test_bauhaus_theme_applied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            run_dashboard("py", "build", "--repo", str(repo), "--skip-install")
            css = (repo / ".docforge" / "dashboard" / "app" / "global.css").read_text(encoding="utf-8")
            self.assertIn("#e30613", css)
            self.assertIn("--color-fd-primary: #e30613", css)
            self.assertIn("--color-fd-background: #0a0a0a", css)
            self.assertIn("--color-fd-background: #ffffff", css)
            self.assertIn('"Avenir Next"', css)
            self.assertIn("--radius-lg: 2px", css)
            self.assertIn("font-variant-numeric: tabular-nums", css)

    def test_build_generates_dashboard_gitignore_rule(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            run_dashboard("py", "build", "--repo", str(repo), "--skip-install")
            gitignore = (repo / ".docforge" / ".gitignore").read_text(encoding="utf-8")
            self.assertIn("dashboard/", gitignore)
            self.assertTrue((repo / ".docforge" / "dashboard" / "package.json").is_file())
            self.assertTrue((repo / ".docforge" / "dashboard" / "lib" / "shared.ts").is_file())

    def test_template_nav_title_links_to_docs_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            run_dashboard("py", "build", "--repo", str(repo), "--skip-install")
            shared = (repo / ".docforge" / "dashboard" / "lib" / "shared.ts").read_text(encoding="utf-8")
            self.assertIn("docsRoute = '/docs'", shared)
            layout = (repo / ".docforge" / "dashboard" / "lib" / "layout.shared.tsx").read_text(encoding="utf-8")
            self.assertIn("docsRoute", layout)
            self.assertIn("url: docsRoute", layout)


class DashboardValidateTests(unittest.TestCase):
    def test_validate_reports_broken_links_and_missing_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            run_dashboard("py", "build", "--repo", str(repo), "--skip-install")
            content = repo / ".docforge" / "dashboard" / "content" / "docs" / "architecture" / "constraints.mdx"
            text = content.read_text(encoding="utf-8")
            content.write_text(
                text.replace("[the index](/docs#documentation)", "[one](/docs/nope) and [two](/docs#missing)"),
                encoding="utf-8",
            )
            for runtime in ("py", "js"):
                result = run_dashboard(runtime, "validate", "--repo", str(repo), "--json")
                self.assertEqual(result.returncode, 1)
                report = json.loads(result.stdout)
                self.assertFalse(report["ok"])
                self.assertTrue(any("broken link" in error for error in report["errors"]))
                self.assertTrue(any("broken anchor" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
