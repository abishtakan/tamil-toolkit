import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import * as tt from "../dist/index.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "../../..");
const GOLDEN_V02 = path.join(ROOT, "tests/golden/lexicon_v02_runtime.jsonl");
const PACKS_DIR = path.join(ROOT, "dist/lexicon-packs");

test("Node WASM passes all lexicon_v02_runtime.jsonl golden vectors", () => {
  tt.lexicon_unload_pack(null);
  const lines = fs
    .readFileSync(GOLDEN_V02, "utf8")
    .split(/\r?\n/)
    .filter((l) => l.trim().length > 0);
  for (const line of lines) {
    const row = JSON.parse(line);
    const req = { op: row.op, input: row.input };
    if ("expected_error" in row) {
      assert.throws(
        () => tt.execute(req),
        (err) => err instanceof Error && err.message === row.expected_error,
        row.id
      );
    } else {
      const actual = tt.execute(req);
      assert.deepEqual(actual, row.expected, row.id);
    }
  }
});

test("Node WASM loads compiled TMLPACK2 packs via Uint8Array and queries/searches/relations", () => {
  const corePath = path.join(PACKS_DIR, "open/core.tlpack");
  const relPath = path.join(PACKS_DIR, "local/local_relations.tlpack");
  const termPath = path.join(PACKS_DIR, "local/local_terminology.tlpack");
  if (!fs.existsSync(corePath) || !fs.existsSync(relPath) || !fs.existsSync(termPath)) {
    return;
  }

  tt.lexicon_unload_pack(null);
  try {
    const sCore = tt.lexicon_load_pack_bytes(new Uint8Array(fs.readFileSync(corePath)));
    const sRel = tt.lexicon_load_pack_bytes(new Uint8Array(fs.readFileSync(relPath)));
    const sTerm = tt.lexicon_load_pack_bytes(new Uint8Array(fs.readFileSync(termPath)));

    assert.equal(sCore.pack_id, "core");
    assert.equal(sCore.category, "dictionary");
    assert.equal(sCore.pack_tier, "verified_open");
    assert.equal(sRel.pack_id, "local_relations");
    assert.equal(sRel.category, "relations");
    assert.equal(sRel.relation_count, 30858);
    assert.equal(sTerm.pack_id, "local_terminology");
    assert.equal(sTerm.category, "terminology");
    assert.equal(sTerm.pack_tier, "local_historical");

    const stats = tt.lexicon_stats();
    assert.equal(stats.pack_count, 3);
    assert.equal(stats.total_relations, 30858);

    // Folded open-only lookup: தமில் -> தமிழ்
    const folded = tt.lexicon_query("\u0ba4\u0bae\u0bbf\u0bb2\u0bcd", {
      tier: "open",
      folded: true,
    });
    assert.equal(folded.status, "matched");
    assert.ok(folded.entries.every((e) => e.pack_tier === "verified_open"));

    // Category filtering on query & search
    const qDict = tt.lexicon_query("\u0ba4\u0bae\u0bbf\u0bb4\u0bcd", { category: "dictionary" });
    assert.equal(qDict.status, "matched");
    assert.deepEqual(qDict.searched_packs, ["core"]);

    const qTerm = tt.lexicon_query("\u0b85\u0b95\u0bcd\u0b95\u0bc1\u0bb3\u0bcd \u0b95\u0bcb\u0b9f\u0bc1", {
      category: "terminology",
    });
    assert.equal(qTerm.status, "matched");
    assert.deepEqual(qTerm.searched_packs, ["local_terminology"]);

    // Variant lookup in 118k local_terminology pack: அக்குள்கோடு -> அக்குள் கோடு
    const variant = tt.lexicon_query("\u0b85\u0b95\u0bcd\u0b95\u0bc1\u0bb3\u0bcd\u0b95\u0bcb\u0b9f\u0bc1");
    assert.equal(variant.status, "matched");
    assert.equal(variant.entries[0].entry.headword, "\u0b85\u0b95\u0bcd\u0b95\u0bc1\u0bb3\u0bcd \u0b95\u0bcb\u0b9f\u0bc1");

    // Prefix search (unfiltered, category-filtered, and cursor-paginated with after_key)
    const search = tt.lexicon_search("\u0ba4\u0bae\u0bbf\u0bb4\u0bcd", { limit: 5 });
    assert.ok(search.hits.length >= 1);
    assert.equal(search.hits[0].headword, "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd");

    const page1 = tt.lexicon_search("\u0ba4\u0bae\u0bbf\u0bb4\u0bcd", { limit: 2 });
    assert.equal(page1.hits.length, 2);
    assert.equal(page1.has_more, true);
    assert.ok(page1.next_cursor);
    const page2 = tt.lexicon_search("\u0ba4\u0bae\u0bbf\u0bb4\u0bcd", {
      limit: 2,
      after_key: page1.next_cursor,
    });
    assert.ok(page2.hits.length >= 1);
    assert.ok(page2.hits.every((h) => h.matched_key > page1.next_cursor));

    const searchDict = tt.lexicon_search("\u0ba4\u0bae\u0bbf\u0bb4\u0bcd", {
      limit: 5,
      category: "dictionary",
    });
    assert.deepEqual(searchDict.searched_packs, ["core"]);
    assert.ok(searchDict.hits.length >= 1);

    // Fuzzy search & longest-prefix stemmer probes
    const fuzzy = tt.lexicon_fuzzy_search("\u0ba4\u0bae\u0bbf\u0bb2\u0bcd", {
      max_distance: 1,
      limit: 5,
    });
    assert.equal(fuzzy.query, "\u0ba4\u0bae\u0bbf\u0bb2\u0bcd");
    assert.equal(fuzzy.max_distance, 1);
    assert.ok(
      fuzzy.hits.some((h) => h.headword === "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd" && h.distance === 1)
    );

    const stems = tt.lexicon_longest_prefix("\u0ba4\u0bae\u0bbf\u0bb4\u0bcd\u0ba8\u0bbe\u0b9f\u0bc1");
    assert.equal(stems.query, "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd\u0ba8\u0bbe\u0b9f\u0bc1");
    assert.ok(stems.prefixes.includes("\u0ba4\u0bae\u0bbf\u0bb4\u0bcd"));

    // Relations lookup (exact & folded)
    const rels = tt.lexicon_relations("\u0b85\u0ba9\u0bcd\u0baa\u0bc1");
    assert.equal(rels.status, "matched");
    assert.ok(rels.relations.length >= 4);

    const relsFolded = tt.lexicon_relations("\u0b85\u0ba3\u0bcd\u0baa\u0bc1", { folded: true });
    assert.equal(relsFolded.status, "matched");
    assert.ok(relsFolded.relations.length >= 4);

    // Unified word definition (meanings + relations + provenance)
    const defTa = tt.lexicon_define("\u0ba4\u0bae\u0bbf\u0bb4\u0bcd");
    assert.equal(defTa.status, "matched");
    assert.equal(defTa.headword, "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd");
    assert.equal(defTa.has_verified_open, true);
    assert.equal(typeof defTa.has_local_historical, "boolean");
    assert.ok(defTa.categories.includes("dictionary"));
    assert.ok(defTa.meanings_en.length >= 1);
    assert.ok(defTa.sources.length >= 1);
    assert.ok(defTa.sources[0].source_id.length > 0);

    const defAnbu = tt.lexicon_define("\u0b85\u0ba9\u0bcd\u0baa\u0bc1");
    assert.equal(defAnbu.status, "matched");
    assert.equal(defAnbu.headword, "\u0b85\u0ba9\u0bcd\u0baa\u0bc1");
    assert.equal(defAnbu.has_verified_open, true);
    assert.ok(defAnbu.meanings_en.length >= 1);
    const hasRel =
      defAnbu.relations.synonyms.length > 0 ||
      defAnbu.relations.antonyms.length > 0 ||
      defAnbu.relations.related.length > 0 ||
      defAnbu.relations.hypernyms.length > 0;
    assert.ok(hasRel);
    assert.ok(defAnbu.sources.length >= 1);
  } finally {
    tt.lexicon_unload_pack(null);
  }
});
