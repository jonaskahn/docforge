"use strict";
/** Shared evidence hashing: raw git-blob hashes plus normalized and
 * line-range-scoped variants used to classify a cited source as fresh,
 * cosmetically drifted (whitespace/EOL-only, or the cited span is
 * untouched), or genuinely stale. Node built-ins only, no git dependency. */

const crypto = require("crypto");
const { BLOB } = require("./provenance_frontmatter.js");

const RANGE_NUM = /^[1-9][0-9]*$/;

function decodeLines(content) {
  let text;
  try {
    text = content.toString("utf8");
    if (Buffer.compare(Buffer.from(text, "utf8"), content) !== 0) return null;
  } catch {
    return null;
  }
  if (text === "") return [];
  const lines = text.split(/\r\n|\r|\n/);
  const last = text[text.length - 1];
  if (lines.length && lines[lines.length - 1] === "" && (last === "\n" || last === "\r")) {
    lines.pop();
  }
  return lines;
}

function rawBlobHash(content) {
  const header = Buffer.from(`blob ${content.length}\0`, "ascii");
  return crypto.createHash("sha1").update(Buffer.concat([header, content])).digest("hex");
}

function gitBlobForPath(fs, filePath) {
  if (!fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) return null;
  return rawBlobHash(fs.readFileSync(filePath));
}

function normalizeTextBytes(content) {
  const lines = decodeLines(content);
  if (lines === null) return null;
  const trimmed = lines.map((line) => line.replace(/[ \t]+$/, ""));
  while (trimmed.length && trimmed[trimmed.length - 1] === "") trimmed.pop();
  if (!trimmed.length) return Buffer.alloc(0);
  return Buffer.from(`${trimmed.join("\n")}\n`, "utf8");
}

function normalizedBlobHash(content) {
  const normalized = normalizeTextBytes(content);
  return normalized === null ? null : rawBlobHash(normalized);
}

function lineCount(content) {
  const lines = decodeLines(content);
  return lines === null ? null : lines.length;
}

function rangeBlobHash(content, start, end) {
  const lines = decodeLines(content);
  if (lines === null || start < 1 || end < start || end > lines.length) return null;
  return rawBlobHash(Buffer.from(lines.slice(start - 1, end).join("\n"), "utf8"));
}

function validRange(evidenceRange, rangeBlob) {
  if (
    evidenceRange && typeof evidenceRange === "object" && !Array.isArray(evidenceRange)
    && typeof evidenceRange.start === "string" && RANGE_NUM.test(evidenceRange.start)
    && typeof evidenceRange.end === "string" && RANGE_NUM.test(evidenceRange.end)
    && Number(evidenceRange.end) >= Number(evidenceRange.start)
    && typeof rangeBlob === "string" && BLOB.test(rangeBlob)
  ) {
    return [Number(evidenceRange.start), Number(evidenceRange.end)];
  }
  return null;
}

function classifySource(source, currentBytes) {
  if (currentBytes === null || currentBytes === undefined) return "missing";
  if (rawBlobHash(currentBytes) === source.git_blob) return "fresh";
  const span = validRange(source.evidence_range, source.range_blob);
  if (span) {
    const currentRange = rangeBlobHash(currentBytes, span[0], span[1]);
    if (currentRange !== null && currentRange === source.range_blob) return "cosmetic";
  }
  const normalized = source.git_blob_normalized;
  if (typeof normalized === "string" && BLOB.test(normalized)) {
    const currentNormalized = normalizedBlobHash(currentBytes);
    if (currentNormalized !== null && currentNormalized === normalized) return "cosmetic";
  }
  return "stale";
}

module.exports = {
  rawBlobHash,
  gitBlobForPath,
  normalizeTextBytes,
  normalizedBlobHash,
  lineCount,
  rangeBlobHash,
  classifySource,
};
