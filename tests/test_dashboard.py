"""Dashboard: metadata reconciliation, signatures, staged build, serving, and stop.

The public CLI is `dashboard start` (reconcile -> build-if-changed -> serve ->
open), `status`, and `stop`; plan, validation, and fingerprints are internal
stages covered here through `start --plan-only` and `start` output.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
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
    provenance,
)

DASH_CLI_PY = ROOT / "skills" / "docforge" / "_shared" / "runtime" / "cli" / "python"
DASH_CLI_JS = ROOT / "skills" / "docforge" / "_shared" / "runtime" / "cli" / "js"


def run_dashboard(
    runtime: str,
    *args: str,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    command = (
        ["python3", str(DASH_CLI_PY / "dashboard.py")]
        if runtime == "py"
        else ["node", str(DASH_CLI_JS / "dashboard.js")]
    )
    return subprocess.run(command + list(args), cwd=ROOT, text=True, capture_output=True, env=env)


def stop_dashboard(runtime: str, repo: Path) -> None:
    run_dashboard(runtime, "stop", "--repo", str(repo))


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


FAKE_NPM = """#!/usr/bin/env python3
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


def fake_npm_env() -> tuple[dict[str, str], Path]:
    root = Path(tempfile.mkdtemp(prefix="docforge-fake-npm-"))
    bin_dir = root / "bin"
    bin_dir.mkdir()
    npm = bin_dir / "npm"
    npm.write_text(FAKE_NPM, encoding="utf-8")
    npm.chmod(0o755)
    env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ.get("PATH", ""))
    return env, root


