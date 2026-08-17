"""Graph-provider precheck/selection and flow-index harvest/revise/organize/render."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from _support import (
    CLI_JS,
    ROOT,
    initialize,
    load_manifest,
    normalized,
    run,
    write_flow_index,
    write_gitnexus_interchange,
)
from runtime.graph.python.graph_source_registry import SOURCES as GRAPH_SOURCES


class GraphProviderTests(unittest.TestCase):
    def test_set_graph_accepts_every_registered_provider_name(self) -> None:
        """A provider name is only ever rejected as `unknown` when it truly
        isn't in the registry — this loop stays valid without editing if a
        4th source is ever added to graph_source_registry.py/.js."""
        names = [source["name"] for source in GRAPH_SOURCES]
        self.assertGreaterEqual(len(names), 1)
        for runtime_name in ("py", "js"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                self.assertEqual(initialize(runtime_name, repo, "spine").returncode, 0)
                for name in names:
                    result = run(
                        runtime_name, "manage_manifest", "set-graph", "--repo", str(repo),
                        "--provider", name,
                    )
                    self.assertNotIn("unknown graph provider", result.stderr)
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

    def test_non_git_root_does_not_leak_ancestor_graph(self) -> None:
        """A .docforge-marked root with no .git of its own must stop the
        upward graph search there — it must not pick up an unrelated graph
        sitting in some ancestor directory (e.g. a parent workspace folder)."""
        with tempfile.TemporaryDirectory() as tmp:
            ancestor = Path(tmp)
            (ancestor / ".ua").mkdir()
            (ancestor / ".ua" / "knowledge-graph.json").write_text("{}\n", encoding="utf-8")
            project = ancestor / "project"
            (project / ".docforge").mkdir(parents=True)
            for runtime in ("py", "js"):
                result = run(runtime, "precheck_graph", "--repo", str(project), "--need", "code")
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn("MISSING  code graph", result.stdout)

    def test_precheck_graph_still_reports_blocked_for_a_pure_collection_root(self) -> None:
        """precheck_graph.py never gains a tier-aware bypass or flag; the
        Portfolio-collection exception (rules.md/planning.md) is entirely an
        agent-followed workflow decision gated on discover_child_repos'
        root_profile_evidence, never a flag on this script."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "svc-a" / ".git").mkdir(parents=True)
            (root / "svc-b" / ".git").mkdir(parents=True)
            for runtime in ("py", "js"):
                result = run(runtime, "precheck_graph", "--repo", str(root), "--need", "code")
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn("BLOCKED", result.stdout)

    def test_git_root_climb_from_subdirectory_still_finds_graph(self) -> None:
        """Pre-existing behavior is unchanged: invoking from a subdirectory
        of a real git repo still climbs up to .git and finds the graph at
        the root."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".git").mkdir()
            (repo / ".ua").mkdir()
            (repo / ".ua" / "knowledge-graph.json").write_text("{}\n", encoding="utf-8")
            sub = repo / "src" / "nested"
            sub.mkdir(parents=True)
            for runtime in ("py", "js"):
                result = run(runtime, "precheck_graph", "--repo", str(sub), "--need", "code")
                self.assertEqual(result.returncode, 0, result.stdout)
                self.assertIn("READY", result.stdout)


class FlowIndexTests(unittest.TestCase):
    def test_flow_index_groups_processes_and_matches_runtime_peers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            processes = []
            for entry in range(10):
                for terminal in range(3):
                    processes.append({
                        "id": f"proc-{entry}-{terminal}",
                        "heuristicLabel": f"Entry{entry} -> Terminal{terminal}",
                        "processType": "cross_community" if terminal == 0 else "intra_community",
                        "stepCount": terminal + 2,
                        "communities": ["comm-a", "comm-b"],
                        "entryPointId": f"Function:src/handlers/Entry{entry}.py:Entry{entry}",
                        "terminalId": f"Function:src/services/Terminal.py:Terminal{terminal}",
                    })
            interchange = {
                "routes": [],
                "processes": processes,
                "communities": [
                    {"id": "comm-a", "heuristicLabel": "API"},
                    {"id": "comm-b", "heuristicLabel": "Services"},
                ],
            }

            indexes = []
            for runtime in ("py", "js"):
                repo = root / runtime
                repo.mkdir()
                write_gitnexus_interchange(repo, interchange)
                result = run(
                    runtime, "flow_index", "harvest",
                    "--repo", str(repo),
                    "--main-limit", "3",
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                index = json.loads((repo / ".docforge/flow-index.json").read_text())
                self.assertEqual(index["summary"]["total"], 10)
                self.assertEqual(index["summary"]["main"], 3)
                self.assertEqual(index["summary"]["deferred"], 7)
                self.assertTrue(all(len(row["evidence"][0]["terminalIds"]) == 3 for row in index["flows"]))
                render = run(runtime, "flow_index", "render", "--repo", str(repo))
                self.assertEqual(render.returncode, 0, render.stderr)
                matrix = (repo / "docs/flows/README.md").read_text()
                self.assertIn("| deferred |", matrix)
                indexes.append(index["flows"])
            for rows in indexes:
                for row in rows:
                    for evidence in row["evidence"]:
                        evidence["artifact"] = Path(evidence["artifact"]).name
            self.assertEqual(indexes[0], indexes[1])

            easy_repo = root / "easy"
            easy_repo.mkdir()
            write_gitnexus_interchange(easy_repo, {
                "routes": [],
                "processes": [processes[0]],
                "communities": [],
            })
            result = run("py", "flow_index", "harvest", "--repo", str(easy_repo))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                json.loads((easy_repo / ".docforge/flow-index.json").read_text())["summary"]["total"],
                1,
            )

    def test_flow_index_augments_partial_ua_domain_graph_across_runtimes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            domain = {
                "nodes": [
                    {"id": "domain:orders", "type": "domain", "name": "Orders"},
                    {"id": "flow:create-order", "type": "flow", "name": "Create Order",
                     "domainMeta": {"entryPoint": "POST /orders", "entryType": "http"}},
                    {"id": "step:create-order:receive", "type": "step", "name": "Receive",
                     "filePath": "src/Controllers/OrderController.cs"},
                ],
                "edges": [
                    {"source": "domain:orders", "target": "flow:create-order", "type": "contains_flow"},
                    {"source": "flow:create-order", "target": "step:create-order:receive", "type": "flow_step"},
                ],
            }
            knowledge = {
                "nodes": [
                    {"id": "class:controller", "type": "class", "name": "OrderController",
                     "filePath": "src/Controllers/OrderController.cs"},
                    {"id": "function:get", "type": "function", "name": "GetOrders",
                     "filePath": "src/Controllers/OrderController.cs"},
                    {"id": "function:helper", "type": "function", "name": "formatDate",
                     "filePath": "src/Controllers/OrderController.cs"},
                ],
                "edges": [
                    {"source": "class:controller", "target": "function:get", "type": "contains"},
                    {"source": "class:controller", "target": "function:helper", "type": "contains"},
                ],
                "layers": [{"name": "Presentation / API", "nodeIds": ["class:controller", "function:get", "function:helper"]}],
            }
            outputs = []
            for runtime in ("py", "js"):
                repo = root / runtime
                ua = repo / ".ua"
                ua.mkdir(parents=True)
                (ua / "domain-graph.json").write_text(json.dumps(domain), encoding="utf-8")
                (ua / "knowledge-graph.json").write_text(json.dumps(knowledge), encoding="utf-8")
                result = run(runtime, "flow_index", "harvest", "--repo", str(repo), "--main-limit", "2")
                self.assertEqual(result.returncode, 0, result.stderr)
                index = json.loads((repo / ".docforge/flow-index.json").read_text())
                self.assertEqual(index["summary"]["confirmed"], 1)
                self.assertEqual({row["name"] for row in index["flows"]},
                                 {"Create Order", "OrderController", "GetOrders"})
                self.assertEqual(index["flows"][0]["name"], "Create Order")
                outputs.append(index["flows"])
            for rows in outputs:
                for row in rows:
                    for evidence in row["evidence"]:
                        evidence["artifact"] = Path(evidence["artifact"]).name
            self.assertEqual(outputs[0], outputs[1])

    def test_flow_index_dedups_community_labels_and_near_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            interchange = {
                "routes": [],
                "processes": [
                    {
                        "id": "proc-a",
                        "entryPointId": "Function:src/search/handler.ts:create_order",
                        "terminalId": "Function:src/db.ts:save",
                        "processType": "cross_community",
                        "stepCount": 4,
                        "communities": ["comm_search_a", "comm_search_b", "comm_jobs"],
                    },
                    {
                        "id": "proc-b",
                        # Different symbol, same file + display name slug -> near-merge.
                        "entryPointId": "Function:src/search/handler.ts:createOrderHandler",
                        "terminalId": "Function:src/db.ts:save",
                        "processType": "cross_community",
                        "stepCount": 6,
                        "communities": ["comm_search_a", "comm_jobs"],
                    },
                ],
                "communities": [
                    {"id": "comm_search_a", "heuristicLabel": "Search"},
                    {"id": "comm_search_b", "heuristicLabel": "Search"},
                    {"id": "comm_jobs", "heuristicLabel": "Jobs"},
                ],
            }

            for runtime in ("py", "js"):
                repo = root / runtime
                repo.mkdir()
                write_gitnexus_interchange(repo, interchange)
                # Force identical display names so path+name near-key collides.
                # Symbols differ, so exact filePath::symbol keys stay distinct first.
                result = run(
                    runtime, "flow_index", "harvest",
                    "--repo", str(repo),
                    "--main-limit", "5",
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                index = json.loads((repo / ".docforge/flow-index.json").read_text(encoding="utf-8"))
                # Without renaming, symbols become names; rewrite names via a second
                # harvest is awkward, so assert label uniqueness + communities file
                # from this export, and assert near-merge with equalized names below.
                self.assertIn("Wrote compact communities summary", result.stdout)
                communities_md = (repo / ".docforge/tmp/communities.md").read_text(encoding="utf-8")
                self.assertIn("| Label | Count | Community IDs |", communities_md)
                self.assertIn("| Search | 2 |", communities_md)
                self.assertIn("| Jobs | 1 |", communities_md)
                self.assertNotIn("| id | heuristicLabel |", communities_md)
                communities_json = json.loads(
                    (repo / ".docforge/tmp/communities.json").read_text(encoding="utf-8")
                )
                self.assertEqual(len(communities_json["labels"]), 2)

                three_id_row = next(
                    row for row in index["flows"]
                    if row["entry_ref"].get("symbol") == "create_order"
                )
                # Unique labels only (not "Search, Search, Jobs").
                self.assertEqual(three_id_row["area"], "Jobs, Search")
                # Distinct community IDs still drive boundaries (3 ids -> 2).
                self.assertEqual(three_id_row["reach"]["boundaries"], 2)

            # Near-duplicate merge: same path + same slugify(name), different symbols.
            merge_interchange = {
                "routes": [
                    {
                        "id": "route-1",
                        "path": "POST /orders",
                        "filePath": "src/orders.ts",
                        "symbol": "create_order",
                        "name": "Create Order",
                    },
                    {
                        "id": "route-2",
                        "path": "POST /orders/v2",
                        "filePath": "src/orders.ts",
                        "symbol": "createOrderHandler",
                        "name": "Create Order",
                    },
                ],
                "processes": [],
                "communities": [],
            }
            for runtime in ("py", "js"):
                repo = root / f"merge-{runtime}"
                repo.mkdir()
                write_gitnexus_interchange(repo, merge_interchange)
                result = run(
                    runtime, "flow_index", "harvest",
                    "--repo", str(repo),
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                index = json.loads((repo / ".docforge/flow-index.json").read_text(encoding="utf-8"))
                self.assertEqual(index["summary"]["total"], 1, index["flows"])
                self.assertEqual(index["flows"][0]["name"], "Create Order")

    def test_flow_index_revise_merges_stubs_and_notices_across_runtimes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            processes = [
                {
                    "id": f"proc-{index}",
                    "entryPointId": f"Function:src/handlers/h{index}.ts:handle{index}",
                    "terminalId": f"Function:src/db.ts:query{index}",
                    "processType": "cross_community",
                    "stepCount": 4 + index,
                    "communities": ["comm-a", "comm-b"],
                }
                for index in range(5)
            ]
            interchange = {
                "routes": [],
                "processes": processes,
                "communities": [
                    {"id": "comm-a", "heuristicLabel": "API"},
                    {"id": "comm-b", "heuristicLabel": "Services"},
                ],
            }

            for runtime in ("py", "js"):
                repo = root / runtime
                repo.mkdir()
                write_gitnexus_interchange(repo, interchange)
                harvest = run(
                    runtime, "flow_index", "harvest",
                    "--repo", str(repo),
                    "--main-limit", "2",
                )
                self.assertEqual(harvest.returncode, 0, harvest.stderr)
                index = json.loads((repo / ".docforge/flow-index.json").read_text(encoding="utf-8"))
                self.assertEqual(index["summary"]["main"], 2)
                self.assertEqual(index["summary"]["deferred"], 3)

                # Preserve a documented row and a skipped row across revise.
                index["flows"][0]["status"] = "documented"
                index["flows"][-1]["status"] = "skipped"
                filled = repo / "docs" / "flows" / f"{index['flows'][0]['slug']}.md"
                filled.parent.mkdir(parents=True, exist_ok=True)
                filled.write_text(
                    "# Existing documented flow\n\nConcrete prose without placeholders.\n",
                    encoding="utf-8",
                )
                (repo / ".docforge/flow-index.json").write_text(
                    json.dumps(index, indent=2) + "\n", encoding="utf-8",
                )

                revise = run(
                    runtime, "flow_index", "revise",
                    "--repo", str(repo),
                    "--main-limit", "2",
                )
                self.assertEqual(revise.returncode, 0, revise.stderr)
                self.assertIn("NOTICE: main-priority flows eligible for full documentation:", revise.stdout)
                self.assertIn('"placeholder"', revise.stdout)

                revised = json.loads((repo / ".docforge/flow-index.json").read_text(encoding="utf-8"))
                statuses = {row["slug"]: row["status"] for row in revised["flows"]}
                self.assertEqual(statuses[index["flows"][0]["slug"]], "documented")
                self.assertEqual(statuses[index["flows"][-1]["slug"]], "skipped")
                self.assertGreaterEqual(revised["summary"]["placeholder"], 3)
                self.assertEqual(revised["summary"]["documented"], 1)
                self.assertEqual(revised["summary"]["skipped"], 1)
                self.assertEqual(revised["summary"]["main"], 2)

                # Documented file must not be overwritten; only main standalone placeholders get stubs.
                self.assertEqual(
                    filled.read_text(encoding="utf-8"),
                    "# Existing documented flow\n\nConcrete prose without placeholders.\n",
                )
                stub_count = 0
                for row in revised["flows"]:
                    self.assertIn(row.get("doc_role"), {"standalone", "member", "index_only"})
                    stub = repo / "docs" / "flows" / f"{row['slug']}.md"
                    if (
                        row["status"] == "placeholder"
                        and row.get("priority") == "main"
                        and row.get("doc_role") == "standalone"
                    ):
                        self.assertTrue(stub.is_file(), stub)
                        self.assertIn("Status: `placeholder`", stub.read_text(encoding="utf-8"))
                        stub_count += 1
                    elif row.get("priority") == "deferred" or row.get("doc_role") == "index_only":
                        self.assertFalse(stub.is_file(), stub)
                self.assertEqual(stub_count, 1)
                self.assertEqual(revised["version"], "1.2")

                render = run(runtime, "flow_index", "render", "--repo", str(repo))
                self.assertEqual(render.returncode, 0, render.stderr)
                matrix = (repo / "docs/flows/README.md").read_text(encoding="utf-8")
                self.assertIn("# Flows", matrix)
                self.assertIn("| Role |", matrix)
                self.assertIn("| placeholder |", matrix)
                self.assertIn(f"](./{index['flows'][0]['slug']}.md)", matrix)

    def test_flow_index_vague_slugs_and_organize_across_runtimes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            interchange = {
                "routes": [],
                "processes": [
                    {
                        "id": "proc-save-a",
                        "entryPointId": "Function:src/modules/highlight/highlight.service.js:save",
                        "terminalId": "Function:src/db.js:write",
                        "processType": "cross_community",
                        "stepCount": 5,
                        "communities": ["comm-a", "comm-b"],
                    },
                    {
                        "id": "proc-save-b",
                        "entryPointId": "Function:src/modules/content/content.service.js:save",
                        "terminalId": "Function:src/db.js:write",
                        "processType": "cross_community",
                        "stepCount": 4,
                        "communities": ["comm-a", "comm-b"],
                    },
                    {
                        "id": "proc-report",
                        "entryPointId": "Function:src/modules/email/report.js:sendContentReport",
                        "terminalId": "Function:src/lib/mailer.js:send",
                        "processType": "cross_community",
                        "stepCount": 6,
                        "communities": ["comm-a", "comm-b"],
                    },
                ],
                "communities": [
                    {"id": "comm-a", "heuristicLabel": "API"},
                    {"id": "comm-b", "heuristicLabel": "Mail"},
                ],
            }

            for runtime in ("py", "js"):
                repo = root / runtime
                repo.mkdir()
                write_gitnexus_interchange(repo, interchange)
                harvest = run(
                    runtime, "flow_index", "harvest",
                    "--repo", str(repo),
                    "--main-limit", "2",
                )
                self.assertEqual(harvest.returncode, 0, harvest.stderr)
                index = json.loads((repo / ".docforge/flow-index.json").read_text(encoding="utf-8"))
                self.assertEqual(index["version"], "1.2")
                slugs = {row["slug"] for row in index["flows"]}
                self.assertIn("highlight-save", slugs)
                self.assertIn("content-save", slugs)
                for row in index["flows"]:
                    self.assertTrue(row.get("display_name"))
                    if row["priority"] == "main":
                        self.assertEqual(row["doc_role"], "standalone")
                        self.assertTrue(str(row["doc_path"]).startswith("docs/flows/"))
                    else:
                        self.assertEqual(row["doc_role"], "index_only")
                        self.assertIsNone(row["doc_path"])

                revise = run(
                    runtime, "flow_index", "revise",
                    "--repo", str(repo),
                    "--main-limit", "2",
                )
                self.assertEqual(revise.returncode, 0, revise.stderr)
                revised = json.loads((repo / ".docforge/flow-index.json").read_text(encoding="utf-8"))
                main_slugs = [
                    row["slug"] for row in revised["flows"]
                    if row["priority"] == "main" and row["doc_role"] == "standalone"
                ]
                for slug in main_slugs:
                    self.assertTrue((repo / "docs" / "flows" / f"{slug}.md").is_file())
                deferred_slugs = [row["slug"] for row in revised["flows"] if row["priority"] == "deferred"]
                for slug in deferred_slugs:
                    self.assertFalse((repo / "docs" / "flows" / f"{slug}.md").is_file())

                emit = run(runtime, "flow_index", "organize", "emit", "--repo", str(repo))
                self.assertEqual(emit.returncode, 0, emit.stderr)
                pack_path = repo / ".docforge/tmp/flow-organization-pack.json"
                self.assertTrue(pack_path.is_file())
                pack = json.loads(pack_path.read_text(encoding="utf-8"))
                self.assertEqual(pack["version"], "1.0")
                self.assertGreaterEqual(len(pack["flows"]), 3)

                parent = next(row for row in revised["flows"] if "email" in row["slug"] or "report" in row["slug"] or row["entry_ref"].get("symbol") == "sendContentReport")
                members = [row for row in revised["flows"] if row["id"] != parent["id"]][:2]
                org = {
                    "version": "1.0",
                    "updates": [
                        {
                            "id": parent["id"],
                            "display_name": "Email scheduled reports",
                            "slug": "scheduled-reports",
                            "family": "email",
                            "doc_role": "standalone",
                            "doc_path": "docs/flows/email/scheduled-reports.md",
                            "compose_members": [row["id"] for row in members],
                        }
                    ],
                }
                org_path = repo / ".docforge/tmp/flow-organization.json"
                org_path.write_text(json.dumps(org, indent=2) + "\n", encoding="utf-8")
                apply = run(
                    runtime, "flow_index", "organize", "apply",
                    "--repo", str(repo),
                    "--organization", str(org_path),
                )
                self.assertEqual(apply.returncode, 0, apply.stderr)
                organized = json.loads((repo / ".docforge/flow-index.json").read_text(encoding="utf-8"))
                parent_row = next(row for row in organized["flows"] if row["id"] == parent["id"])
                self.assertEqual(parent_row["display_name"], "Email scheduled reports")
                self.assertEqual(parent_row["slug"], "scheduled-reports")
                self.assertEqual(parent_row["family"], "email")
                self.assertEqual(parent_row["doc_path"], "docs/flows/email/scheduled-reports.md")
                self.assertEqual(parent_row["doc_role"], "standalone")
                self.assertTrue((repo / "docs/flows/email/scheduled-reports.md").is_file())
                for member in members:
                    member_row = next(row for row in organized["flows"] if row["id"] == member["id"])
                    self.assertEqual(member_row["doc_role"], "member")
                    self.assertEqual(member_row["composed_into"], parent["id"])
                    self.assertIsNone(member_row["doc_path"])

                render = run(runtime, "flow_index", "render", "--repo", str(repo))
                self.assertEqual(render.returncode, 0, render.stderr)
                matrix = (repo / "docs/flows/README.md").read_text(encoding="utf-8")
                self.assertIn("# Flows", matrix)
                self.assertIn("## email", matrix)
                self.assertIn("scheduled-reports.md", matrix)

    def test_flow_index_update_selection_and_summary_writeback_across_runtimes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            interchange = {
                "routes": [],
                "processes": [
                    {
                        "id": "proc-a",
                        "entryPointId": "Function:src/api/orders.js:listOrders",
                        "terminalId": "Function:src/db.js:query",
                        "processType": "cross_community",
                        "stepCount": 4,
                        "communities": ["comm-a", "comm-b"],
                    },
                    {
                        "id": "proc-b",
                        "entryPointId": "Function:src/jobs/cleanup.js:runCleanup",
                        "terminalId": "Function:src/db.js:purge",
                        "processType": "cross_community",
                        "stepCount": 3,
                        "communities": ["comm-a", "comm-b"],
                    },
                ],
                "communities": [
                    {"id": "comm-a", "heuristicLabel": "API"},
                    {"id": "comm-b", "heuristicLabel": "DB"},
                ],
            }

            for runtime in ("py", "js"):
                repo = root / runtime
                repo.mkdir()
                self.assertEqual(initialize("py", repo, "diligence").returncode, 0)
                write_gitnexus_interchange(repo, interchange)
                harvest = run(
                    runtime, "flow_index", "harvest",
                    "--repo", str(repo),
                    "--main-limit", "1",
                )
                self.assertEqual(harvest.returncode, 0, harvest.stderr)
                index = json.loads((repo / ".docforge/flow-index.json").read_text(encoding="utf-8"))
                self.assertEqual(index["version"], "1.2")
                self.assertEqual(index["summary"]["written"], 0)
                main_row = next(row for row in index["flows"] if row["priority"] == "main")
                deferred_row = next(row for row in index["flows"] if row["priority"] == "deferred")

                # 1.1 index upgrades additively on the next write path (revise).
                index["version"] = "1.1"
                (repo / ".docforge/flow-index.json").write_text(
                    json.dumps(index, indent=2) + "\n", encoding="utf-8"
                )
                revised = run(
                    runtime, "flow_index", "revise",
                    "--repo", str(repo),
                    "--main-limit", "1",
                )
                self.assertEqual(revised.returncode, 0, revised.stderr)
                upgraded = json.loads((repo / ".docforge/flow-index.json").read_text(encoding="utf-8"))
                self.assertEqual(upgraded["version"], "1.2")
                self.assertIn("written", upgraded["summary"])

                # Promote the deferred row through the selection gate.
                promoted = run(
                    runtime, "flow_index", "update",
                    "--repo", str(repo),
                    "--id", deferred_row["id"],
                    "--priority", "main",
                    "--status", "placeholder",
                )
                self.assertEqual(promoted.returncode, 0, promoted.stderr)
                promoted_index = json.loads((repo / ".docforge/flow-index.json").read_text(encoding="utf-8"))
                promoted_row = next(row for row in promoted_index["flows"] if row["id"] == deferred_row["id"])
                self.assertEqual(promoted_row["priority"], "main")
                self.assertEqual(promoted_row["status"], "placeholder")
                self.assertEqual(promoted_row["doc_role"], "standalone")
                self.assertTrue(str(promoted_row["doc_path"]).startswith("docs/flows/"))

                # Decline the original main row.
                declined = run(
                    runtime, "flow_index", "update",
                    "--repo", str(repo),
                    "--id", main_row["id"],
                    "--status", "skipped",
                )
                self.assertEqual(declined.returncode, 0, declined.stderr)
                declined_index = json.loads((repo / ".docforge/flow-index.json").read_text(encoding="utf-8"))
                declined_row = next(row for row in declined_index["flows"] if row["id"] == main_row["id"])
                self.assertEqual(declined_row["status"], "skipped")
                self.assertEqual(declined_row["doc_role"], "index_only")
                self.assertIsNone(declined_row["doc_path"])

                # Summary write-back is refused before the row is documented.
                refused = run(
                    runtime, "flow_index", "update",
                    "--repo", str(repo),
                    "--id", promoted_row["id"],
                    "--summary", "Too early.",
                )
                self.assertEqual(refused.returncode, 2)
                self.assertIn("summary write-back requires status 'documented'", refused.stderr)

                # Document it (the manage_manifest add path), then write back.
                accepted = run(
                    "py", "manage_manifest", "add", "--repo", str(repo),
                    "--type", "flow", "--id", promoted_row["id"],
                    "--path", str(promoted_row["doc_path"]),
                )
                self.assertEqual(accepted.returncode, 0, accepted.stderr)
                written = run(
                    runtime, "flow_index", "update",
                    "--repo", str(repo),
                    "--id", promoted_row["id"],
                    "--summary", "Lists orders for the storefront.",
                    "--written",
                )
                self.assertEqual(written.returncode, 0, written.stderr)
                stamped = json.loads((repo / ".docforge/flow-index.json").read_text(encoding="utf-8"))
                stamped_row = next(row for row in stamped["flows"] if row["id"] == promoted_row["id"])
                self.assertEqual(stamped_row["summary"], "Lists orders for the storefront.")
                self.assertTrue(stamped_row["written_at"])
                self.assertEqual(stamped["summary"]["written"], 1)

                # The rendered matrix carries the summary section.
                render = run(runtime, "flow_index", "render", "--repo", str(repo))
                self.assertEqual(render.returncode, 0, render.stderr)
                matrix = (repo / "docs/flows/README.md").read_text(encoding="utf-8")
                self.assertIn("## Flow summaries", matrix)
                self.assertIn("Lists orders for the storefront.", matrix)

    def test_flow_index_import_seeds_derived_candidates_across_runtimes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            analysis = {
                "flows": [
                    {
                        "name": "Order intake",
                        "domain": "Orders",
                        "entryPoint": "POST /orders",
                        "steps": [
                            {"order": 1, "name": "Validate", "path": "src/api/orders.py"},
                            {"order": 2, "name": "Save", "path": "src/db.py"},
                        ],
                    },
                    {
                        "name": "Cleanup job",
                        "entryPoint": "runCleanup",
                        "steps": [{"order": 1, "name": "Purge", "path": "src/jobs/cleanup.py"}],
                    },
                ]
            }
            analysis_path = root / "flow-analysis.json"
            analysis_path.write_text(json.dumps(analysis), encoding="utf-8")

            for runtime in ("py", "js"):
                repo = root / runtime
                repo.mkdir()

                # No index yet: import seeds a fresh 1.2 index.
                imported = run(
                    runtime, "flow_index", "import",
                    "--repo", str(repo),
                    "--analysis", str(analysis_path),
                    "--main-limit", "1",
                )
                self.assertEqual(imported.returncode, 0, imported.stderr)
                index = json.loads((repo / ".docforge/flow-index.json").read_text(encoding="utf-8"))
                self.assertEqual(index["version"], "1.2")
                self.assertEqual(index["summary"]["total"], 2)
                self.assertEqual(index["summary"]["main"], 1)
                self.assertEqual(index["summary"]["deferred"], 1)
                self.assertIn(".docforge/tmp/flow-graph.json", index["sources"])
                main_row = next(row for row in index["flows"] if row["priority"] == "main")
                deferred_row = next(row for row in index["flows"] if row["priority"] == "deferred")
                self.assertEqual(main_row["status"], "placeholder")
                self.assertEqual(main_row["doc_role"], "standalone")
                self.assertTrue(str(main_row["doc_path"]).startswith("docs/flows/"))
                self.assertEqual(main_row["confidence"], "candidate")
                self.assertEqual(deferred_row["doc_role"], "index_only")
                self.assertIsNone(deferred_row["doc_path"])

                # Existing documented row survives a later import unchanged.
                write_flow_index(repo, status="documented",
                                 summary="Charges the card and records the order.")
                reimported = run(
                    runtime, "flow_index", "import",
                    "--repo", str(repo),
                    "--analysis", str(analysis_path),
                    "--main-limit", "1",
                )
                self.assertEqual(reimported.returncode, 0, reimported.stderr)
                merged = json.loads((repo / ".docforge/flow-index.json").read_text(encoding="utf-8"))
                checkout = next(row for row in merged["flows"] if row["id"] == "flow-checkout")
                self.assertEqual(checkout["status"], "documented")
                self.assertEqual(checkout["summary"], "Charges the card and records the order.")
                self.assertEqual(merged["summary"]["written"], 1)

            # Invalid analysis input is rejected.
            bad = root / "bad-analysis.json"
            bad.write_text(json.dumps({"flows": []}), encoding="utf-8")
            rejected = run(
                "py", "flow_index", "import",
                "--repo", str(root / "py"),
                "--analysis", str(bad),
            )
            self.assertEqual(rejected.returncode, 2)
            self.assertIn("non-empty 'flows' list", rejected.stderr)

    def test_manage_manifest_only_adds_main_indexed_flows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.assertEqual(initialize("py", repo, "diligence").returncode, 0)
            write_flow_index(repo, status="deferred")
            rejected = run("py", "manage_manifest", "add", "--repo", str(repo),
                           "--type", "flow", "--id", "flow-checkout",
                           "--path", "docs/flows/checkout.md")
            self.assertEqual(rejected.returncode, 2)
            self.assertIn("only main-priority flows become documents", rejected.stderr)

            write_flow_index(repo, status="placeholder", priority="deferred")
            rejected_placeholder = run(
                "py", "manage_manifest", "add", "--repo", str(repo),
                "--type", "flow", "--id", "flow-checkout",
                "--path", "docs/flows/checkout.md",
            )
            self.assertEqual(rejected_placeholder.returncode, 2)
            self.assertIn("only main-priority flows become documents", rejected_placeholder.stderr)

            write_flow_index(repo, status="placeholder", priority="main")
            accepted = run(
                "py", "manage_manifest", "add", "--repo", str(repo),
                "--type", "flow", "--id", "flow-checkout",
                "--path", "docs/flows/checkout.md",
            )
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            index = json.loads((repo / ".docforge/flow-index.json").read_text(encoding="utf-8"))
            self.assertEqual(index["flows"][0]["status"], "documented")


def _ua_domain(steps_shape: str = "chain", *, cycle: bool = False) -> dict:
    """A minimal UA domain graph with one flow and three ordered steps.

    `steps_shape` picks how the flow reaches its steps: "chain" is what UA
    actually emits (flow -> s1 -> s2 -> s3), "star" is what the old harvester
    assumed (flow -> s1, s2, s3). Both must yield three ordered steps.
    """
    nodes = [
        {"id": "domain:shop", "type": "domain", "name": "Shop"},
        {"id": "flow:checkout", "type": "flow", "name": "Checkout",
         "summary": "Shopper pays and receives confirmation.",
         "complexity": "moderate",
         "domainMeta": {"entryPoint": "POST /checkout", "entryType": "http"}},
    ]
    for order, label in enumerate(("Validate cart", "Charge card", "Send receipt"), start=1):
        nodes.append({
            "id": f"flow:checkout:step:{order}", "type": "flow_step",
            "name": label, "summary": f"{label} happens here.",
            "flowId": "flow:checkout", "order": order,
        })
    edges = [{"source": "domain:shop", "target": "flow:checkout", "type": "contains_flow"}]
    if steps_shape == "chain":
        chain = ["flow:checkout", "flow:checkout:step:1", "flow:checkout:step:2", "flow:checkout:step:3"]
        for order, (src, dst) in enumerate(zip(chain, chain[1:]), start=1):
            edges.append({"source": src, "target": dst, "type": "flow_step", "order": order})
        if cycle:
            edges.append({"source": "flow:checkout:step:3", "target": "flow:checkout:step:1",
                          "type": "flow_step", "order": 4})
    else:
        for order in (1, 2, 3):
            edges.append({"source": "flow:checkout", "target": f"flow:checkout:step:{order}",
                          "type": "flow_step", "order": order})
    return {"version": "1", "project": "fixture", "nodes": nodes, "edges": edges, "layers": [], "tour": []}


def _write_ua(repo: Path, domain: dict, knowledge: dict | None = None) -> None:
    (repo / ".ua").mkdir(parents=True, exist_ok=True)
    (repo / ".ua" / "domain-graph.json").write_text(json.dumps(domain), encoding="utf-8")
    if knowledge is not None:
        (repo / ".ua" / "knowledge-graph.json").write_text(json.dumps(knowledge), encoding="utf-8")


def _harvest_index(runtime: str, repo: Path) -> dict:
    result = run(runtime, "flow_index", "harvest", "--repo", str(repo))
    assert result.returncode == 0, result.stderr
    return json.loads((repo / ".docforge" / "flow-index.json").read_text(encoding="utf-8"))


def _flow_row(index: dict, name: str) -> dict:
    return next(row for row in index["flows"] if row["name"] == name)


class UaFlowChainTests(unittest.TestCase):
    """UA emits flow steps as a chain, not a star. Grouping edges by `source`
    finds exactly one step per flow however long the chain — which is why every
    UA flow used to report `reach.steps: 1`."""

    def test_chain_shape_counts_every_step_on_both_runtimes(self) -> None:
        for runtime in ("py", "js"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                _write_ua(repo, _ua_domain("chain"))
                row = _flow_row(_harvest_index(runtime, repo), "Checkout")
                self.assertEqual(row["reach"]["steps"], 3, f"{runtime}: chain walked as a star")
                names = [step["name"] for step in row["evidence"][0]["steps"]]
                self.assertEqual(names, ["Validate cart", "Charge card", "Send receipt"])

    def test_star_shape_still_counts_every_step(self) -> None:
        for runtime in ("py", "js"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                _write_ua(repo, _ua_domain("star"))
                row = _flow_row(_harvest_index(runtime, repo), "Checkout")
                self.assertEqual(row["reach"]["steps"], 3, f"{runtime}: star shape regressed")

    def test_cyclic_chain_terminates_without_duplicating_steps(self) -> None:
        for runtime in ("py", "js"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                _write_ua(repo, _ua_domain("chain", cycle=True))
                row = _flow_row(_harvest_index(runtime, repo), "Checkout")
                self.assertEqual(row["reach"]["steps"], 3)
                ids = [step["nodeId"] for step in row["evidence"][0]["steps"]]
                self.assertEqual(len(ids), len(set(ids)))

    def test_flow_and_step_prose_survives_into_evidence(self) -> None:
        """UA states the outcome and describes every step; keeping only a count
        is what left downstream flow documents thin."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write_ua(repo, _ua_domain("chain"))
            evidence = _flow_row(_harvest_index("py", repo), "Checkout")["evidence"][0]
            self.assertEqual(evidence["summary"], "Shopper pays and receives confirmation.")
            self.assertEqual(evidence["complexity"], "moderate")
            self.assertEqual(evidence["steps"][1]["summary"], "Charge card happens here.")

    def test_unambiguous_knowledge_match_locates_a_step_and_ambiguity_does_not(self) -> None:
        """A wrong file:line is worse than a missing one — the audit treats
        locators as evidence — so only a single match resolves."""
        knowledge = {"nodes": [
            {"id": "fn:1", "type": "function", "name": "ChargeCard",
             "filePath": "src/billing/charge.js", "lineRange": [12, 44]},
            {"id": "fn:2", "type": "function", "name": "SendReceipt",
             "filePath": "src/mail/a.js", "lineRange": [5, 9]},
            {"id": "fn:3", "type": "function", "name": "SendReceipt",
             "filePath": "src/mail/b.js", "lineRange": [7, 11]},
        ], "edges": [], "layers": []}
        domain = _ua_domain("chain")
        domain["nodes"][3]["name"] = "ChargeCard"
        domain["nodes"][4]["name"] = "SendReceipt"
        for runtime in ("py", "js"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                _write_ua(repo, domain, knowledge)
                steps = _flow_row(_harvest_index(runtime, repo), "Checkout")["evidence"][0]["steps"]
                charge = next(step for step in steps if step["name"] == "ChargeCard")
                receipt = next(step for step in steps if step["name"] == "SendReceipt")
                self.assertEqual(charge["filePath"], "src/billing/charge.js")
                self.assertEqual(charge["line"], 12)
                self.assertNotIn("filePath", receipt, f"{runtime}: guessed an ambiguous locator")

    def test_frontend_entry_layers_are_harvested(self) -> None:
        """`Screens & Routes` is a UI repo's whole entry surface; a layer list
        matching only service/api vocabulary misses it."""
        knowledge = {
            "nodes": [{"id": "fn:home", "type": "function", "name": "handleHomeRequest",
                       "filePath": "src/screens/Home/index.js", "lineRange": [1, 20]}],
            "edges": [],
            "layers": [{"name": "Screens & Routes", "nodeIds": ["fn:home"]}],
        }
        for runtime in ("py", "js"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                _write_ua(repo, _ua_domain("chain"), knowledge)
                index = _harvest_index(runtime, repo)
                names = [row["name"] for row in index["flows"]]
                self.assertIn("handleHomeRequest", names, f"{runtime}: frontend layer filtered out")


class GitnexusOrderedStepTests(unittest.TestCase):
    def test_ordered_steps_are_kept_and_merged_across_shared_entries(self) -> None:
        payload = {
            "routes": [],
            "communities": [{"id": "c-api", "heuristicLabel": "API"}],
            "processes": [
                {"id": "p1", "entryPointId": "Function:src/api.ts:listItems",
                 "terminalId": "Function:src/db.ts:query", "processType": "cross_community",
                 "stepCount": 3, "communities": ["c-api"],
                 "steps": [
                     {"order": 1, "nodeId": "n1", "filePath": "src/api.ts", "symbol": "listItems"},
                     {"order": 2, "nodeId": "n2", "filePath": "src/svc.ts", "symbol": "fetch"},
                     {"order": 3, "nodeId": "n3", "filePath": "src/db.ts", "symbol": "query"}]},
                {"id": "p2", "entryPointId": "Function:src/api.ts:listItems",
                 "terminalId": "Function:src/cache.ts:read", "stepCount": 2, "communities": ["c-api"],
                 "steps": [
                     {"order": 1, "nodeId": "n1", "filePath": "src/api.ts", "symbol": "listItems"},
                     {"order": 2, "nodeId": "n4", "filePath": "src/cache.ts", "symbol": "read"}]},
            ],
        }
        for runtime in ("py", "js"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                write_gitnexus_interchange(repo, payload)
                row = _flow_row(_harvest_index(runtime, repo), "listItems")
                steps = row["evidence"][0]["steps"]
                # n1 is shared by both processes and must appear once.
                self.assertEqual([step["symbol"] for step in steps],
                                 ["listItems", "fetch", "query", "read"])
                self.assertEqual(row["reach"]["steps"], 4)

    def test_interchange_without_steps_falls_back_to_step_count(self) -> None:
        payload = {
            "routes": [], "communities": [],
            "processes": [{"id": "p1", "entryPointId": "Function:src/legacy.ts:run",
                           "terminalId": "Function:src/db.ts:query", "stepCount": 7,
                           "communities": []}],
        }
        for runtime in ("py", "js"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                write_gitnexus_interchange(repo, payload)
                row = _flow_row(_harvest_index(runtime, repo), "run")
                self.assertEqual(row["reach"]["steps"], 7)
                self.assertNotIn("steps", row["evidence"][0])

    def test_ready_flow_source_without_its_interchange_fails_loudly(self) -> None:
        """An indexed native flow source going unread is a setup gap, not an
        absence of flows — harvest used to skip it in silence."""
        for runtime in ("py", "js"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                (repo / ".gitnexus").mkdir()
                (repo / ".gitnexus" / "lbug").write_bytes(b"fixture")
                (repo / ".gitnexus" / "gitnexus.json").write_text(
                    json.dumps({"stats": {"nodes": 10, "processes": 5}}), encoding="utf-8")
                result = run(runtime, "flow_index", "harvest", "--repo", str(repo))
                self.assertEqual(result.returncode, 2)
                self.assertIn("--interchange", result.stderr, f"{runtime}: no remediation named")


class FlowAnalysisSchemaTests(unittest.TestCase):
    V2 = {
        "schemaVersion": 2, "source": "codegraph",
        "flows": [{
            "name": "Crop an uploaded image", "domain": "ai",
            "outcome": "Caller receives a cropped image",
            "trigger": {"kind": "http", "signature": "POST /smartCrop"},
            "actors": ["API client"],
            "entryPoint": {"symbol": "smartCrop", "file": "src/modules/ai/ai.routes.js",
                           "line": 12, "nodeId": "route:1"},
            "steps": [
                {"order": 1, "name": "Route accepts upload", "file": "src/modules/ai/ai.routes.js",
                 "line": 12, "symbol": "smartCrop", "nodeId": "route:1", "evidence": "graph"},
                {"order": 2, "name": "Vision client crops", "file": "src/lib/vision/client.js",
                 "line": 88, "symbol": "crop", "nodeId": "fn:3", "evidence": "graph"}],
            "branches": [{"afterStep": 1, "condition": "no image", "goesTo": "400",
                          "file": "src/modules/ai/ai.controller.js", "line": 44}],
            "rules": [{"statement": "10MB cap", "file": "src/modules/ai/ai.controller.js", "line": 47}],
            "failures": [{"trigger": "timeout", "handling": "502",
                          "file": "src/lib/vision/client.js", "line": 96}],
        }],
    }

    def _import(self, runtime: str, repo: Path, analysis: dict):
        target = repo / "analysis.json"
        target.write_text(json.dumps(analysis), encoding="utf-8")
        return run(runtime, "flow_index", "import", "--repo", str(repo), "--analysis", str(target))

    def test_v2_preserves_every_contract_fact_and_persists_the_pack(self) -> None:
        for runtime in ("py", "js"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                result = self._import(runtime, repo, self.V2)
                self.assertEqual(result.returncode, 0, result.stderr)
                index = json.loads((repo / ".docforge/flow-index.json").read_text(encoding="utf-8"))
                evidence = index["flows"][0]["evidence"][0]
                for key in ("outcome", "actors", "trigger", "steps", "branches", "rules", "failures"):
                    self.assertIn(key, evidence, f"{runtime}: {key} discarded on import")
                # The pack must outlive tmp/, which is wiped between runs.
                self.assertTrue((repo / ".docforge" / "flow-analysis.json").is_file())

    def test_entry_ref_signature_and_path_come_from_the_same_place(self) -> None:
        """Taking the signature from `entryPoint` and the file from
        `steps[0]` produced rows describing two different things."""
        for runtime in ("py", "js"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                self.assertEqual(self._import(runtime, repo, self.V2).returncode, 0)
                index = json.loads((repo / ".docforge/flow-index.json").read_text(encoding="utf-8"))
                entry_ref = index["flows"][0]["entry_ref"]
                self.assertEqual(entry_ref["signature"], "smartCrop")
                self.assertEqual(entry_ref["filePath"], "src/modules/ai/ai.routes.js")
                self.assertEqual(entry_ref["kind"], "http")

    def test_graph_backed_flow_outranks_an_asserted_one(self) -> None:
        asserted = json.loads(json.dumps(self.V2))
        for step in asserted["flows"][0]["steps"]:
            step.pop("nodeId")
            step["evidence"] = "source"
        for runtime in ("py", "js"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                self.assertEqual(self._import(runtime, repo, self.V2).returncode, 0)
                confirmed = json.loads((repo / ".docforge/flow-index.json").read_text(encoding="utf-8"))
                self.assertEqual(confirmed["flows"][0]["confidence"], "confirmed")
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                self.assertEqual(self._import(runtime, repo, asserted).returncode, 0)
                candidate_index = json.loads((repo / ".docforge/flow-index.json").read_text(encoding="utf-8"))
                self.assertEqual(candidate_index["flows"][0]["confidence"], "candidate")
                self.assertLess(candidate_index["flows"][0]["rank"], confirmed["flows"][0]["rank"])

    def test_v2_without_a_step_locator_is_refused_and_writes_nothing(self) -> None:
        broken = json.loads(json.dumps(self.V2))
        broken["flows"][0]["steps"][1].pop("file")
        for runtime in ("py", "js"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                result = self._import(runtime, repo, broken)
                self.assertEqual(result.returncode, 2)
                self.assertIn("file", result.stderr)
                self.assertFalse((repo / ".docforge" / "flow-index.json").exists())

    def test_v1_analysis_still_imports(self) -> None:
        v1 = {"flows": [{"name": "Legacy flow", "entryPoint": "src/jobs/run.js",
                         "domain": "jobs",
                         "steps": [{"order": 1, "name": "Kick off", "path": "src/jobs/run.js"}]}]}
        for runtime in ("py", "js"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                result = self._import(runtime, repo, v1)
                self.assertEqual(result.returncode, 0, result.stderr)
                index = json.loads((repo / ".docforge/flow-index.json").read_text(encoding="utf-8"))
                self.assertEqual(index["flows"][0]["reach"]["steps"], 1)


class FlowIndexSchemaTests(unittest.TestCase):
    def test_codegraph_is_a_valid_provider_in_the_index_schema(self) -> None:
        """write_index derives `providers` from evidence, so a CodeGraph run
        writes `providers: ["codegraph"]` — which the schema used to reject."""
        schema = json.loads(
            (Path(__file__).resolve().parent.parent
             / "skills/docforge/_shared/.metadata/flow-index-schema.json").read_text(encoding="utf-8"))
        self.assertIn("codegraph", schema["properties"]["providers"]["items"]["enum"])


def _build_codegraph_db(path: Path, *, self_edge: bool = False, hub: int = 0) -> None:
    """A miniature CodeGraph index: one route reaching its handler through a
    `references` edge, then a `calls` chain. `references` at hop 1 is the whole
    point — the generic edge filter excluded it, which broke route chains
    before they started."""
    import sqlite3

    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE schema_versions (version INTEGER PRIMARY KEY, applied_at INTEGER, description TEXT);
        CREATE TABLE nodes (id TEXT PRIMARY KEY, kind TEXT, name TEXT, qualified_name TEXT,
                            file_path TEXT, language TEXT, start_line INTEGER, end_line INTEGER,
                            start_column INTEGER, end_column INTEGER, docstring TEXT, signature TEXT,
                            visibility TEXT, is_exported INTEGER DEFAULT 0, is_async INTEGER DEFAULT 0,
                            is_static INTEGER DEFAULT 0, is_abstract INTEGER DEFAULT 0,
                            decorators TEXT, type_parameters TEXT, return_type TEXT, updated_at INTEGER);
        CREATE TABLE edges (id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT, target TEXT,
                            kind TEXT, metadata TEXT, line INTEGER, col INTEGER, provenance TEXT);
        """
    )
    connection.execute("INSERT INTO schema_versions VALUES (8, 0, 'fixture')")

    def node(nid, kind, name, file_path, line, exported=0):
        connection.execute(
            "INSERT INTO nodes (id, kind, name, qualified_name, file_path, language, start_line, "
            "end_line, start_column, end_column, is_exported, updated_at) "
            "VALUES (?,?,?,?,?,'javascript',?,?,0,0,?,0)",
            (nid, kind, name, f"{file_path}::{name}", file_path, line, line + 5, exported),
        )

    def edge(source, target, kind):
        connection.execute("INSERT INTO edges (source, target, kind) VALUES (?,?,?)", (source, target, kind))

    node("route:1", "route", "POST /checkout", "src/routes/checkout.js", 10)
    node("fn:handler", "function", "checkout", "src/controllers/checkout.js", 20, exported=1)
    node("fn:service", "function", "chargeCard", "src/services/billing.js", 30)
    node("fn:model", "function", "saveOrder", "src/models/order.js", 40)
    node("const:db", "constant", "OrderModel", "src/models/order.js", 2)
    edge("route:1", "fn:handler", "references")   # routes reach handlers this way
    edge("fn:handler", "fn:service", "calls")
    edge("fn:service", "fn:model", "calls")
    edge("fn:model", "const:db", "references")
    if self_edge:
        edge("fn:handler", "fn:handler", "calls")
    for index in range(hub):
        node(f"fn:leaf{index}", "function", f"leaf{index}", f"src/lib/leaf{index}.js", 5)
        edge("fn:service", f"fn:leaf{index}", "calls")
    connection.commit()
    connection.close()


class CodegraphReaderTests(unittest.TestCase):
    def _entries(self, runtime: str, repo: Path) -> list:
        result = run(runtime, "graph_source_codegraph_reader", "entries", "--repo", str(repo), "--limit", "10")
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def _paths(self, runtime: str, repo: Path, seed: str) -> list:
        result = run(runtime, "graph_source_codegraph_reader", "paths", "--repo", str(repo), "--seed", seed)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_routes_rank_first_and_paths_are_ordered_with_locators(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _build_codegraph_db(repo / ".codegraph" / "codegraph.db")
            for runtime in ("py", "js"):
                seeds = self._entries(runtime, repo)
                self.assertEqual(seeds[0]["id"], "route:1", f"{runtime}: route did not rank first")
                chains = self._paths(runtime, repo, "route:1")
                longest = chains[0]
                self.assertEqual(
                    [(hop["order"], hop["symbol"], hop["file"], hop["line"]) for hop in longest],
                    [(1, "checkout", "src/controllers/checkout.js", 20),
                     (2, "chargeCard", "src/services/billing.js", 30),
                     (3, "saveOrder", "src/models/order.js", 40),
                     (4, "OrderModel", "src/models/order.js", 2)],
                    f"{runtime}: chain lost order or locators",
                )

    def test_py_and_js_readers_agree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _build_codegraph_db(repo / ".codegraph" / "codegraph.db", hub=9)
            self.assertEqual(self._entries("py", repo), self._entries("js", repo))
            self.assertEqual(self._paths("py", repo, "route:1"), self._paths("js", repo, "route:1"))

    def test_self_recursive_handler_does_not_fabricate_depth(self) -> None:
        """Without a cycle guard a single self-edge walks to the depth limit
        and reports a chain that does not exist."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _build_codegraph_db(repo / ".codegraph" / "codegraph.db", self_edge=True)
            for runtime in ("py", "js"):
                chains = self._paths(runtime, repo, "route:1")
                for chain in chains:
                    ids = [hop["nodeId"] for hop in chain]
                    self.assertEqual(len(ids), len(set(ids)), f"{runtime}: cycle walked")

    def test_fanout_is_capped_but_the_deep_branch_survives(self) -> None:
        """Truncating a fan-out alphabetically amputates whichever branch sorts
        late; on a real repo that cut six-hop flows down to three."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _build_codegraph_db(repo / ".codegraph" / "codegraph.db", hub=30)
            for runtime in ("py", "js"):
                chains = self._paths(runtime, repo, "route:1")
                self.assertLessEqual(len(chains), 12, f"{runtime}: chain cap not applied")
                self.assertEqual(max(len(chain) for chain in chains), 4,
                                 f"{runtime}: deep branch pruned by the fan-out cap")

    def test_unsupported_schema_degrades_instead_of_guessing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            db = repo / ".codegraph" / "codegraph.db"
            _build_codegraph_db(db)
            import sqlite3

            connection = sqlite3.connect(db)
            connection.execute("INSERT INTO schema_versions VALUES (9999, 0, 'from the future')")
            connection.commit()
            connection.close()
            for runtime in ("py", "js"):
                result = run(runtime, "graph_source_codegraph_reader", "entries", "--repo", str(repo))
                self.assertEqual(result.returncode, 1, f"{runtime}: read an unknown schema")

    def test_harvest_seeds_candidates_from_a_codegraph_only_repo(self) -> None:
        """Harvest used to fail outright here, leaving the whole flow set to an
        unguided LLM pass."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _build_codegraph_db(repo / ".codegraph" / "codegraph.db")
            for runtime in ("py", "js"):
                index = _harvest_index(runtime, repo)
                self.assertEqual(index["providers"], ["codegraph"])
                row = _flow_row(index, "POST /checkout")
                self.assertEqual(row["entry_ref"]["kind"], "http")
                self.assertEqual(row["reach"]["steps"], 4)
                self.assertEqual(row["evidence"][0]["steps"][0]["filePath"],
                                 "src/controllers/checkout.js")

    def test_prepare_emits_ordered_clusters_not_a_prose_instruction(self) -> None:
        """`prepare` used to write ~600 bytes of instruction text and no data
        for CodeGraph, which is why the analyzer invented flow skeletons."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _build_codegraph_db(repo / ".codegraph" / "codegraph.db")
            for runtime in ("py", "js"):
                result = run(runtime, "derive_flow_graph", "prepare", "--repo", str(repo))
                self.assertEqual(result.returncode, 0, result.stderr)
                context = json.loads(
                    (repo / ".docforge/tmp/flow-context.json").read_text(encoding="utf-8"))
                self.assertEqual(context["strategy"], "entry-point-first")
                self.assertNotIn("instruction", context, f"{runtime}: still the prose stub")
                cluster = context["clusters"][0]
                self.assertEqual(cluster["entryPoint"]["id"], "route:1")
                self.assertTrue(cluster["paths"][0][0]["file"])


def _two_provider_repo(repo: Path) -> None:
    """A repo where Understand Anything and CodeGraph are BOTH ready — the case
    intake asks about, and the case every lock consumer used to get wrong by
    silently taking UA (first in registry priority)."""
    _write_ua(repo, _ua_domain(), {"nodes": [], "edges": []})
    _build_codegraph_db(repo / ".codegraph" / "codegraph.db")


class GraphLockConsumptionTests(unittest.TestCase):
    """The lock is written by `init`/`set-graph` and must be *read* by every step
    that picks a provider for real work. These pin the read side: without them the
    lock was write-only and the user's answered choice was silently discarded.
    See references/graph/graph-sources.md "Session persistence"."""

    def _prepare(self, runtime: str, repo: Path):
        return run(runtime, "derive_flow_graph", "prepare", "--repo", str(repo))

    def _context(self, repo: Path) -> dict:
        return json.loads((repo / ".docforge" / "tmp" / "flow-context.json").read_text(encoding="utf-8"))

    def test_prepare_uses_the_locked_provider_not_registry_priority(self) -> None:
        """The reported bug: locked to codegraph beside a ready .ua/, derivation
        still built its context from Understand Anything."""
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                _two_provider_repo(repo)
                self.assertEqual(
                    initialize(runtime, repo, "spine", graph_provider="codegraph").returncode, 0
                )
                result = self._prepare(runtime, repo)
                self.assertEqual(result.returncode, 0, result.stderr)
                context = self._context(repo)
                self.assertEqual(context["source"], "codegraph")
                self.assertEqual(context["sourceOrigin"], "lock")
                # Not just the label: the read_mode branch must have followed the
                # lock too. CodeGraph resolves through its offline reader into
                # ordered clusters; a UA context would be a flat JSON dump.
                self.assertEqual(context["strategy"], "entry-point-first")
                self.assertIn("clusters", context)
                self.assertIn("[session lock]", result.stdout)

    def test_prepare_without_a_lock_still_uses_registry_priority(self) -> None:
        """No manifest at all — derivation must keep working, and must say the
        pick was priority rather than a honored choice."""
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                _two_provider_repo(repo)
                result = self._prepare(runtime, repo)
                self.assertEqual(result.returncode, 0, result.stderr)
                context = self._context(repo)
                self.assertEqual(context["source"], "understand-anything")
                self.assertEqual(context["sourceOrigin"], "priority")
                self.assertIn("no provider is locked", result.stdout)
                self.assertIn("set-graph", result.stdout)

    def test_prepare_hard_fails_when_the_locked_graph_is_gone(self) -> None:
        """A stale lock must stop the run, not quietly analyze the provider the
        user declined. Falling back would change read_mode and entry-point seeds
        mid-session while written documents already cite the locked provider."""
        stderrs = []
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                _two_provider_repo(repo)
                initialize(runtime, repo, "spine", graph_provider="codegraph")
                shutil.rmtree(repo / ".codegraph")
                result = self._prepare(runtime, repo)
                self.assertEqual(result.returncode, 1)
                self.assertIn("PREPARE FAILED", result.stderr)
                self.assertIn("codegraph", result.stderr)
                self.assertIn("set-graph", result.stderr)
                self.assertIn("--force", result.stderr)
                # Nothing written: a previous provider's context must not be
                # overwritten with the wrong provider's data.
                self.assertFalse((repo / ".docforge" / "tmp" / "flow-context.json").exists())
                stderrs.append(normalized(result.stderr, [repo]))
        self.assertEqual(stderrs[0], stderrs[1], "stale-lock message must match across runtimes")

    def test_harvest_uses_the_locked_provider_even_when_ua_graphs_exist(self) -> None:
        """flow_index harvest is the flow-recognition entry point. It used to probe
        artifacts in a fixed order with CodeGraph behind an `if not rows` guard, so
        a codegraph-locked repo with a residual .ua/ harvested only UA rows."""
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                _two_provider_repo(repo)
                initialize(runtime, repo, "spine", graph_provider="codegraph")
                result = run(runtime, "flow_index", "harvest", "--repo", str(repo))
                self.assertEqual(result.returncode, 0, result.stderr)
                index = json.loads((repo / ".docforge" / "flow-index.json").read_text(encoding="utf-8"))
                self.assertEqual(index["providers"], ["codegraph"])
                self.assertEqual(index["sources"], [".codegraph/codegraph.db"])

    def test_harvest_uses_ua_when_ua_is_the_locked_provider(self) -> None:
        """The mirror of the case above — the fix must honor whichever provider was
        chosen, not merely prefer CodeGraph."""
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                _two_provider_repo(repo)
                initialize(runtime, repo, "spine", graph_provider="understand-anything")
                result = run(runtime, "flow_index", "harvest", "--repo", str(repo))
                self.assertEqual(result.returncode, 0, result.stderr)
                index = json.loads((repo / ".docforge" / "flow-index.json").read_text(encoding="utf-8"))
                self.assertEqual(index["providers"], ["understand-anything"])

    def test_harvest_fallback_is_announced_and_keeps_sources_clean(self) -> None:
        """When the locked provider genuinely has no flow evidence, falling back
        beats failing — but the substitution must be stated, and `sources` must
        stay real artifact paths because it is persisted into the index."""
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                # UA is ready as a *code* graph but has no domain graph, so it
                # contributes no flow rows; CodeGraph does.
                (repo / ".ua").mkdir()
                (repo / ".ua" / "knowledge-graph.json").write_text(
                    json.dumps({"nodes": [], "edges": []}), encoding="utf-8"
                )
                _build_codegraph_db(repo / ".codegraph" / "codegraph.db")
                initialize(runtime, repo, "spine", graph_provider="understand-anything")
                result = run(runtime, "flow_index", "harvest", "--repo", str(repo))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("NOTICE:", result.stdout)
                self.assertIn("locked provider understand-anything contributed no flow", result.stdout)
                index = json.loads((repo / ".docforge" / "flow-index.json").read_text(encoding="utf-8"))
                self.assertEqual(index["sources"], [".codegraph/codegraph.db"])
                for source in index["sources"]:
                    self.assertNotIn("fallback", source)

    def test_locked_flow_field_describes_the_chosen_provider_only(self) -> None:
        """CodeGraph advertises no flow_graph. Locking it in a repo whose .ua/
        domain graph is present must not record flow: "native" — graph-sources.md
        forbids ever claiming "Native flow source: CodeGraph"."""
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                _two_provider_repo(repo)
                initialize(runtime, repo, "spine", graph_provider="codegraph")
                self.assertEqual(load_manifest(repo)["graph"]["flow"], "none")
                run(runtime, "manage_manifest", "set-graph", "--repo", str(repo),
                    "--provider", "understand-anything", "--force")
                # UA really does have native flows, so the same repo now says so.
                self.assertEqual(load_manifest(repo)["graph"]["flow"], "native")

    def _resolve_locked_js(self, repo: Path, capability: str) -> list:
        """Drive the JS resolver directly — there is no CLI for it, and the four
        origins are a documented contract both runtimes must agree on."""
        result = subprocess.run(
            [
                "node", "-e",
                "const { resolveLocked } = require(process.argv[1]); "
                "const [s, p, o] = resolveLocked(process.argv[2], process.argv[3]); "
                "process.stdout.write(JSON.stringify([s ? s.name : null, p ? true : false, o]));",
                str(CLI_JS / "graph_source_registry.js"), str(repo), capability,
            ],
            cwd=ROOT, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_resolve_locked_reports_all_four_origins_identically(self) -> None:
        """`lock-uncapable` is the signal that a locked provider has no native
        flows and derivation must take over — it must stay distinguishable from
        `lock-stale`, which is an error. Pinned directly because no CLI reaches
        every branch."""
        from runtime.graph.python.graph_source_registry import resolve_locked

        def py(repo: Path, capability: str) -> list:
            source, path, origin = resolve_locked(repo, capability)
            return [source["name"] if source else None, bool(path), origin]

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            # No manifest at all -> registry priority.
            _two_provider_repo(repo)
            self.assertEqual(py(repo, "code_graph"), ["understand-anything", True, "priority"])
            self.assertEqual(self._resolve_locked_js(repo, "code_graph"),
                             ["understand-anything", True, "priority"])

            initialize("py", repo, "spine", graph_provider="codegraph")
            self.assertEqual(py(repo, "code_graph"), ["codegraph", True, "lock"])
            self.assertEqual(self._resolve_locked_js(repo, "code_graph"),
                             ["codegraph", True, "lock"])
            # CodeGraph advertises no flow_graph: derive, do not borrow UA's.
            self.assertEqual(py(repo, "flow_graph"), ["codegraph", False, "lock-uncapable"])
            self.assertEqual(self._resolve_locked_js(repo, "flow_graph"),
                             ["codegraph", False, "lock-uncapable"])

            shutil.rmtree(repo / ".codegraph")
            self.assertEqual(py(repo, "code_graph"), ["codegraph", False, "lock-stale"])
            self.assertEqual(self._resolve_locked_js(repo, "code_graph"),
                             ["codegraph", False, "lock-stale"])

    def test_precheck_and_diagnose_stay_lock_free(self) -> None:
        """Precheck is the *pre-lock* discovery tool: it must keep reporting every
        ready provider so intake can ask which should be primary — that question is
        what creates the lock. It gains no lock awareness and no flag, ever."""
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                _two_provider_repo(repo)
                initialize(runtime, repo, "spine", graph_provider="codegraph")
                result = run(runtime, "precheck_graph", "--repo", str(repo), "--need", "code")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("2 sources are ready", result.stdout)
                self.assertIn("understand-anything", result.stdout)
                self.assertIn("codegraph", result.stdout)


if __name__ == "__main__":
    unittest.main()
