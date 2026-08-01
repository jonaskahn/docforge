"""--category and --route: group/document resolution, compat serialization,
unknown-id/group exit codes, and Python/Node parity."""

from __future__ import annotations

import json
import unittest

from _support import ROOT, run

SKILL_ROOT = ROOT / "skills" / "docforge" / "_shared"
CATALOG_DIR = SKILL_ROOT / ".metadata" / "catalog"


class RoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = json.loads((CATALOG_DIR / "index.json").read_text(encoding="utf-8"))

    def test_every_group_resolves_via_category(self) -> None:
        for group in self.index["groups"]:
            with self.subTest(group=group):
                for runtime in ("py", "js"):
                    result = run(runtime, "query_catalog", "--category", group)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    payload = json.loads(result.stdout)
                    self.assertEqual(payload["category"], group)
                    self.assertTrue(payload["summary"])
                    self.assertTrue(payload["documents"])
                    for doc in payload["documents"]:
                        self.assertIn("id", doc)
                        self.assertTrue(doc["summary"])
                        self.assertTrue((SKILL_ROOT / doc["record"]).is_file(), doc["record"])

    def test_every_document_id_resolves_via_route(self) -> None:
        for entry in self.index["document_types"]:
            doc_id = entry["id"]
            with self.subTest(id=doc_id):
                for runtime in ("py", "js"):
                    result = run(runtime, "query_catalog", "--route", doc_id)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    payload = json.loads(result.stdout)
                    self.assertEqual(payload["id"], doc_id)
                    self.assertTrue(payload["contract"])
                    self.assertTrue((SKILL_ROOT / payload["contract"]).is_file())
                    self.assertTrue(payload["template"])
                    self.assertTrue((SKILL_ROOT / payload["template"]).is_file())
                    if payload["instruction"] is not None:
                        self.assertTrue((SKILL_ROOT / payload["instruction"]).is_file())
                    if doc_id == "concept":
                        self.assertEqual(payload["instruction"], "content/architecture/instructions/concept.md")
                    self.assertTrue((SKILL_ROOT / payload["definition"]).is_file())
                    self.assertLess(len(result.stdout.encode("utf-8")), 4096)
                    for value in (payload["definition"], payload["contract"], payload["template"]):
                        self.assertNotIn("\\", value)
                    if payload["instruction"]:
                        self.assertNotIn("\\", payload["instruction"])

    def test_unknown_group_and_id_exit_two(self) -> None:
        for runtime in ("py", "js"):
            result = run(runtime, "query_catalog", "--category", "not-a-group")
            self.assertEqual(result.returncode, 2)
            result = run(runtime, "query_catalog", "--route", "not-a-document")
            self.assertEqual(result.returncode, 2)

    def test_route_and_category_are_byte_equivalent_across_runtimes(self) -> None:
        sample_ids = [entry["id"] for entry in self.index["document_types"][:5]]
        for doc_id in sample_ids:
            py_out = run("py", "query_catalog", "--route", doc_id).stdout
            js_out = run("js", "query_catalog", "--route", doc_id).stdout
            self.assertEqual(py_out, js_out, doc_id)
        for group in self.index["groups"][:3]:
            py_out = run("py", "query_catalog", "--category", group).stdout
            js_out = run("js", "query_catalog", "--category", group).stdout
            self.assertEqual(py_out, js_out, group)

    def test_legacy_modes_do_not_leak_new_fields(self) -> None:
        for runtime in ("py", "js"):
            result = run(runtime, "query_catalog", "--id", "arch_high_level")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            for leaked in ("summary", "contract_file", "template_file"):
                self.assertNotIn(leaked, payload)
            self.assertIn("scaffold_template", payload)

            tier_result = run(runtime, "query_catalog", "--tier", "spine")
            self.assertEqual(tier_result.returncode, 0, tier_result.stderr)
            rows = json.loads(tier_result.stdout)
            for row in rows:
                self.assertEqual(set(row), {"id", "tier", "path"})


if __name__ == "__main__":
    unittest.main()
