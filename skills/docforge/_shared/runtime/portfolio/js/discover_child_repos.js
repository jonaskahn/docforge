#!/usr/bin/env node
"use strict";
/** Discover child repos and resolve cross-member dependency edges. */

const fs = require("fs");
const path = require("path");
const manifestDeps = require("../../common/js/manifest_deps.js");
const detectProfiles = require("../../catalog/js/detect_profiles.js");

const DEFAULT_EXCLUDES = new Set([".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"]);
const IGNORED_WALK = new Set([
  ...DEFAULT_EXCLUDES,
  ".codegraph",
  ".gitnexus",
  ".docforge",
  ".build",
  "DerivedData",
]);

function isDir(p) {
  try {
    return fs.statSync(p).isDirectory();
  } catch {
    return false;
  }
}

function exists(p) {
  return fs.existsSync(p);
}

function parseGitmodules(root) {
  const gmPath = path.join(root, ".gitmodules");
  if (!exists(gmPath)) return {};
  const text = fs.readFileSync(gmPath, "utf8");
  const declared = {};
  let currentName = null;
  let currentPath = null;
  let currentUrl = null;

  function flush() {
    if (currentPath) {
      declared[path.posix.normalize(currentPath)] = { name: currentName, url: currentUrl };
    }
  }

  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#") || line.startsWith(";")) continue;
    const sectionMatch = line.match(/^\[submodule\s+"([^"]*)"\]$/);
    if (sectionMatch) {
      flush();
      currentName = sectionMatch[1];
      currentPath = null;
      currentUrl = null;
      continue;
    }
    const kv = line.match(/^(\w+)\s*=\s*(.*)$/);
    if (kv && currentName !== null) {
      const [, key, value] = kv;
      if (key === "path") currentPath = value.trim();
      else if (key === "url") currentUrl = value.trim();
    }
  }
  flush();
  return declared;
}

function hasOwnGit(p) {
  const marker = path.join(p, ".git");
  try {
    const stat = fs.statSync(marker);
    return stat.isDirectory() || stat.isFile();
  } catch {
    return false;
  }
}

function findNestedRepos(root, excludes) {
  const found = [];
  function walk(dir) {
    let entries;
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
      return;
    }
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      if (excludes.has(entry.name)) continue;
      const full = path.join(dir, entry.name);
      if (hasOwnGit(full)) found.push(full);
      walk(full);
    }
  }
  walk(root);
  return found;
}

function readManifestTier(repoPath) {
  const target = path.join(repoPath, ".docforge", "manifest.json");
  if (!exists(target)) return null;
  try {
    const data = JSON.parse(fs.readFileSync(target, "utf8"));
    return (data.project && data.project.tier) || null;
  } catch {
    return null;
  }
}

function docforgeStatus(repoPath, tier) {
  const arch = path.join(repoPath, "docs", "architecture");
  const hasOverview = exists(path.join(arch, "high-level.md")) || exists(path.join(arch, "overview.md"));
  const hasManifest = exists(path.join(repoPath, ".docforge", "manifest.json"));
  if (hasManifest) return tier ? `docforge baseline + provenance (tier: ${tier})` : "docforge baseline + provenance";
  if (hasOverview) return "docforge baseline present (no provenance manifest yet)";
  return "none — needs generation";
}

function inventoryManifests(repo) {
  const found = [];
  function walk(dir) {
    let entries;
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
      return;
    }
    for (const entry of entries.sort((a, b) => a.name.localeCompare(b.name))) {
      if (IGNORED_WALK.has(entry.name)) continue;
      const full = path.join(dir, entry.name);
      if (entry.isSymbolicLink()) continue;
      if (entry.isDirectory()) walk(full);
      else if (entry.isFile()) {
        found.push([path.relative(repo, full).split(path.sep).join("/"), full]);
      }
    }
  }
  if (isDir(repo)) walk(repo);
  return found;
}

function loadRepoIdentity(root) {
  const target = path.join(root, ".metadata", "portfolio", "repo-identity.json");
  if (!exists(target)) return new Map();
  let data;
  try {
    data = JSON.parse(fs.readFileSync(target, "utf8"));
  } catch {
    return new Map();
  }
  const mapping = new Map();
  for (const row of data.packages || []) {
    if (!row.ecosystem || !row.name) continue;
    const key = `${row.ecosystem}:${manifestDeps.normalize(row.ecosystem, row.name)}`;
    mapping.set(key, row);
  }
  return mapping;
}

