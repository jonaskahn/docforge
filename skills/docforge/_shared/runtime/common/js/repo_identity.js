"use strict";
/**
 * Repository web identity: the one declared place a forge URL may come from.
 *
 * Reader-facing documentation names a source in readable prose, but a reader who
 * must open the file needs a link that works. A repo-relative link cannot: it
 * 404s in a generated static site, and the line anchor it would need does not
 * survive a rename. So a source link is an absolute permalink built from a
 * **declared** base and a **pinned** commit.
 *
 * That is a deliberate, bounded exception to host neutrality, which exists to
 * confine forge-specific knowledge to a small number of declared locations
 * rather than to forbid forge features. The base lives in `project.repository`
 * in the manifest and nowhere else, so migrating forges is a re-run, never a
 * hand edit across every document.
 *
 * Not a public CLI.
 */

const { execFileSync } = require("child_process");

// Line-anchor syntax genuinely differs per forge and cannot be guessed from a
// URL, which is why the flavor is declared rather than inferred for a
// self-hosted host. `{start}`/`{end}` are omitted when a mention names no range.
const BLOB_TEMPLATES = {
  github: "{web_base}/blob/{commit}/{path}#L{start}-L{end}",
  gitlab: "{web_base}/-/blob/{commit}/{path}#L{start}-{end}",
  gitea: "{web_base}/src/commit/{commit}/{path}#L{start}-L{end}",
  bitbucket: "{web_base}/src/{commit}/{path}#lines-{start}:{end}",
  generic: "{web_base}/blob/{commit}/{path}",
};
// Only hosts whose flavor is unambiguous. A self-hosted domain is never guessed:
// a wrong guess produces a link that resolves to the right file with the wrong
// lines highlighted, which is worse than asking once.
const KNOWN_HOSTS = {
  "github.com": "github",
  "gitlab.com": "gitlab",
  "bitbucket.org": "bitbucket",
  "codeberg.org": "gitea",
};
const COMMIT_RE = /^[0-9a-f]{40}$/;
const FORGE_FLAVORS = Object.keys(BLOB_TEMPLATES);

function git(repo, args) {
  try {
    return execFileSync("git", ["-C", repo, ...args], {
      encoding: "utf8",
      timeout: 10000,
      stdio: ["ignore", "pipe", "ignore"],
    }).trim();
  } catch {
    return "";
  }
}

/**
 * The `origin` remote as an https URL, or null.
 *
 * Normalizes the SSH form (`git@host:org/repo.git`) so a declared base is
 * browsable regardless of how the working copy was cloned.
 */
function gitRemoteUrl(repo) {
  let value = git(repo, ["config", "--get", "remote.origin.url"]);
  if (!value) return null;
  value = value.replace(/\.git$/, "");
  if (value.startsWith("git@")) {
    value = value.replace(":", "/").replace("git@", "https://");
  }
  return value.startsWith("http://") || value.startsWith("https://") ? value : null;
}

/** The commit a document's links should pin to. */
function headCommit(repo) {
  const value = git(repo, ["rev-parse", "HEAD"]);
  return COMMIT_RE.test(value) ? value : null;
}

function hostOf(url) {
  const remainder = url.includes("://") ? url.split("://")[1] : url;
  return remainder.split("/")[0].toLowerCase();
}

/**
 * The forge flavor when the host makes it unambiguous, else null.
 *
 * Null means "ask the user once"; it never means "assume github".
 */
function detectFlavor(webBase) {
  return KNOWN_HOSTS[hostOf(webBase)] || null;
}

/**
 * Everything detectable about a repository's web identity.
 *
 * `forge` is null when the host is self-hosted, which is the signal to ask.
 */
function detect(repo) {
  const webBase = gitRemoteUrl(repo);
  if (webBase === null) return null;
  const flavor = detectFlavor(webBase);
  return {
    web_base: webBase,
    forge: flavor,
    blob_template: flavor ? BLOB_TEMPLATES[flavor] : null,
  };
}

/**
 * Validate a declared identity and fill in its template.
 *
 * Throws with a reader-facing message, so a bad declaration fails at
 * declaration time rather than producing links that 404 later.
 */
function normalize(record) {
  const webBase = String((record && record.web_base) || "").replace(/\/+$/, "");
  if (!(webBase.startsWith("http://") || webBase.startsWith("https://"))) {
    throw new Error("repository.web_base must be an http(s) URL");
  }
  const forge = (record && record.forge) || "generic";
  if (!(forge in BLOB_TEMPLATES)) {
    throw new Error(`repository.forge must be one of: ${FORGE_FLAVORS.slice().sort().join(", ")}`);
  }
  const template = (record && record.blob_template) || BLOB_TEMPLATES[forge];
  if (!template.includes("{web_base}") || !template.includes("{path}")) {
    throw new Error("repository.blob_template must contain {web_base} and {path}");
  }
  const normalized = { web_base: webBase, forge, blob_template: template };
  for (const optional of ["declared_by", "declared_at"]) {
    if (record && record[optional]) normalized[optional] = record[optional];
  }
  return normalized;
}

/**
 * An absolute permalink to `path` at `commit`.
 *
 * Omits the line fragment when no range is given -- a module-orientation
 * mention wants the file, not a line that a refactor will move.
 */
function blobUrl(identity, commit, filePath, start = null, end = null) {
  let template = identity.blob_template;
  if (start === null || start === undefined) template = template.split("#")[0];
  return template
    .replace("{web_base}", identity.web_base.replace(/\/+$/, ""))
    .replace("{commit}", commit)
    .replace("{path}", String(filePath).replace(/^\/+/, ""))
    .replace("{start}", String(start))
    .replace("{end}", String(end === null || end === undefined ? start : end));
}

/**
 * The declared identity from a manifest, or null when undeclared.
 *
 * Undeclared is a supported state: documentation that never needs to send a
 * reader into source stays link-free, and every existing manifest predates this
 * field.
 */
function identityOf(manifest) {
  const record = ((manifest || {}).project || {}).repository;
  if (!record || typeof record !== "object" || !record.web_base) return null;
  try {
    return normalize(record);
  } catch {
    return null;
  }
}

module.exports = {
  BLOB_TEMPLATES,
  FORGE_FLAVORS,
  KNOWN_HOSTS,
  blobUrl,
  detect,
  detectFlavor,
  gitRemoteUrl,
  headCommit,
  identityOf,
  normalize,
};

if (require.main === module) {
  process.stderr.write("error: repo_identity.js is a shared module, not a CLI\n");
  process.exit(2);
}
