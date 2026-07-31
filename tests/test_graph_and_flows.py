"""Graph-provider precheck/selection and flow-index harvest/revise/organize/render."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _support import initialize, load_manifest, normalized, run, write_flow_index


class GraphProviderTests(unittest.TestCase):
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


class FlowIndexTests(unittest.TestCase):
    def test_flow_index_groups_processes_and_matches_runtime_peers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            export = root / "gitnexus-export.json"
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
            export.write_text(json.dumps({
                "routes": [],
                "processes": processes,
                "communities": [
                    {"id": "comm-a", "heuristicLabel": "API"},
                    {"id": "comm-b", "heuristicLabel": "Services"},
                ],
            }), encoding="utf-8")

            indexes = []
            for runtime in ("py", "js"):
                repo = root / runtime
                repo.mkdir()
                result = run(
                    runtime, "flow_index", "harvest",
                    "--repo", str(repo),
                    "--gitnexus-export", str(export),
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
                matrix = (repo / "docs/flows/INDEX.md").read_text()
                self.assertIn("| deferred |", matrix)
                indexes.append(index["flows"])
            self.assertEqual(indexes[0], indexes[1])

            easy_export = root / "easy-export.json"
            easy_export.write_text(json.dumps({
                "routes": [],
                "processes": [processes[0]],
                "communities": [],
            }), encoding="utf-8")
            easy_repo = root / "easy"
            easy_repo.mkdir()
            result = run("py", "flow_index", "harvest", "--repo", str(easy_repo),
                         "--gitnexus-export", str(easy_export))
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
            export = root / "export.json"
            export.write_text(json.dumps({
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
            }), encoding="utf-8")

            for runtime in ("py", "js"):
                repo = root / runtime
                repo.mkdir()
                # Force identical display names so path+name near-key collides.
                # Symbols differ, so exact filePath::symbol keys stay distinct first.
                result = run(
                    runtime, "flow_index", "harvest",
                    "--repo", str(repo),
                    "--gitnexus-export", str(export),
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
            merge_export = root / "merge-export.json"
            merge_export.write_text(json.dumps({
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
            }), encoding="utf-8")
            for runtime in ("py", "js"):
                repo = root / f"merge-{runtime}"
                repo.mkdir()
                result = run(
                    runtime, "flow_index", "harvest",
                    "--repo", str(repo),
                    "--gitnexus-export", str(merge_export),
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                index = json.loads((repo / ".docforge/flow-index.json").read_text(encoding="utf-8"))
                self.assertEqual(index["summary"]["total"], 1, index["flows"])
                self.assertEqual(index["flows"][0]["name"], "Create Order")

    def test_flow_index_revise_merges_stubs_and_notices_across_runtimes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            export = root / "export.json"
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
            export.write_text(json.dumps({
                "routes": [],
                "processes": processes,
                "communities": [
                    {"id": "comm-a", "heuristicLabel": "API"},
                    {"id": "comm-b", "heuristicLabel": "Services"},
                ],
            }), encoding="utf-8")

            for runtime in ("py", "js"):
                repo = root / runtime
                repo.mkdir()
                harvest = run(
                    runtime, "flow_index", "harvest",
                    "--repo", str(repo),
                    "--gitnexus-export", str(export),
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
                    "--gitnexus-export", str(export),
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
                self.assertEqual(revised["version"], "1.1")

                render = run(runtime, "flow_index", "render", "--repo", str(repo))
                self.assertEqual(render.returncode, 0, render.stderr)
                matrix = (repo / "docs/flows/INDEX.md").read_text(encoding="utf-8")
                self.assertIn("| Role |", matrix)
                self.assertIn("| placeholder |", matrix)
                self.assertIn(f"](./{index['flows'][0]['slug']}.md)", matrix)

    def test_flow_index_vague_slugs_and_organize_across_runtimes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            export = root / "export.json"
            export.write_text(json.dumps({
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
            }), encoding="utf-8")

            for runtime in ("py", "js"):
                repo = root / runtime
                repo.mkdir()
                harvest = run(
                    runtime, "flow_index", "harvest",
                    "--repo", str(repo),
                    "--gitnexus-export", str(export),
                    "--main-limit", "2",
                )
                self.assertEqual(harvest.returncode, 0, harvest.stderr)
                index = json.loads((repo / ".docforge/flow-index.json").read_text(encoding="utf-8"))
                self.assertEqual(index["version"], "1.1")
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
                    "--gitnexus-export", str(export),
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
                matrix = (repo / "docs/flows/INDEX.md").read_text(encoding="utf-8")
                self.assertIn("## email", matrix)
                self.assertIn("scheduled-reports.md", matrix)

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


if __name__ == "__main__":
    unittest.main()
