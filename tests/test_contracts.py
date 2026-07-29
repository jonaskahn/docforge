#!/usr/bin/env python3
"""Dependency-free Docforge 2.0 contract fixtures."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "docforge" / "scripts"
PORTFOLIO_PATHS = {
    "docs-portfolio/README.md",
    "docs-portfolio/repo-inventory.md",
    "docs-portfolio/system-context.md",
    "docs-portfolio/decisions/README.md",
    "docs-portfolio/security-posture.md",
    "docs-portfolio/operations.md",
    "docs-portfolio/diligence-index.md",
    "docs-portfolio/glossary.md",
}


def run(runtime: str, script: str, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    command = ["python3", str(SCRIPTS / f"{script}.py")] if runtime == "py" else ["node", str(SCRIPTS / f"{script}.js")]
    return subprocess.run(command + list(args), cwd=cwd or ROOT, text=True, capture_output=True)


def load_manifest(repo: Path) -> dict:
    return json.loads((repo / ".docforge" / "manifest.json").read_text(encoding="utf-8"))


def initialize(
    runtime: str,
    repo: Path,
    tier: str,
    *,
    shapes: tuple[str, ...] = (),
    platforms: tuple[str, ...] = (),
    frameworks: tuple[str, ...] = (),
    concerns: tuple[str, ...] = (),
    audiences: tuple[str, ...] = (),
) -> subprocess.CompletedProcess:
    args = ["init", "--repo", str(repo), "--tier", tier]
    for flag, values in (
        ("shape", shapes),
        ("platform", platforms),
        ("framework", frameworks),
        ("concern", concerns),
        ("audience", audiences),
    ):
        for value in values:
            args += [f"--{flag}", value]
    return run(runtime, "manage_manifest", *args)


def blob_hash(content: bytes) -> str:
    return hashlib.sha1(f"blob {len(content)}\0".encode("ascii") + content).hexdigest()


def provenance(
    *,
    doc_id: str,
    path: str,
    tier: str,
    target_depth: str,
    section_id: str,
    source_path: str,
    source_blob: str,
    role: str = "code",
) -> dict:
    return {
        "schema": "1.0",
        "doc_id": doc_id,
        "path": path,
        "generated_at": "2026-07-27T09:12:44Z",
        "tool_version": "2.0.0",
        "tier": tier,
        "target_depth": target_depth,
        "graph": {"provider": "gitnexus", "flow": "native"},
        "sections": [{
            "id": section_id,
            "sources": [{"path": source_path, "git_blob": source_blob, "role": role}],
            "unresolved": [],
        }],
    }


def markdown_with_provenance(value: dict, body: str) -> str:
    return "---\n" + json.dumps({"docforge_provenance": value}, indent=2) + "\n---\n" + body


def normalized(text: str, roots: list[Path]) -> str:
    for root in roots:
        text = text.replace(str(root), "<REPO>")
    text = re.sub(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\+00:00", "<TIME>", text)
    return text.replace(".py", ".runtime").replace(".js", ".runtime")


class CatalogSelectionTests(unittest.TestCase):
    def test_bare_invocation_requires_interactive_scope_intake(self) -> None:
        skill = (ROOT / "skills" / "docforge" / "SKILL.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("## Bare `/docforge` invocation", skill)
        self.assertIn("interactive intake", skill)
        self.assertIn("Present all applicable unresolved questions together", skill)
        self.assertIn("Collect the applicable answers as one response", skill)
        for question in (
            "Goal or action",
            "Documentation tier",
            "Repository profiles",
            "Graph source, only when unresolved",
            "Execution mode",
        ):
            self.assertIn(question, skill)
        self.assertIn("Always wait for explicit confirmation", skill)
        self.assertIn("including when Auto-accept was selected", skill)
        self.assertNotIn("Ask exactly one applicable question at a time", skill)
        self.assertNotIn("[1] Starter", skill)
        self.assertNotIn("Reply with, for example: `2 R`", skill)
        self.assertIn("Do not initialize a\nmanifest", skill)
        self.assertIn("Engineers + beginners", skill)
        self.assertIn("Missing competitors are normal", skill)
        self.assertIn("Never write against an undisplayed manifest\nrevision", skill)
        self.assertIn("/docforge", readme)
        self.assertIn("all applicable unresolved scope questions together", readme)
        self.assertIn("summarizes the complete scope and asks you to", readme)
        self.assertIn("confirm, edit, or cancel", readme)
        self.assertIn("Only one readable provider is required", readme)

    def test_each_tier_profile_selection_has_manifest_indexes(self) -> None:
        profiles = [
            ("shapes", "data-pipeline"),
            ("shapes", "api-service"),
            ("shapes", "web-app"),
            ("shapes", "desktop-app"),
            ("shapes", "library-sdk"),
            ("shapes", "infrastructure-platform"),
            ("audiences", "business-analysts"),
            ("audiences", "product-owners"),
            ("audiences", "coding-agents"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            for tier in ("spine", "diligence", "portfolio"):
                for dimension, profile in profiles:
                    repo = Path(tmp) / f"{tier}-{profile}"
                    repo.mkdir()
                    result = initialize("py", repo, tier, **{dimension: (profile,)})
                    self.assertEqual(result.returncode, 0, result.stderr)
                    paths = {doc["path"] for doc in load_manifest(repo)["documents"]}
                    for selected in paths:
                        if not selected.startswith(("docs/", "docs-portfolio/")):
                            continue
                        parent = str(Path(selected).parent).replace(os.sep, "/")
                        while parent not in ("docs", "docs-portfolio", "."):
                            self.assertIn(f"{parent}/README.md", paths, (tier, profile, selected))
                            parent = str(Path(parent).parent).replace(os.sep, "/")

    def test_every_tier_and_portfolio_layer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            counts = []
            for tier in ("spine", "diligence", "portfolio"):
                repo = Path(tmp) / tier
                repo.mkdir()
                result = initialize("py", repo, tier)
                self.assertEqual(result.returncode, 0, result.stderr)
                manifest = load_manifest(repo)
                self.assertEqual(manifest["version"], "3.0")
                self.assertEqual(manifest["project"]["tier"], tier)
                self.assertEqual(
                    manifest["project"]["profiles"]["audiences"],
                    ["engineers", "beginners"],
                )
                counts.append(len(manifest["documents"]))
                paths = {doc["path"] for doc in manifest["documents"]}
                if tier == "portfolio":
                    self.assertTrue(PORTFOLIO_PATHS <= paths)
            self.assertLess(counts[0], counts[1])
            self.assertLess(counts[1], counts[2])

    def test_all_canonical_profiles_are_accepted_and_frameworks_add_no_tree(self) -> None:
        catalog = json.loads(
            (ROOT / "skills" / "docforge" / ".metadata" / "catalog.json")
            .read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as tmp:
            base_repo = Path(tmp) / "base"
            profile_repo = Path(tmp) / "profiles"
            base_repo.mkdir()
            profile_repo.mkdir()
            self.assertEqual(initialize("py", base_repo, "spine").returncode, 0)
            args = ["init", "--repo", str(profile_repo), "--tier", "spine"]
            flag_for = {
                "shapes": "--shape",
                "platforms": "--platform",
                "frameworks": "--framework",
                "concerns": "--concern",
                "audiences": "--audience",
            }
            for dimension, definitions in catalog["profiles"].items():
                for definition in definitions:
                    args += [flag_for[dimension], definition["id"]]
            result = run("py", "manage_manifest", *args)
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = load_manifest(profile_repo)
            for dimension, definitions in catalog["profiles"].items():
                self.assertEqual(
                    manifest["project"]["profiles"][dimension],
                    [item["id"] for item in definitions],
                )

            framework_repo = Path(tmp) / "frameworks"
            framework_repo.mkdir()
            framework_args = [
                item
                for definition in catalog["profiles"]["frameworks"]
                for item in ("--framework", definition["id"])
            ]
            framework_result = run(
                "py", "manage_manifest", "init",
                "--repo", str(framework_repo), "--tier", "spine",
                *framework_args,
            )
            self.assertEqual(framework_result.returncode, 0, framework_result.stderr)
            base_paths = {doc["path"] for doc in load_manifest(base_repo)["documents"]}
            framework_paths = {
                doc["path"] for doc in load_manifest(framework_repo)["documents"]
            }
            self.assertEqual(framework_paths, base_paths)

    def test_overlap_deduplicates_and_retains_origins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            result = initialize(
                "py", repo, "spine",
                shapes=("api-service", "library-sdk"),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            docs = load_manifest(repo)["documents"]
            quickstarts = [doc for doc in docs if doc["path"] == "docs/product/quickstart.md"]
            self.assertEqual(len(quickstarts), 1)
            origins = quickstarts[0]["selection"]["origins"]
            self.assertEqual(origins, [
                {"kind": "shape", "id": "api-service"},
                {"kind": "shape", "id": "library-sdk"},
            ])

    def test_conditional_and_dynamic_documents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            result = initialize(
                "py", repo, "diligence",
                audiences=("product-owners", "coding-agents"),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            paths = {doc["path"] for doc in load_manifest(repo)["documents"]}
            self.assertNotIn("docs/engineering/conventions.md", paths)
            self.assertNotIn("docs/product/product-owner/backlog-traceability.md", paths)
            fake_adr = "0001-record-" + "architecture-decisions.md"
            self.assertFalse(any("example-" in path or path.endswith(fake_adr) for path in paths))
            rejected = run("py", "manage_manifest", "add", "--repo", str(repo),
                           "--type", "backlog-traceability", "--id", "po-backlog",
                           "--path", "docs/product/product-owner/backlog-traceability.md")
            self.assertEqual(rejected.returncode, 2)

            (repo / "CONVENTIONS.md").write_text("# Conventions\n", encoding="utf-8")
            (repo / ".docforge" / "tickets.json").write_text("[]\n", encoding="utf-8")
            result = initialize(
                "py", repo, "diligence",
                audiences=("product-owners", "coding-agents"),
            )
            self.assertNotEqual(result.returncode, 0)
            result = run("py", "manage_manifest", "init", "--repo", str(repo), "--tier", "diligence",
                         "--audience", "product-owners", "--audience", "coding-agents", "--force")
            self.assertEqual(result.returncode, 0, result.stderr)
            paths = {doc["path"] for doc in load_manifest(repo)["documents"]}
            self.assertIn("docs/engineering/conventions.md", paths)
            self.assertNotIn("docs/product/product-owner/backlog-traceability.md", paths)
            added = run("py", "manage_manifest", "add", "--repo", str(repo),
                        "--type", "backlog-traceability", "--id", "po-backlog",
                        "--path", "docs/product/product-owner/backlog-traceability.md")
            self.assertEqual(added.returncode, 0, added.stderr)
            backlog = next(
                doc for doc in load_manifest(repo)["documents"]
                if doc["id"] == "po-backlog"
            )
            self.assertEqual(
                backlog["selection"]["origins"],
                [
                    {"kind": "dynamic", "id": "backlog-traceability"},
                    {"kind": "audience", "id": "product-owners"},
                    {"kind": "condition", "id": "ticket_evidence"},
                ],
            )

            result = run("py", "manage_manifest", "add", "--repo", str(repo), "--type", "flow",
                         "--id", "flow-checkout", "--path", "docs/flows/checkout.md")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("docs/flows/checkout.md", {doc["path"] for doc in load_manifest(repo)["documents"]})

    def test_flow_requirement_is_per_document(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            result = initialize(
                "py", repo, "spine",
                audiences=("business-analysts", "product-owners", "coding-agents"),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            docs = {doc["id"]: doc for doc in load_manifest(repo)["documents"]}
            self.assertNotIn("flow_graph", docs["agents_architecture"]["requires"])
            self.assertNotIn("flow_graph", docs["agents_patterns"]["requires"])
            self.assertNotIn("flow_graph", docs["agents_testing"]["requires"])
            self.assertIn("flow_graph", docs["agents_flow"]["requires"])
            self.assertIn("flow_graph", docs["agents_glossary"]["requires"])
            self.assertIn("flow_graph", docs["ba_process_flows"]["requires"])
            self.assertIn("flow_graph", docs["ba_business_rules"]["requires"])
            self.assertIn("flow_graph", docs["ba_requirements"]["requires"])
            self.assertNotIn("flow_graph", docs["po_features"]["requires"])
            self.assertNotIn("flow_graph", docs["po_metrics"]["requires"])
            self.assertNotIn("flow_graph", docs["po_release_notes"]["requires"])

    def test_audience_profile_paths_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            result = initialize(
                "py", repo, "spine",
                audiences=("business-analysts", "product-owners", "coding-agents"),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            paths = {doc["path"] for doc in load_manifest(repo)["documents"]}
            self.assertTrue({
                "docs/product/business-analyst/README.md",
                "docs/product/business-analyst/process-flows.md",
                "docs/product/business-analyst/business-rules.md",
                "docs/product/business-analyst/requirements-traceability.md",
                "docs/product/product-owner/README.md",
                "docs/product/product-owner/feature-catalog.md",
                "docs/product/product-owner/success-metrics.md",
                "docs/product/product-owner/release-notes.md",
                "AGENTS.md",
                "docs/agents/architecture.md",
                "docs/agents/flow.md",
            } <= paths)
            self.assertNotIn(
                "docs/product/product-owner/backlog-traceability.md", paths,
            )

    def test_aliases_normalize_and_obsolete_overlay_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                result = run(
                    runtime, "manage_manifest", "init",
                    "--repo", str(repo), "--tier", "diligence",
                    "--shape", "desktop", "--shape", "desktop-app",
                    "--platform", "mac", "--audience", "agent",
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                profiles = load_manifest(repo)["project"]["profiles"]
                self.assertEqual(profiles["shapes"], ["desktop-app"])
                self.assertEqual(profiles["platforms"], ["macos"])
                self.assertEqual(profiles["audiences"], ["coding-agents"])
                obsolete = run(
                    runtime, "manage_manifest", "init",
                    "--repo", str(repo), "--tier", "spine",
                    "--overlay", "agent", "--force",
                )
                self.assertEqual(obsolete.returncode, 2)
                self.assertIn("--overlay is unsupported in Docforge 2.0", obsolete.stderr)

    def test_desktop_mobile_and_specialized_shape_packs(self) -> None:
        expected = {
            "desktop-app": {
                "docs/architecture/application-lifecycle.md",
                "docs/architecture/ui-and-state.md",
                "docs/architecture/platform-integration.md",
                "docs/security/permissions.md",
                "docs/reference/platform-compatibility.md",
                "docs/operations/distribution.md",
            },
            "cli-tui": {
                "docs/reference/commands.md",
                "docs/reference/output-and-exit-codes.md",
                "docs/operations/distribution.md",
            },
            "embedded-iot": {
                "docs/architecture/hardware-map.md",
                "docs/architecture/firmware-lifecycle.md",
                "docs/operations/flashing-and-recovery.md",
            },
            "smart-contract": {
                "docs/architecture/contract-system.md",
                "docs/security/economic-invariants.md",
                "docs/operations/network-deployment.md",
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            for shape, required in expected.items():
                repo = Path(tmp) / shape
                repo.mkdir()
                result = initialize("py", repo, "spine", shapes=(shape,))
                self.assertEqual(result.returncode, 0, result.stderr)
                paths = {doc["path"] for doc in load_manifest(repo)["documents"]}
                self.assertTrue(required <= paths, (shape, required - paths))

    def test_profile_detection_for_native_macos_mixed_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            project = repo / "EasyKey.xcodeproj"
            project.mkdir()
            (project / "project.pbxproj").write_text(
                "SDKROOT = macosx; com.apple.product-type.framework;\n",
                encoding="utf-8",
            )
            source = repo / "App.swift"
            source.write_text(
                "import SwiftUI\nimport AppKit\n// accessibility Keychain SMAppService\n",
                encoding="utf-8",
            )
            (repo / "Localizable.xcstrings").write_text("{}\n", encoding="utf-8")
            outputs = []
            detected_payloads = []
            for runtime in ("py", "js"):
                result = run(runtime, "detect_profiles", "--repo", str(repo), "--json")
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                detected = {
                    (item["dimension"], item["id"]): item["confidence"]
                    for item in payload["detections"]
                }
                for item in (
                    ("shapes", "desktop-app"),
                    ("shapes", "library-sdk"),
                    ("platforms", "macos"),
                    ("frameworks", "swiftui"),
                    ("frameworks", "appkit"),
                    ("concerns", "localization"),
                    ("concerns", "secure-storage"),
                    ("concerns", "login-helper"),
                ):
                    self.assertIn(item, detected)
                outputs.append(normalized(result.stdout, [repo]))
                if runtime == "py":
                    init_result = initialize(
                        runtime, repo, "spine",
                        shapes=("desktop-app", "library-sdk"),
                        platforms=("macos",),
                        frameworks=("swiftui", "appkit"),
                        concerns=("localization", "secure-storage", "login-helper"),
                    )
                else:
                    init_result = run(
                        runtime, "manage_manifest", "init",
                        "--repo", str(repo), "--tier", "spine",
                        "--shape", "desktop-app", "--shape", "library-sdk",
                        "--platform", "macos",
                        "--framework", "swiftui", "--framework", "appkit",
                        "--concern", "localization",
                        "--concern", "secure-storage",
                        "--concern", "login-helper",
                        "--force",
                    )
                self.assertEqual(init_result.returncode, 0, init_result.stderr)
                saved = load_manifest(repo)
                self.assertNotIn(
                    "accessibility", saved["project"]["profiles"]["concerns"],
                )
                detected_payloads.append(saved["discovery"])
            self.assertEqual(outputs[0], outputs[1])
            self.assertEqual(detected_payloads[0], detected_payloads[1])
            self.assertTrue(detected_payloads[0])


class PairedRuntimeTests(unittest.TestCase):
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
                    self.assertEqual((py_repo / rel).read_bytes(), (js_repo / rel).read_bytes())

    def test_unknown_flags_exit_two(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                result = run(runtime, "scaffold_docs", "--repo", tmp, "--manifest", "missing", "--wat")
                self.assertEqual(result.returncode, 2)
                result = run(runtime, "precheck_graph", "--repo", tmp, "--need", "domain")
                self.assertEqual(result.returncode, 2)

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


class GraphAndStateTests(unittest.TestCase):
    def test_missing_native_and_derived_graph_states(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for runtime in ("py", "js"):
                self.assertEqual(run(runtime, "precheck_graph", "--repo", str(repo), "--need", "code").returncode, 1)
            (repo / ".ua").mkdir()
            (repo / ".ua" / "knowledge-graph.json").write_text("{}\n", encoding="utf-8")
            for runtime in ("py", "js"):
                self.assertEqual(run(runtime, "precheck_graph", "--repo", str(repo), "--need", "code").returncode, 0)
                self.assertEqual(run(runtime, "precheck_graph", "--repo", str(repo), "--need", "flow").returncode, 1)
            (repo / ".docforge" / "tmp").mkdir(parents=True)
            (repo / ".docforge" / "tmp" / "flow-graph.json").write_text("{}\n", encoding="utf-8")
            for runtime in ("py", "js"):
                self.assertEqual(run(runtime, "precheck_graph", "--repo", str(repo), "--need", "flow").returncode, 0)
            (repo / ".ua" / "domain-graph.json").write_text("{}\n", encoding="utf-8")
            (repo / ".codegraph").mkdir()
            (repo / ".codegraph" / "codegraph.db").write_bytes(b"fixture")
            py_result = run("py", "precheck_graph", "--repo", str(repo), "--need", "flow")
            js_result = run("js", "precheck_graph", "--repo", str(repo), "--need", "flow")
            self.assertEqual(normalized(py_result.stdout, [repo]), normalized(js_result.stdout, [repo]))
            self.assertIn("2 sources are ready", py_result.stdout)

    def test_gitnexus_current_metadata_and_native_process_detection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            graph_dir = repo / ".gitnexus"
            graph_dir.mkdir()
            (graph_dir / "lbug").write_bytes(b"fixture")
            (graph_dir / "gitnexus.json").write_text(json.dumps({
                "stats": {"nodes": 12, "edges": 20, "processes": 3},
            }) + "\n", encoding="utf-8")
            outputs = []
            for runtime in ("py", "js"):
                detected = run(
                    runtime, "graph_source_gitnexus", "detect",
                    "--repo", str(repo),
                )
                self.assertEqual(detected.returncode, 0, detected.stderr)
                self.assertIn("3 processes", detected.stdout)
                precheck = run(
                    runtime, "precheck_graph", "--repo", str(repo),
                    "--need", "flow",
                )
                self.assertEqual(precheck.returncode, 0, precheck.stderr)
                self.assertIn("(source: gitnexus, authoritative)", precheck.stdout)
                self.assertNotIn("CodeGraph", precheck.stdout)
                self.assertNotIn("Understand", precheck.stdout)
                self.assertNotIn("MISSING", precheck.stdout)
                outputs.append(normalized(precheck.stdout, [repo]))
            self.assertEqual(outputs[0], outputs[1])

    def test_completion_requires_independent_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.assertEqual(initialize("py", repo, "spine").returncode, 0)
            for status in ("in_progress", "generated"):
                result = run("py", "manage_manifest", "set", "--repo", str(repo), "--id", "arch_high_level", "--status", status)
                self.assertEqual(result.returncode, 0, result.stderr)
            rejected = run("py", "manage_manifest", "set", "--repo", str(repo), "--id", "arch_high_level", "--status", "complete")
            self.assertEqual(rejected.returncode, 2)
            report = repo / ".docforge" / "audits" / "arch_high_level.md"
            report.parent.mkdir(parents=True)
            report.write_text("# Audit\n", encoding="utf-8")
            passed = run("py", "manage_manifest", "audit", "--repo", str(repo), "--id", "arch_high_level",
                         "--mode", "cold-pass", "--verdict", "PASS",
                         "--report", ".docforge/audits/arch_high_level.md")
            self.assertEqual(passed.returncode, 0, passed.stderr)
            complete = run("py", "manage_manifest", "set", "--repo", str(repo), "--id", "arch_high_level", "--status", "complete")
            self.assertEqual(complete.returncode, 0, complete.stderr)
            self.assertEqual(
                run("py", "manage_manifest", "set", "--repo", str(repo), "--id",
                    "arch_high_level", "--status", "in_progress").returncode,
                0,
            )
            self.assertEqual(
                run("py", "manage_manifest", "set", "--repo", str(repo), "--id",
                    "arch_high_level", "--status", "generated").returncode,
                0,
            )
            stale_pass = run("py", "manage_manifest", "set", "--repo", str(repo),
                             "--id", "arch_high_level", "--status", "complete")
            self.assertEqual(stale_pass.returncode, 2)
            repassed = run("py", "manage_manifest", "audit", "--repo", str(repo),
                           "--id", "arch_high_level", "--mode", "subagent",
                           "--verdict", "PASS",
                           "--report", ".docforge/audits/arch_high_level.md")
            self.assertEqual(repassed.returncode, 0, repassed.stderr)
            doc = next(item for item in load_manifest(repo)["documents"] if item["id"] == "arch_high_level")
            self.assertEqual(doc["audit"]["mode"], "subagent")


class ProvenanceAndAuditTests(unittest.TestCase):
    def test_root_sync_preserves_manifest_and_detects_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "source.txt"
            source.write_text("one\n", encoding="utf-8")
            content_hash = blob_hash(source.read_bytes())
            doc = repo / "README.md"
            doc.write_text(
                markdown_with_provenance(
                    provenance(
                        doc_id="root_readme", path="README.md", tier="spine",
                        target_depth="overview", section_id="readme",
                        source_path="source.txt", source_blob=content_hash,
                    ),
                    "# Readme\n",
                ),
                encoding="utf-8",
            )
            manifest = {
                "version": "3.0",
                "project": {"name": "fixture", "root": str(repo), "tier": "spine", "profiles": {
                    "shapes": [], "platforms": [], "frameworks": [],
                    "concerns": [], "audiences": [],
                }},
                "discovery": [],
                "documents": [{
                    "id": "root_readme", "type": "root-readme", "path": "README.md",
                    "status": "complete", "provenance": {
                        "schema": "1.0", "doc_id": "root_readme", "path": "README.md",
                        "generated_at": "<GENERATED_AT>", "tool_version": "2.0.0",
                        "tier": "spine", "target_depth": "overview",
                        "graph": {"provider": "<GRAPH_PROVIDER>", "flow": "<FLOW_CAPABILITY>"},
                        "sections": [],
                    },
                    "selection": {"origins": [], "evidence": []}, "audit": {"verdict": "PASS"},
                }],
                "metadata": {},
            }
            manifest_path = repo / ".docforge" / "manifest.json"
            manifest_path.parent.mkdir()
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            for runtime in ("py", "js"):
                result = run(runtime, "check_staleness", "--manifest", str(manifest_path), "--sync-provenance")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("FRESH", result.stdout)
                saved = json.loads(manifest_path.read_text(encoding="utf-8"))
                self.assertEqual(saved["documents"][0]["type"], "root-readme")
                self.assertEqual(saved["documents"][0]["status"], "complete")
                self.assertEqual(saved["documents"][0]["provenance"]["schema"], "1.0")
                self.assertEqual(saved["documents"][0]["provenance"]["doc_id"], "root_readme")
            source.write_text("two\n", encoding="utf-8")
            for runtime in ("py", "js"):
                result = run(runtime, "check_staleness", "--manifest", str(manifest_path), "--section", "readme")
                self.assertEqual(result.returncode, 1)
                self.assertIn("PARTIAL", result.stdout)
            source.unlink()
            for runtime in ("py", "js"):
                result = run(runtime, "check_staleness", "--manifest", str(manifest_path))
                self.assertEqual(result.returncode, 1)
                self.assertIn("MISSING", result.stdout)
            saved = json.loads(manifest_path.read_text(encoding="utf-8"))
            saved["documents"][0]["provenance"]["sections"] = []
            manifest_path.write_text(json.dumps(saved, indent=2) + "\n", encoding="utf-8")
            for runtime in ("py", "js"):
                result = run(runtime, "check_staleness", "--manifest", str(manifest_path))
                self.assertEqual(result.returncode, 1)
                self.assertIn("UNTRACKED", result.stdout)

    def test_scaffold_audit_exit_codes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            document = {
                "id": "only", "type": "generic", "path": "docs/only.md", "group": "reference",
                "selection": {"origins": [], "evidence": []}, "status": "complete", "requires": [],
                "scaffold_template": "generic.md", "instruction_file": None, "target_depth": "reference",
                "write_order": 1, "provenance_mode": "sections", "audit_profile": "standard",
                "provenance": {"sections": []}, "audit": None,
            }
            manifest = {
                "version": "3.0", "project": {"name": "fixture", "root": str(repo), "tier": "spine", "profiles": {
                    "shapes": [], "platforms": [], "frameworks": [],
                    "concerns": [], "audiences": [],
                }}, "discovery": [],
                "documents": [document], "metadata": {},
            }
            manifest_path = repo / ".docforge" / "manifest.json"
            manifest_path.parent.mkdir()
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            for runtime in ("py", "js"):
                self.assertEqual(run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(manifest_path), "--audit").returncode, 1)
            source = repo / "source.txt"
            source.write_text("evidence\n", encoding="utf-8")
            target = repo / "docs" / "only.md"
            target.parent.mkdir()
            target.write_text(
                markdown_with_provenance(
                    provenance(
                        doc_id="only", path="docs/only.md", tier="spine",
                        target_depth="reference", section_id="only",
                        source_path="source.txt", source_blob=blob_hash(source.read_bytes()),
                    ),
                    "# Only\n\nComplete evidence-backed content.\n",
                ),
                encoding="utf-8",
            )
            for runtime in ("py", "js"):
                result = run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(manifest_path), "--audit")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_provenance_defect_categories_and_runtime_parity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "source.txt"
            source.write_text("evidence\n", encoding="utf-8")
            good = provenance(
                doc_id="only", path="docs/only.md", tier="spine",
                target_depth="reference", section_id="only",
                source_path="source.txt", source_blob=blob_hash(source.read_bytes()),
            )
            document = {
                "id": "only", "type": "generic", "path": "docs/only.md", "group": "reference",
                "selection": {"origins": [], "evidence": []}, "status": "complete", "requires": [],
                "scaffold_template": "generic.md", "instruction_file": None, "target_depth": "reference",
                "write_order": 1, "provenance_mode": "sections", "audit_profile": "standard",
                "provenance": good, "audit": None,
            }
            manifest = {
                "version": "3.0", "project": {
                    "name": "fixture", "root": str(repo), "tier": "spine",
                    "profiles": {"shapes": [], "platforms": [], "frameworks": [], "concerns": [], "audiences": []},
                },
                "discovery": [], "documents": [document], "metadata": {},
            }
            manifest_path = repo / ".docforge" / "manifest.json"
            manifest_path.parent.mkdir()
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            target = repo / "docs" / "only.md"
            target.parent.mkdir()
            cases = {
                "MISSING PROVENANCE": "# Only\n\nBody.\n",
                "UNPARSEABLE PROVENANCE": "---\n{\n---\n# Only\n\nBody.\n",
                "LEGACY PROVENANCE": "---\n" + json.dumps({"docforge_provenance": {"sections": []}}, indent=2) + "\n---\n# Only\n\nBody.\n",
                "EMPTY PROVENANCE": markdown_with_provenance({**good, "sections": []}, "# Only\n\nBody.\n"),
                "INVALID BLOB": markdown_with_provenance({
                    **good,
                    "sections": [{**good["sections"][0], "sources": [{
                        "path": "source.txt", "git_blob": "placeholder", "role": "code",
                    }]}],
                }, "# Only\n\nBody.\n"),
                "UNKNOWN SOURCE": markdown_with_provenance({
                    **good,
                    "sections": [{**good["sections"][0], "sources": [{
                        "path": "missing.txt", "git_blob": "0" * 40, "role": "code",
                    }]}],
                }, "# Only\n\nBody.\n"),
                "UNKNOWN SECTION": markdown_with_provenance({
                    **good,
                    "sections": [{**good["sections"][0], "id": "not-a-heading"}],
                }, "# Only\n\nBody.\n"),
            }
            for category, text in cases.items():
                with self.subTest(category=category):
                    target.write_text(text, encoding="utf-8")
                    outputs = []
                    for runtime in ("py", "js"):
                        result = run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(manifest_path), "--audit")
                        self.assertEqual(result.returncode, 1)
                        self.assertIn(category, result.stdout)
                        outputs.append(normalized(result.stdout, [repo]))
                    self.assertEqual(outputs[0], outputs[1])

    def test_planned_scaffold_tokens_are_not_written_provenance_defects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for runtime in ("py", "js"):
                repo = Path(tmp) / runtime
                repo.mkdir()
                self.assertEqual(initialize(runtime, repo, "spine").returncode, 0)
                manifest_path = repo / ".docforge" / "manifest.json"
                created = run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(manifest_path), "--document", "arch_high_level")
                self.assertEqual(created.returncode, 0, created.stderr)
                text = (repo / "docs" / "architecture" / "high-level.md").read_text(encoding="utf-8")
                self.assertTrue(text.startswith("---\n{\n"))
                self.assertIn('"schema": "1.0"', text)
                result = run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(manifest_path), "--audit")
                for category in ("EMPTY PROVENANCE", "MISSING PROVENANCE", "LEGACY PROVENANCE", "UNPARSEABLE PROVENANCE"):
                    self.assertNotIn(category, result.stdout)

    def test_staleness_reports_no_blob_unparseable_and_legacy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "source.txt"
            source.write_text("evidence\n", encoding="utf-8")
            value = provenance(
                doc_id="only", path="docs/only.md", tier="spine",
                target_depth="reference", section_id="only",
                source_path="source.txt", source_blob="placeholder",
            )
            document = {
                "id": "only", "type": "generic", "path": "docs/only.md",
                "status": "complete", "provenance_mode": "sections", "provenance": value,
            }
            manifest = {
                "version": "3.0", "project": {"root": str(repo)},
                "documents": [document],
            }
            manifest_path = repo / ".docforge" / "manifest.json"
            manifest_path.parent.mkdir()
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            target = repo / "docs" / "only.md"
            target.parent.mkdir()
            target.write_text(markdown_with_provenance(value, "# Only\n"), encoding="utf-8")
            for runtime in ("py", "js"):
                result = run(runtime, "check_staleness", "--manifest", str(manifest_path))
                self.assertEqual(result.returncode, 1)
                self.assertIn("NO_BLOB", result.stdout)
            target.write_text("---\n{\n---\n# Only\n", encoding="utf-8")
            outputs = []
            for runtime in ("py", "js"):
                result = run(runtime, "check_staleness", "--manifest", str(manifest_path), "--sync-provenance")
                self.assertEqual(result.returncode, 1)
                self.assertIn("UNPARSEABLE", result.stdout)
                outputs.append(normalized(result.stdout, [repo]))
            self.assertEqual(outputs[0], outputs[1])
            target.write_text("---\n" + json.dumps({"docforge_provenance": {"sections": []}}, indent=2) + "\n---\n# Only\n", encoding="utf-8")
            for runtime in ("py", "js"):
                result = run(runtime, "check_staleness", "--manifest", str(manifest_path), "--sync-provenance")
                self.assertEqual(result.returncode, 1)
                self.assertIn("UNTRACKED", result.stdout)
                self.assertIn("legacy provenance", result.stdout)

    def test_lint_placeholder_token_link_and_forge_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            target = repo / "target.md"
            target.write_text("# Target\n\nBody.\n", encoding="utf-8")
            subject = repo / "subject.md"
            subject.write_text(
                "# Subject\n\n{{unfinished}}\n\n<EXTERNAL_CONTACT>\n\n"
                "[dead](missing.md)\n\nHosted on GitHub.\n",
                encoding="utf-8",
            )
            for runtime in ("py", "js"):
                result = run(runtime, "lint_document", "--file", str(subject), "--json")
                self.assertEqual(result.returncode, 1)
                payload = json.loads(result.stdout)
                kinds = {item["kind"] for item in payload["defects"]}
                self.assertTrue({"scaffold-marker", "dead-link", "forge-leakage"} <= kinds)
                self.assertEqual(payload["tokens"], ["<EXTERNAL_CONTACT>"])

    def test_lint_provenance_gate_has_paired_defects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".docforge").mkdir()
            source = repo / "source.txt"
            source.write_text("evidence\n", encoding="utf-8")
            value = provenance(
                doc_id="subject", path="subject.md", tier="spine",
                target_depth="reference", section_id="frontmatter-only",
                source_path="source.txt", source_blob="placeholder",
            )
            subject = repo / "subject.md"
            subject.write_text(
                markdown_with_provenance(value, "# Subject\n\nBody.\n"),
                encoding="utf-8",
            )
            outputs = []
            for runtime in ("py", "js"):
                result = run(runtime, "lint_document", "--file", str(subject), "--json")
                self.assertEqual(result.returncode, 1)
                payload = json.loads(result.stdout)
                kinds = {item["kind"] for item in payload["defects"]}
                self.assertTrue({"invalid blob", "unknown section"} <= kinds)
                outputs.append(payload["defects"])
            self.assertEqual(outputs[0], outputs[1])

    def test_folder_only_promotion_is_audit_defect(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "source.txt"
            source.write_text("flow\n", encoding="utf-8")
            target = repo / "docs" / "flows" / "checkout" / "README.md"
            target.parent.mkdir(parents=True)
            target.write_text(
                markdown_with_provenance(
                    provenance(
                        doc_id="checkout", path="docs/flows/checkout/README.md",
                        tier="diligence", target_depth="deep-dive",
                        section_id="checkout", source_path="source.txt",
                        source_blob=blob_hash(source.read_bytes()),
                    ),
                    "# Checkout\n\nComplete overview.\n",
                ),
                encoding="utf-8",
            )
            document = {
                "id": "checkout", "type": "flow", "path": "docs/flows/checkout/README.md",
                "group": "flows", "selection": {"origins": [], "evidence": []},
                "status": "complete", "requires": ["flow_graph"], "scaffold_template": "generic.md",
                "instruction_file": "flows.md", "target_depth": "deep-dive", "write_order": 1,
                "provenance_mode": "sections", "audit_profile": "flow",
                "provenance": {"sections": []}, "audit": None,
            }
            manifest = {
                "version": "3.0",
                "project": {"name": "fixture", "root": str(repo), "tier": "diligence", "profiles": {
                    "shapes": [], "platforms": [], "frameworks": [],
                    "concerns": [], "audiences": [],
                }},
                "discovery": [],
                "documents": [document], "metadata": {},
            }
            manifest_path = repo / ".docforge" / "manifest.json"
            manifest_path.parent.mkdir()
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            for runtime in ("py", "js"):
                result = run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(manifest_path), "--audit")
                self.assertEqual(result.returncode, 1)
                self.assertIn("FOLDER-ONLY PROMOTION", result.stdout)


if __name__ == "__main__":
    unittest.main()
