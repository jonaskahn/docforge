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
    MANIFEST_VERSION,
    ROOT,
    initialize,
    run,
    blob_hash,
    load_manifest,
    normalized_blob_hash,
    provenance,
    remove_sidecar_entry,
    write_written_doc,
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


# Like FAKE_NPM, but its fake "install" also drops a `node_modules/mermaid`
# marker (satisfying the mandatory gate's own precondition check) and
# overwrites the just-scaffolded `scripts/validate_mermaid.mjs` with a stub
# that always reports every diagram it is handed as invalid -- real
# `mermaid`/`jsdom` are never installed, so this is plumbing-only: it proves
# the gate wires a validator's blocking verdict into an aborted `start`/
# `export`, not that real Mermaid detection works (that needs the opt-in
# slow tier, which runs the real template script for real).
FAKE_NPM_BROKEN_MERMAID = """#!/usr/bin/env python3
import http.server
import sys
from pathlib import Path

args = sys.argv[1:]
prefix = Path(args[args.index("--prefix") + 1])

if "install" in args or "ci" in args:
    (prefix / "node_modules").mkdir(parents=True, exist_ok=True)
    (prefix / "node_modules" / "mermaid").mkdir(parents=True, exist_ok=True)
    (prefix / "package-lock.json").write_text("{}", encoding="utf-8")
    fake_validator = prefix / "scripts" / "validate_mermaid.mjs"
    fake_validator.parent.mkdir(parents=True, exist_ok=True)
    fake_validator.write_text(
        "let raw = '';\\n"
        "for await (const chunk of process.stdin) raw += chunk;\\n"
        "const tasks = JSON.parse(raw || '[]');\\n"
        "process.stdout.write(JSON.stringify(tasks.map("
        "() => ({ ok: false, error: 'fixture: forced failure' }))));\\n",
        encoding="utf-8",
    )
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


def fake_npm_broken_mermaid_env() -> tuple[dict[str, str], Path]:
    root = Path(tempfile.mkdtemp(prefix="docforge-fake-npm-broken-mermaid-"))
    bin_dir = root / "bin"
    bin_dir.mkdir()
    npm = bin_dir / "npm"
    npm.write_text(FAKE_NPM_BROKEN_MERMAID, encoding="utf-8")
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


def written_doc(
    doc_id: str,
    path: str,
    body: str,
    write_order: int = 10,
    nav_order: int | None = None,
    group: str = "architecture",
    doc_type: str = "generic",
    provenance_mode: str = "sections",
) -> dict:
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
        "type": doc_type,
        "path": path,
        "group": group,
        "selection": {"origins": [{"kind": "dynamic", "id": "generic"}], "evidence": []},
        "status": "generated",
        "requires": [],
        "scaffold_template": "unused",
        "target_depth": "orientation",
        "write_order": write_order,
        "provenance_mode": provenance_mode,
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
        "version": MANIFEST_VERSION,
        "generated_at": "2026-08-01T00:00:00Z",
        "project": {
            "name": "fixture", "root": str(repo), "tier": "spine",
            "provenance_storage": "json", "profiles": {},
        },
        "discovery": [],
        "documents": docs,
        "metadata": {},
    }
    manifest_path = repo / ".docforge" / "manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    for doc in docs:
        write_written_doc(repo, doc, bodies[doc["id"]])


SIG_RE = re.compile(r"render_sig: ([0-9a-f]{64})")


def reconcile_report(runtime: str, repo: Path) -> dict:
    """Call `reconcile_metadata` directly in either runtime — the npm-free way
    to exercise the stage on its own."""
    manifest_path = repo / ".docforge" / "manifest.json"
    if runtime == "py":
        from runtime.dashboard.python.dashboard import reconcile_metadata
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return reconcile_metadata(repo, manifest, dry_run=True)
    script = (
        "const d=require(process.argv[1]);const fs=require('fs');"
        "const m=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));"
        "console.log(JSON.stringify(d.reconcileMetadata(process.argv[2],m,true)));"
    )
    result = subprocess.run(
        ["node", "-e", script, str(DASH_CLI_JS / "dashboard.js"), str(repo), str(manifest_path)],
        text=True, capture_output=True, check=True,
    )
    return json.loads(result.stdout)


def mermaid_tasks_report(runtime: str, repo: Path) -> list[dict]:
    """Call `mermaid_tasks` directly in either runtime -- the npm-free way to
    check fence extraction on its own."""
    manifest_path = repo / ".docforge" / "manifest.json"
    if runtime == "py":
        from runtime.dashboard.python.dashboard import mermaid_tasks
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return mermaid_tasks(repo, manifest)
    script = (
        "const d=require(process.argv[1]);const fs=require('fs');"
        "const m=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));"
        "console.log(JSON.stringify(d.mermaidTasks(process.argv[2],m)));"
    )
    result = subprocess.run(
        ["node", "-e", script, str(DASH_CLI_JS / "dashboard.js"), str(repo), str(manifest_path)],
        text=True, capture_output=True, check=True,
    )
    return json.loads(result.stdout)


def mermaid_findings_report(runtime: str, repo: Path, dashboard_dir: Path) -> dict:
    """Call `mermaid_findings` directly against a manually prepared
    `dashboard_dir` (marker `node_modules/mermaid` + a stub validator script)
    -- exercises the subprocess/JSON contract without a real npm install."""
    manifest_path = repo / ".docforge" / "manifest.json"
    if runtime == "py":
        from runtime.dashboard.python.dashboard import mermaid_findings
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return mermaid_findings(repo, manifest, dashboard_dir)
    script = (
        "const d=require(process.argv[1]);const fs=require('fs');"
        "const m=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));"
        "console.log(JSON.stringify(d.mermaidFindings(process.argv[2],m,process.argv[4])));"
    )
    result = subprocess.run(
        ["node", "-e", script, str(DASH_CLI_JS / "dashboard.js"),
         str(repo), str(manifest_path), str(dashboard_dir)],
        text=True, capture_output=True, check=True,
    )
    return json.loads(result.stdout)


def rewrite_with_documents(runtime: str, documents: list[dict], source_path: str, body: str) -> str:
    """Run link projection against a supplied mixed document set."""
    if runtime == "py":
        from runtime.dashboard.python.dashboard import build_ledger, convert_body
        ledger = build_ledger(documents)
        ledger["assets"] = set()
        return convert_body(body, source_path, ledger, set())[0]
    script = (
        "const d=require(process.argv[1]);const fs=require('fs');"
        "const p=JSON.parse(fs.readFileSync(0,'utf8'));"
        "const ledger=d.buildLedger(p.documents);ledger.assets=new Set();"
        "console.log(JSON.stringify(d.convertBody(p.body,p.source_path,ledger,new Set())[0]));"
    )
    result = subprocess.run(
        ["node", "-e", script, str(DASH_CLI_JS / "dashboard.js")],
        input=json.dumps({"documents": documents, "source_path": source_path, "body": body}),
        text=True, capture_output=True, check=True,
    )
    return json.loads(result.stdout)


class DashboardRetiredDocumentTests(unittest.TestCase):
    def test_reconcile_leaves_retired_documents_alone(self) -> None:
        """`retire` moves or deletes the file, so the existence guard usually
        hides retired entries from reconcile. When the file is still on disk —
        restored by hand, or a retire that stopped half way — reconcile must
        still leave an out-of-scope document's metadata untouched, the way
        `plan` and `scaffold_docs --audit` already do."""
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    seed_repo(repo)
                    manifest_path = repo / ".docforge" / "manifest.json"
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    target = next(d for d in manifest["documents"] if d["id"] == "product_overview")
                    target["status"] = "retired"
                    # Drift that reconcile would otherwise "fix" in place.
                    target["title"] = "Renamed After Retirement"
                    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

                    report = reconcile_report(runtime, repo)
                    touched = {
                        entry["doc"]
                        for key in ("reconciled", "unchanged", "skipped", "errors")
                        for entry in report[key]
                    }
                    self.assertNotIn("product_overview", touched)
                    self.assertIn("docs_index", touched)


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
                    source = (repo / "docs" / "product" / "overview.md").read_text(encoding="utf-8")
                    self.assertEqual(source, "# Overview\n\nBody.\n", "the source file must stay frontmatter-free")
                    sidecar = json.loads((repo / ".docforge" / "provenance" / "docs" / "product.json").read_text(encoding="utf-8"))
                    entry = sidecar["files"]["overview.md"]
                    self.assertEqual(entry["id"], "product_overview")
                    self.assertEqual(entry["title"], "Product Overview")
                    self.assertEqual(entry["description"], "Fixture description for product overview.")
                    # The rendered page's own title follows the body's H1
                    # instead — a deliberate, separate mechanism from sidecar
                    # reconcile, unrelated to what this test is checking.
                    page = (repo / ".docforge" / "dashboard" / "content" / "docs" / "product" / "overview.mdx").read_text(encoding="utf-8")
                    self.assertTrue(page.startswith('---\nid: "product_overview"\n'))
                    self.assertIn('title: "Overview"', page)
                    self.assertIn('description: "Fixture description for product overview."', page)
                    self.assertIn('# Overview\n\nBody.\n', page)
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
            (repo / ".docforge" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            write_written_doc(repo, manifest["documents"][-2], "# Architecture\n")
            write_written_doc(repo, manifest["documents"][-1], "# Architecture\n")
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
            write_written_doc(repo, manifest["documents"][-2], "# Changelog\n")
            write_written_doc(repo, manifest["documents"][-1], "# Root Readme\n")
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
                    write_written_doc(repo, doc, body)
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
                write_written_doc(repo, manifest["documents"][-1], "# Product\n")
                try:
                    result = run_dashboard(runtime, "start", "--repo", str(repo), "--no-open", env=env)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    content = repo / ".docforge" / "dashboard" / "content" / "docs"
                    root_meta = json.loads((content / "meta.json").read_text(encoding="utf-8"))
                    # no nav_order: architecture (9) sorts before product (19)
                    self.assertEqual(root_meta["pages"], ["index", "architecture", "product"])
                finally:
                    stop_dashboard(runtime, repo)

    def test_dashboard_excludes_agent_context_from_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            manifest = load_manifest(repo)
            manifest["documents"].append(written_doc("changelog", "CHANGELOG.md", "# Changelog\n", write_order=5))
            manifest["documents"].append(written_doc(
                "claude_local", "CLAUDE.local.md", "# Local\n", write_order=202,
                group="agent-context", doc_type="fixed-shim", provenance_mode="manifest",
            ))
            (repo / ".docforge" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            write_written_doc(repo, manifest["documents"][-2], "# Changelog\n")
            write_written_doc(repo, manifest["documents"][-1], "# Local\n")
            for runtime in ("py", "js"):
                result = run_dashboard(runtime, "start", "--repo", str(repo), "--plan-only")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("claude_local", result.stdout)
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
                write_written_doc(repo, doc, body)
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

    def test_start_build_excludes_agent_context_from_mixed_tree(self) -> None:
        env, _bin = fake_npm_env()
        agent_specs = [
            ("agents_kernel", "AGENTS.md", "agents-kernel", "# Demo Repo\n\nKernel rules.\n", "manifest"),
            ("claude_shim", "CLAUDE.md", "agents-kernel", "# Claude\n\nAgent shim.\n", "manifest"),
            ("claude_local", "CLAUDE.local.md", "fixed-shim", "# Local\n\nPreferences.\n", "manifest"),
            ("claude_settings", ".claude/settings.json", "machine-config", "{}\n", "manifest"),
            (
                "agents_index", "docs/agents/README.md", "folder-index",
                "# Agents\n\nKernel lives at [AGENTS.md](../../AGENTS.md).\n", "sections",
            ),
            (
                "agents_compact", "docs/agents.md", "compact-doc",
                "# Coding-agent views\n\n[Architecture](agents/architecture.md).\n", "sections",
            ),
            (
                "agents_architecture", "docs/agents/architecture.md", "agents-architecture",
                "# Agent architecture\n\n[Human docs](../README.md).\n", "sections",
            ),
        ]
        link_body = (
            "[kernel](../AGENTS.md) [shim](../CLAUDE.md) "
            "[local](../CLAUDE.local.md) [settings](../.claude/settings.json) "
            "[index](agents/README.md) [compact](agents.md) "
            "[topic](agents/architecture.md)\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                seed_repo(repo)
                manifest = load_manifest(repo)
                agent_docs = []
                for offset, (doc_id, path, doc_type, body, provenance_mode) in enumerate(agent_specs):
                    doc = written_doc(
                        doc_id, path, body, write_order=200 + offset,
                        group="agent-context", doc_type=doc_type,
                        provenance_mode=provenance_mode,
                    )
                    agent_docs.append(doc)
                    target = repo / path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(body, encoding="utf-8")
                manifest["documents"].extend(agent_docs)
                (repo / ".docforge" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
                src = repo / "src"
                src.mkdir()
                (src / "main.ts").write_bytes(b"evidence")
                try:
                    plan = run_dashboard(runtime, "start", "--repo", str(repo), "--plan-only")
                    self.assertEqual(plan.returncode, 0, plan.stdout + plan.stderr)
                    self.assertIn("3 pages in 3 folders; 0 problems", plan.stdout)
                    for doc in agent_docs:
                        self.assertNotIn(doc["id"], plan.stdout)
                    self.assertNotIn("/docs/agents", plan.stdout)
                    self.assertNotIn("/docs/root/agents", plan.stdout)
                    self.assertEqual(
                        rewrite_with_documents(runtime, manifest["documents"], "docs/README.md", link_body),
                        link_body,
                        "agent-context documents must not become dashboard link targets",
                    )

                    result = run_dashboard(runtime, "start", "--repo", str(repo), "--no-open", env=env)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn("metadata: 0 reconciled, 3 unchanged", result.stdout)
                    self.assertIn("converted 3 documents", result.stdout)
                    content = repo / ".docforge" / "dashboard" / "content" / "docs"
                    self.assertFalse((content / "agents").exists())
                    self.assertFalse((content / "root").exists())
                    self.assertFalse((content / "agents.mdx").exists())
                    root_meta = json.loads((content / "meta.json").read_text(encoding="utf-8"))
                    self.assertEqual(root_meta["pages"], ["index", "architecture", "product"])
                    rendered = "\n".join(
                        path.read_text(encoding="utf-8")
                        for path in content.rglob("*")
                        if path.is_file()
                    )
                    for doc in agent_docs:
                        self.assertNotIn(doc["id"], rendered)
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
                write_written_doc(repo, doc, "# Extras\n\nSee [missing](../missing.md).\n")
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
        # A doc/*.md doc with no sidecar entry is a `metadata` scan finding,
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
                    remove_sidecar_entry(repo, "docs/product/overview.md")
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
    def test_render_signature_ignores_agent_changes_but_tracks_human_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            manifest = load_manifest(repo)
            agent = written_doc(
                "agents_architecture", "docs/agents/architecture.md", "# Agent architecture\n",
                write_order=205, group="agent-context", doc_type="agents-architecture",
            )
            manifest["documents"].append(agent)
            (repo / ".docforge" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            write_written_doc(repo, agent, "# Agent architecture\n\nInitial agent detail.\n")

            def signatures() -> dict[str, str]:
                values = {}
                for runtime in ("py", "js"):
                    result = run_dashboard(runtime, "start", "--repo", str(repo), "--plan-only")
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    match = SIG_RE.search(result.stdout)
                    self.assertIsNotNone(match, result.stdout)
                    values[runtime] = match.group(1)
                self.assertEqual(values["py"], values["js"])
                return values

            before = signatures()
            (repo / agent["path"]).write_text("# Agent architecture\n\nChanged agent detail.\n", encoding="utf-8")
            manifest = load_manifest(repo)
            manifest_agent = next(doc for doc in manifest["documents"] if doc["id"] == agent["id"])
            manifest_agent["title"] = "Changed Agent Metadata"
            manifest_agent["description"] = "Still not reader-facing."
            manifest_agent["nav_order"] = 1
            (repo / ".docforge" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            after_agent_change = signatures()
            self.assertEqual(before, after_agent_change)

            human = repo / "docs" / "README.md"
            human.write_text(human.read_text(encoding="utf-8") + "\nHuman-facing change.\n", encoding="utf-8")
            after_human_change = signatures()
            self.assertNotEqual(after_agent_change, after_human_change)

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
                    write_written_doc(repo, doc, body)
                src = repo / "src"
                src.mkdir()
                (src / "main.ts").write_bytes(b"changed after provenance")
                # The json-mode equivalent of "no frontmatter": drop the
                # sidecar entry reconcile needs, rather than corrupt the body.
                remove_sidecar_entry(repo, "docs/product/overview.md")
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
                write_written_doc(repo, doc, "# Drift\n")
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


def prepare_fake_mermaid_dashboard(dashboard_dir: Path, valid: bool) -> None:
    """A minimal stand-in for a real `mermaid`/`jsdom` install: a marker
    `node_modules/mermaid` directory (satisfies the gate's own precondition
    check) and a stub validator script that reports every task it is handed
    as uniformly valid or invalid. Plumbing only -- see
    FAKE_NPM_BROKEN_MERMAID's docstring for why this can't prove real
    Mermaid detection."""
    (dashboard_dir / "node_modules" / "mermaid").mkdir(parents=True, exist_ok=True)
    scripts = dashboard_dir / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    verdict = "{ ok: true, error: null }" if valid else "{ ok: false, error: 'fixture: forced failure' }"
    (scripts / "validate_mermaid.mjs").write_text(
        "let raw = '';\n"
        "for await (const chunk of process.stdin) raw += chunk;\n"
        "const tasks = JSON.parse(raw || '[]');\n"
        f"process.stdout.write(JSON.stringify(tasks.map(() => ({verdict}))));\n",
        encoding="utf-8",
    )


class DashboardMermaidValidationTests(unittest.TestCase):
    """Plumbing coverage for the real-rendering Mermaid gate: fence
    extraction, the validator subprocess/JSON contract, scan's opportunistic
    inclusion, and that a blocking verdict actually aborts `start`. None of
    this proves real Mermaid detection -- these fixtures never install real
    `mermaid`/`jsdom` -- that is the opt-in slow tier's job."""

    def test_mermaid_tasks_extracts_fences_from_included_documents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                seed_repo(repo)
                tasks = mermaid_tasks_report(runtime, repo)
                self.assertEqual(len(tasks), 1)
                self.assertEqual(tasks[0]["doc"], "architecture_constraints")
                self.assertIn("graph TD;", tasks[0]["chart"])
                self.assertIn("A-->B;", tasks[0]["chart"])
                self.assertGreater(tasks[0]["line"], 0)

    def test_mermaid_findings_reports_blocking_from_stub_validator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                seed_repo(repo)
                dashboard_dir = repo / "fake-dashboard"
                prepare_fake_mermaid_dashboard(dashboard_dir, valid=False)
                result = mermaid_findings_report(runtime, repo, dashboard_dir)
                self.assertTrue(result["blocking"])
                self.assertEqual(result["counts"]["invalid_mermaid"], 1)
                self.assertEqual(len(result["problems"]), 1)
                problem = result["problems"][0]
                self.assertEqual(problem["kind"], "invalid_mermaid")
                self.assertEqual(problem["doc"], "architecture_constraints")
                self.assertTrue(problem["blocking"])
                self.assertIn("fixture: forced failure", problem["detail"])

    def test_mermaid_findings_reports_clean_from_stub_validator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                seed_repo(repo)
                dashboard_dir = repo / "fake-dashboard"
                prepare_fake_mermaid_dashboard(dashboard_dir, valid=True)
                result = mermaid_findings_report(runtime, repo, dashboard_dir)
                self.assertFalse(result["blocking"])
                self.assertEqual(result["problems"], [])

    def test_mermaid_findings_skips_without_installed_mermaid(self) -> None:
        # No `node_modules/mermaid` marker at all -- e.g. `ensure_dependencies`
        # never ran, or ran against a fake/corrupted install. Skip rather than
        # crash: this is the same precondition the mandatory gate itself
        # relies on to stay safe under this repo's fake-npm test fixtures.
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                seed_repo(repo)
                dashboard_dir = repo / "fake-dashboard"
                dashboard_dir.mkdir()
                result = mermaid_findings_report(runtime, repo, dashboard_dir)
                self.assertFalse(result["blocking"])
                self.assertEqual(result["problems"], [])

    def test_scan_opportunistically_includes_mermaid_findings_when_installed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                seed_repo(repo)
                dashboard_dir = repo / "fake-dashboard"
                prepare_fake_mermaid_dashboard(dashboard_dir, valid=False)
                result = run_dashboard(
                    runtime, "scan", "--repo", str(repo), "--dashboard", str(dashboard_dir), "--json",
                )
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                payload = json.loads(result.stdout)
                kinds = {p["kind"] for p in payload["problems"]}
                self.assertIn("invalid_mermaid", kinds)
                self.assertTrue(payload["blocking"])

    def test_scan_skips_mermaid_check_without_a_dashboard_install(self) -> None:
        # The default path for every ordinary `scan`: no `--dashboard`
        # override, nothing ever installed. Must stay instant and clean
        # w.r.t. the mermaid check specifically (unrelated findings, like
        # provenance drift from the fixture's own `src/main.ts` reference,
        # are not this test's concern).
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                seed_repo(repo)
                result = run_dashboard(runtime, "scan", "--repo", str(repo), "--json")
                payload = json.loads(result.stdout)
                self.assertEqual(payload["counts"]["invalid_mermaid"], 0)
                self.assertNotIn("invalid_mermaid", {p["kind"] for p in payload["problems"]})

    def test_start_aborts_when_mermaid_diagrams_are_invalid(self) -> None:
        env, _bin = fake_npm_broken_mermaid_env()
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                seed_repo(repo)
                try:
                    result = run_dashboard(runtime, "start", "--repo", str(repo), "--no-open", env=env)
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    self.assertIn("mermaid: 1 invalid diagram(s) found", result.stdout)
                    self.assertIn("[invalid_mermaid] (blocking)", result.stdout)
                    self.assertIn("architecture_constraints", result.stdout)
                    self.assertIn("dashboard was NOT opened: invalid Mermaid diagrams found", result.stdout)
                    self.assertIn("invalid Mermaid diagrams found", result.stderr)
                finally:
                    stop_dashboard(runtime, repo)


