#!/usr/bin/env python3
"""Create and maintain the docforge tracking manifest at <repo>/.docforge/manifest.json.

The manifest is the durable plan and fill-state of the documentation tree: one
entry per planned document, its group, path, template, and status. Step 0 Gate 1
writes it with everything `planned`; the write loop advances each document's
status as it lands.

Subcommands
-----------
  init     write a fresh .docforge/manifest.json for a tier (spine documents),
           every status "planned". Overlay and discovered-flow documents are
           added later with `add`.
  add      append one document to a group (a discovered flow, an overlay doc).
  set      change one document's status by id, recompute counts, stamp the time.
  status   print the plan as a table with a status summary.

Statuses: planned -> in_progress -> generated -> needs_review -> complete (or skipped).
Paths mirror references/docs-tree.md and scripts/docs_scaffold.py exactly.

Examples
--------
    python manifest_sync.py init   --repo ../my-service --tier 2 --name my-service
    python manifest_sync.py add    --repo ../my-service --group flows \\
                                    --id flow_checkout --type flows \\
                                    --path docs/flows/checkout.md --needs-dg
    python manifest_sync.py set    --repo ../my-service --id setup_guide --status complete
    python manifest_sync.py status --repo ../my-service

Standard library only.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_JSON = SKILL_ROOT / ".metadata" / "document-templates.json"

MANIFEST_REL = ".docforge/manifest.json"

STATUSES = ["planned", "in_progress", "generated", "needs_review", "complete", "skipped"]
GROUPS = ["architecture", "flows", "product", "engineering", "operations",
          "reference", "security", "contributing", "records", "agent-context"]

# Spine plan: the documents a tier implies, keyed to the same paths docs_scaffold.py
# emits. `template` and `requires_*` are resolved from document-templates.json by type.
# (group, id, type, path, min_tier)
SPINE_PLAN: list[tuple[str, str, str, str, int]] = [
    ("architecture", "arch_high_level", "architecture-high-level", "docs/architecture/high-level.md", 1),
    ("architecture", "arch_low_level",  "architecture-low-level",  "docs/architecture/low-level.md", 2),
    ("architecture", "dependencies",    "dependencies-inventory",  "docs/architecture/dependencies.md", 2),
    ("architecture", "tech_debt",       "tech-debt-register",      "docs/architecture/tech-debt.md", 2),
    ("architecture", "adr_index",       "decision-records",        "docs/architecture/decisions/README.md", 2),
    ("product",      "product_overview","product-overview",        "docs/product/overview.md", 1),
    ("engineering",  "setup_guide",     "setup-guide",             "docs/engineering/setup.md", 1),
    ("reference",    "limitations",     "limitations-register",    "docs/reference/limitations.md", 1),
    ("security",     "security_policy", "security-policy",         "SECURITY.md", 2),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_template_index() -> dict[str, dict]:
    """type -> {template, needs_kg, needs_dg} from document-templates.json."""
    data = json.loads(TEMPLATES_JSON.read_text(encoding="utf-8"))
    idx: dict[str, dict] = {}
    for t in data.get("templates", []):
        req = t.get("requires", [])
        idx[t["type"]] = {
            "template": t.get("instruction_file"),
            "needs_kg": "knowledge_graph" in req,
            "needs_dg": "domain_graph" in req,
        }
    return idx


def make_doc(id_: str, type_: str, path: str, template: str | None,
             needs_kg: bool, needs_dg: bool) -> dict:
    return {
        "id": id_,
        "type": type_,
        "path": path,
        "status": "planned",
        "requires_domain_graph": needs_dg,
        "requires_knowledge_graph": needs_kg,
        "template": template,
        # Per-section provenance, filled as the document is written and stamped
        # (each entry: {"id": <anchor>, "sources": [{"path", "git_blob"}]}).
        # check_provenance.py reads this to decide staleness; empty while planned.
        "sections": [],
    }


def manifest_path(repo: Path) -> Path:
    return repo / MANIFEST_REL


def load_manifest(repo: Path) -> dict:
    p = manifest_path(repo)
    if not p.exists():
        sys.exit(f"No manifest at {p}. Run `init` first.")
    return json.loads(p.read_text(encoding="utf-8"))


def recount(man: dict) -> None:
    docs = [d for g in man["document_groups"] for d in g["documents"]]
    man.setdefault("metadata", {})
    man["metadata"].update({
        "total_documents": len(docs),
        "completed": sum(1 for d in docs if d["status"] == "complete"),
        "in_progress": sum(1 for d in docs if d["status"] == "in_progress"),
        "requires_review": sum(1 for d in docs if d["status"] == "needs_review"),
        "last_updated": now_iso(),
    })


def save_manifest(repo: Path, man: dict) -> None:
    recount(man)
    p = manifest_path(repo)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(man, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_init(args) -> int:
    p = manifest_path(args.repo)
    if p.exists() and not args.force:
        sys.exit(f"{p} exists. Pass --force to overwrite.")

    if not args.no_agent_context and "agent-context" not in args.overlay:
        args.overlay.append("agent-context")

    tidx = load_template_index()
    groups: dict[str, list[dict]] = {}
    for group, id_, type_, path, min_tier in SPINE_PLAN:
        if min_tier > args.tier:
            continue
        meta = tidx.get(type_, {})
        doc = make_doc(id_, type_, path, meta.get("template"),
                       meta.get("needs_kg", False), meta.get("needs_dg", False))
        groups.setdefault(group, []).append(doc)

    # flows is always present but discovered later via `add`
    groups.setdefault("flows", [])

    ordered = [g for g in GROUPS if g in groups]
    man = {
        "version": "1.1",
        "generated_at": now_iso(),
        "project_context": {
            "repo_name": args.name,
            "repo_path": str(args.repo.resolve()),
            "tier": {1: "core", 2: "standard", 3: "extended"}[args.tier],
            "overlays": args.overlay,
        },
        "document_groups": [{"group": g, "documents": groups[g]} for g in ordered],
        "metadata": {},
    }
    save_manifest(args.repo, man)
    n = sum(len(v) for v in groups.values())
    print(f"Wrote {manifest_path(args.repo)} — tier {args.tier}, {n} spine documents planned.")
    print("Add discovered flows and overlay documents with `add`; advance status with `set`.")
    return 0


def cmd_add(args) -> int:
    man = load_manifest(args.repo)
    if args.group not in GROUPS:
        sys.exit(f"Unknown group '{args.group}'. One of: {', '.join(GROUPS)}")

    all_ids = {d["id"] for g in man["document_groups"] for d in g["documents"]}
    if args.id in all_ids:
        sys.exit(f"Document id '{args.id}' already in manifest.")

    tidx = load_template_index()
    meta = tidx.get(args.type, {})
    template = args.template or meta.get("template")
    needs_kg = args.needs_kg or meta.get("needs_kg", False)
    needs_dg = args.needs_dg or meta.get("needs_dg", False)
    doc = make_doc(args.id, args.type, args.path, template, needs_kg, needs_dg)

    # Rebuild document_groups with new doc added to target group
    groups_map = {g["group"]: g["documents"] for g in man["document_groups"]}
    if args.group not in groups_map:
        groups_map[args.group] = []
    groups_map[args.group].append(doc)

    # Reconstruct document_groups in canonical order
    man["document_groups"] = [
        {"group": g, "documents": groups_map[g]}
        for g in GROUPS if g in groups_map
    ]

    save_manifest(args.repo, man)
    print(f"Added {args.id} ({args.path}) to group '{args.group}', status planned.")
    return 0


def cmd_set(args) -> int:
    if args.status not in STATUSES:
        sys.exit(f"Invalid status '{args.status}'. One of: {', '.join(STATUSES)}")
    man = load_manifest(args.repo)
    for g in man["document_groups"]:
        for d in g["documents"]:
            if d["id"] == args.id:
                old = d["status"]
                d["status"] = args.status
                save_manifest(args.repo, man)
                print(f"{args.id}: {old} -> {args.status}")
                return 0
    sys.exit(f"No document with id '{args.id}' in manifest.")


def cmd_status(args) -> int:
    man = load_manifest(args.repo)
    ctx = man.get("project_context", {})
    print(f"repo: {ctx.get('repo_name')}  tier: {ctx.get('tier')}  "
          f"overlays: {', '.join(ctx.get('overlays') or []) or 'none'}")
    print(f"updated: {man.get('metadata', {}).get('last_updated')}\n")

    rows = []
    for g in man["document_groups"]:
        for d in g["documents"]:
            rows.append((g["group"], d["status"], d["id"], d["path"]))
    if not rows:
        print("(no documents planned)")
        return 0
    w_grp = max(len(r[0]) for r in rows)
    w_st = max(len(r[1]) for r in rows)
    w_id = max(len(r[2]) for r in rows)
    for grp, st, id_, path in rows:
        print(f"  {grp:<{w_grp}}  {st:<{w_st}}  {id_:<{w_id}}  {path}")

    counts: dict[str, int] = {}
    for _, st, _, _ in rows:
        counts[st] = counts.get(st, 0) + 1
    summary = "  ".join(f"{k}={v}" for k, v in sorted(counts.items()))
    print(f"\n{len(rows)} documents:  {summary}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add_repo(sp):
        sp.add_argument("--repo", required=True, type=Path, help="path to the target repository")

    sp = sub.add_parser("init", help="write a fresh manifest for a tier")
    add_repo(sp)
    sp.add_argument("--tier", type=int, default=2, choices=[1, 2, 3])
    sp.add_argument("--name", default=None, help="repo name for project_context")
    sp.add_argument("--overlay", action="append", default=[], help="repeatable overlay name")
    sp.add_argument("--no-agent-context", action="store_true", dest="no_agent_context",
                     help="opt out of the agent-context overlay, which is otherwise "
                          "recorded by default on every init")
    sp.add_argument("--force", action="store_true", help="overwrite an existing manifest")
    sp.set_defaults(func=cmd_init)

    sp = sub.add_parser("add", help="append one document")
    add_repo(sp)
    sp.add_argument("--group", required=True)
    sp.add_argument("--id", required=True)
    sp.add_argument("--type", required=True)
    sp.add_argument("--path", required=True)
    sp.add_argument("--template", default=None)
    sp.add_argument("--needs-kg", action="store_true", dest="needs_kg")
    sp.add_argument("--needs-dg", action="store_true", dest="needs_dg")
    sp.set_defaults(func=cmd_add)

    sp = sub.add_parser("set", help="change one document's status")
    add_repo(sp)
    sp.add_argument("--id", required=True)
    sp.add_argument("--status", required=True, choices=STATUSES)
    sp.set_defaults(func=cmd_set)

    sp = sub.add_parser("status", help="print the plan and status summary")
    add_repo(sp)
    sp.set_defaults(func=cmd_status)

    args = ap.parse_args()
    if not args.repo.is_dir():
        print(f"Not a directory: {args.repo}", file=sys.stderr)
        return 1
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
