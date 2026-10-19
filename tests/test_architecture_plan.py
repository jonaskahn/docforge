"""Adaptive deep architecture: the architecture-plan ledger, provenance 2.2
external sources, working depth, and the subsystem catalog records."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _support import ROOT, run

SKILL_ROOT = ROOT / "skills" / "docforge" / "_shared"
CLI_PY = SKILL_ROOT / "runtime" / "cli" / "python"
CLI_JS = SKILL_ROOT / "runtime" / "cli" / "js"


def _seed_repo(repo: Path, scale_class: str = "medium") -> Path:
    (repo / ".docforge").mkdir(parents=True, exist_ok=True)
    (repo / "src").mkdir(exist_ok=True)
    (repo / "docs").mkdir(exist_ok=True)
    (repo / "src" / "app.py").write_text("def main():\n    pass\n", encoding="utf-8")
    (repo / ".docforge" / "manifest.json").write_text(json.dumps({
        "version": "3.10",
        "project": {
            "name": "fixture",
            "root": str(repo),
            "tier": "diligence",
            "scale": {"class": scale_class, "layout": "standard", "decided_by": "detected"},
            "profiles": {"shapes": ["api-service"], "platforms": [], "frameworks": [],
                         "concerns": [], "audiences": []},
        },
        "documents": [],
        "metadata": {},
    }, indent=2) + "\n", encoding="utf-8")
    return repo


def _analysis_with_documents(scale_class: str = "medium") -> dict:
    return {
        "schema": "1.0",
        "project": {
            "scale": scale_class,
            "layout": "standard",
            "tier": "diligence",
            "profiles": {"shapes": ["api-service"]},
            "graph_lock": None,
        },
        "system": {
            "capability": "Serve the API",
            "drivers": ["multi-tenant"],
            "actors": ["user"],
            "external_systems": ["payment-provider"],
            "deployable_blocks": [
                {"id": "api", "name": "API service", "technology": "python", "parent": None},
                {"id": "db", "name": "Database", "technology": "postgres", "parent": None},
            ],
            "subsystem_candidates": [
                {"id": "billing", "name": "Billing", "parent": "api",
                 "evidence": "modules/billing", "confidence": "high"},
            ],
            "deployment_nodes": ["app-node", "db-node"],
            "relationships": [
                {"origin": "api", "destination": "db", "action": "persists",
                 "protocol": "sql", "evidence": "src"},
            ],
            "invariants": [],
            "trust_boundaries": [],
            "failure_domains": [],
            "quality_constraints": [],
            "conflicts": [],
        },
        "documents": [
            {
                "id": "arch_high_level", "path": "docs/architecture/high-level.md",
                "reader_question": "what surrounds the system", "fact_owner": "architecture-high-level",
                "parent_blocks": [], "evidence_questions": ["boundaries"],
                "required_capabilities": ["code_graph"], "external_research_questions": [],
                "dependencies": [], "batch": 1, "rationale": "stable overview", "state": "proposed",
            },
            {
                "id": "architecture_subsystem_billing",
                "path": "docs/architecture/subsystems/billing.md",
                "reader_question": "how does billing work", "fact_owner": "architecture-subsystem",
                "parent_blocks": ["api"], "evidence_questions": ["billing internals"],
                "required_capabilities": ["code_graph"], "external_research_questions": [],
                "dependencies": ["arch_high_level"], "batch": 2,
                "rationale": "significant subsystem", "state": "proposed",
            },
        ],
        "research": {"policy": "off", "authorized": False, "questions": [], "sources": []},
        "adjudication": {"proposals": [], "adjudicator": None, "merged": [], "omitted": [],
                         "expansions": []},
        "audit": {"status": "pending", "verdict": None, "report": None},
        "workers": {"evidence": 6, "proposals": 3},
    }


class ArchitecturePlanParityTests(unittest.TestCase):
    def test_prepare_and_full_cycle_parity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _seed_repo(Path(tmp))
            py_prep = run("py", "architecture_plan", "prepare", "--repo", str(repo),
                          "--manifest", str(repo / ".docforge" / "manifest.json"))
            js_prep = run("js", "architecture_plan", "prepare", "--repo", str(repo),
                          "--manifest", str(repo / ".docforge" / "manifest.json"))
            self.assertEqual(py_prep.returncode, js_prep.returncode, js_prep.stderr)
            self.assertEqual(py_prep.stdout, js_prep.stdout)

            analysis = _analysis_with_documents()
            path = repo / "analysis.json"
            path.write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
            for runtime in ("py", "js"):
                result = run(runtime, "architecture_plan", "import", "--repo", str(repo),
                             "--analysis", str(path))
                self.assertEqual(result.returncode, 0, result.stderr)
            ledger = json.loads((repo / ".docforge" / "architecture-plan.json").read_text(encoding="utf-8"))
            self.assertEqual(ledger["schema"], "1.0")

            # decide records the confirmed pack and research policy. It is a
            # one-shot confirmation, so each runtime gets its own repo copy.
            for runtime in ("py", "js"):
                repo_for = _seed_repo(Path(tmp) / f"{runtime}")
                path_for = repo_for / "analysis.json"
                path_for.write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
                result = run(runtime, "architecture_plan", "import", "--repo", str(repo_for),
                             "--analysis", str(path_for))
                self.assertEqual(result.returncode, 0, result.stderr)
                result = run(runtime, "architecture_plan", "decide", "--repo", str(repo_for),
                             "--select", "arch_high_level", "architecture_subsystem_billing",
                             "--research-policy", "official-primary")
                self.assertEqual(result.returncode, 0, result.stderr)
                ledger = json.loads((repo_for / ".docforge" / "architecture-plan.json").read_text(encoding="utf-8"))
                states = {doc["id"]: doc["state"] for doc in ledger["documents"]}
                self.assertEqual(states["arch_high_level"], "selected")
                self.assertEqual(states["architecture_subsystem_billing"], "selected")
                self.assertEqual(ledger["research"]["policy"], "official-primary")
                self.assertTrue(ledger["research"]["authorized"])

            py_repo = Path(tmp) / "py"
            js_repo = Path(tmp) / "js"
            import re
            def _normalized(text: str) -> str:
                return re.sub(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?Z", "<TIME>", text)
            py_status = run("py", "architecture_plan", "status", "--repo", str(py_repo), "--json")
            js_status = run("js", "architecture_plan", "status", "--repo", str(js_repo), "--json")
            self.assertEqual(_normalized(py_status.stdout), _normalized(js_status.stdout))
            self.assertIn("architecture_subsystem_billing", py_status.stdout)

            py_val = run("py", "architecture_plan", "validate", "--repo", str(py_repo))
            js_val = run("js", "architecture_plan", "validate", "--repo", str(js_repo))
            self.assertEqual(py_val.returncode, 0, py_val.stderr)
            self.assertEqual(py_val.stdout, js_val.stdout)

            py_audit = run("py", "architecture_plan", "audit", "--repo", str(py_repo),
                           "--verdict", "PASS", "--report", str(py_repo / "report.md"))
            js_audit = run("js", "architecture_plan", "audit", "--repo", str(js_repo),
                           "--verdict", "PASS", "--report", str(js_repo / "report.md"))
            self.assertEqual(py_audit.returncode, 0, py_audit.stderr)
            self.assertEqual(js_audit.returncode, 0, js_audit.stderr)
            ledger = json.loads((py_repo / ".docforge" / "architecture-plan.json").read_text(encoding="utf-8"))
            self.assertEqual(ledger["audit"]["status"], "passed")

    def test_validation_catches_structural_defects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _seed_repo(Path(tmp))
            cases = {
                "duplicate": lambda p: (p["documents"].append(dict(p["documents"][0])), p)[1],
                "dangling_parent": lambda p: (
                    p["documents"][1].__setitem__("parent_blocks", ["nope"]), p)[1],
                "dangling_dependency": lambda p: (
                    p["documents"][1].__setitem__("dependencies", ["missing"]), p)[1],
                "unknown_source": lambda p: (
                    p["documents"][1].__setitem__("external_refs", [
                        {"source_id": "ext-nope", "relation": "method", "supports": "x"}]), p)[1],
            }
            for name, mutate in cases.items():
                analysis = _analysis_with_documents()
                mutate(analysis)
                path = repo / f"{name}.json"
                path.write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
                result = run("py", "architecture_plan", "import", "--repo", str(repo),
                             "--analysis", str(path))
                self.assertEqual(result.returncode, 1, f"{name}: expected failure")

    def test_scale_aware_worker_schedule(self) -> None:
        """The evidence/proposal worker counts follow project.scale.class."""
        from runtime.architecture.python import architecture_plan
        self.assertEqual(architecture_plan.EVIDENCE_WORKERS_BY_SCALE["small"], 3)
        self.assertEqual(architecture_plan.EVIDENCE_WORKERS_BY_SCALE["medium"], 6)
        self.assertEqual(architecture_plan.EVIDENCE_WORKERS_BY_SCALE["large"], 8)
        self.assertEqual(architecture_plan.PROPOSAL_AGENTS_BY_SCALE["small"], 2)
        self.assertEqual(architecture_plan.PROPOSAL_AGENTS_BY_SCALE["medium"], 3)
        self.assertEqual(architecture_plan.PROPOSAL_AGENTS_BY_SCALE["large"], 4)

    def test_architecture_plan_schema_is_valid(self) -> None:
        schema = json.loads((SKILL_ROOT / ".metadata" / "architecture-plan-schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["schema"]["const"], "1.0")
        self.assertIn("documents", schema["required"])
        self.assertIn("research", schema["required"])
        self.assertIn("audit", schema["required"])


class ProvenanceExternalSourcesTests(unittest.TestCase):
    def test_provenance_22_round_trip_in_both_runtimes(self) -> None:
        provenance = {
            "schema": "2.2", "doc_id": "arch_high_level", "path": "docs/architecture/high-level.md",
            "generated_at": "2026-08-27T00:00:00Z",
            "generator": {"name": "docforge", "version": "2.28.0"},
            "tier": "diligence", "target_depth": "working",
            "graph": {"provider": "gitnexus", "flow": "native"},
            "external_sources": [
                {"id": "ext-c4-deployment", "url": "https://c4model.com/diagrams/deployment",
                 "title": "Deployment diagram", "publisher": "C4 model", "kind": "official-doc",
                 "accessed_at": "2026-08-27T00:00:00Z", "version": "current at access",
                 "locator": "Scope"},
            ],
            "sections": [
                {"id": "deployment", "sources": [
                    {"path": "src/app.py", "git_blob": "3b18e512dba79e4c8300dd08aeb37f8e728b8dad",
                     "role": "code"},
                ], "external_refs": [
                    {"source_id": "ext-c4-deployment", "relation": "method",
                     "supports": "The deployment view maps running instances onto nodes."},
                ], "unresolved": []},
            ],
        }
        import sys
        sys.path.insert(0, str(SKILL_ROOT))
        from runtime.common.python.provenance_frontmatter import emit_yaml, parse_frontmatter
        text = emit_yaml(provenance)
        state, parsed, _ = parse_frontmatter(text)
        self.assertEqual(state, "ok")
        self.assertEqual(parsed, provenance)

        import subprocess
        node_script = (
            "const pf = require(process.argv[1]); "
            "const p = JSON.parse(process.argv[2]); "
            "const out = pf.parseFrontmatter(pf.emitYaml(p)); "
            "console.log(out.state); console.log(JSON.stringify(out.provenance));"
        )
        js = subprocess.run(
            ["node", "-e", node_script,
             str(CLI_JS.parent.parent / "common" / "js" / "provenance_frontmatter.js"),
             json.dumps(provenance)],
            cwd=ROOT, text=True, capture_output=True,
        )
        self.assertEqual(js.returncode, 0, js.stderr)
        lines = js.stdout.strip().splitlines()
        self.assertEqual(lines[0], "ok")
        self.assertEqual(json.loads(lines[1]), provenance)

    def test_external_refs_report_as_external_unchecked(self) -> None:
        """A FRESH document carrying external refs reports EXTERNAL_UNCHECKED
        alongside its repository verdict, never as Git-hash freshness."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _seed_repo(Path(tmp))
            manifest = json.loads((repo / ".docforge" / "manifest.json").read_text(encoding="utf-8"))
            source = repo / "src" / "app.py"
            import subprocess
            blob = subprocess.run(
                ["python3", "-c",
                 "import sys, hashlib; "
                 "p = sys.argv[1]; b = open(p,'rb').read(); "
                 "print(hashlib.sha1(b'blob %d\\0' % len(b) + b).hexdigest())",
                 str(source)],
                capture_output=True, text=True,
            ).stdout.strip()
            manifest["documents"] = [{
                "id": "arch_high_level", "path": "docs/architecture/high-level.md",
                "status": "generated", "group": "architecture", "type": "architecture-high-level",
                "write_order": 10, "provenance_mode": "sections", "requires": ["code_graph"],
                "audit_profile": "architecture", "description": "High-level architecture.",
                "target_depth": "working", "dominant_form": "flowchart",
                "provenance": {
                    "schema": "2.2", "doc_id": "arch_high_level",
                    "path": "docs/architecture/high-level.md",
                    "generated_at": "2026-08-27T00:00:00Z",
                    "generator": {"name": "docforge", "version": "2.28.0"},
                    "tier": "diligence", "target_depth": "working",
                    "graph": {"provider": "gitnexus", "flow": "native"},
                    "external_sources": [
                        {"id": "ext-c4", "url": "https://c4model.com/diagrams",
                         "title": "Deployment diagram", "publisher": "C4 model",
                         "kind": "official-doc", "accessed_at": "2026-08-27T00:00:00Z"},
                    ],
                    "sections": [{
                        "id": "deployment", "sources": [
                            {"path": "src/app.py", "git_blob": blob, "role": "code"},
                        ],
                        "external_refs": [
                            {"source_id": "ext-c4", "relation": "method", "supports": "maps instances"},
                        ],
                        "unresolved": [],
                    }],
                },
            }]
            (repo / ".docforge" / "manifest.json").write_text(
                json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
            )
            for runtime in ("py", "js"):
                result = run(runtime, "check_staleness", "--manifest", str(repo / ".docforge" / "manifest.json"))
                self.assertIn("EXTERNAL_UNCHECKED", result.stdout, f"{runtime}: external refs must report unchecked")
                self.assertEqual(result.returncode, 0, result.stderr)


