"""Dashboard: metadata reconciliation, route planning, MDX conversion, validation, fingerprinting."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
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

INDEX_BODY = """# Docs Index

## Documentation

See [architecture/](architecture/README.md) and [product/overview.md](product/overview.md).
"""

CONSTRAINTS_BODY = """# Constraints

Owner is <TEAM_OWNER>. Literal braces {stay} safe.

```js
const x = '<TEAM_OWNER> {not escaped}';
```

See [the index](../README.md#docs-index).

```mermaid
graph TD;
  A-->B;
```
"""


def written_doc(doc_id: str, path: str, body: str) -> dict:
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
        "write_order": 10,
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
        written_doc("docs_index", "docs/README.md", INDEX_BODY),
        written_doc("architecture_constraints", "docs/architecture/constraints.md", CONSTRAINTS_BODY),
        written_doc("product_overview", "docs/product/overview.md", bodies["product_overview"]),
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


class DashboardFingerprintTests(unittest.TestCase):
    def test_fingerprint_parity_and_sensitivity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            py = run_dashboard("py", "fingerprint", "--repo", str(repo)).stdout.strip()
            js = run_dashboard("js", "fingerprint", "--repo", str(repo)).stdout.strip()
            self.assertEqual(py, js)
            before = py
            manifest = load_manifest(repo)
            manifest["documents"][0]["write_order"] = 99
            (repo / ".docforge" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            py_after = run_dashboard("py", "fingerprint", "--repo", str(repo)).stdout.strip()
            self.assertNotEqual(before, py_after)


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
                self.assertIn("Owner is &lt;TEAM_OWNER&gt;", text)
                self.assertIn("&#123;stay&#125;", text)
                self.assertIn("const x = '<TEAM_OWNER> {not escaped}';", text)
                self.assertIn("[the index](/docs#docs-index)", text)
                self.assertIn("```mermaid", text)
                validate = run_dashboard(runtime, "validate", "--repo", str(repo))
                self.assertEqual(validate.returncode, 0, validate.stdout)

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

    def test_build_generates_dashboard_gitignore_rule(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            run_dashboard("py", "build", "--repo", str(repo), "--skip-install")
            gitignore = (repo / ".docforge" / ".gitignore").read_text(encoding="utf-8")
            self.assertIn("dashboard/", gitignore)
            self.assertTrue((repo / ".docforge" / "dashboard" / "package.json").is_file())
            self.assertTrue((repo / ".docforge" / "dashboard" / "lib" / "shared.ts").is_file())


class DashboardValidateTests(unittest.TestCase):
    def test_validate_reports_broken_links_and_missing_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            seed_repo(repo)
            run_dashboard("py", "build", "--repo", str(repo), "--skip-install")
            content = repo / ".docforge" / "dashboard" / "content" / "docs" / "architecture" / "constraints.mdx"
            text = content.read_text(encoding="utf-8")
            content.write_text(
                text.replace("[the index](/docs#docs-index)", "[one](/docs/nope) and [two](/docs#missing)"),
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
