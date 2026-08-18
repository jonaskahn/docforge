"""Compact layout: the fold mechanism, standard-layout invariance, merged-file
scaffolding, composed contracts, and layout switching — Python/Node parity.

Compact is a second axis alongside tier, available at Spine and Diligence but
never Portfolio: every tier keeps its standard tree byte-identical, and a
compact tier covers the same subjects in fewer, denser files.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _support import initialize, load_manifest, run


def seed_source_files(repo: Path, count: int) -> None:
    src = repo / "src"
    src.mkdir(parents=True, exist_ok=True)
    for index in range(count):
        (src / f"mod_{index}.py").write_text("x = 1\n", encoding="utf-8")


def compact_tree(repo: Path) -> dict[str, str]:
    manifest = load_manifest(repo)
    assert manifest["project"]["scale"]["layout"] == "compact", manifest["project"]["scale"]
    return {doc["id"]: doc["path"] for doc in manifest["documents"]}


class CompactFoldTests(unittest.TestCase):
    def test_small_fixture_detects_compact_and_folds(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    seed_source_files(repo, 7)
                    self.assertEqual(initialize(runtime, repo, "spine", layout=None).returncode, 0)
                    docs = compact_tree(repo)
                    self.assertEqual(
                        sorted(docs.values()),
                        [
                            "CHANGELOG.md", "README.md",
                            "docs/README.md", "docs/architecture.md",
                            "docs/engineering.md", "docs/flows.md",
                            "docs/product.md", "docs/reference.md",
                        ],
                    )
                    manifest = load_manifest(repo)
                    members = {
                        doc["id"]: doc.get("compact_members")
                        for doc in manifest["documents"]
                        if doc.get("compact_members")
                    }
                    self.assertEqual(members["product_compact"], ["product_index", "product_overview"])
                    self.assertEqual(members["architecture_compact"], ["architecture_index", "arch_high_level"])
                    self.assertEqual(
                        members["engineering_compact"],
                        ["engineering_index", "setup_guide", "testing_guide"],
                    )
                    self.assertEqual(
                        members["reference_compact"],
                        ["reference_index", "configuration", "limitations", "tech_stack"],
                    )
                    # The flow index folds too: compact has no `docs/flows/`
                    # folder for it to sit in.
                    self.assertEqual(members["flows_compact"], ["flows_index"])
                    for doc in manifest["documents"]:
                        if doc.get("compact_members"):
                            kinds = {origin["kind"] for origin in doc["selection"]["origins"]}
                            self.assertIn("compact", kinds)
                            self.assertIn("tier", kinds)

    def test_standard_layout_never_folds_any_tier(self) -> None:
        for runtime in ("py", "js"):
            for tier in ("spine", "diligence", "portfolio"):
                with self.subTest(runtime=runtime, tier=tier):
                    with tempfile.TemporaryDirectory() as tmp:
                        repo = Path(tmp)
                        seed_source_files(repo, 7)
                        self.assertEqual(initialize(runtime, repo, tier, layout="standard").returncode, 0)
                        manifest = load_manifest(repo)
                        self.assertTrue(all(not doc.get("compact_members") for doc in manifest["documents"]))
                        self.assertNotIn("product_compact", {doc["id"] for doc in manifest["documents"]})
                        self.assertIn("docs/product/README.md", {doc["path"] for doc in manifest["documents"]})

    def test_compact_covers_same_subjects_as_standard_spine(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            standard_repo = Path(tmp) / "standard"
            compact_repo = Path(tmp) / "compact"
            standard_repo.mkdir()
            compact_repo.mkdir()
            seed_source_files(standard_repo, 7)
            seed_source_files(compact_repo, 7)
            self.assertEqual(initialize("py", standard_repo, "spine", layout="standard").returncode, 0)
            self.assertEqual(initialize("py", compact_repo, "spine", layout=None).returncode, 0)
            standard_ids = {doc["id"] for doc in load_manifest(standard_repo)["documents"]}
            compact = load_manifest(compact_repo)
            unfolded = {
                member
                for doc in compact["documents"]
                for member in (doc.get("compact_members") or [])
            }
            kept = {doc["id"] for doc in compact["documents"] if not doc.get("compact_members")}
            self.assertEqual(unfolded | kept, standard_ids)

    def test_dry_run_tree_shows_merged_entries(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    seed_source_files(repo, 7)
                    self.assertEqual(initialize(runtime, repo, "spine", layout=None).returncode, 0)
                    preview = run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(repo / ".docforge" / "manifest.json"), "--dry-run")
                    self.assertEqual(preview.returncode, 0, preview.stderr)
                    self.assertIn("product_compact", preview.stdout)
                    self.assertIn("docs/product.md", preview.stdout)
                    self.assertNotIn("docs/product/README.md", preview.stdout)

    def test_scaffold_writes_merged_files(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    seed_source_files(repo, 7)
                    self.assertEqual(initialize(runtime, repo, "spine", layout=None).returncode, 0)
                    scaffold = run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(repo / ".docforge" / "manifest.json"), "--document", "product_compact")
                    self.assertEqual(scaffold.returncode, 0, scaffold.stderr)
                    target = repo / "docs" / "product.md"
                    self.assertTrue(target.is_file())
                    text = target.read_text(encoding="utf-8")
                    self.assertTrue(text.startswith("# "))
                    self.assertIn("## At a glance", text)
                    self.assertIn("## Overview", text)

    def test_route_composes_member_contracts(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    result = run(runtime, "query_catalog", "--route", "engineering_compact")
                    self.assertEqual(result.returncode, 0, result.stderr)
                    payload = json.loads(result.stdout)
                    self.assertEqual(payload["id"], "engineering_compact")
                    self.assertIn("## setup_guide", payload["contract"])
                    self.assertIn("## testing_guide", payload["contract"])
                    members = payload["compact"]["members"]
                    # No manifest is given, so this is the catalog's full
                    # roster: the tier-driven core followed by the
                    # profile-driven members in `compact_order`.
                    self.assertEqual(
                        [member["id"] for member in members],
                        [
                            "engineering_index", "setup_guide", "testing_guide",
                            "conventions", "release_guide",
                            "data_quality", "library_publishing", "web_styling",
                        ],
                    )
                    self.assertEqual([member["order"] for member in members], [1, 2, 3, 4, 5, 6, 7, 8])

    def test_agents_compact_route_preserves_member_requires_without_gating_aggregate(self) -> None:
        expected = {
            "agents_architecture": ["code_graph"],
            "agents_patterns": ["code_graph"],
            "agents_testing": ["manifests"],
            "agents_conventions": [],
            "agents_tech_debt": [],
            "agents_flow": ["flow_graph"],
            "agents_glossary": ["flow_graph"],
        }
        observed = {}
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                result = run(runtime, "query_catalog", "--route", "agents_compact")
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["requires"], [])
                members = payload["compact"]["members"]
                self.assertEqual(
                    {member["id"]: member["requires"] for member in members},
                    expected,
                )
                self.assertEqual([member["order"] for member in members], list(range(1, 8)))
                observed[runtime] = payload
        self.assertEqual(observed["py"], observed["js"])

    def test_member_ordering_is_total_when_orders_tie(self) -> None:
        """`compact_order` defaults to 0, so two members can tie. The sort key
        must fall through to the id — comparing the raw `(order, document)`
        pairs would compare two dicts and raise.

        Python-only: `manage_manifest.js` is an execution shim that exits on
        `require`, so its peer helper cannot be imported. The ordering that a
        user can actually reach is covered in both runtimes by
        `test_route_composes_member_contracts`.
        """
        from runtime.manifest.python.manage_manifest import _compact_member_key

        members = [(0, {"id": "zebra"}), (0, {"id": "alpha"}), (1, {"id": "beta"})]
        ordered = [doc["id"] for _order, doc in sorted(members, key=_compact_member_key)]
        self.assertEqual(ordered, ["alpha", "zebra", "beta"])

    def test_reconcile_layout_switch_merges_and_splits(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    seed_source_files(repo, 7)
                    self.assertEqual(initialize(runtime, repo, "spine", layout="standard").returncode, 0)
                    manifest_path = repo / ".docforge" / "manifest.json"
                    for status in ("in_progress", "generated"):
                        result = run(runtime, "manage_manifest", "set", "--repo", str(repo), "--id", "product_overview", "--status", status)
                        self.assertEqual(result.returncode, 0, result.stderr)
                    scaffold = run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(manifest_path), "--document", "product_overview")
                    self.assertEqual(scaffold.returncode, 0, scaffold.stderr)
                    # standard -> compact
                    merge = run(runtime, "manage_manifest", "reconcile", "--repo", str(repo), "--layout", "compact")
                    self.assertEqual(merge.returncode, 0, merge.stderr)
                    self.assertIn("layout: standard -> compact", merge.stdout)
                    manifest = load_manifest(repo)
                    ids = {doc["id"] for doc in manifest["documents"]}
                    self.assertIn("product_compact", ids)
                    self.assertNotIn("product_index", ids)
                    # The written component is preserved as a retire candidate;
                    # reconcile never touches its file.
                    self.assertIn("retire: product_overview", merge.stdout)
                    overview = next(doc for doc in manifest["documents"] if doc["id"] == "product_overview")
                    self.assertEqual(overview["status"], "generated")
                    self.assertEqual(manifest["project"]["scale"]["layout"], "compact")
                    self.assertEqual(manifest["project"]["scale"]["decided_by"], "user")
                    # Approved retirement completes the merge.
                    retired = run(runtime, "manage_manifest", "retire", "--repo", str(repo), "--doc", "product_overview", "--mode", "obsolete")
                    self.assertEqual(retired.returncode, 0, retired.stderr)
                    overview = next(doc for doc in load_manifest(repo)["documents"] if doc["id"] == "product_overview")
                    self.assertEqual(overview["status"], "retired")
                    # compact -> standard
                    split = run(runtime, "manage_manifest", "reconcile", "--repo", str(repo), "--layout", "standard")
                    self.assertEqual(split.returncode, 0, split.stderr)
                    self.assertIn("layout: compact -> standard", split.stdout)
                    ids = {doc["id"] for doc in load_manifest(repo)["documents"]}
                    self.assertNotIn("product_compact", ids)
                    self.assertIn("product_index", ids)
                    self.assertIn("product_overview", ids)
                    overview = next(doc for doc in load_manifest(repo)["documents"] if doc["id"] == "product_overview")
                    self.assertEqual(overview["status"], "planned", "re-selected retired doc is planned for a fresh scaffold")

    def test_gate_runs_on_compact_tree(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    seed_source_files(repo, 7)
                    self.assertEqual(initialize(runtime, repo, "spine", layout=None).returncode, 0)
                    audit = run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(repo / ".docforge" / "manifest.json"), "--audit")
                    self.assertEqual(audit.returncode, 1, audit.stderr)
                    self.assertIn("docs/product.md", audit.stdout)
                    self.assertNotIn("docs/product/README.md", audit.stdout)
                    self.assertIn("8 manifest documents checked", audit.stdout)

    def test_compact_diligence_covers_same_subjects_in_fewer_files_than_standard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            standard_repo = Path(tmp) / "standard"
            compact_repo = Path(tmp) / "compact"
            standard_repo.mkdir()
            compact_repo.mkdir()
            seed_source_files(standard_repo, 7)
            seed_source_files(compact_repo, 7)
            self.assertEqual(initialize("py", standard_repo, "diligence", layout="standard").returncode, 0)
            self.assertEqual(initialize("py", compact_repo, "diligence", layout="compact").returncode, 0)
            standard_docs = load_manifest(standard_repo)["documents"]
            compact_docs = load_manifest(compact_repo)["documents"]
            self.assertLess(len(compact_docs), len(standard_docs))
            standard_ids = {doc["id"] for doc in standard_docs}
            unfolded = {
                member
                for doc in compact_docs
                for member in (doc.get("compact_members") or [])
            }
            kept = {doc["id"] for doc in compact_docs if not doc.get("compact_members")}
            # Standard layout omits an index whose only children are dynamic:
            # it would materialize a folder and README that can never gain a
            # child until discovery seeds one. Compact folds the same subject
            # as a `##` section inside a merged file, which costs no folder, so
            # it keeps the member. That is the one intended difference.
            dynamic_only_indexes = {"decisions_index", "concepts_index", "runbooks_index"}
            self.assertEqual((unfolded | kept) - dynamic_only_indexes, standard_ids)
            self.assertTrue(dynamic_only_indexes <= unfolded)
            self.assertFalse(dynamic_only_indexes & standard_ids)
            merged_paths = {doc["path"] for doc in compact_docs if doc.get("compact_members")}
            self.assertEqual(
                merged_paths,
                {
                    "docs/architecture.md", "docs/concepts.md", "docs/contributing.md",
                    "docs/decisions.md", "docs/engineering.md", "docs/flows.md",
                    "docs/operations.md", "docs/product.md", "docs/reference.md",
                    "docs/security.md",
                },
            )
            # A collection index folds into its own merged file, where it
            # becomes that file's candidate matrix. Compact materializes no
            # collection folder at all.
            standalone_paths = {doc["path"] for doc in compact_docs if not doc.get("compact_members")}
            for collection_index in (
                "docs/architecture/concepts/README.md",
                "docs/architecture/decisions/README.md",
                "docs/operations/runbooks/README.md",
                "docs/flows/README.md",
            ):
                self.assertNotIn(collection_index, standalone_paths)
            # Only the fixed tooling paths stay files of their own.
            self.assertEqual(
                standalone_paths,
                {"CHANGELOG.md", "CONTRIBUTING.md", "README.md", "SECURITY.md", "docs/README.md"},
            )

    def test_compact_diligence_gate_runs_on_folded_tree(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    seed_source_files(repo, 7)
                    self.assertEqual(initialize(runtime, repo, "diligence", layout="compact").returncode, 0)
                    audit = run(runtime, "scaffold_docs", "--repo", str(repo), "--manifest", str(repo / ".docforge" / "manifest.json"), "--audit")
                    self.assertEqual(audit.returncode, 1, audit.stderr)
                    self.assertIn("docs/security.md", audit.stdout)
                    self.assertIn("15 manifest documents checked", audit.stdout)

    def test_compact_is_rejected_at_portfolio_tier(self) -> None:
        """Portfolio is standard-only. Its value is per-member separation --
        an inventory row and a system-context view per repository -- so folding
        the collection layer into one file erases what the tier exists for. An
        explicit compact pick is refused rather than silently coerced."""
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    seed_source_files(repo, 7)
                    result = initialize(runtime, repo, "portfolio", layout="compact")
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(
                        "portfolio tier requires standard layout",
                        result.stdout + result.stderr,
                    )
                    self.assertFalse((repo / ".docforge" / "manifest.json").exists())

    def test_portfolio_forces_standard_when_scale_detects_compact(self) -> None:
        """A 7-file collection root detects `small` -> `compact`. The tier
        overrides that without a flag, and says why via `tier-constraint` --
        never silently, and never as a user pick."""
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    seed_source_files(repo, 7)
                    self.assertEqual(initialize(runtime, repo, "portfolio", layout=None).returncode, 0)
                    manifest = load_manifest(repo)
                    scale = manifest["project"]["scale"]
                    self.assertEqual(scale["class"], "small")
                    self.assertEqual(scale["layout"], "standard")
                    self.assertEqual(scale["decided_by"], "tier-constraint")
                    self.assertEqual(scale["detected_class"], "small")
                    paths = {doc["path"] for doc in manifest["documents"]}
                    self.assertNotIn("docs-portfolio.md", paths)
                    # The portfolio layer stays one file per member subject.
                    # `decisions/` and `epics/` are not listed: both index
                    # dynamic-only children, so they appear once a record is
                    # seeded rather than on tier alone.
                    for path in (
                        "docs-portfolio/README.md", "docs-portfolio/repo-inventory.md",
                        "docs-portfolio/system-context.md", "docs-portfolio/security-posture.md",
                        "docs-portfolio/operations.md", "docs-portfolio/diligence-index.md",
                        "docs-portfolio/glossary.md",
                    ):
                        self.assertIn(path, paths)

    def test_reconcile_to_portfolio_drops_a_compact_manifest_to_standard(self) -> None:
        """Changing tier to portfolio is legal on a compact manifest and must
        switch the layout, re-planning every folded member through the ordinary
        compact->standard path."""
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    seed_source_files(repo, 7)
                    self.assertEqual(initialize(runtime, repo, "diligence", layout="compact").returncode, 0)
                    self.assertTrue(
                        any(doc["id"] == "product_compact" for doc in load_manifest(repo)["documents"])
                    )
                    result = run(runtime, "manage_manifest", "reconcile", "--repo", str(repo), "--tier", "portfolio")
                    self.assertEqual(result.returncode, 0, result.stderr)
                    manifest = load_manifest(repo)
                    scale = manifest["project"]["scale"]
                    self.assertEqual(scale["layout"], "standard")
                    self.assertEqual(scale["decided_by"], "tier-constraint")
                    ids = {doc["id"] for doc in manifest["documents"]}
                    self.assertEqual({i for i in ids if i.endswith("_compact")}, set())
                    self.assertIn("product_index", ids)
                    self.assertIn("portfolio_readme", ids)


class LayoutReconcileRecordTests(unittest.TestCase):
    def test_layout_switch_on_a_manifest_without_scale_writes_a_complete_record(self) -> None:
        """`reconcile --layout` used to copy whatever `project.scale` held and
        patch `layout` onto it. On a manifest predating the field that left a
        record with no `class`, which the schema requires."""
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    seed_source_files(repo, 7)
                    self.assertEqual(initialize(runtime, repo, "spine", layout="standard").returncode, 0)
                    manifest_path = repo / ".docforge" / "manifest.json"
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    del manifest["project"]["scale"]
                    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

                    result = run(runtime, "manage_manifest", "reconcile", "--repo", str(repo), "--layout", "compact")
                    self.assertEqual(result.returncode, 0, result.stderr)
                    scale = load_manifest(repo)["project"]["scale"]
                    self.assertEqual(
                        set(scale) >= {"class", "layout", "decided_by", "decided_at", "signals"},
                        True,
                        scale,
                    )
                    self.assertEqual(scale["layout"], "compact")
                    self.assertEqual(scale["decided_by"], "user")
                    self.assertIn(scale["class"], ("small", "medium", "large"))


class CompactWithProfilesTests(unittest.TestCase):
    """Every other compact test uses the bare, no-profile repo. These use a
    real one, because profiles are where compact used to leak: a confirmed
    shape once added a standalone file per profile document, so a "compact"
    tree grew with every dimension the user selected."""

    SCOPE = {"shapes": ("library-sdk",), "audiences": ("engineers", "beginners", "coding-agents")}
    # Four shapes plus a platform and two concerns push `docs/architecture.md`
    # past COMPACT_SECTION_CAP (14).
    SPILL_SCOPE = {
        "shapes": ("web-app", "api-service", "mobile-app", "desktop-app"),
        "platforms": ("pwa",),
        "concerns": ("persistence", "ai-ml"),
        "audiences": ("engineers", "beginners"),
    }

    def test_agent_context_folds_but_host_contract_files_do_not(self) -> None:
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    seed_source_files(repo, 7)
                    (repo / ".editorconfig").write_text("root = true\n", encoding="utf-8")
                    self.assertEqual(
                        initialize(runtime, repo, "diligence", layout="compact", **self.SCOPE).returncode, 0
                    )
                    docs = load_manifest(repo)["documents"]
                    by_id = {doc["id"]: doc for doc in docs}
                    merged = by_id["agents_compact"]
                    self.assertEqual(merged["path"], "docs/agents.md")
                    self.assertEqual(
                        merged["compact_members"],
                        [
                            "agents_architecture", "agents_patterns", "agents_testing",
                            "agents_conventions", "agents_tech_debt", "agents_flow",
                            "agents_glossary",
                        ],
                    )
                    self.assertEqual(
                        merged["requires"], [],
                        "member evidence requirements must not gate the whole aggregate",
                    )
                    self.assertNotIn("agents_index", by_id)
                    paths = {doc["path"] for doc in docs}
                    self.assertFalse(
                        {p for p in paths if p.startswith("docs/agents/")},
                        "no agent view keeps its own file once the group folds",
                    )
                    # Fixed host-contract paths are never folded away.
                    for path in ("AGENTS.md", "CLAUDE.md", "CLAUDE.local.md", ".claude/settings.json"):
                        self.assertIn(path, paths)

    def test_profile_driven_documents_fold_into_their_group(self) -> None:
        """A confirmed shape must add sections, not files. `library-sdk` selects
        `docs/reference/api.md`, `compatibility.md`, `docs/product/quickstart.md`,
        and `docs/engineering/publishing.md`; in compact layout every one of
        them is a `##` inside its group's merged file."""
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    seed_source_files(repo, 7)
                    self.assertEqual(
                        initialize(runtime, repo, "diligence", layout="compact", **self.SCOPE).returncode, 0
                    )
                    docs = load_manifest(repo)["documents"]
                    by_id = {doc["id"]: doc for doc in docs}
                    for member, group in (
                        ("api_reference", "reference_compact"),
                        ("library_compatibility", "reference_compact"),
                        ("library_publishing", "engineering_compact"),
                        ("quickstart", "product_compact"),
                        ("library_migrations_index", "product_compact"),
                    ):
                        self.assertIn(member, by_id[group]["compact_members"])
                    paths = {doc["path"] for doc in docs}
                    self.assertFalse(
                        {p for p in paths if p.startswith(("docs/reference/", "docs/engineering/", "docs/product/"))},
                        "a confirmed shape adds sections, not files",
                    )

    def test_file_count_is_independent_of_confirmed_profiles(self) -> None:
        """The invariant the whole layout exists for: in compact layout the
        tree is a function of layout and tier, not of how much the repository
        turns out to be."""
        with tempfile.TemporaryDirectory() as tmp:
            counts = []
            for index, scope in enumerate((
                {"audiences": ("engineers", "beginners")},
                {"shapes": ("api-service",), "audiences": ("engineers", "beginners")},
                {"shapes": ("api-service", "web-app", "library-sdk"),
                 "audiences": ("engineers", "beginners")},
            )):
                repo = Path(tmp) / f"repo{index}"
                repo.mkdir()
                seed_source_files(repo, 7)
                self.assertEqual(
                    initialize("py", repo, "diligence", layout="compact", **scope).returncode, 0
                )
                counts.append(len(load_manifest(repo)["documents"]))
            self.assertEqual(counts[0], counts[1], counts)
            self.assertEqual(counts[1], counts[2], counts)

    def test_spilled_overflow_must_be_linked_by_the_merged_file(self) -> None:
        """A group past COMPACT_SECTION_CAP keeps its overflow at standard
        paths with no README above them. If the merged file does not link them,
        nothing does — so the audit must fail rather than silently exempt every
        merged file."""
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    seed_source_files(repo, 7)
                    self.assertEqual(
                        initialize(runtime, repo, "diligence", layout="compact", **self.SPILL_SCOPE).returncode, 0
                    )
                    docs = load_manifest(repo)["documents"]
                    merged = next(doc for doc in docs if doc["path"] == "docs/architecture.md")
                    self.assertEqual(len(merged["compact_members"]), 14)
                    self.assertIn("docs/architecture/state.md", {doc["path"] for doc in docs})

                    manifest_path = repo / ".docforge" / "manifest.json"
                    for doc in docs:
                        run(runtime, "scaffold_docs", "--repo", str(repo),
                            "--manifest", str(manifest_path), "--document", doc["id"])
                    audit = run(runtime, "scaffold_docs", "--repo", str(repo),
                                "--manifest", str(manifest_path), "--audit")
                    self.assertEqual(audit.returncode, 1)
                    self.assertIn(
                        "docs/architecture.md: missing link to docs/architecture/state.md",
                        audit.stdout,
                    )
                    # Linking the spilled child clears that finding.
                    architecture = repo / "docs" / "architecture.md"
                    architecture.write_text(
                        architecture.read_text(encoding="utf-8")
                        + "\n- [State](architecture/state.md)\n",
                        encoding="utf-8",
                    )
                    after = run(runtime, "scaffold_docs", "--repo", str(repo),
                                "--manifest", str(manifest_path), "--audit")
                    self.assertNotIn("docs/architecture.md: missing link", after.stdout)

    def test_dynamic_instances_fold_as_sections_within_budget(self) -> None:
        """A discovered flow becomes a `##` on `docs/flows.md`, not a file. Past
        COMPACT_DYNAMIC_CAP the command refuses rather than silently dropping
        the instance or growing the tree."""
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    seed_source_files(repo, 7)
                    self.assertEqual(
                        initialize(runtime, repo, "diligence", layout="compact").returncode, 0
                    )
                    before = len(load_manifest(repo)["documents"])
                    for index in range(6):
                        added = run(runtime, "manage_manifest", "add", "--repo", str(repo),
                                    "--type", "adr", "--id", f"adr_{index}",
                                    "--path", f"docs/architecture/decisions/choice-{index}.md")
                        self.assertEqual(added.returncode, 0, added.stderr)
                    manifest = load_manifest(repo)
                    self.assertEqual(len(manifest["documents"]), before)
                    merged = next(doc for doc in manifest["documents"] if doc["id"] == "decisions_compact")
                    sections = [m for m in merged["compact_members"] if isinstance(m, dict)]
                    self.assertEqual([m["slug"] for m in sections],
                                     [f"choice-{index}" for index in range(6)])
                    self.assertEqual({m["id"] for m in sections}, {"adr"})

                    over = run(runtime, "manage_manifest", "add", "--repo", str(repo),
                               "--type", "adr", "--id", "adr_6",
                               "--path", "docs/architecture/decisions/choice-6.md")
                    self.assertEqual(over.returncode, 2)
                    self.assertIn("candidate matrix", over.stdout + over.stderr)
                    self.assertEqual(len(load_manifest(repo)["documents"]), before)

    def test_standard_layout_still_gives_each_instance_its_own_file(self) -> None:
        """The fold is strictly a compact-layout behavior."""
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    seed_source_files(repo, 7)
                    self.assertEqual(
                        initialize(runtime, repo, "diligence", layout="standard").returncode, 0
                    )
                    added = run(runtime, "manage_manifest", "add", "--repo", str(repo),
                                "--type", "adr", "--id", "adr_0",
                                "--path", "docs/architecture/decisions/choice-0.md")
                    self.assertEqual(added.returncode, 0, added.stderr)
                    paths = {doc["path"] for doc in load_manifest(repo)["documents"]}
                    self.assertIn("docs/architecture/decisions/choice-0.md", paths)

    def test_layout_round_trip_preserves_folded_dynamic_instances(self) -> None:
        """`document-composition.md` promises no content is lost in either
        direction. A merged entry is not selected in standard layout, so
        without an explicit hand-off its `{id, slug, title}` sections would be
        dropped with it — three recorded decisions gone on one reconcile."""
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    seed_source_files(repo, 7)
                    self.assertEqual(
                        initialize(runtime, repo, "diligence", layout="compact").returncode, 0
                    )
                    for index in range(3):
                        added = run(runtime, "manage_manifest", "add", "--repo", str(repo),
                                    "--type", "adr", "--id", f"adr_{index}",
                                    "--path", f"docs/architecture/decisions/d{index}.md")
                        self.assertEqual(added.returncode, 0, added.stderr)

                    def sections() -> list[str]:
                        merged = next(
                            (doc for doc in load_manifest(repo)["documents"]
                             if doc["id"] == "decisions_compact"), None
                        )
                        if merged is None:
                            return []
                        return [m["slug"] for m in merged["compact_members"] if isinstance(m, dict)]

                    def adr_paths() -> list[str]:
                        return sorted(
                            doc["path"] for doc in load_manifest(repo)["documents"]
                            if doc.get("type") == "adr"
                        )

                    expected_paths = [f"docs/architecture/decisions/d{i}.md" for i in range(3)]
                    self.assertEqual(sections(), ["d0", "d1", "d2"])

                    for layout, expect_sections, expect_paths in (
                        ("standard", [], expected_paths),
                        ("compact", ["d0", "d1", "d2"], []),
                        ("standard", [], expected_paths),
                    ):
                        result = run(runtime, "manage_manifest", "reconcile",
                                     "--repo", str(repo), "--layout", layout)
                        self.assertEqual(result.returncode, 0, result.stderr)
                        self.assertEqual(sections(), expect_sections, layout)
                        self.assertEqual(adr_paths(), expect_paths, layout)

    def test_compact_spine_does_not_resurrect_diligence_indexes(self) -> None:
        """`security_index` is Diligence-only, so at Spine it is never selected
        and never folds. The ancestor pass must still skip it: a shape that
        selects `docs/security/authentication.md` used to drag a bare
        `docs/security/README.md` into a compact tree."""
        for runtime in ("py", "js"):
            with self.subTest(runtime=runtime):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    seed_source_files(repo, 7)
                    self.assertEqual(
                        initialize(runtime, repo, "spine", layout="compact",
                                   shapes=("api-service",),
                                   audiences=("engineers", "beginners")).returncode, 0
                    )
                    paths = {doc["path"] for doc in load_manifest(repo)["documents"]}
                    self.assertNotIn("docs/security/README.md", paths)
                    self.assertNotIn("docs/reference/README.md", paths)
                    self.assertIn("docs/security.md", paths)


if __name__ == "__main__":
    unittest.main()
