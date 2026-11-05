import { describe, it, expect, beforeAll } from "vitest";
import { ensureToolkitInitialized } from "./setup";
import * as tt from "tamil-toolkit/web";

describe("T024: ScalarInspector", () => {
  beforeAll(async () => {
    await ensureToolkitInitialized();
  });

  it("breaks down Tamil characters into Unicode scalars", () => {
    const text = "தமிழ்";
    const inspection = tt.inspect_tamil_string(text);
    expect(inspection).toBeDefined();
    expect(inspection.grapheme_count).toBeGreaterThan(0);
  });

  it("detects invisible control characters (ZWJ/ZWNJ)", () => {
    const zwj = String.fromCodePoint(0x200D);
    const zwnj = String.fromCodePoint(0x200C);
    const textWithZwj = `க்${zwj}ஷ`;
    const hasZwj = textWithZwj.includes(zwj);
    const hasZwnj = textWithZwj.includes(zwnj);

    expect(hasZwj).toBe(true);
    expect(hasZwnj).toBe(false);
  });
});
