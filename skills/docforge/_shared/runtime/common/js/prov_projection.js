"use strict";
/** Deterministically project provenance 2.0 into Docforge's core PROV relations. */

function projectCore(provenance) {
  const document = `doc:${provenance.doc_id}@${provenance.content_hash || provenance.generated_at}`;
  const activity = `generation:${provenance.doc_id}@${provenance.generated_at}`;
  const agent = `agent:${provenance.generator.name}@${provenance.generator.version}`;
  const sources = new Map(); const roles = new Map();
  for (const section of provenance.sections || []) for (const source of section.sources || []) {
    const key = `${source.path}\0${source.git_blob}`;
    if (roles.has(key) && roles.get(key) !== source.role) throw new Error(`conflicting source roles for ${source.path}@${source.git_blob}`);
    roles.set(key, source.role); sources.set(key, `source:${source.path}@${source.git_blob}`);
  }
  const relations = [
    { relation: "wasGeneratedBy", subject: document, object: activity },
    { relation: "wasAttributedTo", subject: document, object: agent },
    { relation: "wasAssociatedWith", subject: activity, object: agent },
  ];
  for (const key of [...sources.keys()].sort()) {
    const source = sources.get(key);
    relations.push({ relation: "used", subject: activity, object: source });
    relations.push({ relation: "wasDerivedFrom", subject: document, object: source });
  }
  return relations;
}
module.exports = { projectCore };