function resolveDependencyEdges(root, members) {
  const identityMap = loadRepoIdentity(root);
  const memberDirs = members
    .filter((item) => item.membership !== "parent" && isDir(item.path))
    .map((item) => [item, item.path]);

  const perMember = [];
  const identityOwners = new Map();
  for (const [, memberPath] of memberDirs) {
    const files = inventoryManifests(memberPath);
    const identities = manifestDeps.extractPackageIdentities(files);
    const dependencies = manifestDeps.extractDependencies(files);
    const repoId = path.basename(memberPath);
    for (const [ecosystem, names] of Object.entries(identities)) {
      for (const name of Object.keys(names)) {
        const key = `${ecosystem}:${name}`;
        if (!identityOwners.has(key)) identityOwners.set(key, repoId);
      }
    }
    perMember.push({ repoId, path: memberPath, identities, dependencies });
  }
  for (const [key, row] of identityMap.entries()) {
    identityOwners.set(key, row.repo_id);
  }

  const edges = [];
  const seen = new Set();
  for (const member of perMember) {
    for (const [ecosystem, deps] of Object.entries(member.dependencies)) {
      for (const depName of Object.keys(deps)) {
        const key = `${ecosystem}:${depName}`;
        const target = identityOwners.get(key);
        if (!target || target === member.repoId) continue;
        const resolution = identityMap.has(key) ? "mapping" : "heuristic";
        let coupling = "shared library";
        if (identityMap.has(key) && identityMap.get(key).coupling_default) {
          coupling = identityMap.get(key).coupling_default;
        }
        const edgeKey = `${member.repoId}|${target}|${coupling}`;
        if (seen.has(edgeKey)) continue;
        seen.add(edgeKey);
        edges.push({
          repo: member.repoId,
          depends_on: target,
          coupling_type: coupling,
          resolution,
          ecosystem,
          package: depName,
        });
      }
    }
  }
  edges.sort((a, b) =>
    `${a.repo}:${a.depends_on}:${a.package}`.localeCompare(`${b.repo}:${b.depends_on}:${b.package}`),
  );
  return edges;
}

function loadFlowSignatures(repoPath) {
  const target = path.join(repoPath, ".docforge", "flow-index.json");
  if (!exists(target)) return [];
  let data;
  try {
    data = JSON.parse(fs.readFileSync(target, "utf8"));
  } catch {
    return [];
  }
  const signatures = [];
  for (const flow of data.flows || []) {
    const entryRef = flow.entry_ref || {};
    if (entryRef.kind && entryRef.signature) {
      signatures.push({ kind: entryRef.kind, signature: entryRef.signature });
    }
  }
  return signatures;
}

function loadFlowEvidenceText(repoPath) {
  const target = path.join(repoPath, ".docforge", "flow-index.json");
  if (!exists(target)) return "";
  try {
    const data = JSON.parse(fs.readFileSync(target, "utf8"));
    return JSON.stringify(data.flows || []);
  } catch {
    return "";
  }
}

function loadRepoIdentityFlows(root) {
  const target = path.join(root, ".metadata", "portfolio", "repo-identity.json");
  if (!exists(target)) return [];
  let data;
  try {
    data = JSON.parse(fs.readFileSync(target, "utf8"));
  } catch {
    return [];
  }
  const edges = [];
  for (const row of data.flows || []) {
    let repoId = row.repo_id;
    let counterpart = row.counterpart_repo_id;
    const channel = row.channel || {};
    const signature = channel.signature;
    if (!(repoId && counterpart && signature)) continue;
    if (row.role === "consumer") {
      [repoId, counterpart] = [counterpart, repoId];
    }
    edges.push({ repo: repoId, counterpart, channel });
  }
  return edges;
}

function resolveFlowEdges(root, members) {
  const memberDirs = members
    .filter((item) => item.membership !== "parent" && isDir(item.path))
    .map((item) => item.path);

  const signaturesByRepo = new Map();
  const evidenceByRepo = new Map();
  for (const memberPath of memberDirs) {
    const repoId = path.basename(memberPath);
    signaturesByRepo.set(repoId, loadFlowSignatures(memberPath));
    evidenceByRepo.set(repoId, loadFlowEvidenceText(memberPath));
  }

  const edges = [];
  const seen = new Set();

  for (const row of loadRepoIdentityFlows(root)) {
    const { repo: repoId, counterpart, channel } = row;
    const signature = channel.signature;
    const key = `${repoId}|${counterpart}|${signature}`;
    if (seen.has(key)) continue;
    seen.add(key);
    edges.push({
      repo: repoId,
      counterpart,
      channel_kind: channel.kind,
      signature,
      resolution: "mapping",
    });
  }

  for (const [ownerId, signatures] of signaturesByRepo.entries()) {
    for (const sig of signatures) {
      const signature = sig.signature;
      for (const [callerId, evidenceText] of evidenceByRepo.entries()) {
        if (callerId === ownerId) continue;
        if (signature && evidenceText.includes(signature)) {
          const key = `${callerId}|${ownerId}|${signature}`;
          if (seen.has(key)) continue;
          seen.add(key);
          edges.push({
            repo: callerId,
            counterpart: ownerId,
            channel_kind: sig.kind,
            signature,
            resolution: "heuristic",
          });
        }
      }
    }
  }

  edges.sort((a, b) =>
    `${a.repo}:${a.counterpart}:${a.signature}`.localeCompare(`${b.repo}:${b.counterpart}:${b.signature}`),
  );
  return edges;
}

