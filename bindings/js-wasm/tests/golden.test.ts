import { readFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join } from "node:path";
import { beforeAll, describe, expect, test } from "vitest";
import { execute, type Request } from "../src/index.js";
import { init, execute as executeWeb } from "../src/web.js";

beforeAll(async () => {
  const bytes = readFileSync(new URL("../pkg-web/tamil_toolkit_bg.wasm", import.meta.url));
  await init({ module_or_path: bytes });
});

const root = fileURLToPath(new URL("../../../tests/golden/", import.meta.url));
const manifest = JSON.parse(readFileSync(join(root, "manifest.json"), "utf8"));
if (manifest.version !== 1) throw new Error("Unsupported golden manifest");
const ids = new Set<string>();
const files = new Set<string>();
const cases: (Request & { id: string; expected?: unknown; expected_error?: string })[] = [];
for (const suite of manifest.suites) {
  if (files.has(suite.file)) throw new Error(`Duplicate suite: ${suite.file}`);
  files.add(suite.file);
  if (!["active", "planned"].includes(suite.status)) throw new Error("Unknown suite status");
  const text = readFileSync(join(root, suite.file), "utf8").trim();
  const rows = text ? text.split(/\r?\n/).map((line) => JSON.parse(line)) : [];
  for (const row of rows) {
    if (ids.has(row.id)) throw new Error(`Duplicate id: ${row.id}`);
    ids.add(row.id);
  }
  if (suite.status === "active") {
    if (!rows.length) throw new Error(`Empty active suite: ${suite.file}`);
    for (const row of rows) {
      if (!suite.operations.includes(row.op)) throw new Error(`Undeclared operation: ${row.op}`);
      if (Number("expected" in row) + Number("expected_error" in row) !== 1) throw new Error(`Invalid outcome: ${row.id}`);
      if ("expected_error" in row && (typeof row.expected_error !== "string" || !row.expected_error)) throw new Error(`Invalid error: ${row.id}`);
      cases.push(row);
    }
  } else console.info(`PLANNED ${suite.file}: ${suite.reason}`);
}
const onDisk = readdirSync(root).filter((name) => name.endsWith(".jsonl")).sort();
if (JSON.stringify([...files].sort()) !== JSON.stringify(onDisk)) throw new Error("Unregistered golden suite");
if (!cases.length) throw new Error("No active golden vectors");

describe("shared golden vectors through real WASM", () => {
  for (const row of cases) test(row.id, () => {
    for (const invoke of [execute, executeWeb]) {
      if ("expected_error" in row) {
        let failure: unknown;
        try { invoke(row); } catch (error) { failure = error; }
        expect(failure).toBeInstanceOf(Error);
        expect((failure as Error).message).toBe(row.expected_error);
      } else {
        expect(invoke(row)).toEqual(row.expected);
      }
    }
  });
});
test("unsupported operations and invalid inputs throw across WASM", () => {
  expect(() => execute({ op: "unknown", input: "" })).toThrow();
  expect(() => execute({ op: "get_letters", input: 1 })).toThrow();
});