class CompactRoutePlanTests(unittest.TestCase):
    """A merged compact file and its unfolded children share a name:
    `docs/reference.md` next to `docs/reference/`. Routing the merged page as
    `reference.mdx` collides with that directory, and Fumadocs resolves the
    name to the folder — dropping the section's main content from the sidebar
    and listing the folder twice."""

    DOCS = [
        {"id": "docs_index", "path": "docs/README.md", "type": "docs-index",
         "title": "Documentation", "group": "root", "nav_order": 0},
        {"id": "product_compact", "path": "docs/product.md", "type": "compact-doc",
         "title": "Product", "group": "product", "nav_order": 10},
        {"id": "reference_compact", "path": "docs/reference.md", "type": "compact-doc",
         "title": "Reference", "group": "reference", "nav_order": 40},
        {"id": "api_reference", "path": "docs/reference/api.md", "type": "api-reference",
         "title": "API", "group": "reference", "nav_order": 41},
        {"id": "library_compatibility", "path": "docs/reference/compatibility.md",
         "type": "generic", "title": "Compatibility", "group": "reference", "nav_order": 42},
    ]

    def _plan(self, runtime: str) -> tuple[dict[str, str], dict[str, list[str]]]:
        """`({doc_id: output_path|url}, {folder: pages})` from the real generator."""
        if runtime == "py":
            script = (
                "import json,sys;sys.path.insert(0,%r);"
                "from runtime.dashboard.python import dashboard as d;"
                "docs=json.loads(sys.stdin.read());"
                "led=d.build_ledger(docs);"
                "print(json.dumps({'pages':led['pages'],"
                "'plans':{k:v['pages'] for k,v in d.meta_plans(led,{'documents':docs}).items()}}))"
                % str(ROOT / "skills" / "docforge" / "_shared")
            )
            command = ["python3", "-c", script]
        else:
            script = (
                "const d=require(%r);let s='';process.stdin.on('data',c=>s+=c)"
                ".on('end',()=>{const docs=JSON.parse(s);const led=d.buildLedger(docs);"
                "const plans={};for(const[k,v]of Object.entries(d.metaPlans(led,{documents:docs})))"
                "plans[k]=v.pages;"
                "console.log(JSON.stringify({pages:led.pages,plans}));});"
                % str(ROOT / "skills" / "docforge" / "_shared" / "runtime"
                      / "dashboard" / "js" / "dashboard.js")
            )
            command = ["node", "-e", script]
        result = subprocess.run(
            command, input=json.dumps(self.DOCS), text=True, capture_output=True, check=True
        )
        data = json.loads(result.stdout)
        routes = {page["doc_id"]: (page["output_path"], page["url"]) for page in data["pages"]}
        return routes, data["plans"]

    def test_merged_page_routes_as_its_folder_index_at_the_same_url(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                routes, _ = self._plan(runtime)
                # The URL is byte-identical to the pre-fix route, so no link churn.
                self.assertEqual(routes["reference_compact"], ("reference/index.mdx", "/docs/reference"))
                self.assertEqual(routes["product_compact"], ("product/index.mdx", "/docs/product"))
                # Unfolded children keep their own routes and nest under it.
                self.assertEqual(routes["api_reference"], ("reference/api.mdx", "/docs/reference/api"))

    def test_sidebar_lists_each_node_once(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                _, plans = self._plan(runtime)
                self.assertEqual(plans[""], ["index", "product", "reference"])
                self.assertEqual(plans["reference"], ["index", "api", "compatibility"])
                for folder, pages in plans.items():
                    self.assertEqual(
                        len(pages), len(set(pages)),
                        f"duplicate sidebar entry in {folder or '(root)'}: {pages}",
                    )


class DashboardAgentOnlyTreeTests(unittest.TestCase):
    """An agents-only repository has no human-facing documentation, so a
    browsable site has nothing to show. That is a scope fact, not a defect --
    and forcing a `docs/README.md` would make the human tree index the agent
    overlay, which the one-way boundary forbids."""

    NO_HUMAN_DOCS = "no human-facing documentation to render"

    def test_scan_reports_clean_no_human_docs_state(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                initialized = initialize(
                    runtime, repo, "spine",
                    audiences=("coding-agents",), layout="standard", groups=("agents",),
                )
                self.assertEqual(initialized.returncode, 0, initialized.stdout + initialized.stderr)
                result = run_dashboard(runtime, "scan", "--repo", str(repo))
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                lines = [line for line in (result.stdout + result.stderr).splitlines() if line.strip()]
                self.assertEqual(len(lines), 1, lines)
                self.assertIn(self.NO_HUMAN_DOCS, lines[0])
                self.assertNotIn("no docs index", lines[0])
                self.assertNotIn("revise", lines[0].lower())

                json_result = run_dashboard(runtime, "scan", "--repo", str(repo), "--json")
                self.assertEqual(json_result.returncode, 0, json_result.stderr)
                payload = json.loads(json_result.stdout)
                self.assertTrue(payload["no_human_docs"])
                self.assertFalse(payload["blocking"])
                self.assertEqual(payload["problems"], [])
                self.assertIn(self.NO_HUMAN_DOCS, payload["message"])
                self.assertTrue(all(count == 0 for count in payload["counts"].values()))

    def test_start_and_export_exit_before_dashboard_work(self) -> None:
        env, _bin = fake_npm_env()
        for runtime in ("py", "js"):
            for command in ("start", "export"):
                with self.subTest(runtime=runtime, command=command), tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    initialized = initialize(
                        runtime, repo, "spine",
                        audiences=("coding-agents",), layout="standard", groups=("agents",),
                    )
                    self.assertEqual(initialized.returncode, 0, initialized.stdout + initialized.stderr)
                    args = [command, "--repo", str(repo)]
                    if command == "start":
                        args.append("--no-open")
                    try:
                        result = run_dashboard(runtime, *args, env=env)
                        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                        lines = [line for line in (result.stdout + result.stderr).splitlines() if line.strip()]
                        self.assertEqual(len(lines), 1, lines)
                        self.assertIn(self.NO_HUMAN_DOCS, lines[0])
                        self.assertNotIn("revise", lines[0].lower())
                        self.assertFalse(
                            (repo / ".docforge" / "dashboard").exists(),
                            f"{command} performed dashboard work for an agent-only manifest",
                        )
                    finally:
                        stop_dashboard(runtime, repo)

    def test_a_human_tree_still_demands_its_docs_index(self) -> None:
        """The original message must survive for the case it was written for."""
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                initialize(runtime, repo, "spine", layout="standard")
                result = run(runtime, "dashboard", "scan", "--repo", str(repo))
                combined = result.stdout + result.stderr
                self.assertIn("no docs index", combined)
                self.assertNotIn(self.NO_HUMAN_DOCS, combined)


if __name__ == "__main__":
    unittest.main()
