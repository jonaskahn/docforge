"""Dashboard: metadata reconciliation, signatures, staged build, serving,
static export, and stop.

The public CLI is `dashboard start` (reconcile -> build-if-changed -> serve ->
open), `export` (reconcile -> build-if-changed -> `next build` into `out/`),
`status`, and `stop`; plan, validation, and fingerprints are internal
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
    normalized_blob_hash,
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
from pathlib import Path

args = sys.argv[1:]
prefix = Path(args[args.index("--prefix") + 1])

if "install" in args or "ci" in args:
    (prefix / "node_modules").mkdir(parents=True, exist_ok=True)
    (prefix / "package-lock.json").write_text("{}", encoding="utf-8")
    sys.exit(0)

port = int(args[args.index("-p") + 1])

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, _format, *_args):
        pass

http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
"""


EXPORT_NPM = """#!/usr/bin/env python3
import sys
from pathlib import Path

args = sys.argv[1:]
prefix = Path(args[args.index("--prefix") + 1])

if "install" in args or "ci" in args:
    (prefix / "node_modules").mkdir(parents=True, exist_ok=True)
    (prefix / "package-lock.json").write_text("{}", encoding="utf-8")
    sys.exit(0)

if "build" not in args:
    sys.exit(1)
out = prefix / "out"
out.mkdir(parents=True, exist_ok=True)
count_file = out / ".build-count"
count = int(count_file.read_text(encoding="utf-8")) if count_file.is_file() else 0
count += 1
count_file.write_text(str(count), encoding="utf-8")
index = out / "docs" / "index.html"
index.parent.mkdir(parents=True, exist_ok=True)
index.write_text(f"<html>export {count}</html>", encoding="utf-8")
nested = out / "docs" / "architecture" / "constraints" / "index.html"
nested.parent.mkdir(parents=True, exist_ok=True)
nested.write_text(f"<html>nested {count}</html>", encoding="utf-8")
"""


def fake_npm_export_env() -> tuple[dict[str, str], Path]:
    """Fake `npm run build`: writes `out/docs/index.html` and records how many
    times the export build actually ran."""
    root = Path(tempfile.mkdtemp(prefix="docforge-fake-npm-export-"))
    bin_dir = root / "bin"
    bin_dir.mkdir()
    npm = bin_dir / "npm"
    npm.write_text(EXPORT_NPM, encoding="utf-8")
    npm.chmod(0o755)
    env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ.get("PATH", ""))
    return env, root


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


