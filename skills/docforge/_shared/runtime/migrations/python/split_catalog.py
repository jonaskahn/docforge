#!/usr/bin/env python3
"""One-shot: split .metadata/catalog.json into catalog/index.json + types/ + profiles/.

Applies Phase 0.10 infrastructure-platform signal widening and bumps version to 2.17.0.
Re-runnable: overwrites the split tree from the monolith when present, otherwise from
the already-split index + types (round-trip).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent.parent.parent
METADATA = SKILL_ROOT / ".metadata"
MONOLITH = METADATA / "catalog.json"
CATALOG_DIR = METADATA / "catalog"
INDEX_PATH = CATALOG_DIR / "index.json"
TYPES_DIR = CATALOG_DIR / "types"
PROFILES_DIR = CATALOG_DIR / "profiles"

TARGET_VERSION = "2.17.0"

INFRA_EXTRA_SIGNALS = [
    {"kind": "path", "pattern": "ansible.cfg"},
    {"kind": "path", "pattern": "**/playbook*.yml", "strength": "weak"},
    {"kind": "path", "pattern": "**/roles/**", "strength": "weak"},
    {"kind": "path", "pattern": "**/kustomization.yaml"},
    {
        "kind": "content",
        "pattern": "**/*.{yaml,yml}",
        "contains": "apiVersion:",
        "strength": "weak",
    },
    {
        "kind": "content",
        "pattern": "**/*.{yaml,yml}",
        "contains": "kind: Application",
        "strength": "weak",
    },
    {
        "kind": "content",
        "pattern": "**/*.{yaml,yml}",
        "contains": "kind: Kustomization",
        "strength": "weak",
    },
    {
        "kind": "content",
        "pattern": "**/*.{yaml,yml}",
        "contains": "kind: HelmRelease",
        "strength": "weak",
    },
    {
        "kind": "content",
        "pattern": "**/*.{yaml,yml}",
        "contains": "AWSTemplateFormatVersion",
        "strength": "weak",
    },
]
INFRA_EXTRA_ALIASES = ["deployment-config", "iac"]


def dump(value: object) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def load_monolith() -> dict:
    if MONOLITH.is_file():
        return json.loads(MONOLITH.read_text(encoding="utf-8"))
    if not INDEX_PATH.is_file():
        raise SystemExit(f"error: neither {MONOLITH} nor {INDEX_PATH} exists")
    # Reconstruct from split for re-apply of signal patches.
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    profiles = {}
    for dimension in ("shapes", "platforms", "frameworks", "concerns", "audiences"):
        path = PROFILES_DIR / f"{dimension}.json"
        profiles[dimension] = json.loads(path.read_text(encoding="utf-8"))
    documents = []
    for row in index["document_types"]:
        detail = json.loads((TYPES_DIR / f"{row['id']}.json").read_text(encoding="utf-8"))
        documents.append(detail)
    return {
        "$schema": "catalog-schema.json",
        "version": index["version"],
        "tiers": [
            {"id": tid, "order": meta["order"]}
            for tid, meta in index["tiers"].items()
        ]
        if isinstance(index.get("tiers"), dict)
        else index.get("tiers", []),
        "profiles": profiles,
        "groups": index.get("groups", []),
        "capabilities": index.get("capabilities", []),
        "documents": documents,
        "cue_hints": index.get("cue_hints", []),
    }


def apply_infra_widening(catalog: dict) -> None:
    shapes = catalog["profiles"]["shapes"]
    infra = next(s for s in shapes if s["id"] == "infrastructure-platform")
    existing = {(s.get("kind"), s.get("pattern"), s.get("contains")) for s in infra["signals"]}
    for signal in INFRA_EXTRA_SIGNALS:
        key = (signal.get("kind"), signal.get("pattern"), signal.get("contains"))
        if key not in existing:
            infra["signals"].append(signal)
            existing.add(key)
    aliases = list(infra.get("aliases", []))
    for alias in INFRA_EXTRA_ALIASES:
        if alias not in aliases:
            aliases.append(alias)
    infra["aliases"] = aliases


def normalize_tiers(tiers) -> dict:
    if isinstance(tiers, dict):
        return tiers
    return {item["id"]: {"order": item["order"]} for item in tiers}


def emit(catalog: dict, *, dry_run: bool) -> dict:
    catalog = json.loads(json.dumps(catalog))  # deep copy
    apply_infra_widening(catalog)
    catalog["version"] = TARGET_VERSION

    tiers = normalize_tiers(catalog["tiers"])
    document_types = [
        {
            "id": doc["id"],
            "tier": doc["selection"]["min_tier"],
            "path": doc["path"],
        }
        for doc in catalog["documents"]
    ]
    index = {
        "$schema": "catalog-index-schema.json",
        "version": TARGET_VERSION,
        "tiers": tiers,
        "groups": catalog["groups"],
        "capabilities": catalog["capabilities"],
        "cue_hints": catalog.get("cue_hints", []),
        "document_types": document_types,
    }

    type_files = {doc["id"]: doc for doc in catalog["documents"]}
    profile_files = {
        dimension: catalog["profiles"][dimension]
        for dimension in ("shapes", "platforms", "frameworks", "concerns", "audiences")
    }

    summary = {
        "version": TARGET_VERSION,
        "document_types": len(type_files),
        "profiles": {k: len(v) for k, v in profile_files.items()},
        "infra_signals": len(
            next(s for s in profile_files["shapes"] if s["id"] == "infrastructure-platform")[
                "signals"
            ]
        ),
        "infra_aliases": next(
            s for s in profile_files["shapes"] if s["id"] == "infrastructure-platform"
        )["aliases"],
    }

    if dry_run:
        print(json.dumps(summary, indent=2))
        return summary

    TYPES_DIR.mkdir(parents=True, exist_ok=True)
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(dump(index), encoding="utf-8")
    for doc_id, detail in type_files.items():
        (TYPES_DIR / f"{doc_id}.json").write_text(dump(detail), encoding="utf-8")
    for dimension, definitions in profile_files.items():
        (PROFILES_DIR / f"{dimension}.json").write_text(dump(definitions), encoding="utf-8")

    # Round-trip check: reconstruct monolith shape and compare documents field-for-field.
    reconstructed_docs = []
    for row in index["document_types"]:
        reconstructed_docs.append(
            json.loads((TYPES_DIR / f"{row['id']}.json").read_text(encoding="utf-8"))
        )
    original_docs = {d["id"]: d for d in catalog["documents"]}
    for doc in reconstructed_docs:
        # catalog["documents"] already has version-bumped copy; strip nothing.
        orig = original_docs[doc["id"]]
        if doc != orig:
            raise SystemExit(f"error: round-trip mismatch for document {doc['id']}")

    print(
        f"Wrote {INDEX_PATH.relative_to(SKILL_ROOT)} + "
        f"{len(type_files)} types + {len(profile_files)} profile files "
        f"(version {TARGET_VERSION})."
    )
    print(json.dumps(summary, indent=2))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--root",
        type=Path,
        help="skill root override (default: derived from this file's location)",
    )
    args = parser.parse_args()
    global METADATA, MONOLITH, INDEX_PATH, TYPES_DIR, PROFILES_DIR, SKILL_ROOT
    if args.root:
        root = Path(args.root).resolve()
        SKILL_ROOT = root
        METADATA = root / ".metadata"
        MONOLITH = METADATA / "catalog.json"
        INDEX_PATH = METADATA / "catalog" / "index.json"
        TYPES_DIR = METADATA / "catalog" / "types"
        PROFILES_DIR = METADATA / "catalog" / "profiles"
    try:
        catalog = load_monolith()
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1
    emit(catalog, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
