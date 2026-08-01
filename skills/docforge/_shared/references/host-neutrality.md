# Host neutrality

Documentation outlives the platform it was written on. Repos migrate between GitHub, GitLab, Gitea, Forgejo, Bitbucket, Azure Repos, SourceHut and bare self-hosted remotes; monorepos get split; companies get acquired and consolidate onto whatever the acquirer runs. Prose that names a forge is prose that will be wrong, and the wrongness is scattered across dozens of files where nobody will find it.

The strategy is not to avoid forge features — they are useful — but to **confine forge-specific knowledge to a small number of declared locations** so migration is a bounded task.

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

Exactly three places may contain forge-specific detail. Everywhere else stays neutral.

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

## Portable content choices

**Diagrams.** Mermaid illustrations follow [`illustration.md`](illustration.md) for complexity budgets, rendering, and fallback rules. Always precede a diagram with one or two sentences stating what it shows.

**Links.** Relative paths (`../architecture/high-level.md`) work when browsing the forge, in most editors, and in generated static sites. Absolute URLs to the current host break on migration and on forks. Never link to a line number in another file; link to the file by path and describe the location in prose — never anchor to a private symbol a rename would break (durability rule R1 in `document-composition.md`).

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