def written_doc(doc_id: str, path: str, body: str, write_order: int = 10, nav_order: int | None = None) -> dict:
    value = provenance(
        doc_id=doc_id,
        path=path,
        tier="spine",
        target_depth="orientation",
        section_id="main",
        source_path="src/main.ts",
        source_blob=blob_hash(b"evidence"),
    )
    document = {
        "id": doc_id,
        "title": doc_id.replace("_", " ").title(),
        "description": f"Fixture description for {doc_id.replace('_', ' ')}.",
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
    if nav_order is not None:
        document["nav_order"] = nav_order
    return document


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
        "version": "3.2",
        "generated_at": "2026-08-01T00:00:00Z",
        "project": {
            "name": "fixture", "root": str(repo), "tier": "spine",
            "provenance_storage": "markdown", "profiles": {},
        },
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
                    result = run_dashboard(runtime, "start", "--repo", str(repo), "--no-open", env=env)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    text = (repo / "docs" / "product" / "overview.md").read_text(encoding="utf-8")
                    self.assertTrue(text.startswith('---\nid: "product_overview"\n'))
                    self.assertIn('title: "Product Overview"', text)
                    self.assertIn('description: "Fixture description for product overview."', text)
                    self.assertIn('# Overview\n\nBody.\n', text)
                    self.assertIn("converted 3 documents", result.stdout)
                    second = run_dashboard(runtime, "start", "--repo", str(repo), "--no-open", env=env)
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


class DashboardNavigationTests(unittest.TestCase):
    def test_nav_order_drives_sidebar_meta_ordering(self) -> None:
        env, _bin = fake_npm_env()
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                seed_repo(repo)
                manifest = load_manifest(repo)
                additions = [
                    ("product_index", "docs/product/README.md", "# Product\n", 19, 10),
                    ("architecture_index", "docs/architecture/README.md", "# Architecture\n", 9, 20),
                    ("flows_index", "docs/flows/README.md", "# Flows\n", 21, 30),
                    ("concepts_index", "docs/architecture/concepts/README.md", "# Concepts\n", 15, 25),
                    ("concept_dedup", "docs/architecture/concepts/dedup.md", "# Dedup\n", 18, 26),
                    ("changelog", "CHANGELOG.md", "# Changelog\n", 5, None),
                ]
                paired = [(written_doc(doc_id, path, body, write_order=wo, nav_order=nav), body) for doc_id, path, body, wo, nav in additions]
                manifest["documents"].extend(doc for doc, _ in paired)
                for doc in manifest["documents"]:
                    if doc["id"] == "architecture_constraints":
                        doc["nav_order"] = 30
                (repo / ".docforge" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
                for doc, body in paired:
                    target = repo / doc["path"]
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(markdown_with_provenance(doc["provenance"], body), encoding="utf-8")
                try:
                    result = run_dashboard(runtime, "start", "--repo", str(repo), "--no-open", env=env)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    content = repo / ".docforge" / "dashboard" / "content" / "docs"
                    root_meta = json.loads((content / "meta.json").read_text(encoding="utf-8"))
                    self.assertEqual(root_meta["title"], "Documentation")
                    self.assertEqual(root_meta["pages"], ["index", "product", "architecture", "flows", "root"])
                    arch_meta = json.loads((content / "architecture" / "meta.json").read_text(encoding="utf-8"))
                    self.assertEqual(arch_meta["title"], "Architecture")
                    self.assertEqual(arch_meta["pages"], ["index", "concepts", "constraints"])
                    concepts_meta = json.loads((content / "architecture" / "concepts" / "meta.json").read_text(encoding="utf-8"))
                    self.assertEqual(concepts_meta["pages"], ["index", "dedup"])
                    root_meta = json.loads((content / "root" / "meta.json").read_text(encoding="utf-8"))
                    self.assertEqual(root_meta["title"], "Project")
                    self.assertEqual(root_meta["pages"], ["changelog"])
                finally:
                    stop_dashboard(runtime, repo)

    def test_nav_order_falls_back_to_write_order(self) -> None:
        env, _bin = fake_npm_env()
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                seed_repo(repo)
                manifest = load_manifest(repo)
                manifest["documents"].append(written_doc("product_index", "docs/product/README.md", "# Product\n", write_order=19))
                (repo / ".docforge" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
                (repo / "docs" / "product" / "README.md").write_text(
                    markdown_with_provenance(manifest["documents"][-1]["provenance"], "# Product\n"),
                    encoding="utf-8",
                )
                try:
                    result = run_dashboard(runtime, "start", "--repo", str(repo), "--no-open", env=env)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    content = repo / ".docforge" / "dashboard" / "content" / "docs"
                    root_meta = json.loads((content / "meta.json").read_text(encoding="utf-8"))
                    # no nav_order: architecture (9) sorts before product (19)
                    self.assertEqual(root_meta["pages"], ["index", "architecture", "product"])
                finally:
                    stop_dashboard(runtime, repo)

    def test_dashboard_excludes_claude_local_from_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            manifest = load_manifest(repo)
            manifest["documents"].append(written_doc("changelog", "CHANGELOG.md", "# Changelog\n", write_order=5))
            manifest["documents"].append(written_doc("claude_local", "CLAUDE.local.md", "# Local\n", write_order=202))
            (repo / ".docforge" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            (repo / "CHANGELOG.md").write_text(
                markdown_with_provenance(manifest["documents"][-2]["provenance"], "# Changelog\n"),
                encoding="utf-8",
            )
            (repo / "CLAUDE.local.md").write_text(
                markdown_with_provenance(manifest["documents"][-1]["provenance"], "# Local\n"),
                encoding="utf-8",
            )
            for runtime in ("py", "js"):
                result = run_dashboard(runtime, "start", "--repo", str(repo), "--plan-only")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("/docs/root/claude.local", result.stdout)
                self.assertIn("-> /docs/root/changelog", result.stdout)
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
                    result = run_dashboard(runtime, "start", "--repo", str(repo), "--no-open", env=env)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    output = repo / ".docforge" / "dashboard" / "content" / "docs" / "architecture" / "constraints.mdx"
                    text = output.read_text(encoding="utf-8")
                    self.assertTrue(text.startswith('---\nid: "architecture_constraints"\n'))
                    self.assertIn('title: "Constraints"', text)
                    self.assertIn('description: "Fixture description for architecture constraints."', text)
                    self.assertNotIn("docforge_provenance:", text)
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
                    result = run_dashboard(runtime, "start", "--repo", str(repo), "--no-open", env=env)
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
            "generator": {"name": "docforge", "version": "2.17.0"},
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
                    result = run_dashboard(runtime, "start", "--repo", str(repo), "--no-open", env=env)
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
        # Broken internal links are `broken_link` scan findings, always
        # blocking: `start` now short-circuits on the scan result before
        # ever attempting a build, so this fails fast via scan, not via a
        # convert/validate crash.
        env, _bin = fake_npm_env()
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
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
                    result = run_dashboard(runtime, "start", "--repo", str(repo), "--no-open", env=env)
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    self.assertIn("[broken_link] (blocking)", result.stdout + result.stderr)
                    self.assertIn("scan found blocking problems", result.stdout + result.stderr)
                    self.assertIn("dashboard was NOT opened", result.stdout + result.stderr)
                    self.assertIn("/docforge-revise", result.stdout + result.stderr)
                finally:
                    stop_dashboard(runtime, repo)

    def test_start_force_rebuilds_even_when_unchanged(self) -> None:
        env, _bin = fake_npm_env()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            try:
                first = run_dashboard("py", "start", "--repo", str(repo), "--no-open", env=env)
                self.assertEqual(first.returncode, 0, first.stderr)
                self.assertIn("converted 3 documents", first.stdout)
                unchanged = run_dashboard("py", "start", "--repo", str(repo), "--no-open", env=env)
                self.assertEqual(unchanged.returncode, 0, unchanged.stderr)
                self.assertIn("signature unchanged", unchanged.stdout)
                forced = run_dashboard("py", "start", "--repo", str(repo), "--force", "--no-open", env=env)
                self.assertEqual(forced.returncode, 0, forced.stderr)
                self.assertIn("converted 3 documents", forced.stdout)
            finally:
                stop_dashboard("py", repo)

    def test_failed_conversion_leaves_previous_dashboard_untouched(self) -> None:
        # A doc/*.md doc with no frontmatter is a `metadata` scan finding,
        # blocking because the doc is included: `start` short-circuits on
        # scan before staging anything, so `.staging` is never even created.
        env, _bin = fake_npm_env()
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                seed_repo(repo)
                try:
                    first = run_dashboard(runtime, "start", "--repo", str(repo), "--no-open", env=env)
                    self.assertEqual(first.returncode, 0, first.stderr)
                    index = repo / ".docforge" / "dashboard" / "content" / "docs" / "index.mdx"
                    self.assertTrue(index.is_file())
                    (repo / "docs" / "product" / "overview.md").write_text("# Broken\n\nNo frontmatter.\n", encoding="utf-8")
                    broken = run_dashboard(runtime, "start", "--repo", str(repo), "--no-open", env=env)
                    self.assertEqual(broken.returncode, 1)
                    self.assertIn("[metadata] (blocking)", broken.stdout + broken.stderr)
                    self.assertIn("scan found blocking problems", broken.stdout + broken.stderr)
                    self.assertIn("dashboard was NOT opened", broken.stdout + broken.stderr)
                    self.assertIn("/docforge-revise", broken.stdout + broken.stderr)
                    self.assertTrue(index.is_file(), "previous dashboard must survive a failed conversion")
                    self.assertFalse((repo / ".docforge" / "dashboard" / "content" / ".staging").exists())
                finally:
                    stop_dashboard(runtime, repo)


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

    def test_render_signature_changes_when_description_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            before = SIG_RE.search(run_dashboard("py", "start", "--repo", str(repo), "--plan-only").stdout).group(1)
            manifest = load_manifest(repo)
            manifest["documents"][0]["description"] = "A revised reader-facing description."
            (repo / ".docforge" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            after = SIG_RE.search(run_dashboard("py", "start", "--repo", str(repo), "--plan-only").stdout).group(1)
            self.assertNotEqual(before, after)

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
                    result = run_dashboard(runtime, "start", "--repo", str(repo), "--no-open", env=env)
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


class DashboardExportTests(unittest.TestCase):
    def test_export_builds_static_output_and_is_idempotent(self) -> None:
        env, _bin = fake_npm_export_env()
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                seed_repo(repo)
                dashboard = repo / ".docforge" / "dashboard"
                state_path = dashboard / ".docforge-dashboard.json"
                first = run_dashboard(runtime, "export", "--repo", str(repo), env=env)
                self.assertEqual(first.returncode, 0, first.stderr)
                self.assertIn("exported:", first.stdout)
                self.assertIn("converted 3 documents", first.stdout)
                self.assertNotIn("running in the background", first.stdout)
                index = dashboard / "out" / "docs" / "index.html"
                self.assertTrue(index.is_file(), "static export did not emit out/docs/index.html")
                nested = dashboard / "out" / "docs" / "architecture" / "constraints" / "index.html"
                self.assertTrue(nested.is_file(), "static export did not emit out/docs/architecture/constraints/index.html")
                flat = [p.name for p in (dashboard / "out").rglob("*.html") if p.name not in {"index.html"}]
                self.assertEqual(flat, [], f"export emitted flat html files: {flat}")
                self.assertFalse((dashboard / "out" / "docs.html").exists(), "export must not emit docs.html")
                self.assertEqual((dashboard / "out" / ".build-count").read_text(encoding="utf-8"), "1")
                state = json.loads(state_path.read_text(encoding="utf-8"))
                self.assertIn("export_sig", state)
                self.assertIn("exported_at", state)
                self.assertNotIn("pid", state)

                second = run_dashboard(runtime, "export", "--repo", str(repo), env=env)
                self.assertEqual(second.returncode, 0, second.stderr)
                self.assertIn("export up to date:", second.stdout)
                self.assertEqual((dashboard / "out" / ".build-count").read_text(encoding="utf-8"), "1", "export rebuilt when nothing changed")

    def test_export_rebuilds_when_content_changes(self) -> None:
        env, _bin = fake_npm_export_env()
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                seed_repo(repo)
                dashboard = repo / ".docforge" / "dashboard"
                first = run_dashboard(runtime, "export", "--repo", str(repo), env=env)
                self.assertEqual(first.returncode, 0, first.stderr)
                doc = repo / "docs" / "architecture" / "constraints.md"
                doc.write_text(doc.read_text(encoding="utf-8") + "\nUpdated paragraph.\n", encoding="utf-8")
                rerun = run_dashboard(runtime, "export", "--repo", str(repo), env=env)
                self.assertEqual(rerun.returncode, 0, rerun.stderr)
                self.assertIn("exported:", rerun.stdout)
                self.assertEqual((dashboard / "out" / ".build-count").read_text(encoding="utf-8"), "2", "content change did not rebuild the export")

    def test_export_takes_no_extra_params_and_start_rejects_export_flag(self) -> None:
        env, _bin = fake_npm_export_env()
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                seed_repo(repo)
                for extra in (["--force"], ["--plan-only"], ["--port", "4321"]):
                    result = run_dashboard(runtime, "export", "--repo", str(repo), *extra, env=env)
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                legacy = run_dashboard(runtime, "start", "--repo", str(repo), "--export", env=env)
                self.assertEqual(legacy.returncode, 2, legacy.stdout + legacy.stderr)
                self.assertFalse((repo / ".docforge" / "dashboard" / "out").exists())


class DashboardScanTests(unittest.TestCase):
    def test_scan_clean_repo_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                seed_repo(repo)
                src = repo / "src"
                src.mkdir()
                (src / "main.ts").write_bytes(b"evidence")
                result = run_dashboard(runtime, "scan", "--repo", str(repo))
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("0 problems", result.stdout)
                json_result = run_dashboard(runtime, "scan", "--repo", str(repo), "--json")
                self.assertEqual(json_result.returncode, 0, json_result.stderr)
                self.assertEqual(json.loads(json_result.stdout)["problems"], [])

    def test_scan_reports_issues_and_suggests_revision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                seed_repo(repo)
                manifest = load_manifest(repo)
                broken = written_doc("architecture_extras", "docs/architecture/extras.md", "# Extras\n", write_order=8)
                incomplete = written_doc("product_incomplete", "docs/product/incomplete.md", "# Incomplete\n", write_order=20)
                incomplete["status"] = "in_progress"
                drift = written_doc("product_drift", "docs/product/drift.md", "# Drift\n", write_order=21)
                manifest["documents"] += [broken, incomplete, drift]
                (repo / ".docforge" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
                for doc, body in (
                    (broken, "# Extras\n\nSee [missing](../missing.md).\n"),
                    (incomplete, "# Incomplete\n"),
                    (drift, "# Drift\n"),
                ):
                    target = repo / doc["path"]
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(markdown_with_provenance(doc["provenance"], body), encoding="utf-8")
                src = repo / "src"
                src.mkdir()
                (src / "main.ts").write_bytes(b"changed after provenance")
                (repo / "docs" / "product" / "overview.md").write_text("# Overview\n\nNo frontmatter.\n", encoding="utf-8")
                (repo / "docs" / "product" / "untracked.md").write_text("# Untracked\n", encoding="utf-8")
                result = run_dashboard(runtime, "scan", "--repo", str(repo))
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("you should revise again", result.stdout)
                for kind in ("broken_link", "incomplete", "drift", "metadata", "untracked"):
                    self.assertIn(f"[{kind}]", result.stdout)
                for kind in ("broken_link", "metadata"):
                    self.assertIn(f"[{kind}] (blocking)", result.stdout)
                for kind in ("incomplete", "drift", "untracked"):
                    self.assertIn(f"[{kind}]", result.stdout)
                    self.assertNotIn(f"[{kind}] (blocking)", result.stdout)
                json_result = run_dashboard(runtime, "scan", "--repo", str(repo), "--json")
                payload = json.loads(json_result.stdout)
                self.assertTrue(payload["blocking"])
                by_kind = {}
                for problem in payload["problems"]:
                    by_kind.setdefault(problem["kind"], []).append(problem["blocking"])
                self.assertTrue(all(by_kind["broken_link"]))
                self.assertTrue(all(by_kind["metadata"]))
                for kind in ("incomplete", "drift", "untracked"):
                    self.assertFalse(any(by_kind[kind]))

    def test_scan_suppresses_cosmetic_only_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                seed_repo(repo)
                src = repo / "src"
                src.mkdir()
                # Keep seed_repo's own 3 documents FRESH (they cite src/main.ts
                # with git_blob = blob_hash(b"evidence") and no normalized hash).
                (src / "main.ts").write_bytes(b"evidence")
                # A separate source, cited by one new document, isolates the
                # cosmetic-drift assertion from the pre-existing fixtures.
                original = b"one\ntwo\n"
                (src / "extra.ts").write_bytes(original)
                value = provenance(
                    doc_id="product_drift", path="docs/product/drift.md", tier="spine",
                    target_depth="orientation", section_id="main",
                    source_path="src/extra.ts", source_blob=blob_hash(original),
                    normalized_blob=normalized_blob_hash(original),
                )
                doc = {
                    "id": "product_drift", "title": "Product Drift",
                    "description": "Fixture description for product drift.",
                    "type": "generic", "path": "docs/product/drift.md", "group": "product",
                    "selection": {"origins": [{"kind": "dynamic", "id": "generic"}], "evidence": []},
                    "status": "generated", "requires": [], "scaffold_template": "unused",
                    "target_depth": "orientation", "write_order": 21,
                    "provenance_mode": "sections", "audit_profile": "standard",
                    "provenance": value, "audit": None,
                }
                manifest = load_manifest(repo)
                manifest["documents"].append(doc)
                (repo / ".docforge" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
                target = repo / doc["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(markdown_with_provenance(value, "# Drift\n"), encoding="utf-8")
                # Whitespace/EOL-only change relative to git_blob; git_blob_normalized still matches.
                (src / "extra.ts").write_bytes(b"one\r\ntwo  \r\n")
                result = run_dashboard(runtime, "scan", "--repo", str(repo))
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertNotIn("[drift]", result.stdout)

    def test_start_reports_scan_findings_before_building(self) -> None:
        # `untracked` is advisory-only (never blocking): `start` still
        # builds and serves, it just prints the finding and the suggestion.
        env, _bin = fake_npm_env()
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                seed_repo(repo)
                (repo / "docs" / "product" / "untracked.md").write_text("# Untracked\n", encoding="utf-8")
                try:
                    result = run_dashboard(runtime, "start", "--repo", str(repo), "--no-open", env=env)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn("you should revise again", result.stdout)
                    self.assertIn("[untracked]", result.stdout)
                    self.assertNotIn("[untracked] (blocking)", result.stdout)
                    self.assertIn("converted 3 documents", result.stdout)
                finally:
                    stop_dashboard(runtime, repo)


if __name__ == "__main__":
    unittest.main()
