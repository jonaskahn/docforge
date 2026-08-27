"""Adaptive flow-analysis v3 ledger and flow-index 1.3 integration."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _support import run, write_flow_index


def seed_repo(repo: Path, scale_class: str = "medium") -> Path:
    (repo / ".docforge").mkdir(parents=True, exist_ok=True)
    (repo / "src").mkdir(exist_ok=True)
    (repo / "src" / "flow.py").write_text("def run():\n    return True\n", encoding="utf-8")
    (repo / ".docforge" / "manifest.json").write_text(json.dumps({
        "version": "3.10",
        "project": {
            "name": "fixture", "root": str(repo), "tier": "diligence",
            "scale": {"class": scale_class, "layout": "standard", "decided_by": "detected"},
            "profiles": {"shapes": [], "platforms": [], "frameworks": [], "concerns": [], "audiences": []},
        },
        "documents": [], "metadata": {},
    }, indent=2) + "\n", encoding="utf-8")
    return repo


def flow_card(flow_id: str = "flow-checkout", characteristic: str = "request-command") -> dict:
    section_by_kind = {
        "request-command": ["Request and authorization", "Commit and response"],
        "event-message": ["Envelope and acknowledgement", "Replay and eventual outcome"],
        "scheduled-batch": ["Selection window", "Checkpoint and restart"],
        "lifecycle-stateful": ["Guarded transitions", "Terminal states"],
        "streaming-interactive": ["Stream lifecycle", "Cancellation and backpressure"],
        "fan-out-orchestration": ["Parallel branches", "Join and compensation"],
        "resource-lifecycle": ["Allocation and readiness", "Ownership and teardown"],
    }
    sections = section_by_kind[characteristic]
    diagram = {
        "request-command": "sequenceDiagram",
        "event-message": "flowchart",
        "scheduled-batch": "flowchart",
        "lifecycle-stateful": "stateDiagram-v2",
        "streaming-interactive": "sequenceDiagram",
        "fan-out-orchestration": "flowchart",
        "resource-lifecycle": "stateDiagram-v2",
    }[characteristic]
    return {
        "id": flow_id,
        "name": flow_id.removeprefix("flow-").replace("-", " ").title(),
        "reader_question": f"How does {flow_id} reach its outcome?",
        "parent_flow": None,
        "analysis_state": "ready",
        "decision": "proposed",
        "characteristics": [characteristic],
        "trigger": {"kind": "internal", "signature": "run()", "preconditions": None},
        "guarantee": "The requested work reaches one recorded terminal outcome.",
        "terminal_outcomes": [{"condition": "success", "outcome": "work recorded"}],
        "actors": {"initiator": "caller", "visible": ["service"], "hidden": ["store"]},
        "steps": [{
            "order": 1, "name": "Run work", "actor": "service", "file": "src/flow.py",
            "line": 1, "symbol": "run", "nodeId": None, "evidence": "source",
            "boundary_crossing": False, "async_handoff": False,
            "state_change": "work recorded", "inputs": "request", "outputs": "result",
        }],
        "flow_patterns": {"decisions": [], "event_waits": [], "loops": [], "parallel_work": [], "joins": []},
        "modules": [{"name": "residual-state", "evidence": "src/flow.py:1"}],
        "failures": [],
        "document_design": {
            "section_order": sections,
            "diagrams": [{"form": diagram, "section": sections[0], "question": "What is the characteristic-specific runtime shape?"}],
        },
        "evidence_gaps": [], "conflicts": [], "external_research_questions": [],
        "decomposition_proposals": [],
    }


def analysis_pack(flows: list[dict] | None = None) -> dict:
    return {
        "schemaVersion": 3,
        "source": "fixture",
        "generated_at": "2026-08-27T00:00:00Z",
        "research_policy": None,
        "workers": {"evidence": 6, "proposals": 3},
        "audit": {"status": "pending", "verdict": None, "report": None},
        "flows": flows or [flow_card()],
    }


class FlowAnalysisPrepareParityTests(unittest.TestCase):
    def test_prepare_is_scale_aware_and_paired(self) -> None:
        for klass, expected in (("small", (3, 2)), ("medium", (6, 3)), ("large", (8, 4))):
            with tempfile.TemporaryDirectory() as tmp:
                repo = seed_repo(Path(tmp), klass)
                py = run("py", "flow_analysis", "prepare", "--repo", str(repo), "--json")
                js = run("js", "flow_analysis", "prepare", "--repo", str(repo), "--json")
                self.assertEqual(py.returncode, 0, py.stderr)
                self.assertEqual(js.returncode, 0, js.stderr)
                py_data, js_data = json.loads(py.stdout), json.loads(js.stdout)
                py_data.pop("generated_at"); js_data.pop("generated_at")
                self.assertEqual(py_data, js_data)
                self.assertEqual((py_data["workers"]["evidence"], py_data["workers"]["proposals"]), expected)


class FlowAnalysisLedgerTests(unittest.TestCase):
    def test_import_decide_status_validate_and_audit(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = seed_repo(Path(tmp))
                card = flow_card()
                card["decomposition_proposals"] = [{
                    "id": "split-checkout", "name": "Split checkout",
                    "rationale": "Payment has an independent guarantee and failure domain.",
                    "entry_boundary": "payment authorization",
                    "approved": False,
                    "proposed_flows": [{"id": "flow-payment", "name": "Authorize payment", "guarantee": "authorization recorded"}],
                }]
                source = repo / "analysis.json"
                source.write_text(json.dumps(analysis_pack([card])), encoding="utf-8")
                imported = run(runtime, "flow_analysis", "import", "--repo", str(repo), "--analysis", str(source))
                self.assertEqual(imported.returncode, 0, imported.stderr)
                decided = run(runtime, "flow_analysis", "decide", "--repo", str(repo),
                              "--select", "flow-checkout", "--approve-decomposition", "split-checkout",
                              "--research-policy", "off")
                self.assertEqual(decided.returncode, 0, decided.stderr)
                status = run(runtime, "flow_analysis", "status", "--repo", str(repo), "--json")
                self.assertEqual(status.returncode, 0, status.stderr)
                self.assertEqual(json.loads(status.stdout)["selected_flows"][0]["id"], "flow-checkout")
                valid = run(runtime, "flow_analysis", "validate", "--repo", str(repo))
                self.assertEqual(valid.returncode, 0, valid.stderr)
                report = repo / "audit.md"
                report.write_text("All guarantees, branches, residue, recovery, ownership, gaps, and headings checked.\n", encoding="utf-8")
                audit = run(runtime, "flow_analysis", "audit", "--repo", str(repo), "--verdict", "PASS", "--report", str(report))
                self.assertEqual(audit.returncode, 0, audit.stderr)
                ledger = json.loads((repo / ".docforge" / "flow-analysis.json").read_text())
                self.assertEqual(ledger["audit"]["status"], "passed")
                self.assertEqual(ledger["flows"][0]["analysis_state"], "audited")

    def test_v1_v2_migration_preserves_evidence_without_deep_synthesis(self) -> None:
        for runtime in ("py", "js"):
            for version in (1, 2):
                with self.subTest(runtime=runtime, version=version), tempfile.TemporaryDirectory() as tmp:
                    repo = seed_repo(Path(tmp))
                    old = {"schemaVersion": version, "source": "legacy", "flows": [{"name": "Legacy", "outcome": "kept", "steps": [{"name": "old"}]}]}
                    source = repo / "legacy.json"
                    source.write_text(json.dumps(old), encoding="utf-8")
                    result = run(runtime, "flow_analysis", "import", "--repo", str(repo), "--analysis", str(source))
                    self.assertEqual(result.returncode, 0, result.stderr)
                    migrated = json.loads((repo / ".docforge" / "flow-analysis.json").read_text())
                    flow = migrated["flows"][0]
                    self.assertEqual(migrated["schemaVersion"], 3)
                    self.assertEqual(flow["analysis_state"], "legacy-needs-analysis")
                    self.assertEqual(flow["legacy_evidence"]["outcome"], "kept")
                    self.assertNotIn("guarantee", flow)

    def test_malformed_refs_cycles_and_missing_files_are_rejected(self) -> None:
        mutations = []
        missing_file = flow_card(); missing_file["steps"][0]["file"] = "src/missing.py"; mutations.append(missing_file)
        missing_step = flow_card(); missing_step["flow_patterns"]["decisions"] = [{"step_order": 9}]; mutations.append(missing_step)
        cycle_a = flow_card("flow-a"); cycle_b = flow_card("flow-b"); cycle_a["parent_flow"] = "flow-b"; cycle_b["parent_flow"] = "flow-a"
        cases = [[mutations[0]], [mutations[1]], [cycle_a, cycle_b]]
        for runtime in ("py", "js"):
            for flows in cases:
                with self.subTest(runtime=runtime, case=flows[0]["id"]), tempfile.TemporaryDirectory() as tmp:
                    repo = seed_repo(Path(tmp)); source = repo / "bad.json"
                    source.write_text(json.dumps(analysis_pack(flows)), encoding="utf-8")
                    result = run(runtime, "flow_analysis", "import", "--repo", str(repo), "--analysis", str(source))
                    self.assertNotEqual(result.returncode, 0)

    def test_characteristics_produce_materially_different_designs(self) -> None:
        kinds = ["request-command", "event-message", "scheduled-batch", "lifecycle-stateful", "streaming-interactive", "fan-out-orchestration", "resource-lifecycle"]
        flows = [flow_card(f"flow-kind-{index}", kind) for index, kind in enumerate(kinds, 1)]
        sections = {tuple(flow["document_design"]["section_order"]) for flow in flows}
        forms = {flow["document_design"]["diagrams"][0]["form"] for flow in flows}
        self.assertEqual(len(sections), len(kinds))
        self.assertEqual(forms, {"sequenceDiagram", "flowchart", "stateDiagram-v2"})


class FlowIndex13Tests(unittest.TestCase):
    def test_apply_analysis_adds_only_approved_children_and_migrates_12(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = seed_repo(Path(tmp)); write_flow_index(repo)
                card = flow_card()
                card["decomposition_proposals"] = [{
                    "id": "split", "name": "Split", "rationale": "separate guarantee",
                    "entry_boundary": "child entry", "approved": True,
                    "proposed_flows": [{"id": "flow-child", "name": "Child flow", "family_path": "checkout"}],
                }, {
                    "id": "declined", "name": "No split", "rationale": "not approved",
                    "entry_boundary": "other", "approved": False,
                    "proposed_flows": [{"id": "flow-not-added", "name": "Not added"}],
                }]
                (repo / ".docforge" / "flow-analysis.json").write_text(json.dumps(analysis_pack([card])), encoding="utf-8")
                result = run(runtime, "flow_index", "apply-analysis", "--repo", str(repo))
                self.assertEqual(result.returncode, 0, result.stderr)
                index = json.loads((repo / ".docforge" / "flow-index.json").read_text())
                self.assertEqual(index["version"], "1.3")
                rows = {row["id"]: row for row in index["flows"]}
                self.assertEqual(rows["flow-checkout"]["analysis_state"], "ready")
                self.assertEqual(rows["flow-child"]["parent_flow"], "flow-checkout")
                self.assertEqual(rows["flow-child"]["analysis_state"], "not-analyzed")
                self.assertNotIn("flow-not-added", rows)


if __name__ == "__main__":
    unittest.main()
