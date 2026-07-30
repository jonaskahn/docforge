"""Shared fixtures for the Docforge test suite. Not collected as tests itself."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "docforge" / "scripts"
sys.path.insert(0, str(SCRIPTS))

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


def write_flow_index(
    repo: Path,
    *,
    status: str = "main",
    priority: str | None = None,
) -> None:
    target = repo / ".docforge" / "flow-index.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    resolved_priority = priority or (status if status in {"main", "deferred"} else "main")
    doc_role = "standalone" if resolved_priority == "main" else "index_only"
    flow = {
        "id": "flow-checkout",
        "name": "Checkout",
        "display_name": "Checkout",
        "slug": "checkout",
        "family": None,
        "doc_role": doc_role,
        "composed_into": None,
        "doc_path": "docs/flows/checkout.md" if doc_role == "standalone" else None,
        "entry_ref": {"kind": "http", "signature": "POST /checkout", "filePath": "src/checkout.py", "symbol": "checkout"},
        "area": "Checkout",
        "evidence": [{"provider": "gitnexus", "artifact": "fixture", "nodeId": "checkout"}],
        "confidence": "candidate",
        "reach": {"steps": 3, "boundaries": 1, "churn": 0},
        "rank": 515,
        "priority": resolved_priority,
        "status": status,
    }
    target.write_text(json.dumps({
        "version": "1.1",
        "generated_at": "2026-07-29T00:00:00+00:00",
        "project": "fixture",
        "sources": ["fixture"],
        "providers": ["gitnexus"],
        "summary": {
            "total": 1,
            "main": int(resolved_priority == "main"),
            "deferred": int(resolved_priority == "deferred"),
            "placeholder": int(status == "placeholder"),
            "documented": int(status == "documented"),
            "skipped": int(status == "skipped"),
            "confirmed": 0,
        },
        "flows": [flow],
    }, indent=2) + "\n", encoding="utf-8")


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
        "schema": "2.0",
        "doc_id": doc_id,
        "path": path,
        "generated_at": "2026-07-27T09:12:44Z",
        "generator": {"name": "docforge", "version": "2.1.0"},
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
    from provenance_frontmatter import emit_yaml
    return emit_yaml(value) + (body if body.endswith("\n") or not body else body + "\n")


def normalized(text: str, roots: list[Path]) -> str:
    for root in roots:
        text = text.replace(str(root), "<REPO>")
    text = re.sub(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\+00:00", "<TIME>", text)
    return text.replace(".py", ".runtime").replace(".js", ".runtime")