class WorkingDepthAndSubsystemCatalogTests(unittest.TestCase):
    def test_working_is_a_valid_target_depth(self) -> None:
        catalog = json.loads((SKILL_ROOT / ".metadata" / "catalog" / "index.json").read_text(encoding="utf-8"))
        self.assertEqual(catalog["version"], "2.28.0")
        import sys
        sys.path.insert(0, str(SKILL_ROOT))
        from runtime.catalog.python.query_catalog import TARGET_DEPTHS
        self.assertIn("working", TARGET_DEPTHS)

    def test_arch_high_level_is_working_depth(self) -> None:
        record = json.loads(
            (SKILL_ROOT / ".metadata" / "catalog" / "documents" / "architecture" / "arch_high_level.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(record["target_depth"], "working")
        self.assertIn("3.1.0", record["contract_revision"])

    def test_subsystem_records_are_registered(self) -> None:
        catalog = json.loads((SKILL_ROOT / ".metadata" / "catalog" / "index.json").read_text(encoding="utf-8"))
        ids = {row["id"] for row in catalog["document_types"]}
        self.assertIn("architecture_subsystem", ids)
        self.assertIn("architecture_subsystems_index", ids)
        subsystem = json.loads(
            (SKILL_ROOT / ".metadata" / "catalog" / "documents" / "architecture" / "architecture_subsystem.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(subsystem["target_depth"], "deep-dive")
        self.assertTrue(subsystem.get("selection_evidence_required"))
        self.assertEqual(subsystem["model_depth"]["c4"], "component-evidence")
        self.assertEqual(subsystem["model_depth"]["arc42"], "runtime-scenarios")

    def test_subsystem_documents_fold_into_compact_architecture(self) -> None:
        compact = json.loads(
            (SKILL_ROOT / ".metadata" / "catalog" / "documents" / "architecture" / "architecture_compact.json")
            .read_text(encoding="utf-8")
        )
        self.assertIn("architecture_subsystem", compact["compact_members"])

    def test_subsystems_index_requires_children(self) -> None:
        index = json.loads(
            (SKILL_ROOT / ".metadata" / "catalog" / "documents" / "architecture" / "architecture_subsystems_index.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(index["selection"]["requires_children"], ["architecture-subsystem"])

    def test_deep_dive_frame_reference_exists(self) -> None:
        frame = (SKILL_ROOT / "references" / "deep-dive-frame.md").read_text(encoding="utf-8")
        self.assertIn("What decision does this document support?", frame)
        self.assertIn("Which neighboring document owns excluded detail?", frame)


if __name__ == "__main__":
    unittest.main()