function parseArgs(argv) {
  const args = { exclude: [], json: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--root") args.root = argv[++i];
    else if (a === "--exclude") args.exclude.push(argv[++i]);
    else if (a === "--json") args.json = true;
  }
  return args;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.root) {
    console.error("usage: discover_child_repos.js --root <path> [--exclude <name>]... [--json]");
    return 2;
  }
  let root = path.resolve(args.root);
  try {
    root = fs.realpathSync(root);
  } catch {
    // Fall through with the unresolved absolute path; the isDir check below reports it.
  }
  if (!isDir(root)) {
    console.error(`Not a directory: ${root}`);
    return 2;
  }
  const excludes = new Set([...DEFAULT_EXCLUDES, ...args.exclude]);
  const declared = parseGitmodules(root);
  const nested = findNestedRepos(root, excludes);
  const declaredPaths = new Set(Object.keys(declared).map((p) => path.join(root, p)));
  const detected = nested.filter((p) => !declaredPaths.has(p));

  const rootTier = readManifestTier(root);
  const collection = [
    { path: root, membership: "parent", status: docforgeStatus(root, rootTier), tier: rootTier },
  ];
  for (const [relPath, meta] of Object.entries(declared)) {
    const full = path.join(root, relPath);
    let tier = null;
    let status = "not checked out locally";
    if (exists(full)) {
      tier = readManifestTier(full);
      status = docforgeStatus(full, tier);
    }
    collection.push({
      path: full,
      membership: "declared (submodule)",
      submodule_name: meta.name,
      submodule_url: meta.url,
      status,
      tier,
    });
  }
  for (const full of detected) {
    const tier = readManifestTier(full);
    collection.push({
      path: full,
      membership: "detected — NOT in .gitmodules",
      status: docforgeStatus(full, tier),
      tier,
    });
  }

  const needsGeneration = collection.filter((c) => c.status.startsWith("none"));
  const dependencyEdges = resolveDependencyEdges(root, collection);
  const flowEdges = resolveFlowEdges(root, collection);
  const rootProfileEvidence = detectProfiles.detect(root);

  if (args.json) {
    console.log(
      JSON.stringify(
        {
          root,
          collection,
          needs_generation: needsGeneration.map((c) => c.path),
          dependency_edges: dependencyEdges,
          flow_edges: flowEdges,
          root_profile_evidence: rootProfileEvidence,
        },
        null,
        2,
      ),
    );
    return 0;
  }

  console.log(`Repo collection under ${root}\n`);
  if (rootProfileEvidence.length === 0) {
    console.log("Root profile evidence: none — this repository has no source of its own to graph.\n");
  }
  for (const c of collection) {
    const flag = c.status.startsWith("none") ? "  <-- needs docforge generation before diligence" : "";
    console.log(`[${c.membership}] ${c.path}\n    status: ${c.status}${flag}\n`);
  }
  if (collection.some((c) => c.membership.startsWith("detected"))) {
    console.log("NOTE: one or more detected child repos are not declared in .gitmodules.");
    console.log("      Confirm with the repo owner whether each is in scope before proceeding.\n");
  }
  if (needsGeneration.length) {
    console.log(`${needsGeneration.length} repo(s) need a docforge baseline before the portfolio layer is built:`);
    for (const c of needsGeneration) console.log(`  - ${c.path}`);
  }
  if (dependencyEdges.length) {
    console.log(`\n${dependencyEdges.length} dependency edge(s):`);
    for (const edge of dependencyEdges) {
      console.log(
        `  - ${edge.repo} → ${edge.depends_on} (${edge.coupling_type}, ${edge.resolution})`,
      );
    }
  }
  if (flowEdges.length) {
    console.log(`\n${flowEdges.length} flow edge(s):`);
    for (const edge of flowEdges) {
      console.log(
        `  - ${edge.repo} → ${edge.counterpart} (${edge.channel_kind}: ${edge.signature}, ${edge.resolution})`,
      );
    }
  }
  return 0;
}

process.exit(main());
