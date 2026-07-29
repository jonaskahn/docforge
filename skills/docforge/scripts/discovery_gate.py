#!/usr/bin/env python3
"""Validate and apply discovery-gate judgments (offline; no model I/O)."""

from __future__ import annotations

import json
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
GATE_SCHEMA_PATH = SKILL_ROOT / ".metadata" / "discovery-gate-schema.json"
ACTIONS = {"promote", "keep", "demote", "drop", "propose"}
CONFIDENCES = {"confirmed", "candidate", "suppressed"}
DIMENSIONS = {"shapes", "platforms", "frameworks", "concerns", "audiences"}


def needs_gate(detections: list[dict], cues: list[dict] | None = None) -> bool:
    if any(item.get("confidence") == "candidate" for item in detections):
        return True
    if any(item.get("ambiguous_with") for item in detections):
        return True
    if cues:
        for cue in cues:
            profiles = cue.get("candidate_profiles") or []
            if len(profiles) >= 2:
                return True
    return False


def _catalog_id_set(pack: dict) -> set[tuple[str, str]]:
    allowed: set[tuple[str, str]] = set()
    catalog_ids = pack.get("catalog_ids") or {}
    for dimension, ids in catalog_ids.items():
        for identifier in ids:
            allowed.add((dimension, identifier))
    for item in pack.get("detections") or []:
        allowed.add((item["dimension"], item["id"]))
    for cue in pack.get("cues") or []:
        for row in cue.get("candidate_profiles") or []:
            allowed.add((row["dimension"], row["id"]))
    return allowed


def validate_judgment(judgment: dict, pack: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(judgment, dict):
        return ["judgment must be an object"]
    if judgment.get("version") != 1:
        errors.append("judgment.version must be 1")
    if not isinstance(judgment.get("notes_for_user"), str):
        errors.append("judgment.notes_for_user must be a string")
    decisions = judgment.get("decisions")
    if not isinstance(decisions, list):
        errors.append("judgment.decisions must be an array")
        return errors
    allowed = _catalog_id_set(pack)
    seen: set[tuple[str, str]] = set()
    for index, decision in enumerate(decisions):
        label = f"decisions[{index}]"
        if not isinstance(decision, dict):
            errors.append(f"{label}: must be an object")
            continue
        dimension = decision.get("dimension")
        identifier = decision.get("id")
        action = decision.get("action")
        confidence = decision.get("confidence")
        reason = decision.get("reason")
        grounded = decision.get("grounded_cues", [])
        if dimension not in DIMENSIONS:
            errors.append(f"{label}: unknown dimension")
        if not isinstance(identifier, str) or not identifier:
            errors.append(f"{label}: id required")
        if action not in ACTIONS:
            errors.append(f"{label}: invalid action")
        if confidence not in CONFIDENCES:
            errors.append(f"{label}: invalid confidence")
        if not isinstance(reason, str) or not reason.strip():
            errors.append(f"{label}: reason required")
        if grounded is not None and not isinstance(grounded, list):
            errors.append(f"{label}: grounded_cues must be an array")
        key = (dimension, identifier)
        if key in seen:
            errors.append(f"{label}: duplicate decision for {dimension}:{identifier}")
        seen.add(key)
        if dimension in DIMENSIONS and isinstance(identifier, str) and key not in allowed:
            errors.append(f"{label}: id not in pack catalog_ids or candidate_profiles")
        if action == "propose" and key not in allowed:
            errors.append(f"{label}: propose target must appear in pack candidates")
    return errors


def apply_judgment(detections: list[dict], judgment: dict, pack: dict | None = None) -> dict:
    """Return ranked recommendations. Fail-open: invalid judgment leaves detections unchanged."""
    pack = pack or {
        "catalog_ids": {},
        "detections": detections,
        "cues": [],
    }
    errors = validate_judgment(judgment, pack)
    if errors:
        return {
            "ok": False,
            "errors": errors,
            "recommended": [
                item for item in detections if item.get("confidence") == "confirmed"
            ],
            "also_possible": [
                item for item in detections if item.get("confidence") == "candidate"
            ],
            "dismissed": [],
            "detections": detections,
            "notes_for_user": "",
        }

    by_key = {
        (item["dimension"], item["id"]): dict(item)
        for item in detections
    }
    recommended_keys: list[tuple[str, str]] = []
    also_keys: list[tuple[str, str]] = []
    dismissed_keys: list[tuple[str, str]] = []
    decided: set[tuple[str, str]] = set()

    for decision in judgment.get("decisions", []):
        key = (decision["dimension"], decision["id"])
        decided.add(key)
        row = by_key.get(key)
        if row is None:
            row = {
                "dimension": decision["dimension"],
                "id": decision["id"],
                "confidence": decision.get("confidence", "candidate"),
                "evidence": [],
                "match_strength": "weak",
                "cues": list(decision.get("grounded_cues") or []),
                "ambiguous_with": [],
            }
            by_key[key] = row
        row = dict(row)
        row["gate_action"] = decision["action"]
        row["gate_reason"] = decision.get("reason", "")
        if decision.get("confidence") in CONFIDENCES:
            row["confidence"] = (
                "candidate"
                if decision["confidence"] == "suppressed"
                else decision["confidence"]
            )
        by_key[key] = row
        action = decision["action"]
        if action in {"promote", "propose"}:
            recommended_keys.append(key)
        elif action == "keep":
            if row.get("confidence") == "confirmed" or row.get("match_strength") == "strong":
                recommended_keys.append(key)
            else:
                also_keys.append(key)
        elif action == "demote":
            also_keys.append(key)
        elif action == "drop":
            dismissed_keys.append(key)

    for key, row in by_key.items():
        if key in decided:
            continue
        if row.get("confidence") == "confirmed":
            recommended_keys.append(key)
        else:
            also_keys.append(key)

    def materialize(keys: list[tuple[str, str]]) -> list[dict]:
        rows = []
        seen = set()
        for index, key in enumerate(keys):
            if key in seen or key not in by_key:
                continue
            seen.add(key)
            row = dict(by_key[key])
            row["prefer_rank"] = index + 1
            rows.append(row)
        return rows

    return {
        "ok": True,
        "errors": [],
        "recommended": materialize(recommended_keys),
        "also_possible": materialize(also_keys),
        "dismissed": materialize(dismissed_keys),
        "detections": [by_key[key] for key in sorted(by_key)],
        "notes_for_user": judgment.get("notes_for_user", ""),
    }


def load_schema() -> dict:
    return json.loads(GATE_SCHEMA_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit("discovery_gate is a library module")
