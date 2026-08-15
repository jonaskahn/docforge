"""Shared fixtures for the Docforge test suite. Not collected as tests itself."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI_PY = ROOT / "skills" / "docforge" / "_shared" / "runtime" / "cli" / "python"
CLI_JS = ROOT / "skills" / "docforge" / "_shared" / "runtime" / "cli" / "js"
sys.path.insert(0, str(ROOT / "skills" / "docforge" / "_shared"))
sys.path.insert(0, str(CLI_PY))

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
    command = (
        ["python3", str(CLI_PY / f"{script}.py")]
        if runtime == "py"
        else ["node", str(CLI_JS / f"{script}.js")]
    )
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
    layout: str | None = "standard",
) -> subprocess.CompletedProcess:
    """Standard layout by default so tree-shape assertions stay stable; pass
    `layout=None` to let scale detection (and the compact fold) apply."""
    args = ["init", "--repo", str(repo), "--tier", tier]
    if layout is not None:
        args += ["--layout", layout]
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


def normalized_blob_hash(content: bytes) -> str:
    """Independent reimplementation of evidence_hash's normalization (CRLF/CR
    -> LF, trailing whitespace stripped per line, trailing blank lines
    dropped) — deliberately not importing the runtime module, so tests treat
    it as a black box rather than asserting self-consistency."""
    text = re.sub(rb"\r\n|\r", b"\n", content).decode("utf-8")
    lines = [line.rstrip(" \t") for line in text.split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    normalized_bytes = b"" if not lines else ("\n".join(lines) + "\n").encode("utf-8")
    return blob_hash(normalized_bytes)


def range_blob_hash(content: bytes, start: int, end: int) -> str:
    """Independent reimplementation of evidence_hash's 1-indexed inclusive
    line-range hashing."""
    lines = re.sub(rb"\r\n|\r", b"\n", content).decode("utf-8").split("\n")
    if lines and lines[-1] == "" and content.endswith((b"\n", b"\r")):
        lines.pop()
    return blob_hash("\n".join(lines[start - 1:end]).encode("utf-8"))


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
    normalized_blob: str | None = None,
    evidence_range: tuple[int, int] | None = None,
    range_blob: str | None = None,
) -> dict:
    source = {"path": source_path, "git_blob": source_blob}
    if normalized_blob is not None:
        source["git_blob_normalized"] = normalized_blob
    if evidence_range is not None:
        source["evidence_range"] = {"start": str(evidence_range[0]), "end": str(evidence_range[1])}
    if range_blob is not None:
        source["range_blob"] = range_blob
    source["role"] = role
    return {
        "schema": "2.0",
        "doc_id": doc_id,
        "path": path,
        "generated_at": "2026-07-27T09:12:44Z",
        "generator": {"name": "docforge", "version": "2.17.0"},
        "tier": tier,
        "target_depth": target_depth,
        "graph": {"provider": "gitnexus", "flow": "native"},
        "sections": [{
            "id": section_id,
            "sources": [source],
            "unresolved": [],
        }],
    }


def markdown_with_provenance(value: dict, body: str) -> str:
    """Build legacy inline-frontmatter markdown — for migration fixtures
    only. The steady-state store never writes this; use `write_written_doc`
    for a document that should already look migrated."""
    from runtime.common.python.provenance_frontmatter import emit_yaml
    return emit_yaml(value) + (body if body.endswith("\n") or not body else body + "\n")


def write_written_doc(repo: Path, doc: dict, body: str) -> None:
    """Write a document's frontmatter-free body and stamp its folder sidecar
    entry — what the real write pipeline produces under the (only) json
    storage mode. Overwrites any prior sidecar entry for the same path."""
    from runtime.common.python import provenance_store as store
    target = repo / doc["path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body if body.endswith("\n") or not body else body + "\n", encoding="utf-8")
    entry: dict = {"id": doc["id"], "title": doc.get("title") or doc["id"]}
    if doc.get("description"):
        entry["description"] = doc["description"]
    entry["provenance"] = doc["provenance"]
    store.write_entry(repo, doc["path"], entry)


def remove_sidecar_entry(repo: Path, doc_path: str) -> None:
    """Drop a document's sidecar entry — the json-mode equivalent of a
    legacy document losing its frontmatter block."""
    from runtime.common.python import provenance_store as store
    store.remove_entry(repo, doc_path)


def normalized(text: str, roots: list[Path]) -> str:
    for root in roots:
        text = text.replace(str(root), "<REPO>")
    text = re.sub(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\+00:00", "<TIME>", text)
    return text.replace(".py", ".runtime").replace(".js", ".runtime")
