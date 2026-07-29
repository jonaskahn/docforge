#!/usr/bin/env node
"use strict";
// Structured dependency extraction from project-definition manifests.
// Node peer of manifest_deps.py — identical algorithm so detect_profiles output
// stays byte-identical across runtimes. Built-in modules only.

const fs = require("fs");
const path = require("path");

const MAX_MANIFEST_BYTES = 1024 * 1024;
const ECOSYSTEMS = ["npm", "composer", "pip", "cargo", "go", "gem", "maven", "gradle", "nuget", "pub"];

function compareText(a, b) {
  return Buffer.compare(Buffer.from(a, "utf8"), Buffer.from(b, "utf8"));
}

function normalize(ecosystem, name) {
  let value = name.trim().toLowerCase();
  if (ecosystem === "pip") {
    let collapsed = "";
    let previousDash = false;
    for (const char of value) {
      if (char === "-" || char === "_" || char === ".") {
        if (!previousDash) collapsed += "-";
        previousDash = true;
      } else {
        collapsed += char;
        previousDash = false;
      }
    }
    value = collapsed.replace(/^-+/, "").replace(/-+$/, "");
  }
  return value;
}

function read(target) {
  try {
    if (fs.statSync(target).size > MAX_MANIFEST_BYTES) return null;
    return fs.readFileSync(target, "utf8");
  } catch (error) {
    return null;
  }
}

function jsonKeys(text, sections) {
  const names = [];
  let data;
  try {
    data = JSON.parse(text);
  } catch (error) {
    return names;
  }
  if (typeof data !== "object" || data === null || Array.isArray(data)) return names;
  for (const section of sections) {
    const table = data[section];
    if (table && typeof table === "object" && !Array.isArray(table)) {
      for (const key of Object.keys(table)) names.push(String(key));
    }
  }
  return names;
}

function isNameChar(char) {
  return /[A-Za-z0-9]/.test(char) || char === "-" || char === "_" || char === ".";
}

function pep508Name(spec) {
  let token = spec.trim();
  for (const cut of [";", " ", "\t"]) {
    const index = token.indexOf(cut);
    if (index >= 0) token = token.slice(0, index);
  }
  let stop = token.length;
  for (let index = 0; index < token.length; index++) {
    if (!isNameChar(token[index])) {
      stop = index;
      break;
    }
  }
  return token.slice(0, stop);
}

function requirements(text) {
  const names = [];
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.split("#")[0].trim();
    if (!line || line.startsWith("-")) continue;
    const name = pep508Name(line);
    if (name) names.push(name);
  }
  return names;
}

