import { describe, it, expect, beforeAll } from "vitest";
import { ensureToolkitInitialized } from "./setup";
import * as tt from "tamil-toolkit/web";

describe("Dispatcher Sandbox Execution", () => {
  beforeAll(async () => {
    await ensureToolkitInitialized();
  });

  it("executes bamini_to_unicode via dispatcher with input object", () => {
    const res = tt.execute({
      op: "bamini_to_unicode",
      input: { text: "jkpo; nkhop" }
    });
    expect(res).toBe("தமிழ் மொழி");
  });

  it("executes to_words via dispatcher", () => {
    const res = tt.execute({
      op: "to_words",
      input: {
        value: 125000,
        locale: "TN"
      }
    });
    expect(res).toContain("லட்சத்து");
  });

  it("executes currency_to_words via dispatcher", () => {
    const res = tt.execute({
      op: "currency_to_words",
      input: {
        amount_minor: 12500000,
        currency: "INR",
        locale: "TN"
      }
    });
    expect(res).toContain("ரூபாய்");
  });

  it("executes sort_words via dispatcher", () => {
    const res = tt.execute({
      op: "sort_words",
      input: ["பாரதி", "அகத்தியர்", "கம்பர்"]
    });
    expect(res).toEqual(["அகத்தியர்", "கம்பர்", "பாரதி"]);
  });

  it("executes inspect_tamil_string via dispatcher", () => {
    const res = tt.execute({
      op: "inspect_tamil_string",
      input: "தமிழ்"
    });
    expect(res).toHaveProperty("grapheme_count");
  });
});
