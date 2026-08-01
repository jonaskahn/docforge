"""Deterministically project provenance 2.0 into Docforge's core PROV relations."""

from __future__ import annotations


def project_core(provenance: dict) -> list[dict]:
    document = f"doc:{provenance['doc_id']}@{provenance.get('content_hash') or provenance['generated_at']}"
    activity = f"generation:{provenance['doc_id']}@{provenance['generated_at']}"
    generator = provenance["generator"]
    agent = f"agent:{generator['name']}@{generator['version']}"
    sources: dict[tuple[str, str], str] = {}
    roles: dict[tuple[str, str], str] = {}
    for section in provenance.get("sections", []):
        for source in section.get("sources", []):
            key = (source["path"], source["git_blob"])
            if key in roles and roles[key] != source.get("role"):
                raise ValueError(f"conflicting source roles for {key[0]}@{key[1]}")
            roles[key] = source.get("role")
            sources[key] = f"source:{key[0]}@{key[1]}"
    relations = [
        {"relation": "wasGeneratedBy", "subject": document, "object": activity},
        {"relation": "wasAttributedTo", "subject": document, "object": agent},
        {"relation": "wasAssociatedWith", "subject": activity, "object": agent},
    ]
    for key in sorted(sources):
        source = sources[key]
        relations.extend([
            {"relation": "used", "subject": activity, "object": source},
            {"relation": "wasDerivedFrom", "subject": document, "object": source},
        ])
    return relations