function sectionHeader(line) {
  const stripped = line.trim();
  if (stripped.startsWith("[") && stripped.endsWith("]") && stripped.length > 2) {
    return stripped.slice(1, -1).trim().replace(/^["']|["']$/g, "");
  }
  return null;
}

function quotedTokens(text) {
  const tokens = [];
  let quote = "";
  let current = "";
  for (const char of text) {
    if (quote) {
      if (char === quote) {
        tokens.push(current);
        current = "";
        quote = "";
      } else {
        current += char;
      }
    } else if (char === '"' || char === "'") {
      quote = char;
    }
  }
  return tokens;
}

function pyproject(text) {
  const names = [];
  let section = "";
  let inArray = false;
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.split("#")[0];
    const header = sectionHeader(line);
    if (header !== null) {
      section = header;
      inArray = false;
      continue;
    }
    let stripped = line.trim();
    if (!stripped) continue;
    if (section === "project") {
      const key = stripped.split("=")[0].trim();
      if (inArray || key === "dependencies") {
        if (stripped.includes("=") && key === "dependencies") {
          stripped = stripped.slice(stripped.indexOf("=") + 1);
        }
        inArray = !stripped.includes("]");
        for (const spec of quotedTokens(stripped)) {
          const name = pep508Name(spec);
          if (name) names.push(name);
        }
      }
    } else if (section === "project.optional-dependencies") {
      const body = stripped.includes("=") ? stripped.slice(stripped.indexOf("=") + 1) : stripped;
      for (const spec of quotedTokens(body)) {
        const name = pep508Name(spec);
        if (name) names.push(name);
      }
    } else if (section.startsWith("tool.poetry") && section.endsWith("dependencies")) {
      const key = stripped.split("=")[0].trim().replace(/^["']|["']$/g, "");
      if (key && key.toLowerCase() !== "python") names.push(key);
    }
  }
  return names;
}

function cargo(text) {
  const names = [];
  let section = "";
  const deps = new Set(["dependencies", "dev-dependencies", "build-dependencies"]);
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.split("#")[0];
    const header = sectionHeader(line);
    if (header !== null) {
      section = header;
      const parts = header.split(".");
      for (let index = 0; index < parts.length; index++) {
        if (deps.has(parts[index]) && index + 1 < parts.length) {
          const candidate = parts[index + 1];
          if (candidate && !candidate.startsWith("'") && !candidate.startsWith('"')) names.push(candidate);
          break;
        }
      }
      continue;
    }
    const stripped = line.trim();
    const leaf = section.split(".").pop();
    if (!stripped || !deps.has(leaf)) continue;
    const key = stripped.split("=")[0].split(".")[0].trim().replace(/^["']|["']$/g, "");
    if (key) names.push(key);
  }
  return names;
}

function goMod(text) {
  const names = [];
  let inBlock = false;
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.split("//")[0].trim();
    if (!line) continue;
    if (inBlock) {
      if (line.startsWith(")")) {
        inBlock = false;
        continue;
      }
      names.push(line.split(/\s+/)[0]);
    } else if (line.startsWith("require (")) {
      inBlock = true;
    } else if (line.startsWith("require ")) {
      const parts = line.slice("require ".length).trim().split(/\s+/);
      if (parts.length && parts[0]) names.push(parts[0]);
    }
  }
  return names;
}

function gemfile(text) {
  const names = [];
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.split("#")[0].trim();
    if (!line.startsWith("gem ")) continue;
    const tokens = quotedTokens(line);
    if (tokens.length) names.push(tokens[0]);
  }
  return names;
}

function innerText(block, tag) {
  const openTag = "<" + tag;
  const start = block.indexOf(openTag);
  if (start < 0) return null;
  const gt = block.indexOf(">", start);
  if (gt < 0) return null;
  const end = block.indexOf("</" + tag, gt);
  if (end < 0) return null;
  return block.slice(gt + 1, end).trim();
}

function blocks(text, tag) {
  const found = [];
  const openTag = "<" + tag;
  const closeTag = "</" + tag + ">";
  let search = 0;
  while (true) {
    const start = text.indexOf(openTag, search);
    if (start < 0) break;
    const end = text.indexOf(closeTag, start);
    if (end < 0) break;
    found.push(text.slice(start, end + closeTag.length));
    search = end + closeTag.length;
  }
  return found;
}

function pom(text) {
  const names = [];
  for (const tag of ["dependency", "plugin"]) {
    for (const block of blocks(text, tag)) {
      const group = innerText(block, "groupId");
      const artifact = innerText(block, "artifactId");
      if (group) names.push(group);
      if (group && artifact) names.push(group + ":" + artifact);
    }
  }
  return names;
}

function attr(text, name) {
  const values = [];
  const needle = name + "=";
  let search = 0;
  while (true) {
    const index = text.indexOf(needle, search);
    if (index < 0) break;
    const rest = text.slice(index + needle.length).replace(/^\s+/, "");
    if (rest && (rest[0] === '"' || rest[0] === "'")) {
      const quote = rest[0];
      const end = rest.indexOf(quote, 1);
      if (end > 0) {
        values.push(rest.slice(1, end));
        search = index + needle.length + end + 1;
        continue;
      }
    }
    search = index + needle.length;
  }
  return values;
}

function csproj(text) {
  const names = [];
  for (const value of attr(text, "Sdk")) names.push(value);
  let search = 0;
  while (true) {
    const index = text.indexOf("<PackageReference", search);
    if (index < 0) break;
    const gt = text.indexOf(">", index);
    const segment = text.slice(index, gt > 0 ? gt : text.length);
    for (const value of attr(segment, "Include")) names.push(value);
    search = gt > 0 ? gt + 1 : text.length;
  }
  return names;
}

function gradle(text) {
  const names = [];
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.split("//")[0].trim();
    if (!line) continue;
    const tokens = quotedTokens(line);
    const words = line.replace(/\(/g, " ").replace(/\)/g, " ").split(/\s+/);
    if (words.includes("id") || line.includes("plugin") || line.includes("plugins")) {
      for (const token of tokens) names.push(token);
    }
    for (const token of tokens) {
      if (token.includes(":")) {
        const parts = token.split(":");
        if (parts.length >= 2 && parts[0] && parts[1]) {
          names.push(parts[0] + ":" + parts[1]);
          names.push(parts[0]);
        }
      }
    }
  }
  return names;
}

function pubspec(text) {
  const names = [];
  let inDeps = false;
  for (const raw of text.split(/\r?\n/)) {
    if (!raw.trim() || raw.replace(/^\s+/, "").startsWith("#")) continue;
    const indent = raw.length - raw.replace(/^\s+/, "").length;
    const stripped = raw.trim();
    if (indent === 0) {
      const key = stripped.split(":")[0].trim();
      inDeps = key === "dependencies" || key === "dev_dependencies";
      continue;
    }
    if (inDeps && indent <= 2 && stripped.includes(":")) {
      const key = stripped.split(":")[0].trim();
      if (key) names.push(key);
    }
  }
  return names;
}

function classify(name) {
  const lower = name.toLowerCase();
  if (name === "package.json") return ["npm", "npm"];
  if (name === "composer.json") return ["composer", "composer"];
  if (lower.startsWith("requirements") && lower.endsWith(".txt")) return ["pip", "requirements"];
  if (name === "pyproject.toml") return ["pip", "pyproject"];
  if (name === "Cargo.toml") return ["cargo", "cargo"];
  if (name === "go.mod") return ["go", "go"];
  if (name === "Gemfile") return ["gem", "gem"];
  if (name === "pom.xml") return ["maven", "maven"];
  if (name.endsWith(".gradle") || name.endsWith(".gradle.kts")) return ["gradle", "gradle"];
  if (name.endsWith(".csproj")) return ["nuget", "csproj"];
  if (name === "pubspec.yaml" || name === "pubspec.yml") return ["pub", "pubspec"];
  return null;
}

const PARSERS = {
  npm: (text) => jsonKeys(text, ["dependencies", "devDependencies", "peerDependencies", "optionalDependencies"]),
  composer: (text) => jsonKeys(text, ["require", "require-dev"]),
  requirements,
  pyproject,
  cargo,
  go: goMod,
  gem: gemfile,
  maven: pom,
  csproj,
  gradle,
  pubspec,
};

function extractDependencies(files) {
  const index = {};
  for (const [relative, target] of files) {
    const name = path.posix.basename(relative.split(path.sep).join("/"));
    const classified = classify(name);
    if (classified === null) continue;
    const [ecosystem, parserKey] = classified;
    const text = read(target);
    if (text === null) continue;
    for (const rawName of PARSERS[parserKey](text)) {
      const key = normalize(ecosystem, rawName);
      if (!key) continue;
      if (!index[ecosystem]) index[ecosystem] = {};
      if (!index[ecosystem][key]) index[ecosystem][key] = [];
      if (!index[ecosystem][key].includes(relative)) index[ecosystem][key].push(relative);
    }
  }
  for (const ecosystem of Object.keys(index)) {
    for (const key of Object.keys(index[ecosystem])) {
      index[ecosystem][key] = [...new Set(index[ecosystem][key])].sort(compareText);
    }
  }
  return index;
}

module.exports = { extractDependencies, normalize, ECOSYSTEMS };
