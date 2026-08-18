#!/usr/bin/env python3
"""Repository web identity: the one declared place a forge URL may come from.

Reader-facing documentation names a source in readable prose, but a reader who
must open the file needs a link that works. A repo-relative link cannot: it
404s in a generated static site, and the line anchor it would need does not
survive a rename. So a source link is an absolute permalink built from a
**declared** base and a **pinned** commit.

That is a deliberate, bounded exception to host neutrality, which exists to
confine forge-specific knowledge to a small number of declared locations rather
than to forbid forge features. The base lives in `project.repository` in the
manifest and nowhere else, so migrating forges is a re-run, never a hand edit
across every document.

Not a public CLI.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

# Line-anchor syntax genuinely differs per forge and cannot be guessed from a
# URL, which is why the flavor is declared rather than inferred for a
# self-hosted host. `{start}`/`{end}` are omitted when a mention names no range.
BLOB_TEMPLATES = {
    "github": "{web_base}/blob/{commit}/{path}#L{start}-L{end}",
    "gitlab": "{web_base}/-/blob/{commit}/{path}#L{start}-{end}",
    "gitea": "{web_base}/src/commit/{commit}/{path}#L{start}-L{end}",
    "bitbucket": "{web_base}/src/{commit}/{path}#lines-{start}:{end}",
    "generic": "{web_base}/blob/{commit}/{path}",
}
# Only hosts whose flavor is unambiguous. A self-hosted domain is never guessed:
# a wrong guess produces a link that resolves to the right file with the wrong
# lines highlighted, which is worse than asking once.
KNOWN_HOSTS = {
    "github.com": "github",
    "gitlab.com": "gitlab",
    "bitbucket.org": "bitbucket",
    "codeberg.org": "gitea",
}
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
FORGE_FLAVORS = tuple(BLOB_TEMPLATES)


def git_remote_url(repo: Path) -> str | None:
    """The `origin` remote as an https URL, or None.

    Normalizes the SSH form (`git@host:org/repo.git`) so a declared base is
    browsable regardless of how the working copy was cloned."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "config", "--get", "remote.origin.url"],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = result.stdout.strip() if result.returncode == 0 else ""
    if not value:
        return None
    value = value.removesuffix(".git")
    if value.startswith("git@"):
        value = value.replace(":", "/", 1).replace("git@", "https://", 1)
    if value.startswith(("http://", "https://")):
        return value
    return None


def head_commit(repo: Path) -> str | None:
    """The commit a document's links should pin to."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = result.stdout.strip() if result.returncode == 0 else ""
    return value if COMMIT_RE.match(value) else None


def host_of(url: str) -> str:
    remainder = url.split("://", 1)[-1]
    return remainder.split("/", 1)[0].lower()


def detect_flavor(web_base: str) -> str | None:
    """The forge flavor when the host makes it unambiguous, else None.

    None means "ask the user once"; it never means "assume github"."""
    return KNOWN_HOSTS.get(host_of(web_base))


def detect(repo: Path) -> dict | None:
    """Everything detectable about a repository's web identity.

    `forge` is None when the host is self-hosted, which is the signal to ask.
    """
    web_base = git_remote_url(repo)
    if web_base is None:
        return None
    flavor = detect_flavor(web_base)
    return {
        "web_base": web_base,
        "forge": flavor,
        "blob_template": BLOB_TEMPLATES[flavor] if flavor else None,
    }


def normalize(record: dict) -> dict:
    """Validate a declared identity and fill in its template.

    Raises ValueError with a reader-facing message, so a bad declaration fails
    at declaration time rather than producing links that 404 later."""
    web_base = str(record.get("web_base") or "").rstrip("/")
    if not web_base.startswith(("http://", "https://")):
        raise ValueError("repository.web_base must be an http(s) URL")
    forge = record.get("forge") or "generic"
    if forge not in BLOB_TEMPLATES:
        raise ValueError(
            f"repository.forge must be one of: {', '.join(sorted(BLOB_TEMPLATES))}"
        )
    template = record.get("blob_template") or BLOB_TEMPLATES[forge]
    if "{web_base}" not in template or "{path}" not in template:
        raise ValueError("repository.blob_template must contain {web_base} and {path}")
    normalized = {"web_base": web_base, "forge": forge, "blob_template": template}
    for optional in ("declared_by", "declared_at"):
        if record.get(optional):
            normalized[optional] = record[optional]
    return normalized


def blob_url(
    identity: dict,
    commit: str,
    path: str,
    start: int | None = None,
    end: int | None = None,
) -> str:
    """An absolute permalink to `path` at `commit`.

    Omits the line fragment when no range is given -- a module-orientation
    mention wants the file, not a line that a refactor will move."""
    template = identity["blob_template"]
    if start is None:
        template = template.split("#", 1)[0]
    return (
        template
        .replace("{web_base}", identity["web_base"].rstrip("/"))
        .replace("{commit}", commit)
        .replace("{path}", path.lstrip("/"))
        .replace("{start}", str(start))
        .replace("{end}", str(end if end is not None else start))
    )


def identity_of(manifest: dict) -> dict | None:
    """The declared identity from a manifest, or None when undeclared.

    Undeclared is a supported state: documentation that never needs to send a
    reader into source stays link-free, and every existing manifest predates
    this field."""
    record = (manifest.get("project") or {}).get("repository")
    if not isinstance(record, dict) or not record.get("web_base"):
        return None
    try:
        return normalize(record)
    except ValueError:
        return None


if __name__ == "__main__":
    raise SystemExit("repo_identity.py is a shared module, not a CLI")
