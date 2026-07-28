#!/usr/bin/env python3
"""Scaffold and audit a repository documentation tree.

Two modes:

  scaffold  create the docs/ tree for a tier and overlays, seeding files from
            assets/templates/ where a template exists

  audit     report what is missing, what still holds unfilled {{…}} scaffold
            markers, which internal links are broken, which other generated
            documents are named in backtick text instead of being linked to
            (unlinked file mentions), where forge-specific language has
            leaked into documents that are supposed to be host-neutral, and
            which flow/concept folders were promoted without a real subfile
            (folder-only-readme). Typed <UPPER_SNAKE> human-fill tokens are
            listed separately and do not count as defects.

Examples
--------
    python scaffold_docs.py --repo ../my-service --tier 2 --overlay api
    python scaffold_docs.py --repo ../my-service --tier 2 --overlay api --dry-run
    python scaffold_docs.py --repo ../my-service --audit

Standard library only.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_ROOT / "assets" / "templates"

# ---------------------------------------------------------------------------
# Tree specification.  (path, tier, template-or-None)
# Directories are implied by their files; every directory also gets a README.md.
# ---------------------------------------------------------------------------

SPINE: list[tuple[str, int, str | None]] = [
    ("README.md", 1, "root-readme.md"),
    ("CHANGELOG.md", 1, "changelog.md"),
    ("SECURITY.md", 2, "root-security.md"),
    ("docs/README.md", 1, "docs-index.md"),
    ("docs/product/overview.md", 1, None),
    ("docs/product/capabilities.md", 2, None),
    ("docs/product/roadmap.md", 2, None),
    ("docs/flows/README.md", 2, None),
    ("docs/architecture/high-level.md", 1, "architecture-high-level.md"),
    ("docs/architecture/low-level.md", 2, "architecture-low-level.md"),
    ("docs/architecture/data-flow.md", 2, None),
    ("docs/architecture/dependencies.md", 2, "dependencies.md"),
    ("docs/architecture/tech-debt.md", 2, "tech-debt.md"),
    ("docs/architecture/constraints.md", 2, "constraints.md"),
    ("docs/architecture/concepts/README.md", 2, None),
    ("docs/architecture/decisions/0001-record-architecture-decisions.md", 2, "adr.md"),
    ("docs/engineering/setup.md", 1, "setup.md"),
    ("docs/engineering/testing.md", 1, None),
    ("docs/engineering/conventions.md", 2, None),
    ("docs/engineering/release.md", 2, None),
    ("docs/operations/deployment.md", 2, None),
    ("docs/operations/observability.md", 2, None),
    ("docs/operations/runbooks/example-symptom.md", 2, "runbook.md"),
    ("docs/reference/configuration.md", 1, None),
    ("docs/reference/limitations.md", 1, "limitations.md"),
    ("docs/reference/glossary.md", 2, None),
    ("docs/security/threat-model.md", 2, None),
    ("docs/security/data-handling.md", 2, None),
    ("docs/contributing/README.md", 2, None),
    ("docs/contributing/ownership.md", 2, None),
    ("docs/contributing/templates/bug-report.md", 2, None),
    ("docs/contributing/templates/feature-request.md", 2, None),
    ("docs/contributing/templates/change-proposal.md", 2, None),
]

OVERLAYS: dict[str, list[tuple[str, str | None]]] = {
    "data-pipeline": [
        ("docs/architecture/data-flow.md", None),
        ("docs/architecture/contracts/README.md", None),
        ("docs/architecture/contracts/example-dataset.md", "data-contract.md"),
        ("docs/engineering/data-quality.md", None),
        ("docs/reference/data-types.md", None),
        ("docs/operations/runbooks/backfill.md", "runbook.md"),
        ("docs/operations/runbooks/failed-run.md", "runbook.md"),
        ("docs/operations/runbooks/schema-change.md", "runbook.md"),
    ],
    "api": [
        ("docs/product/quickstart.md", None),
        ("docs/product/versioning.md", None),
        ("docs/reference/api.md", None),
        ("docs/reference/errors.md", "error-catalog.md"),
        ("docs/reference/rate-limits.md", None),
        ("docs/security/authentication.md", None),
    ],
    "web": [
        ("docs/architecture/rendering.md", None),
        ("docs/architecture/state.md", None),
        ("docs/architecture/ui-components.md", None),
        ("docs/engineering/styling.md", None),
        ("docs/reference/browser-support.md", None),
    ],
    "library": [
        ("docs/product/quickstart.md", None),
        ("docs/product/migration/README.md", None),
        ("docs/reference/api.md", None),
        ("docs/reference/compatibility.md", None),
        ("docs/engineering/publishing.md", None),
    ],
    "infrastructure": [
        ("docs/architecture/environments.md", None),
        ("docs/architecture/network.md", None),
        ("docs/operations/apply.md", None),
        ("docs/operations/state.md", None),
        ("docs/operations/disaster-recovery.md", None),
        ("docs/reference/resources.md", None),
        ("docs/reference/access.md", None),
    ],
    "business-analyst": [
        ("docs/product/business-analyst/README.md", "ba-readme.md"),
        ("docs/product/business-analyst/business-rules.md", "business-rules.md"),
        ("docs/product/business-analyst/process-flows.md", "process-flows.md"),
        ("docs/product/business-analyst/requirements-traceability.md", "requirements-traceability.md"),
    ],
    "product-owner": [
        ("docs/product/product-owner/README.md", "po-readme.md"),
        ("docs/product/product-owner/feature-catalog.md", "feature-catalog.md"),
        ("docs/product/product-owner/success-metrics.md", "success-metrics.md"),
        ("docs/product/product-owner/release-notes.md", "release-notes.md"),
        ("docs/product/product-owner/backlog-traceability.md", "backlog-traceability.md"),
    ],
    # AI-agent context files (AGENTS.md kernel + docs/agents/ brief stubs). See
    # references/overlay-agent-context.md. agents-conventions.md (conditional on an
    # existing CONVENTIONS.md) and the cross-vendor mirrors are deliberately excluded
    # here — they're hand-pulled at finalization time, never scaffolded up front.
    "agent-context": [
        ("AGENTS.md", "agents-kernel.md"),
        ("CLAUDE.md", "claude-md.md"),
        ("CLAUDE.local.md", "claude-local-md.md"),
        (".claude/settings.json", "claude-settings.json"),
        ("docs/agents/architecture.md", "agents-architecture.md"),
        ("docs/agents/patterns.md", "agents-patterns.md"),
        ("docs/agents/glossary.md", "agents-glossary.md"),
        ("docs/agents/testing.md", "agents-testing.md"),
        ("docs/agents/tech-debt.md", "agents-tech-debt.md"),
        ("docs/agents/flow.md", "agents-flow.md"),
    ],
}

FOLDER_BLURBS = {
    "docs/product": "What this does and why it exists — written for business readers.",
    "docs/flows": "One file per business flow, flat by default; promoted to a folder only once a real per-reader deep-dive is written.",
    "docs/architecture": "How the system is built, and why — high-level map, low-level detail, concepts, decisions.",
    "docs/architecture/concepts": "Deep-dive subsystems, flat by default; promoted to a folder only once a real engineering deep-dive is written.",
    "docs/architecture/decisions": "Architecture decision records. Append-only; superseded records keep their number.",
    "docs/architecture/contracts": "Data contracts for every dataset consumed or published.",
    "docs/engineering": "Setup, testing, conventions and release — everything a contributor needs.",
    "docs/operations": "Deployment, observability and runbooks.",
    "docs/operations/runbooks": "One file per recurring incident or procedure, named by symptom.",
    "docs/reference": "Lookup material: configuration, limitations, errors, glossary.",
    "docs/security": "Threat model, data handling and disclosure process.",
    "docs/contributing": "How changes are proposed, reviewed and merged.",
    "docs/contributing/templates": "Host-neutral issue and change templates.",
    "docs/product/migration": "One guide per major version transition.",
    "docs/product/business-analyst": "Business rules, process flows and requirements traceability — for a Business Analyst.",
    "docs/product/product-owner": "Feature value, success metrics and release notes — for a Product Owner.",
    "docs/agents": "Machine-consumption context for AI coding agents — brief stubs that link to (never restate) the human-facing documents that own each fact. The entry kernel is root AGENTS.md, not this folder's index.",
}

PLACEHOLDER = re.compile(r"\{\{[^}]+\}\}")   # {{…}} scaffold marker — must be filled
TODO = re.compile(r"TODO\(([^)]*)\)")        # retired punt form — treated as a defect
# Typed human-fill token: <UPPER_SNAKE> standing in for one genuinely external value.
# These are intentional and expected; they are reported separately, not as defects.
TOKEN = re.compile(r"<[A-Z][A-Z0-9_]{2,}>")
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
# A backtick-quoted path ending in .md — a candidate cross-reference that
# should be an actual link, not bare text naming the file.
MENTION = re.compile(r"`([A-Za-z0-9_./-]+\.md)`")
FORGE = re.compile(
    r"\b(github|gitlab|bitbucket|gitea|forgejo|sourcehut|azure devops|"
    r"pull request|merge request|github actions|gitlab ci|codeowners)\b",
    re.IGNORECASE,
)
NEUTRAL_ZONE = ("docs/contributing/",)


# ---------------------------------------------------------------------------
# Scaffold
# ---------------------------------------------------------------------------

def folder_readme(rel_dir: str) -> str:
    blurb = FOLDER_BLURBS.get(rel_dir, "{{One line: what lives in this folder.}}")
    title = rel_dir.rstrip("/").split("/")[-1].replace("-", " ").title()
    return f"# {title}\n\n{blurb}\n\n| Document | Contents |\n|---|---|\n| | |\n"


def collect(tier: int, overlays: list[str]) -> dict[str, str | None]:
    wanted: dict[str, str | None] = {
        path: tpl for path, t, tpl in SPINE if t <= tier
    }
    for name in overlays:
        for path, tpl in OVERLAYS.get(name, []):
            wanted.setdefault(path, tpl)
    return wanted


def scaffold(repo: Path, tier: int, overlays: list[str], dry_run: bool) -> int:
    wanted = collect(tier, overlays)

    # every directory under docs/ gets an index
    dirs = {str(Path(p).parent) for p in wanted if p.startswith("docs/")}
    for d in sorted(dirs):
        idx = f"{d}/README.md"
        if idx not in wanted:
            wanted[idx] = "__folder_readme__"

    created, skipped = 0, 0
    for rel in sorted(wanted):
        target = repo / rel
        if target.exists():
            skipped += 1
            continue
        tpl = wanted[rel]
        if tpl == "__folder_readme__":
            body = folder_readme(str(Path(rel).parent))
        elif tpl and (TEMPLATES / tpl).exists():
            body = (TEMPLATES / tpl).read_text(encoding="utf-8")
        else:
            title = Path(rel).stem.replace("-", " ").title()
            body = (
                f"# {title}\n\n_Last reviewed: {{{{YYYY-MM-DD}}}}_\n\n"
                "{{Write this section from evidence in the repository. "
                "Delete this file if it does not apply.}}\n"
            )
        print(f"{'would create' if dry_run else 'create'}  {rel}")
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")
        created += 1

    print(f"\n{created} created, {skipped} already present.")
    if created and not dry_run:
        print(
            "\nThese are scaffolds, not deliverables. Write every section you have "
            "evidence for in full; the only marks that may survive are typed "
            "<UPPER_SNAKE> tokens for genuinely external facts. No {{…}} marker "
            "should remain before presenting."
        )
    return 0


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------

def audit(repo: Path, tier: int, overlays: list[str]) -> int:
    docs = repo / "docs"
    if not docs.is_dir():
        print("No docs/ directory found. Run scaffold mode first.")
        return 1

    files = sorted(p for p in docs.rglob("*.md") if "_archive" not in p.parts)
    for extra in ("README.md", "SECURITY.md", "CONTRIBUTING.md", "AGENTS.md", "CLAUDE.md"):
        p = repo / extra
        if p.exists():
            files.append(p)

    findings: dict[str, list[str]] = {
        "missing": [], "unfilled scaffold": [], "empty": [],
        "broken links": [], "unlinked file mentions": [],
        "forge leakage": [], "no review date": [],
        "folder-only-readme": [],
    }
    # Informational, not a defect: typed <UPPER_SNAKE> tokens are the sanctioned
    # human-fill slots for genuinely external facts. Listed so a reviewer knows
    # exactly what remains to fill, but excluded from the defect total.
    tokens: list[str] = []

    wanted = collect(tier, overlays)
    for rel in sorted(wanted):
        if not (repo / rel).exists():
            findings["missing"].append(rel)

    # A flow or concept promoted to a folder but never given a real subfile: the
    # exact shape that produces a dangling "Go deeper" link. Flat files are the
    # default and carry no defect; a folder must earn its existence with content.
    for parent in ("docs/flows", "docs/architecture/concepts"):
        parent_dir = repo / parent
        if not parent_dir.is_dir():
            continue
        for child in sorted(parent_dir.iterdir()):
            if not child.is_dir() or child.name.startswith("_"):
                continue
            siblings = [p for p in child.glob("*.md") if p.name != "README.md"]
            if (child / "README.md").exists() and not siblings:
                findings["folder-only-readme"].append(f"{child.relative_to(repo).as_posix()}/")

    for path in files:
        rel = path.relative_to(repo).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")

        n_scaffold = len(PLACEHOLDER.findall(text)) + len(TODO.findall(text))
        if n_scaffold:
            findings["unfilled scaffold"].append(f"{rel} ({n_scaffold})")

        n_token = len(set(TOKEN.findall(text)))
        if n_token:
            tokens.append(f"{rel} ({n_token})")

        body = "\n".join(
            ln for ln in text.splitlines()
            if ln.strip() and not ln.lstrip().startswith("#")
        )
        if len(body) < 120:
            findings["empty"].append(rel)

        linked_targets = {t.split("#")[0] for t in LINK.findall(text)}
        for target in LINK.findall(text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            if "{{" in target or "NNNN" in target:  # unfilled template link
                continue
            if TOKEN.search(target):  # link points through a human-fill token
                continue
            resolved = (path.parent / target.split("#")[0]).resolve()
            if not resolved.exists():
                findings["broken links"].append(f"{rel} -> {target}")

        # a real file named in backticks but never actually linked to
        for line in text.splitlines():
            for m in MENTION.finditer(line):
                target = m.group(1)
                if target in linked_targets or target.split("/")[-1] in linked_targets:
                    continue
                before = line[m.start() - 1] if m.start() > 0 else ""
                after = line[m.end():m.end() + 2]
                if before == "[" and after.startswith("("):
                    continue  # `` `file.md` `` used as the label of its own link
                resolved = (path.parent / target).resolve()
                if resolved.exists():
                    findings["unlinked file mentions"].append(f"{rel} -> {target}")

        if not rel.startswith(NEUTRAL_ZONE) and rel != "CONTRIBUTING.md":
            hits = {m.group(0).lower() for m in FORGE.finditer(text)}
            if hits:
                findings["forge leakage"].append(f"{rel}: {', '.join(sorted(hits))}")

        volatile = ("limitations", "dependencies", "setup", "configuration",
                    "overview", "high-level", "low-level", "tech-debt",
                    "constraints", "runbook")
        if (any(v in rel for v in volatile) and not rel.endswith("README.md")
                and "Last reviewed" not in text):
            findings["no review date"].append(rel)

    total = sum(len(v) for v in findings.values())
    for label, items in findings.items():
        if not items:
            continue
        print(f"\n{label.upper()} ({len(items)})")
        for item in items[:25]:
            print(f"  {item}")
        if len(items) > 25:
            print(f"  ... and {len(items) - 25} more")

    if tokens:
        print(f"\nHUMAN-FILL TOKENS ({len(tokens)})  — not defects; external facts "
              "for a human to fill in during review")
        for item in tokens[:25]:
            print(f"  {item}")
        if len(tokens) > 25:
            print(f"  ... and {len(tokens) - 25} more")

    print(f"\n{len(files)} documents checked, {total} defects"
          + (f", {len(tokens)} files with human-fill tokens." if tokens else "."))
    if not total:
        print("No defects. Any UNFILLED SCAFFOLD count must be zero before presenting; "
              "typed <UPPER_SNAKE> tokens are fine to leave for human review. Now apply "
              "the judgement checks in references/quality-bar.md — this script cannot "
              "tell you whether the content is true.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True, type=Path, help="path to the repository")
    ap.add_argument("--tier", type=int, default=2, choices=[1, 2, 3],
                    help="1 spine, 2 diligence, 3 portfolio (default 2)")
    ap.add_argument("--overlay", action="append", default=[],
                    choices=sorted(OVERLAYS), help="repeatable")
    ap.add_argument("--no-agent-context", action="store_true",
                    help="opt out of the agent-context overlay, which is otherwise "
                         "included by default on every run")
    ap.add_argument("--audit", action="store_true", help="audit instead of scaffold")
    ap.add_argument("--dry-run", action="store_true", help="show what would be created")
    args = ap.parse_args()

    if not args.no_agent_context and "agent-context" not in args.overlay:
        args.overlay.append("agent-context")

    if not args.repo.is_dir():
        print(f"Not a directory: {args.repo}", file=sys.stderr)
        return 1
    if args.audit:
        return audit(args.repo, args.tier, args.overlay)
    return scaffold(args.repo, args.tier, args.overlay, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