INDEX_BODY = """# Documentation

## Introduction

See [constraints](architecture/constraints.md) and [product/overview.md](product/overview.md).

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


SIG_RE = re.compile(r"render_sig: ([0-9a-f]{64})")


class DashboardStartTests(unittest.TestCase):
    def test_start_reconciles_metadata_and_is_idempotent(self) -> None:
        env, _bin = fake_npm_env()
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                seed_repo(repo)
                try:
                    result = run_dashboard(runtime, "start", "--repo", str(repo), "--no-open", "--skip-install", env=env)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    text = (repo / "docs" / "product" / "overview.md").read_text(encoding="utf-8")
                    self.assertTrue(text.startswith('---\nid: "product_overview"\n'))
                    self.assertIn('title: "Product Overview"', text)
                    self.assertIn('# Overview\n\nBody.\n', text)
                    self.assertIn("converted 3 documents", result.stdout)
                    second = run_dashboard(runtime, "start", "--repo", str(repo), "--no-open", "--skip-install", env=env)
                    self.assertEqual(second.returncode, 0, second.stderr)
                    self.assertIn("metadata: 0 reconciled, 3 unchanged", second.stdout)
                    self.assertIn("signature unchanged", second.stdout)
                finally:
                    stop_dashboard(runtime, repo)

    def test_start_plan_only_reports_route_plan_and_duplicate_urls(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            result = run_dashboard("py", "start", "--repo", str(repo), "--plan-only")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("3 pages in 3 folders; 0 problems", result.stdout)
            self.assertIn("/docs", result.stdout)
            self.assertIn("render_sig: ", result.stdout)

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
                result = run_dashboard(runtime, "start", "--repo", str(repo), "--plan-only")
                self.assertEqual(result.returncode, 1)
                self.assertTrue(any("duplicate url" in line for line in result.stdout.splitlines()))

    def test_start_plan_only_routes_root_level_documents(self) -> None:
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
                result = run_dashboard(runtime, "start", "--repo", str(repo), "--plan-only")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("-> /docs/root/changelog", result.stdout)
                self.assertIn("-> /docs/root/readme", result.stdout)
                self.assertIn("0 problems", result.stdout)


class DashboardBuildTests(unittest.TestCase):
    def test_start_build_converts_escapes_and_rewrites_links(self) -> None:
        env, _bin = fake_npm_env()
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                seed_repo(repo)
                try:
                    result = run_dashboard(runtime, "start", "--repo", str(repo), "--no-open", "--skip-install", env=env)
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
                finally:
                    stop_dashboard(runtime, repo)

    def test_start_build_strips_html_comments_but_keeps_content(self) -> None:
        env, _bin = fake_npm_env()
        body = (
            "# Glossary\n\n"
            "Intro.\n\n"
            "<!-- docforge-children:start -->\n"
            "| Term | Meaning |\n"
            "| --- | --- |\n"
            "| Foo | Bar |\n"
            "<!-- docforge-children:end -->\n\n"
            "A `<!-- inline -->` stays code.\n\n"
            "```md\n"
            "<!-- keep me in code -->\n"
            "raw\n"
            "```\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                seed_repo(repo)
                manifest = load_manifest(repo)
                doc = written_doc("reference_glossary", "docs/reference/glossary.md", body, write_order=25)
                manifest["documents"].append(doc)
                (repo / ".docforge" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
                target = repo / "docs" / "reference" / "glossary.md"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(markdown_with_provenance(doc["provenance"], body), encoding="utf-8")
                try:
                    result = run_dashboard(runtime, "start", "--repo", str(repo), "--no-open", "--skip-install", env=env)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    text = (repo / ".docforge" / "dashboard" / "content" / "docs" / "reference" / "glossary.mdx").read_text(encoding="utf-8")
                    self.assertIn("| Foo | Bar |", text)
                    self.assertNotIn("docforge-children", text)
                    self.assertNotIn("&lt;!--", text)
                    self.assertIn("`<!-- inline -->`", text)
                    self.assertIn("<!-- keep me in code -->", text)
                    self.assertIn("raw", text)
                finally:
                    stop_dashboard(runtime, repo)

    def test_start_build_renders_manifest_provenance_agents_and_rewrites_link(self) -> None:
        env, _bin = fake_npm_env()
        agents_body = "# Demo Repo\n\nKernel rules.\n"
        agents_provenance = {
            "schema": "2.0",
            "doc_id": "agents_kernel",
            "path": "AGENTS.md",
            "generated_at": "2026-08-01T00:00:00Z",
            "generator": {"name": "docforge", "version": "2.8.0"},
            "tier": "spine",
            "target_depth": "orientation",
            "graph": {"provider": "fixture", "flow": "none"},
            "sections": [],
        }
        agents_doc = {
            "id": "agents_kernel",
            "title": "Agent Kernel",
            "type": "agents-kernel",
            "path": "AGENTS.md",
            "group": "agent-context",
            "selection": {"origins": [{"kind": "static", "id": "agents-kernel"}], "evidence": []},
            "status": "complete",
            "requires": ["code_graph", "manifests"],
            "scaffold_template": "content/agent-context/templates/agents-kernel.md",
            "target_depth": "orientation",
            "write_order": 200,
            "provenance_mode": "manifest",
            "audit_profile": "agents-kernel",
            "provenance": agents_provenance,
            "audit": {"mode": "cold-pass", "verdict": "PASS", "report": ".docforge/audits/agents.md"},
        }
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                seed_repo(repo)
                manifest = load_manifest(repo)
                agents_index = written_doc("agents_index", "docs/agents/README.md", "# Agents\n", write_order=28)
                manifest["documents"].append(agents_doc)
                manifest["documents"].append(agents_index)
                (repo / ".docforge" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
                (repo / "AGENTS.md").write_text(agents_body, encoding="utf-8")
                readme_path = repo / "docs" / "agents" / "README.md"
                readme_path.parent.mkdir(parents=True, exist_ok=True)
                readme_path.write_text(
                    markdown_with_provenance(
                        agents_index["provenance"],
                        "# Agents\n\nKernel lives at [AGENTS.md](../../AGENTS.md).\n",
                    ),
                    encoding="utf-8",
                )
                try:
                    plan = run_dashboard(runtime, "start", "--repo", str(repo), "--plan-only")
                    self.assertEqual(plan.returncode, 0, plan.stderr)
                    self.assertIn("-> /docs/root/agents", plan.stdout)
                    result = run_dashboard(runtime, "start", "--repo", str(repo), "--no-open", "--skip-install", env=env)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    root_page = repo / ".docforge" / "dashboard" / "content" / "docs" / "root" / "agents.mdx"
                    self.assertTrue(root_page.is_file(), "AGENTS.md must render as a dashboard page")
                    self.assertIn('title: "Demo Repo"', root_page.read_text(encoding="utf-8"))
                    agents_index_mdx = repo / ".docforge" / "dashboard" / "content" / "docs" / "agents" / "index.mdx"
                    text = agents_index_mdx.read_text(encoding="utf-8")
                    self.assertIn("](/docs/root/agents)", text)
                    self.assertNotIn("../../AGENTS.md", text)
                finally:
                    stop_dashboard(runtime, repo)

    def test_unresolved_internal_markdown_link_fails_validation(self) -> None:
        env, _bin = fake_npm_env()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            manifest = load_manifest(repo)
            doc = written_doc(
                "architecture_extras", "docs/architecture/extras.md",
                "# Extras\n\nSee [missing](../missing.md).\n", write_order=8,
            )
            manifest["documents"].append(doc)
            (repo / ".docforge" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            (repo / "docs" / "architecture" / "extras.md").write_text(
                markdown_with_provenance(doc["provenance"], "# Extras\n\nSee [missing](../missing.md).\n"),
                encoding="utf-8",
            )
            try:
                result = run_dashboard("py", "start", "--repo", str(repo), "--no-open", "--skip-install", env=env)
                self.assertEqual(result.returncode, 1)
                self.assertIn("unresolved internal link", result.stdout + result.stderr)
                self.assertIn("dashboard was NOT opened", result.stdout + result.stderr)
                self.assertIn("/docforge-revise", result.stdout + result.stderr)
            finally:
                stop_dashboard("py", repo)

    def test_start_force_rebuilds_even_when_unchanged(self) -> None:
        env, _bin = fake_npm_env()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            try:
                first = run_dashboard("py", "start", "--repo", str(repo), "--no-open", "--skip-install", env=env)
                self.assertEqual(first.returncode, 0, first.stderr)
                self.assertIn("converted 3 documents", first.stdout)
                unchanged = run_dashboard("py", "start", "--repo", str(repo), "--no-open", "--skip-install", env=env)
                self.assertEqual(unchanged.returncode, 0, unchanged.stderr)
                self.assertIn("signature unchanged", unchanged.stdout)
                forced = run_dashboard("py", "start", "--repo", str(repo), "--force", "--no-open", "--skip-install", env=env)
                self.assertEqual(forced.returncode, 0, forced.stderr)
                self.assertIn("converted 3 documents", forced.stdout)
            finally:
                stop_dashboard("py", repo)

    def test_failed_conversion_leaves_previous_dashboard_untouched(self) -> None:
        env, _bin = fake_npm_env()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            try:
                first = run_dashboard("py", "start", "--repo", str(repo), "--no-open", "--skip-install", env=env)
                self.assertEqual(first.returncode, 0, first.stderr)
                index = repo / ".docforge" / "dashboard" / "content" / "docs" / "index.mdx"
                self.assertTrue(index.is_file())
                (repo / "docs" / "product" / "overview.md").write_text("# Broken\n\nNo frontmatter.\n", encoding="utf-8")
                broken = run_dashboard("py", "start", "--repo", str(repo), "--no-open", "--skip-install", env=env)
                self.assertEqual(broken.returncode, 1)
                self.assertIn("has no frontmatter", broken.stdout + broken.stderr)
                self.assertIn("dashboard was NOT opened", broken.stdout + broken.stderr)
                self.assertIn("/docforge-revise", broken.stdout + broken.stderr)
                self.assertTrue(index.is_file(), "previous dashboard must survive a failed conversion")
                self.assertFalse((repo / ".docforge" / "dashboard" / "content" / ".staging").exists())
            finally:
                stop_dashboard("py", repo)


class DashboardSignatureTests(unittest.TestCase):
    def test_render_signature_parity_and_sensitivity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            py = run_dashboard("py", "start", "--repo", str(repo), "--plan-only").stdout
            js = run_dashboard("js", "start", "--repo", str(repo), "--plan-only").stdout
            self.assertEqual(SIG_RE.search(py).group(1), SIG_RE.search(js).group(1))
            before = SIG_RE.search(py).group(1)
            (repo / "docs" / "README.md").write_text(
                markdown_with_provenance(load_manifest(repo)["documents"][0]["provenance"], "# Documentation\n\nChanged.\n"),
                encoding="utf-8",
            )
            after = run_dashboard("py", "start", "--repo", str(repo), "--plan-only").stdout
            self.assertNotEqual(before, SIG_RE.search(after).group(1))

    def test_render_signature_ignores_flow_index_and_root_package_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            (repo / ".docforge" / "flow-index.json").write_text('{"version": "1.1"}\n', encoding="utf-8")
            (repo / "package.json").write_text('{"name": "repo"}\n', encoding="utf-8")
            before = SIG_RE.search(run_dashboard("py", "start", "--repo", str(repo), "--plan-only").stdout).group(1)
            (repo / ".docforge" / "flow-index.json").write_text('{"version": "1.1", "extra": true}\n', encoding="utf-8")
            (repo / "package.json").write_text('{"name": "repo", "scripts": {}}\n', encoding="utf-8")
            after = SIG_RE.search(run_dashboard("py", "start", "--repo", str(repo), "--plan-only").stdout).group(1)
            self.assertEqual(before, after)


class DashboardServerTests(unittest.TestCase):
    def test_start_serves_detached_and_stop_shuts_down(self) -> None:
        env, _bin = fake_npm_env()
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                seed_repo(repo)
                dashboard = repo / ".docforge" / "dashboard"
                state_path = dashboard / ".docforge-dashboard.json"
                try:
                    result = run_dashboard(runtime, "start", "--repo", str(repo), "--no-open", "--skip-install", env=env)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn("running in the background", result.stdout)
                    state = json.loads(state_path.read_text(encoding="utf-8"))
                    self.assertTrue(url_responds(state["url"]), "dashboard server did not start")
                    self.assertTrue(wait_until(lambda: url_responds(state["url"])))

                    status = run_dashboard(runtime, "status", "--repo", str(repo), "--json")
                    self.assertEqual(status.returncode, 0, status.stderr)
                    report = json.loads(status.stdout)
                    self.assertTrue(report["server"]["running"])
                    self.assertTrue(report["render_sig"]["match"])
                    self.assertEqual(report["counts"]["included_docs"], 3)

                    stopped = run_dashboard(runtime, "stop", "--repo", str(repo))
                    self.assertEqual(stopped.returncode, 0, stopped.stderr)
                    self.assertIn("stopped: True", stopped.stdout)
                    self.assertTrue(wait_until(lambda: not url_responds(state["url"])), "server port remained open")
                    state = json.loads(state_path.read_text(encoding="utf-8"))
                    self.assertNotIn("pid", state)
                    self.assertNotIn("port", state)
                finally:
                    stop_dashboard(runtime, repo)


if __name__ == "__main__":
    unittest.main()
