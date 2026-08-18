# Host neutrality

This file owns neutral vocabulary and forge-confinement. Generated prose must
not name a specific forge platform (GitHub, GitLab, Gitea, Forgejo, Bitbucket,
Azure Repos, SourceHut, or a self-hosted remote): documentation outlives the
platform it was written on, and repos migrate, split, or get acquired onto a
different one. The strategy is not to avoid forge features — they are useful
— but to **confine forge-specific knowledge to a small number of declared
locations** so migration is a bounded task.

## Vocabulary

Use the neutral term in all generated prose:

| Do not write | Write |
|---|---|
| GitHub issue, GitLab issue | the issue tracker |
| pull request, merge request | change request (or "pull/merge request" when both audiences read it) |
| GitHub Actions, GitLab CI, Jenkins | the CI pipeline |
| `.github/workflows/ci.yml` | the CI configuration (name the file only in `contributing/`) |
| GitHub Releases | the release process — see `docs/engineering/release.md` |
| CODEOWNERS | ownership — see `docs/contributing/ownership.md` |
| GitHub Security Advisory | the private disclosure channel |
| GitHub Discussions | the discussion forum |
| repo Wiki | `docs/` (do not split documentation across a wiki at all) |

The commands `git`, `git log`, `git blame`, `git tag`, and semantic version tags are safe: they are Git, not a forge.

## The confinement rule

Exactly four places may contain forge-specific detail. Everywhere else stays neutral.

**1. `docs/contributing/README.md`** — one clearly marked section:

```markdown
## Platform specifics
> This project is currently hosted on <platform>. This section is the only
> place in the documentation that depends on that; everything else is neutral.

- Issue tracker: <url>
- Change requests: <workflow, required approvals, merge strategy>
- CI: <where pipeline definitions live, how to read a failed run>
- Ownership rules: mirrored from `ownership.md` into <platform's native file>
```

**2. Forge-native configuration files at their required paths** — `.github/`, `.gitlab/`, `.gitea/`, `.forgejo/`, `Jenkinsfile`, `azure-pipelines.yml`. These are code, not documentation. They must live where the platform expects them, and they should be *generated from* or *point at* the canonical Markdown in `docs/contributing/templates/` rather than being the original.

**3. A single ownership file at the platform's required path** — derived from `docs/contributing/ownership.md`, which stays the human-readable source of truth explaining *why* each area has the owner it has.

**4. `project.repository` in `.docforge/manifest.json`** — the web base, forge flavor, and permalink template every source link is built from. It exists for the same reason as the other three: a reader who must open a file needs a link that works, and a repository-relative link 404s in a generated static site. Confining the host to one declared value keeps migration bounded — re-declare it and re-run, never hand-edit links across every document. Nothing else in the tree may name a forge or hardcode a host, and the generated prose around a link still uses neutral vocabulary.

## Portable content choices

**Diagrams.** Mermaid illustrations follow [`illustration.md`](illustration.md) for complexity budgets, rendering, and fallback rules. Always precede a diagram with one or two sentences stating what it shows.

**Links between documents.** Relative paths (`../architecture/high-level.md`) work when browsing the forge, in most editors, and in generated static sites. A hand-written absolute URL to the current host breaks on migration and on forks, so documentation links stay relative. Link generated documentation for related topics.

**Links into source.** A repository-relative link into source is *not* portable in the way a document link is: it 404s in the rendered site, since only `.md` targets resolve there. So a source link is an absolute permalink built from the declared base in confinement location 4 and pinned to a commit — generated mechanically, never hand-written. Claim evidence still stays in provenance, and a private symbol is still never linked. The form, and when a mention earns a link at all, are owned by [`evidence-presentation.md`](evidence-presentation.md).

**Callouts.** Blockquote-based callouts are the only universally portable form:

```markdown
> **Warning:** this operation is not idempotent; a retry duplicates rows.
```

Platform-specific alert syntaxes (`> [!WARNING]`, `:::danger`, `{% hint %}`) render as literal noise on hosts that do not support them. Use them only if the project has committed to one platform and has said so in the contributing docs.

**Anchors.** Heading-derived anchors differ subtly between renderers. For links that must not break, add an explicit anchor (`<a id="stable-name"></a>`) above the heading.

**Badges.** Status badges are host- and vendor-coupled by nature. Keep them to the root `README.md`, where the cost of fixing them after a migration is one file.

## Auditing for leakage

Before presenting, grep the generated documentation for forge names and platform-specific syntax. The scaffold script does this under `--audit`; the equivalent by hand:

```bash
grep -rniE 'github|gitlab|bitbucket|gitea|forgejo|pull request|merge request' docs/ \
  --include='*.md' | grep -v 'docs/contributing/'
```

Every hit outside `docs/contributing/` is either a rewrite or a deliberate exception that should be justified in the response to the user.
