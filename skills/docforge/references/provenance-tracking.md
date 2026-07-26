# Provenance tracking — git-hash metadata for update decisions

Every document this skill produces carries enough metadata to answer one question cheaply, without re-reading the code: **has anything this document depends on changed since it was written?**

## The unit is a flow or section, not a whole file

Docs rarely map one-to-one to a single source file — `process-flows.md`'s "Order approval" entry might depend on four files across three modules, while "Refund eligibility" a few headings down depends on one different file entirely. Track provenance at the granularity of **the section a heading covers**, with its file list underneath. This is what lets an update touch only the section that actually changed instead of the whole document.

## Two places metadata lives

### 1. Per-document frontmatter

Every generated `.md` file gets a YAML block at the top:

```yaml
---
docforge_provenance:
  doc: docs/product/business-analyst/business-rules.md
  generated_at: 2026-07-26T09:40:00Z
  graph_snapshot: .ua/knowledge-graph.json@a3f9c21   # the graph's own version marker, if it exposes one; omit otherwise
  sections:
    - id: order-approval-threshold
      sources:
        - path: src/orders/approval.py
          git_blob: 8f3a1c2b9e4d7061a5c3e0f2b9d4a1c7e6f8b302
        - path: src/config/thresholds.py
          git_blob: b91e4470d1c2a8f3e5b7091d4a6c2f8e0b1d3a56
    - id: refund-eligibility
      sources:
        - path: src/orders/refunds.py
          git_blob: 4c7d0a112f3b6e9d8c5a2f1e0b7d4c9a6e3f8102
---
```

`git_blob` is the output of `git hash-object <path>` at generation time — the content hash of the working-tree file, independent of commit history. Use `git hash-object`, **not** `git rev-parse HEAD:<path>`: the latter reflects only the last commit and misses uncommitted edits, which is exactly the situation where a doc is most likely to already be stale.

`id` for each section must match a real heading anchor in the document (`### Rule: <name>` → slug `order-approval-threshold`), so an update can locate and replace precisely that section.

### 2. The repo-level manifest

`.docforge/manifest.json` aggregates every document's frontmatter into one file, so a full staleness sweep doesn't require opening every document in the tree:

```json
{
  "generated_at": "2026-07-26T09:40:00Z",
  "documents": {
    "docs/product/business-analyst/business-rules.md": {
      "sections": {
        "order-approval-threshold": {
          "sources": {
            "src/orders/approval.py": "8f3a1c2b9e4d7061a5c3e0f2b9d4a1c7e6f8b302",
            "src/config/thresholds.py": "b91e4470d1c2a8f3e5b7091d4a6c2f8e0b1d3a56"
          }
        },
        "refund-eligibility": {
          "sources": { "src/orders/refunds.py": "4c7d0a112f3b6e9d8c5a2f1e0b7d4c9a6e3f8102" }
        }
      }
    }
  }
}
```

Treat per-document frontmatter as the source of truth and the manifest as a derived index — rebuild it with `scripts/check_provenance.py --rebuild-manifest` rather than hand-editing both. Commit `.docforge/manifest.json`; it is small, plain text, and lets a teammate check staleness without re-running any generation.

## The staleness algorithm

For each `(document, section, file)` triple recorded:

1. Compute the file's current hash: `git hash-object <path>`.
2. Path no longer exists → `MISSING`. Never delete the claim silently; the underlying logic likely moved rather than vanished — surface it for human review.
3. Current hash equals recorded hash → `FRESH` for that file.
4. Current hash differs → `STALE` for that file, and therefore for the section that cites it.

Roll up per document: `FRESH` only if every section is `FRESH`. A document with one stale section reports as `PARTIAL — section <id> stale (<file> changed)`, not a blanket "stale," so the rewrite step knows exactly what to touch.

## Partial rewrite

When a section reports `PARTIAL`:

1. Re-run the narrow graph query that produced it originally — e.g. "what changed in `src/orders/approval.py` relevant to the approval-threshold rule."
2. Replace only the content between that section's heading and the next heading of equal or higher level. Everything outside those bounds is untouched.
3. Recompute and re-stamp only that section's `git_blob` hashes.
4. Leave every other section's frontmatter entry exactly as it was.

Whole-document regeneration is warranted only when most sections are stale simultaneously, or the document's own structure changed — a business rule was added or removed, not merely an existing one modified.

## Running the check

```
python scripts/check_provenance.py --manifest .docforge/manifest.json
```

Reports one line per document: `FRESH`; `PARTIAL — <section-id> (<path> changed)`; or `STALE — no section granularity recorded` (this last case is for pre-existing docs adopted into the manifest without frontmatter — see below). Add `--flow <name>` to filter to one business flow, `--json` for machine-readable output in a CI check, `--rebuild-manifest` to regenerate the manifest from every document's frontmatter after a manual edit.

## Adopting provenance on a pre-existing document

A doc written before this skill existed has no frontmatter. Don't retrofit fabricated hashes as if they'd always been there. Instead: read the document, identify which files its claims currently draw from (or should), stamp *current* hashes as the baseline, and mark `adopted: true` in the frontmatter — so a future reviewer knows the baseline was assigned at adoption time, not at original authorship, and doesn't mistake "no changes detected" for "verified accurate since it was first written."

## Anti-patterns

- Hashing a whole directory or module instead of the specific files actually cited — defeats section-level partial rewrite and makes nearly every document "stale" on any nearby, unrelated change.
- Using commit SHAs as the tracked value instead of blob hashes — a file's content can be identical across two different commits (touched then reverted), and a commit-keyed check would falsely flag it stale.
- Skipping the manifest and relying only on scattered per-file frontmatter — fine for checking one document, expensive for auditing a whole tree on a schedule.
- Treating a `MISSING` source as license to delete the corresponding rule or feature entry outright — confirm it moved before removing anything a stakeholder may still rely on.
