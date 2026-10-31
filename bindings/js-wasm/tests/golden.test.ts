import { readFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join } from "node:path";
import { beforeAll, describe, expect, test } from "vitest";
import { execute, type Request, type Currency, type Locale, type CodecErrorPolicy } from "../src/index.js";
import { init, execute as executeWeb } from "../src/web.js";
import * as nodeApi from "../src/index.js";
import * as webApi from "../src/web.js";

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

test("collation convenience APIs on both WASM targets", () => {
  const words = cases.find((row) => row.id === "collate_words_basic")!;
  const key = cases.find((row) => row.id === "collate_key_001")!;
  for (const api of [nodeApi, webApi]) {
    expect(api.sort_words(words.input as string[])).toEqual(words.expected);
    expect(api.sort_key(key.input as string)).toEqual(key.expected);
    expect(api.search_key(key.input as string)).toEqual(key.expected);
    expect(api.compare(key.input as string, key.input as string)).toBe(0);
  }
});

test("numeral convenience APIs on both WASM targets", () => {
  const number = cases.find((row) => row.id === "num_014")!;
  const defaultNumber = cases.find((row) => row.id === "number_default_locale")!;
  for (const api of [nodeApi, webApi]) {
    expect(api.to_words(1025, "SL")).toBe(number.expected);
    expect(api.to_words(100000)).toBe(defaultNumber.expected);
    for (const row of cases) {
      if ((row.op === "format_currency" || row.op === "currency_to_words") && "expected" in row) {
        const input = row.input as { amount_minor: number; currency: Currency; locale?: Locale };
        expect(api[row.op](input.amount_minor, input.currency, input.locale)).toBe(row.expected);
      }
    }
    expect(() => api.format_currency(1, "USD" as Currency)).toThrow("unsupported currency");
  }
});

test("codec convenience API on both WASM targets", () => {
  const word = cases.find((row) => row.id === "codec_word_000_tn_strict")!;
  const preserved = cases.find((row) => row.id === "codec_joiner_boundary_0")!;
  for (const api of [nodeApi, webApi]) {
    expect(api.bamini_to_unicode((word.input as { text: string }).text)).toBe(word.expected);
    const input = preserved.input as { text: string; errors: CodecErrorPolicy };
    expect(api.bamini_to_unicode(input.text, input.errors)).toBe(preserved.expected);
    expect(() => api.bamini_to_unicode("*")).toThrow("ambiguous Bamini sequence");
    expect(() => api.bamini_to_unicode("f", "ignore" as CodecErrorPolicy)).toThrow("unsupported codec error policy");
  }
});

test("encoder convenience API on both WASM targets", () => {
  const word = cases.find((row) => row.id === "encode_word_000_tn")!;
  const nfd = cases.find((row) => row.id.startsWith("encode_mapping_") && row.id.endsWith("_tn_nfd"))!;
  const collision = cases.find((row) => row.id === "encode_collision_000_tn")!;
  for (const api of [nodeApi, webApi]) {
    const text = (word.input as { text: string }).text;
    const encoded = api.unicode_to_bamini(text);
    expect(encoded).toBe(word.expected);
    expect(api.bamini_to_unicode(encoded)).toBe(api.normalize_nfc(text));
    expect(api.unicode_to_bamini((nfd.input as { text: string }).text)).toBe(nfd.expected);
    expect(() => api.unicode_to_bamini((collision.input as { text: string }).text)).toThrow(collision.expected_error);
  }
});
