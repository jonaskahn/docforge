#!/usr/bin/env node
/**
 * Real Mermaid syntax validation, run from inside the dashboard instance
 * directory so `mermaid`/`jsdom` resolve from its own `node_modules` --
 * this script carries no docforge-specific logic and needs no shared module.
 *
 * Reads a JSON array of `{"chart": "<mermaid source>"}` from stdin, writes a
 * JSON array of `{"ok": bool, "error": string|null}` (same order) to stdout.
 * `mermaid.render()` needs real text layout (`getBBox`), which jsdom does not
 * implement, so this only ever calls `mermaid.parse()` -- syntax-only, no
 * layout, no Puppeteer/Chromium required.
 */

import { JSDOM } from "jsdom";

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  return Buffer.concat(chunks).toString("utf8");
}

async function main() {
  const raw = await readStdin();
  let tasks;
  try {
    tasks = JSON.parse(raw || "[]");
  } catch (error) {
    process.stderr.write(`invalid JSON on stdin: ${error.message}\n`);
    return 2;
  }
  if (!Array.isArray(tasks)) {
    process.stderr.write("expected a JSON array on stdin\n");
    return 2;
  }

  const dom = new JSDOM("<!doctype html><html><body></body></html>", {
    pretendToBeVisual: true,
    url: "http://localhost/",
  });
  globalThis.window = dom.window;
  globalThis.document = dom.window.document;
  Object.defineProperty(globalThis, "navigator", { value: dom.window.navigator, configurable: true });
  globalThis.SVGElement = dom.window.SVGElement;
  globalThis.HTMLElement = dom.window.HTMLElement;
  globalThis.Node = dom.window.Node;
  globalThis.DOMParser = dom.window.DOMParser;
  globalThis.self = dom.window;

  const mermaid = (await import("mermaid")).default;
  mermaid.initialize({ startOnLoad: false });

  const results = [];
  for (const task of tasks) {
    const chart = (task && typeof task.chart === "string") ? task.chart : "";
    try {
      await mermaid.parse(chart);
      results.push({ ok: true, error: null });
    } catch (error) {
      results.push({ ok: false, error: String(error.message || error).split("\n")[0] });
    }
  }

  process.stdout.write(JSON.stringify(results));
  return 0;
}

main()
  .then((code) => { process.exitCode = code; })
  .catch((error) => {
    process.stderr.write(`fatal: ${error.stack || error.message}\n`);
    process.exitCode = 1;
  });
