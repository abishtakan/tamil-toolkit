import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, it, expect, beforeAll } from "vitest";
import type * as tt from "tamil-toolkit/web";
import { ensureToolkitInitialized } from "./setup";
import { getLexiconPacks, lookupLexicon } from "../lib/engine";
import {
  CANONICAL_LEXICON_EXAMPLES,
  CANONICAL_PACK_MANIFESTS,
  CONTRACT_TEST_PRESETS,
  ExtendedEntryDetail,
  ExtendedManifest,
  FULL_PROFILE_SUMMARY,
  RawBrowseIndexPayload,
  RawExtendedLetterRow,
  buildLexiconLookupOptions,
  buildLexiconRawRequest,
  collectEntryProvenance,
  computeLoadedPackTotals,
  deriveFiniteScopeOptions,
  extractSafeLinksFromProvenance,
  filterBrowseItems,
  findExtendedLetterBucket,
  getPackNoticeLinks,
  inspectExactQuery,
  parseBrowseIndex,
  parseExtendedLetterRows,
  sanitizeSafeExternalUrl,
  sanitizeSafeNoticeHref,
  sha256PrefixHex,
  summarizeAcceptance,
  verifyPackCatalogAlignment,
} from "../lib/lexicon";

describe("LexiconExplorer: Rust WASM Lookup, Option Preservation, Unknown Scopes & Safe Links", () => {
  let loadedPacks: tt.LexiconPackInfo[] = [];

  beforeAll(async () => {
    await ensureToolkitInitialized();
    loadedPacks = getLexiconPacks();
  });

  describe("Real WASM pack metadata and exact lookup", () => {
    it("discovers compiled packs from Rust lexicon_packs without mocking", () => {
      expect(Array.isArray(loadedPacks)).toBe(true);
      expect(loadedPacks.length).toBeGreaterThan(0);

      const core = loadedPacks.find((p) => p.id === "core");
      expect(core).toBeDefined();
      expect(core?.available).toBe(true);
      expect(core?.schema_version).toBe(1);
      expect(core?.coverage.language_ids).toContain("tam");
      expect(core?.coverage.region_codes).toContain("MY");
      expect(core?.coverage.register_codes).toContain("colloquial");
    });

    it("returns both homographs for நன்றி with human-reviewed provenance", () => {
      const res = lookupLexicon("நன்றி", { packs: ["core"] });
      expect(res.status).toBe("matched");
      expect(res.canonical_query).toBe("நன்றி");
      expect(res.entries).toHaveLength(2);

      const posValues = res.entries.map((e) => e.part_of_speech.value).sort();
      expect(posValues).toEqual(["INTJ", "NOUN"]);

      const totalSenses = res.entries.reduce((sum, e) => sum + e.senses.length, 0);
      expect(totalSenses).toBe(3);

      const prov = collectEntryProvenance(res.entries[0]);
      const summary = summarizeAcceptance(prov);
      expect(summary.hasHuman).toBe(true);
      expect(summary.hasAuto).toBe(false);
      expect(summary.actors).toContain("abish");
      expect(summary.safeLinks.length).toBeGreaterThan(0);
      expect(summary.safeLinks[0].href.startsWith("https://en.wiktionary.org/")).toBe(true);
    });

    it("returns all 9 senses for செப்பம் in display_order", () => {
      const res = lookupLexicon("செப்பம்", { packs: ["core"] });
      expect(res.status).toBe("matched");
      expect(res.entries).toHaveLength(1);
      expect(res.entries[0].senses).toHaveLength(9);
      expect(res.entries[0].senses.map((s) => s.display_order)).toEqual([
        1, 2, 3, 4, 5, 6, 7, 8, 9,
      ]);
    });

    it("returns automated acceptance metadata for bulk entries like கடை", () => {
      const res = lookupLexicon("கடை", { packs: ["core"] });
      expect(res.status).toBe("matched");
      expect(res.entries).toHaveLength(4);

      const prov = collectEntryProvenance(res.entries[0]);
      const summary = summarizeAcceptance(prov);
      expect(summary.hasAuto).toBe(true);
      expect(summary.hasHuman).toBe(false);
      expect(summary.methods).toContain("wiktionary-bulk-v1");
      expect(summary.safeLinks.some((l) => l.label === "permalink")).toBe(true);
      expect(summary.safeLinks.some((l) => l.label === "history")).toBe(true);
    });

    it("handles unknown region scopes faithfully without inference", () => {
      // நன்றி has region.state === 'unknown'; filtering by MY must exclude it
      const unfiltered = lookupLexicon("நன்றி", { packs: ["core"] });
      expect(unfiltered.entries[0].region.state).toBe("unknown");

      const filteredNanri = lookupLexicon("நன்றி", { packs: ["core"], region: "MY" });
      expect(filteredNanri.status).toBe("not_found");
      expect(filteredNanri.entries).toHaveLength(0);

      // பசியாறை is attested MY at sense level in core
      const filteredPasiyaarai = lookupLexicon("பசியாறை", { packs: ["core"], region: "MY" });
      expect(filteredPasiyaarai.status).toBe("matched");
      expect(filteredPasiyaarai.entries).toHaveLength(1);
      expect(filteredPasiyaarai.entries[0].senses[0].region.state).toBe("attested");
      expect(filteredPasiyaarai.entries[0].senses[0].region.codes).toContain("MY");
    });

    it("queries names_taxa and regional packs with attested SL and JAFFNA scopes when compiled", () => {
      const packIds = new Set(loadedPacks.map((p) => p.id));
      if (packIds.has("names_taxa")) {
        const namesRes = lookupLexicon("தம்பிரான்", { packs: ["names_taxa"], region: "SL" });
        expect(namesRes.status).toBe("matched");
        expect(namesRes.entries[0].senses.length).toBeGreaterThan(0);
      }
      if (packIds.has("regional")) {
        const regRes = lookupLexicon("கோளாறு", { packs: ["regional"], region: "JAFFNA" });
        expect(regRes.status).toBe("matched");
        expect(regRes.entries[0].senses.some((s) => s.region.codes.includes("JAFFNA"))).toBe(true);
      }
    });

    it("filters by attested register code and preserves unknown register availability", () => {
      const matched = lookupLexicon("தடவை", { packs: ["core"], register: "colloquial" });
      expect(matched.status).toBe("matched");
      expect(matched.entries[0].register.availability).toBe("available");
      expect(matched.entries[0].register.value).toBe("colloquial");

      const excluded = lookupLexicon("நன்றி", { packs: ["core"], register: "colloquial" });
      expect(excluded.status).toBe("not_found");
    });

    it("preserves whitespace, joiners, soft hyphens, and performs Rust NFC canonicalization", () => {
      const ws = lookupLexicon(" நன்றி ", { packs: ["core"] });
      expect(ws.status).toBe("not_found");
      expect(ws.canonical_query).toBe(" நன்றி ");

      const zwj = lookupLexicon(String.fromCodePoint(0xba8, 0xba9, 0xbcd, 0xbb1, 0xbbf, 0x200d), { packs: ["core"] });
      expect(zwj.status).toBe("not_found");
      expect(zwj.canonical_query).toBe(String.fromCodePoint(0xba8, 0xba9, 0xbcd, 0xbb1, 0xbbf, 0x200d));

      const zwnj = lookupLexicon(String.fromCodePoint(0xba8, 0xba9, 0xbcd, 0xbb1, 0xbbf, 0x200c), { packs: ["core"] });
      expect(zwnj.status).toBe("not_found");
      expect(zwnj.canonical_query).toBe(String.fromCodePoint(0xba8, 0xba9, 0xbcd, 0xbb1, 0xbbf, 0x200c));

      const shy = lookupLexicon("நன்றி\u00AD", { packs: ["core"] });
      expect(shy.status).toBe("not_found");
      expect(shy.canonical_query).toBe("நன்றி\u00AD");

      const nfd = lookupLexicon(String.fromCodePoint(0xb95, 0xbc6, 0xbbe), { packs: ["core"] });
      expect(nfd.status).toBe("not_found");
      expect(nfd.canonical_query).toBe("\u0B95\u0BCA");
    });

    it("surfaces exact Rust contract errors for empty/unknown/unavailable packs and invalid filters", () => {
      const emptyPacksOpts = buildLexiconLookupOptions({ packs: [] });
      expect(emptyPacksOpts).toEqual({ packs: [] });
      expect(() => lookupLexicon("நன்றி", emptyPacksOpts)).toThrow(
        "lexicon: packs must be a nonempty string array"
      );

      expect(() => lookupLexicon("நன்றி", { packs: ["nonexistent_pack"] })).toThrow(
        "lexicon: unknown pack 'nonexistent_pack'"
      );

      expect(() => lookupLexicon("நன்றி", { packs: ["terminology"] })).toThrow(
        "lexicon: pack unavailable 'terminology'"
      );

      expect(() => lookupLexicon("நன்றி", { packs: ["core"], region: "UNKNOWN_REGION" })).toThrow(
        "lexicon: unknown region 'UNKNOWN_REGION'"
      );

      expect(() =>
        lookupLexicon("நன்றி", { packs: ["core"], register: "invalid_register" })
      ).toThrow("lexicon: unknown register 'invalid_register'");

      const emptyRegionOpts = buildLexiconLookupOptions({ packs: ["core"], region: "" });
      expect(emptyRegionOpts).toEqual({ packs: ["core"], region: "" });
      expect(() => lookupLexicon("நன்றி", emptyRegionOpts)).toThrow("lexicon: invalid options");
    });
  });

  describe("Option preservation and query diagnostics helpers", () => {
    it("preserves explicit empty packs and empty filter strings instead of dropping them", () => {
      const opts = buildLexiconLookupOptions({ packs: [], region: "", register: "" });
      expect(opts).toEqual({ packs: [], region: "", register: "" });

      const rawReq = buildLexiconRawRequest(String.fromCodePoint(0x20, 0x20, 0xba8, 0xba9, 0xbcd, 0xbb1, 0xbbf, 0x200d, 0x20), opts);
      expect(rawReq).toEqual({
        op: "lexicon_lookup",
        input: String.fromCodePoint(0x20, 0x20, 0xba8, 0xba9, 0xbcd, 0xbb1, 0xbbf, 0x200d, 0x20),
        packs: [],
        region: "",
        register: "",
      });
    });

    it("omits undefined options cleanly without mutating the query string", () => {
      const opts = buildLexiconLookupOptions({ packs: ["core"] });
      expect(opts).toEqual({ packs: ["core"] });
      expect("region" in (opts ?? {})).toBe(false);

      const rawReq = buildLexiconRawRequest(String.fromCodePoint(0xba8, 0xba9, 0xbcd, 0xbb1, 0xbbf, 0x200c), undefined);
      expect(rawReq).toEqual({ op: "lexicon_lookup", input: String.fromCodePoint(0xba8, 0xba9, 0xbcd, 0xbb1, 0xbbf, 0x200c) });
    });

    it("inspects leading/trailing whitespace and invisible joiners without altering input", () => {
      const diag = inspectExactQuery(String.fromCodePoint(0x20, 0xba8, 0xba9, 0xbcd, 0xbb1, 0xbbf, 0x200d, 0x200c, 0xad, 0x20));
      expect(diag.hasLeadingOrTrailingWhitespace).toBe(true);
      expect(diag.hasJoinersOrSoftHyphen).toBe(true);
      expect(diag.joinerLabels).toEqual([
        "ZWJ (U+200D)",
        "ZWNJ (U+200C)",
        "SHY (U+00AD)",
      ]);
      expect(diag.utf8Bytes).toBeGreaterThan(10);
    });
  });

  describe("Finite scope derivation (unknown scopes not inferred)", () => {
    const samplePacks: tt.LexiconPackInfo[] = [
      {
        id: "core",
        dataset_version: "0.1.0+a211334e3659",
        schema_version: 1,
        index_format_version: 1,
        manifest_sha256: "a".repeat(64),
        available: true,
        coverage: {
          language_ids: ["tam"],
          region_codes: ["MY"],
          register_codes: ["colloquial", "formal"],
          unknown_region_entries: 10335,
        },
      },
      {
        id: "regional",
        dataset_version: "0.1.0+b97b5f21230d",
        schema_version: 1,
        index_format_version: 1,
        manifest_sha256: "b".repeat(64),
        available: true,
        coverage: {
          language_ids: ["tam"],
          region_codes: ["JAFFNA", "SL", "TN"],
          register_codes: ["dialectal", "colloquial"],
          unknown_region_entries: 190,
        },
      },
    ];

    it("includes all actual finite registry regions including valid unattested codes and tracks attested coverage separately", () => {
      const coreOnly = deriveFiniteScopeOptions(samplePacks, ["core"]);
      expect(coreOnly.attestedRegions).toEqual(["MY"]);
      // Valid registry codes (including unattested ones) are available in the finite registry
      expect(coreOnly.regions).toContain("MY");
      expect(coreOnly.regions).toContain("JAFFNA");
      expect(coreOnly.regions).toContain("BATTICALOA");
      expect(coreOnly.regions).toContain("VANNI");
      expect(coreOnly.regions).toHaveLength(16);
      expect(
        coreOnly.regionEntries.find((r) => r.code === "BATTICALOA")?.attestedInSelectedPacks
      ).toBe(false);
      expect(
        coreOnly.regionEntries.find((r) => r.code === "MY")?.attestedInSelectedPacks
      ).toBe(true);
      expect(coreOnly.registers).toEqual(["colloquial", "formal"]);
      expect(coreOnly.unknownRegionEntries).toBe(10335);

      const both = deriveFiniteScopeOptions(samplePacks, ["core", "regional"]);
      expect(both.attestedRegions).toEqual(["JAFFNA", "MY", "SL", "TN"]);
      expect(both.regions).toHaveLength(16);
      expect(
        both.regionEntries.find((r) => r.code === "JAFFNA")?.attestedInSelectedPacks
      ).toBe(true);
      expect(
        both.regionEntries.find((r) => r.code === "BATTICALOA")?.attestedInSelectedPacks
      ).toBe(false);
      expect(both.registers).toEqual(["colloquial", "dialectal", "formal"]);
      expect(both.unknownRegionEntries).toBe(10525);
    });

    it("accepts valid unattested registry regions in real WASM lookup without erroring", () => {
      const batticaloa = lookupLexicon("நன்றி", { packs: ["core"], region: "BATTICALOA" });
      expect(batticaloa.status).toBe("not_found");
      const vanni = lookupLexicon("நன்றி", { packs: ["core"], region: "VANNI" });
      expect(vanni.status).toBe("not_found");
    });

    it("returns empty finite scopes when no packs are selected", () => {
      const none = deriveFiniteScopeOptions(samplePacks, []);
      expect(none.regions).toEqual([]);
      expect(none.regionEntries).toEqual([]);
      expect(none.attestedRegions).toEqual([]);
      expect(none.registers).toEqual([]);
      expect(none.unknownRegionEntries).toBe(0);
    });
  });

  describe("Safe source links sanitization & extraction", () => {
    it("rejects javascript, data, file, http, and malformed URLs", () => {
      expect(sanitizeSafeExternalUrl("javascript:alert(1)")).toBeNull();
      expect(sanitizeSafeExternalUrl("DATA:text/html,<script>alert(1)</script>")).toBeNull();
      expect(sanitizeSafeExternalUrl("vbscript:msgbox(1)")).toBeNull();
      expect(sanitizeSafeExternalUrl("file:///C:/secret.txt")).toBeNull();
      expect(sanitizeSafeExternalUrl("http://en.wiktionary.org/wiki/test")).toBeNull();
      expect(sanitizeSafeExternalUrl("//evil.example/path")).toBeNull();
      expect(sanitizeSafeExternalUrl("https://en.wiktionary.org/wiki/test with space")).toBeNull();
      expect(sanitizeSafeExternalUrl("")).toBeNull();
    });

    it("accepts strictly valid https URLs and filters unsafe links from provenance locators", () => {
      const prov = {
        source_id: "src_500a9dbc-1724-5c2e-9e64-d34f44ad62b8",
        locator: JSON.stringify({
          permalink: "https://en.wiktionary.org/w/index.php?title=test&oldid=123",
          history_url: "javascript:alert(1)",
          url: "data:text/plain,bad",
        }),
      };
      const links = extractSafeLinksFromProvenance(prov);
      expect(links).toEqual([
        {
          label: "permalink",
          href: "https://en.wiktionary.org/w/index.php?title=test&oldid=123",
        },
      ]);
    });

    it("does not synthesize links for unknown source IDs when locator has no https URL", () => {
      const links = extractSafeLinksFromProvenance({
        source_id: "src_untrusted_custom",
        locator: "pageid=123&oldid=456",
      });
      expect(links).toEqual([]);
    });
  });

  describe("Declarative manifest totals & canonical examples coverage", () => {
    it("matches checked-in full profile totals and excluded intake disclosure", () => {
      const availableSum = FULL_PROFILE_SUMMARY.availablePacks.reduce(
        (acc, id) => {
          const m = CANONICAL_PACK_MANIFESTS[id];
          return {
            entries: acc.entries + m.entry_count,
            senses: acc.senses + m.sense_count,
          };
        },
        { entries: 0, senses: 0 }
      );

      expect(availableSum.entries).toBe(11377);
      expect(availableSum.senses).toBe(25742);
      expect(FULL_PROFILE_SUMMARY.entries).toBe(11377);
      expect(FULL_PROFILE_SUMMARY.senses).toBe(25742);
      expect(FULL_PROFILE_SUMMARY.distinctForms).toBe(9410);
      expect(FULL_PROFILE_SUMMARY.excludedHistoricalRecords).toBe(307243);
      expect(CANONICAL_PACK_MANIFESTS.terminology.expected_in_full_profile).toBe(false);

      const loaded = computeLoadedPackTotals(loadedPacks);
      expect(loaded.loadedPackIds.length).toBe(loadedPacks.length);
      expect(loaded.entries).toBeGreaterThan(0);

      const alignment = verifyPackCatalogAlignment(loadedPacks);
      expect(alignment.hasStaleMismatch).toBe(false);
      if (loadedPacks.length === 3) {
        expect(alignment.isFullCatalogVerified).toBe(true);
        expect(alignment.verifiedLoadedEntries).toBe(11377);
        expect(alignment.verifiedLoadedSenses).toBe(25742);
        expect(alignment.verifiedDistinctHeadwords).toBe(9410);
      }
    });

    it("withholds static counts and flags stale_mismatch when engine manifest_sha256 differs from catalog", () => {
      const staleCore: tt.LexiconPackInfo[] = [
        {
          id: "core",
          dataset_version: "0.1.0+000000000000",
          schema_version: 1,
          index_format_version: 1,
          manifest_sha256: "0".repeat(64),
          available: true,
          coverage: {
            language_ids: ["tam"],
            region_codes: ["MY"],
            register_codes: ["colloquial"],
            unknown_region_entries: 1,
          },
        },
      ];

      const alignment = verifyPackCatalogAlignment(staleCore);
      expect(alignment.hasStaleMismatch).toBe(true);
      expect(alignment.isFullCatalogVerified).toBe(false);
      expect(alignment.stalePackIds).toEqual(["core"]);
      expect(alignment.byPack.core.status).toBe("stale_mismatch");
      expect(alignment.byPack.core.verifiedEntryCount).toBeNull();
      expect(alignment.byPack.core.verifiedSenseCount).toBeNull();
      expect(alignment.verifiedDistinctHeadwords).toBeNull();
      expect(alignment.verifiedLoadedEntries).toBe(0);
      expect(computeLoadedPackTotals(staleCore).entries).toBe(0);

      const emptyAlignment = verifyPackCatalogAlignment([]);
      expect(emptyAlignment.hasStaleMismatch).toBe(false);
      expect(emptyAlignment.isFullCatalogVerified).toBe(false);
      expect(emptyAlignment.verifiedDistinctHeadwords).toBeNull();
      expect(emptyAlignment.byPack.core.status).toBe("unavailable");
    });

    it("provides strictly validated public attribution notice links for approved packs", () => {
      for (const packId of ["core", "names_taxa", "regional"] as const) {
        const links = getPackNoticeLinks(packId);
        expect(links).toHaveLength(3);
        expect(links[0].href).toBe(`/lexicon-notices/${packId}/ATTRIBUTION_AND_TERMS.md`);
        expect(links[1].href).toBe(`/lexicon-notices/${packId}/notices/ATTRIBUTION_AND_LICENSE.md`);
        expect(links[2].href).toBe(`/lexicon-notices/${packId}/notices/CC-BY-SA-4.0.md`);
      }
      expect(getPackNoticeLinks("terminology")).toEqual([]);

      expect(sanitizeSafeNoticeHref("/lexicon-notices/core/ATTRIBUTION_AND_TERMS.md")).toBe(
        "/lexicon-notices/core/ATTRIBUTION_AND_TERMS.md"
      );
      expect(sanitizeSafeNoticeHref("/lexicon-notices/core/../../etc/passwd")).toBeNull();
      expect(sanitizeSafeNoticeHref("/lexicon-notices/terminology/ATTRIBUTION_AND_TERMS.md")).toBeNull();
      expect(sanitizeSafeNoticeHref("javascript:alert(1)")).toBeNull();
    });

    it("includes canonical examples across core, names_taxa, and regional packs and contract presets", () => {
      const coveredPacks = new Set(CANONICAL_LEXICON_EXAMPLES.flatMap((ex) => ex.packHint));
      expect(coveredPacks.has("core")).toBe(true);
      expect(coveredPacks.has("names_taxa")).toBe(true);
      expect(coveredPacks.has("regional")).toBe(true);
      expect(CONTRACT_TEST_PRESETS.some((p) => p.id === "empty-packs")).toBe(true);
      expect(CONTRACT_TEST_PRESETS.some((p) => p.id === "unavailable-terminology")).toBe(true);
    });
  });

  describe("Alphabetical browse index & bilingual search", () => {
    it("loads public/lexicon-browse-index.json and supports letter, prefix, English gloss, POS, and dialect filters", () => {
      const rawPath = resolve(process.cwd(), "public/lexicon-browse-index.json");
      const raw = JSON.parse(readFileSync(rawPath, "utf-8")) as RawBrowseIndexPayload;
      const index = parseBrowseIndex(raw);

      expect(index.count).toBe(FULL_PROFILE_SUMMARY.distinctForms);
      expect(index.items).toHaveLength(index.count);
      expect(index.letters.length).toBeGreaterThan(20);
      expect(index.letters[0].id).toBe("அ");

      // Tamil prefix search puts exact/prefix matches first
      const tamilPrefix = filterBrowseItems(index.items, { query: "நன்" });
      expect(tamilPrefix.some((item) => item.word === "நன்றி")).toBe(true);

      // English meaning search finds Tamil words by gloss
      const englishHits = filterBrowseItems(index.items, { query: "thank you" });
      expect(englishHits.some((item) => item.word === "நன்றி")).toBe(true);

      // Letter browse filters cleanly to Tamil initial bucket
      const kaBucket = filterBrowseItems(index.items, { letter: "க" });
      expect(kaBucket.length).toBeGreaterThan(100);
      expect(kaBucket.every((item) => item.letter === "க")).toBe(true);

      // Regional dialect filter finds JAFFNA entries
      const jaffnaHits = filterBrowseItems(index.items, { region: "JAFFNA" });
      expect(jaffnaHits.some((item) => item.word === "கோளாறு")).toBe(true);
    });

    it("loads the extended 90k+ CC-BY-SA-4.0 manifest, letter buckets, and headword shards", async () => {
      const manifestPath = resolve(process.cwd(), "public/lexicon-extended/manifest.json");
      const manifest = JSON.parse(readFileSync(manifestPath, "utf-8")) as ExtendedManifest;

      expect(manifest.total_words).toBeGreaterThan(80000);
      expect(manifest.tawiktionary_words).toBeGreaterThan(80000);
      expect(manifest.license).toBe("CC-BY-SA-4.0");
      expect(manifest.letters.length).toBeGreaterThan(25);

      // Find the bucket for அவகுணம் (starts with அ)
      const aBucket = findExtendedLetterBucket("அவகுணம்", manifest.letters);
      expect(aBucket).not.toBeNull();
      const rawRows = JSON.parse(
        readFileSync(resolve(process.cwd(), `public/lexicon-extended/letters/${aBucket!.file}`), "utf-8")
      ) as RawExtendedLetterRow[];
      const items = parseExtendedLetterRows(rawRows, aBucket!.id);
      expect(items.length).toBe(aBucket!.count);
      expect(items.some((item) => item.word === "அவகுணம்")).toBe(true);

      // Verify shard lookup for அவகுணம் returns clean Tamil definition + English translation + permalink
      const shardHex = await sha256PrefixHex("அவகுணம்");
      const shard = JSON.parse(
        readFileSync(resolve(process.cwd(), `public/lexicon-extended/shards/${shardHex}.json`), "utf-8")
      ) as Record<string, ExtendedEntryDetail>;
      const entry = shard["அவகுணம்"];
      expect(entry).toBeDefined();
      expect(entry.tam_defs.length).toBeGreaterThan(0);
      expect(entry.eng_trans.length).toBeGreaterThan(0);
      expect(entry.permalink.startsWith("https://ta.wiktionary.org/")).toBe(true);
    });
  });
});
