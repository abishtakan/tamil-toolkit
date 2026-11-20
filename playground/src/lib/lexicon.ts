import type * as tt from "tamil-toolkit/web";
import lexiconCatalog from "../generated/lexicon-catalog.json";

/**
 * Canonical pack IDs recognized by the Rust lexicon dispatcher (`KNOWN_PACK_IDS`).
 * Ordered for user-facing display, with currently available full-profile packs first.
 */
export const LEXICON_PACK_DISPLAY_ORDER: readonly tt.LexiconPackId[] = [
  "core",
  "names_taxa",
  "regional",
  "terminology",
];

export interface CanonicalPackManifestSummary {
  id: tt.LexiconPackId;
  dataset_version: string | null;
  entry_count: number;
  sense_count: number;
  unknown_region_entries: number;
  expected_in_full_profile: boolean;
}

function buildManifestSummaries(): Record<tt.LexiconPackId, CanonicalPackManifestSummary> {
  const byId: Record<tt.LexiconPackId, CanonicalPackManifestSummary> = {
    core: {
      id: "core",
      dataset_version: null,
      entry_count: 0,
      sense_count: 0,
      unknown_region_entries: 0,
      expected_in_full_profile: false,
    },
    names_taxa: {
      id: "names_taxa",
      dataset_version: null,
      entry_count: 0,
      sense_count: 0,
      unknown_region_entries: 0,
      expected_in_full_profile: false,
    },
    regional: {
      id: "regional",
      dataset_version: null,
      entry_count: 0,
      sense_count: 0,
      unknown_region_entries: 0,
      expected_in_full_profile: false,
    },
    terminology: {
      id: "terminology",
      dataset_version: null,
      entry_count: 0,
      sense_count: 0,
      unknown_region_entries: 0,
      expected_in_full_profile: false,
    },
  };

  for (const pack of lexiconCatalog.packs) {
    const id = pack.id as tt.LexiconPackId;
    if (id in byId) {
      byId[id] = {
        id,
        dataset_version: pack.dataset_version,
        entry_count: pack.entry_count,
        sense_count: pack.sense_count,
        unknown_region_entries: pack.coverage.unknown_region_entries,
        expected_in_full_profile: true,
      };
    }
  }
  return byId;
}

/**
 * Declarative pack totals sourced from `src/generated/lexicon-catalog.json`
 * (generated from checked-in pack manifests). `terminology` has no approved
 * packaged dataset and remains unavailable.
 */
export const CANONICAL_PACK_MANIFESTS: Record<tt.LexiconPackId, CanonicalPackManifestSummary> =
  buildManifestSummaries();

/**
 * Declarative totals for the current checked-in full profile (`core` + `names_taxa` + `regional`),
 * plus the quarantined unverified historical intake count.
 */
export const FULL_PROFILE_SUMMARY = {
  availablePacks: lexiconCatalog.packs.map((p) => p.id) as tt.LexiconPackId[],
  unavailablePacks: ["terminology"] as const satisfies readonly tt.LexiconPackId[],
  distinctForms: lexiconCatalog.distinct_headwords,
  entries: lexiconCatalog.total_entries,
  senses: lexiconCatalog.total_senses,
  excludedHistoricalRecords: 307243,
} as const;

export interface CatalogRegionEntry {
  code: string;
  parent_code?: string;
  [key: string]: unknown;
}

/**
 * Finite region registry entries from `src/generated/lexicon-catalog.json`,
 * including valid registry codes that currently have 0 attested entries.
 */
export const REGISTRY_REGIONS: readonly CatalogRegionEntry[] = (
  lexiconCatalog.regions as CatalogRegionEntry[]
)
  .map((r) => ({ ...r }))
  .sort((a, b) => a.code.localeCompare(b.code));

/**
 * Finite register registry codes from `src/generated/lexicon-catalog.json`.
 */
export const REGISTRY_REGISTERS: readonly string[] = [...lexiconCatalog.registers].sort((a, b) =>
  a.localeCompare(b)
);

export interface LexiconExampleItem {
  id: string;
  query: string;
  packHint: tt.LexiconPackId[];
  label_ta: string;
  label_en: string;
  note_ta: string;
  note_en: string;
  regionHint?: string;
  registerHint?: string;
}

/**
 * Examples sourced directly from the checked-in canonical packs across `core`,
 * `names_taxa`, and `regional`, covering homographs, multiple senses,
 * human-reviewed vs automated acceptance, and attested region/register scopes.
 */
export const CANONICAL_LEXICON_EXAMPLES: readonly LexiconExampleItem[] = [
  {
    id: "nanri-homograph",
    query: "நன்றி",
    packHint: ["core"],
    label_ta: "நன்றி (ஒப்பொலிச் சொல்)",
    label_en: "நன்றி (Homographs · Human)",
    note_ta: "2 பதிவுகள் (NOUN + INTJ), 3 பொருள்கள் · மனித மதிப்பாய்வு",
    note_en: "2 entries (NOUN + INTJ), 3 senses · human-reviewed",
  },
  {
    id: "ceppam-multisense",
    query: "செப்பம்",
    packHint: ["core"],
    label_ta: "செப்பம் (9 பொருள்கள்)",
    label_en: "செப்பம் (9 senses)",
    note_ta: "1 பதிவு, 9 பொருள்கள் · மனித மதிப்பாய்வு",
    note_en: "1 entry, 9 senses · human-reviewed",
  },
  {
    id: "kadai-homograph",
    query: "கடை",
    packHint: ["core"],
    label_ta: "கடை (4 ஒப்பொலிகள்)",
    label_en: "கடை (4 homographs)",
    note_ta: "4 தனிப் பதிவுகள், 10 பொருள்கள் · தானியங்கி மூலம்",
    note_en: "4 homograph entries, 10 senses · automated source",
  },
  {
    id: "thadavai-register",
    query: "தடவை",
    packHint: ["core"],
    label_ta: "தடவை (பேச்சு வழக்கு)",
    label_en: "தடவை (colloquial)",
    note_ta: "colloquial நடைப் பதிவு (core)",
    note_en: "Attested colloquial register (core)",
    registerHint: "colloquial",
  },
  {
    id: "pasiyaarai-my",
    query: "பசியாறை",
    packHint: ["core"],
    label_ta: "பசியாறை (MY)",
    label_en: "பசியாறை (MY)",
    note_ta: "மலேசியா (MY) வட்டாரச் சான்று (core)",
    note_en: "Attested MY region (core)",
    regionHint: "MY",
  },
  {
    id: "kaman-crosspack",
    query: "காமன்",
    packHint: ["core", "names_taxa"],
    label_ta: "காமன் (core + names_taxa)",
    label_en: "காமன் (cross-pack)",
    note_ta: "core & names_taxa தொகுப்புகளில் ஒப்பொலிப் பதிவுகள்",
    note_en: "Entries across core & names_taxa (poetic register)",
  },
  {
    id: "thambiran-sl",
    query: "தம்பிரான்",
    packHint: ["names_taxa"],
    label_ta: "தம்பிரான் (names_taxa · SL)",
    label_en: "தம்பிரான் (names_taxa · SL)",
    note_ta: "5 பொருள்கள், இலங்கை (SL) சான்று",
    note_en: "5 senses, attested SL region (names_taxa)",
  },
  {
    id: "kolaaru-jaffna",
    query: "கோளாறு",
    packHint: ["regional"],
    label_ta: "கோளாறு (யாழ்ப்பாணம்)",
    label_en: "கோளாறு (Jaffna)",
    note_ta: "5 பொருள்கள், JAFFNA வட்டாரச் சான்று (regional)",
    note_en: "5 senses, attested JAFFNA region (regional)",
  },
  {
    id: "pinneram-sl",
    query: "பின்னேரம்",
    packHint: ["regional"],
    label_ta: "பின்னேரம் (SL)",
    label_en: "பின்னேரம் (SL)",
    note_ta: "இலங்கை (SL) வட்டாரச் சொல் (regional)",
    note_en: "Attested SL region (regional)",
  },
  {
    id: "thil-chennai",
    query: "தில்",
    packHint: ["regional"],
    label_ta: "தில் (சென்னை)",
    label_en: "தில் (Chennai)",
    note_ta: "சென்னை (CHENNAI) வட்டாரச் சொல் (regional)",
    note_en: "Attested CHENNAI region (regional)",
  },
  {
    id: "sullaan-kongu",
    query: "சுள்ளான்",
    packHint: ["regional"],
    label_ta: "சுள்ளான் (கொங்கு)",
    label_en: "சுள்ளான் (Kongu)",
    note_ta: "கொங்கு (KONGU) வட்டாரச் சொல் (regional)",
    note_en: "Attested KONGU region (regional)",
  },
  {
    id: "aayaa-crosspack",
    query: "ஆயா",
    packHint: ["core", "regional"],
    label_ta: "ஆயா (core + regional)",
    label_en: "ஆயா (core + regional)",
    note_ta: "core (2 பதிவுகள்) + regional (KONGU/CHENNAI)",
    note_en: "core (2 entries) + regional (KONGU, CHENNAI)",
  },
];

export interface LookupOptionInput {
  packs?: string[];
  region?: string;
  register?: string;
}

/**
 * Preserves caller-supplied options verbatim without stripping empty arrays
 * or empty strings, so contract-level validation errors are surfaced faithfully
 * by the Rust dispatcher.
 */
export function buildLexiconLookupOptions(
  input: LookupOptionInput
): tt.LexiconLookupOptions | undefined {
  const opts: tt.LexiconLookupOptions = {};
  let hasAny = false;
  if (input.packs !== undefined) {
    opts.packs = [...input.packs];
    hasAny = true;
  }
  if (input.region !== undefined) {
    opts.region = input.region;
    hasAny = true;
  }
  if (input.register !== undefined) {
    opts.register = input.register;
    hasAny = true;
  }
  return hasAny ? opts : undefined;
}

/**
 * Builds the exact JSON payload dispatched to `tamil_toolkit::execute_json`,
 * preserving whitespace, joiners, soft hyphens, and explicit options verbatim.
 */
export function buildLexiconRawRequest(
  query: string,
  options?: tt.LexiconLookupOptions
): Record<string, unknown> {
  const req: Record<string, unknown> = {
    op: "lexicon_lookup",
    input: query,
  };
  if (options !== undefined) {
    if (options.packs !== undefined) req.packs = options.packs;
    if (options.region !== undefined) req.region = options.region;
    if (options.register !== undefined) req.register = options.register;
  }
  return req;
}

export interface FiniteRegionOption {
  code: string;
  parent_code?: string;
  attestedInSelectedPacks: boolean;
}

export interface FiniteScopeOptions {
  regions: string[];
  regionEntries: FiniteRegionOption[];
  attestedRegions: string[];
  registers: string[];
  unknownRegionEntries: number;
}

/**
 * Derives finite region and register dropdown options from the canonical
 * region registry (`lexicon-catalog.json`, which includes valid unattested codes)
 * and selected compiled packs' `coverage` metadata. Unknown scopes are never inferred.
 */
export function deriveFiniteScopeOptions(
  availablePacks: readonly tt.LexiconPackInfo[],
  selectedPackIds: readonly string[]
): FiniteScopeOptions {
  const selectedSet = new Set(selectedPackIds);
  const attestedRegionSet = new Set<string>();
  const registerSet = new Set<string>();
  let unknownRegionEntries = 0;
  let matchedPackCount = 0;

  for (const pack of availablePacks) {
    if (!selectedSet.has(pack.id)) continue;
    matchedPackCount++;
    unknownRegionEntries += pack.coverage.unknown_region_entries;
    for (const r of pack.coverage.region_codes) {
      attestedRegionSet.add(r);
    }
    for (const reg of pack.coverage.register_codes) {
      registerSet.add(reg);
    }
  }

  const regionEntries: FiniteRegionOption[] =
    matchedPackCount === 0
      ? []
      : REGISTRY_REGIONS.map((reg) => ({
          code: reg.code,
          parent_code: reg.parent_code,
          attestedInSelectedPacks: attestedRegionSet.has(reg.code),
        }));

  return {
    regions: regionEntries.map((r) => r.code),
    regionEntries,
    attestedRegions: Array.from(attestedRegionSet).sort((a, b) => a.localeCompare(b)),
    registers: Array.from(registerSet).sort((a, b) => a.localeCompare(b)),
    unknownRegionEntries,
  };
}

export interface LoadedPackTotals {
  loadedPackIds: tt.LexiconPackId[];
  verifiedPackIds: tt.LexiconPackId[];
  entries: number;
  senses: number;
  unknownRegionEntries: number;
}

export type PackVerificationStatus = "verified" | "stale_mismatch" | "unavailable";

export interface PackCatalogVerification {
  id: tt.LexiconPackId;
  status: PackVerificationStatus;
  engineManifestSha256: string | null;
  catalogManifestSha256: string | null;
  datasetVersion: string | null;
  verifiedEntryCount: number | null;
  verifiedSenseCount: number | null;
}

export interface CatalogAlignmentReport {
  isFullCatalogVerified: boolean;
  hasStaleMismatch: boolean;
  byPack: Record<tt.LexiconPackId, PackCatalogVerification>;
  verifiedLoadedEntries: number;
  verifiedLoadedSenses: number;
  verifiedDistinctHeadwords: number | null;
  verifiedPackIds: tt.LexiconPackId[];
  stalePackIds: tt.LexiconPackId[];
  unavailablePackIds: tt.LexiconPackId[];
}

/**
 * Verifies every live engine `PackInfo.manifest_sha256` against
 * `src/generated/lexicon-catalog.json` before static counts may be presented.
 * Packs with mismatched hashes are marked `stale_mismatch` and their static
 * catalog counts are withheld (`null`).
 */
export function verifyPackCatalogAlignment(
  enginePacks: readonly tt.LexiconPackInfo[]
): CatalogAlignmentReport {
  const engineById = new Map<string, tt.LexiconPackInfo>();
  for (const pack of enginePacks) {
    engineById.set(pack.id, pack);
  }

  const catalogById = new Map<string, (typeof lexiconCatalog.packs)[number]>();
  for (const pack of lexiconCatalog.packs) {
    catalogById.set(pack.id, pack);
  }

  const byPack = {} as Record<tt.LexiconPackId, PackCatalogVerification>;
  const verifiedPackIds: tt.LexiconPackId[] = [];
  const stalePackIds: tt.LexiconPackId[] = [];
  const unavailablePackIds: tt.LexiconPackId[] = [];
  let verifiedLoadedEntries = 0;
  let verifiedLoadedSenses = 0;

  for (const packId of LEXICON_PACK_DISPLAY_ORDER) {
    const enginePack = engineById.get(packId);
    const catalogPack = catalogById.get(packId);

    if (!enginePack || !enginePack.available) {
      unavailablePackIds.push(packId);
      byPack[packId] = {
        id: packId,
        status: "unavailable",
        engineManifestSha256: null,
        catalogManifestSha256: catalogPack?.manifest_sha256 ?? null,
        datasetVersion: catalogPack?.dataset_version ?? null,
        verifiedEntryCount: null,
        verifiedSenseCount: null,
      };
      continue;
    }

    if (!catalogPack || enginePack.manifest_sha256 !== catalogPack.manifest_sha256) {
      stalePackIds.push(packId);
      byPack[packId] = {
        id: packId,
        status: "stale_mismatch",
        engineManifestSha256: enginePack.manifest_sha256,
        catalogManifestSha256: catalogPack?.manifest_sha256 ?? null,
        datasetVersion: enginePack.dataset_version,
        verifiedEntryCount: null,
        verifiedSenseCount: null,
      };
      continue;
    }

    verifiedPackIds.push(packId);
    verifiedLoadedEntries += catalogPack.entry_count;
    verifiedLoadedSenses += catalogPack.sense_count;
    byPack[packId] = {
      id: packId,
      status: "verified",
      engineManifestSha256: enginePack.manifest_sha256,
      catalogManifestSha256: catalogPack.manifest_sha256,
      datasetVersion: enginePack.dataset_version,
      verifiedEntryCount: catalogPack.entry_count,
      verifiedSenseCount: catalogPack.sense_count,
    };
  }

  const expectedCatalogIds = lexiconCatalog.packs.map((p) => p.id);
  const hasExtraUnverifiedEnginePack = enginePacks.some(
    (p) => !catalogById.has(p.id) || byPack[p.id]?.status !== "verified"
  );
  const isFullCatalogVerified =
    stalePackIds.length === 0 &&
    !hasExtraUnverifiedEnginePack &&
    expectedCatalogIds.every((id) => byPack[id as tt.LexiconPackId]?.status === "verified");

  return {
    isFullCatalogVerified,
    hasStaleMismatch: stalePackIds.length > 0 || hasExtraUnverifiedEnginePack,
    byPack,
    verifiedLoadedEntries,
    verifiedLoadedSenses,
    verifiedDistinctHeadwords: isFullCatalogVerified ? lexiconCatalog.distinct_headwords : null,
    verifiedPackIds,
    stalePackIds,
    unavailablePackIds,
  };
}

/**
 * Computes live loaded totals from `lexicon_packs()` only for packs whose
 * `manifest_sha256` matches `src/generated/lexicon-catalog.json`.
 */
export function computeLoadedPackTotals(
  availablePacks: readonly tt.LexiconPackInfo[]
): LoadedPackTotals {
  const alignment = verifyPackCatalogAlignment(availablePacks);
  let unknownRegionEntries = 0;
  const loadedPackIds: tt.LexiconPackId[] = [];

  for (const pack of availablePacks) {
    loadedPackIds.push(pack.id);
    if (alignment.byPack[pack.id]?.status === "verified") {
      unknownRegionEntries += pack.coverage.unknown_region_entries;
    }
  }

  return {
    loadedPackIds,
    verifiedPackIds: alignment.verifiedPackIds,
    entries: alignment.verifiedLoadedEntries,
    senses: alignment.verifiedLoadedSenses,
    unknownRegionEntries,
  };
}

export interface SafeNoticeLink {
  packId: "core" | "names_taxa" | "regional";
  kind: "attribution_terms" | "license_notice" | "cc_by_sa";
  label_ta: string;
  label_en: string;
  href: string;
}

const SAFE_NOTICE_PATH_REGEX =
  /^\/lexicon-notices\/(core|names_taxa|regional)\/(ATTRIBUTION_AND_TERMS\.md|notices\/ATTRIBUTION_AND_LICENSE\.md|notices\/CC-BY-SA-4\.0\.md)$/;

/**
 * Validates that a local attribution/notice href strictly matches one of the
 * root-published `/lexicon-notices/<pack>/...` Markdown files.
 */
export function sanitizeSafeNoticeHref(raw: unknown): string | null {
  if (typeof raw !== "string") return null;
  const trimmed = raw.trim();
  if (!SAFE_NOTICE_PATH_REGEX.test(trimmed)) return null;
  return trimmed;
}

/**
 * Returns strictly validated public attribution & license notice links for
 * one approved pack (`core`, `names_taxa`, or `regional`).
 */
export function getPackNoticeLinks(packId: tt.LexiconPackId): SafeNoticeLink[] {
  if (packId !== "core" && packId !== "names_taxa" && packId !== "regional") {
    return [];
  }
  const candidates: SafeNoticeLink[] = [
    {
      packId,
      kind: "attribution_terms",
      label_ta: "ஆதார & விதிமுறைகள்",
      label_en: "Attribution & Terms",
      href: `/lexicon-notices/${packId}/ATTRIBUTION_AND_TERMS.md`,
    },
    {
      packId,
      kind: "license_notice",
      label_ta: "உரிம அறிவிப்பு",
      label_en: "Notice",
      href: `/lexicon-notices/${packId}/notices/ATTRIBUTION_AND_LICENSE.md`,
    },
    {
      packId,
      kind: "cc_by_sa",
      label_ta: "CC-BY-SA-4.0",
      label_en: "CC-BY-SA-4.0",
      href: `/lexicon-notices/${packId}/notices/CC-BY-SA-4.0.md`,
    },
  ];
  return candidates.filter((item) => sanitizeSafeNoticeHref(item.href) !== null);
}

export interface SafeSourceLink {
  label: "permalink" | "history" | "source";
  href: string;
}

const KNOWN_WIKTIONARY_REVIEWED_SOURCES = new Set([
  "src_2b7f1069-5437-5079-ac9a-77778e972340",
  "src_2f067835-ab2f-5e90-99a1-51e19822a4a3",
  "src_4cb39d90-06c5-59e2-a1bc-489d7d6a234c",
  "src_5487700e-9258-5179-ac23-19dce7123368",
  "src_9feaeda1-42d8-547c-9af6-f5c533c20c03",
]);

/**
 * Validates an external URL candidate, allowing only `https:` URLs with a valid
 * hostname and rejecting `javascript:`, `data:`, `http:`, `file:`, or control chars.
 */
export function sanitizeSafeExternalUrl(raw: unknown): string | null {
  if (typeof raw !== "string") return null;
  const trimmed = raw.trim();
  if (!trimmed || /[\u0000-\u001F\u007F\s]/.test(trimmed)) return null;
  try {
    const parsed = new URL(trimmed);
    if (parsed.protocol !== "https:") return null;
    if (!parsed.hostname) return null;
    return parsed.toString();
  } catch {
    return null;
  }
}

/**
 * Extracts deduplicated, strictly validated `https:` source links from one
 * provenance record's `locator` (and pinned Wiktionary `revid` for reviewed sources).
 */
export function extractSafeLinksFromProvenance(
  prov: Pick<tt.LexiconProvenance, "source_id" | "locator">
): SafeSourceLink[] {
  const links: SafeSourceLink[] = [];
  const seen = new Set<string>();

  const pushLink = (label: SafeSourceLink["label"], candidate: unknown) => {
    const safe = sanitizeSafeExternalUrl(candidate);
    if (safe && !seen.has(safe)) {
      seen.add(safe);
      links.push({ label, href: safe });
    }
  };

  const rawLocator = prov.locator?.trim() ?? "";
  let revidCandidate: string | null = null;

  if (rawLocator.startsWith("{")) {
    try {
      const parsed = JSON.parse(rawLocator) as Record<string, unknown>;
      if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
        pushLink("permalink", parsed.permalink);
        pushLink("history", parsed.history_url);
        pushLink("source", parsed.url);
        if (
          typeof parsed.revid === "number" &&
          Number.isInteger(parsed.revid) &&
          parsed.revid > 0
        ) {
          revidCandidate = String(parsed.revid);
        } else if (typeof parsed.revid === "string" && /^\d+$/.test(parsed.revid)) {
          revidCandidate = parsed.revid;
        }
      }
    } catch {
      // Non-JSON locator ignored for JSON field extraction
    }
  } else if (rawLocator) {
    const params = new URLSearchParams(rawLocator);
    const oldid = params.get("oldid");
    if (oldid && /^\d+$/.test(oldid)) {
      revidCandidate = oldid;
    }
  }

  if (
    links.length === 0 &&
    revidCandidate &&
    KNOWN_WIKTIONARY_REVIEWED_SOURCES.has(prov.source_id)
  ) {
    pushLink("permalink", `https://en.wiktionary.org/w/index.php?oldid=${revidCandidate}`);
  }

  return links;
}

export interface AcceptanceSummary {
  hasHuman: boolean;
  hasAuto: boolean;
  humanCount: number;
  autoCount: number;
  actors: string[];
  methods: string[];
  totalProvenanceRecords: number;
  safeLinks: SafeSourceLink[];
}

/**
 * Collects distinct provenance records across an entry (including POS, forms,
 * region/register scopes, annotations, and all senses) to summarize human vs
 * automated acceptance without duplicating identical assertion IDs.
 */
export function collectEntryProvenance(entry: tt.LexiconEntry): tt.LexiconProvenance[] {
  const byKey = new Map<string, tt.LexiconProvenance>();
  const addAll = (items: readonly tt.LexiconProvenance[] | undefined) => {
    if (!items) return;
    for (const p of items) {
      const key = `${p.assertion_id}:${p.acceptance.decision_id}`;
      if (!byKey.has(key)) {
        byKey.set(key, p);
      }
    }
  };

  addAll(entry.provenance);
  addAll(entry.part_of_speech.provenance);
  addAll(entry.region.provenance);
  addAll(entry.register.provenance);
  for (const form of entry.forms) addAll(form.provenance);
  for (const ann of entry.annotations) addAll(ann.field.provenance);
  for (const sense of entry.senses) {
    addAll(sense.provenance);
    addAll(sense.region.provenance);
    addAll(sense.register.provenance);
    for (const comp of sense.components) addAll(comp.provenance);
    for (const ex of sense.examples) addAll(ex.provenance);
    for (const rel of sense.relations) addAll(rel.provenance);
    for (const ann of sense.annotations) addAll(ann.field.provenance);
  }

  return Array.from(byKey.values());
}

export function summarizeAcceptance(
  provenanceList: readonly tt.LexiconProvenance[]
): AcceptanceSummary {
  let humanCount = 0;
  let autoCount = 0;
  const actorSet = new Set<string>();
  const methodSet = new Set<string>();
  const linkMap = new Map<string, SafeSourceLink>();

  for (const prov of provenanceList) {
    if (prov.acceptance.kind === "accepted_human") {
      humanCount++;
    } else if (prov.acceptance.kind === "accepted_auto_source") {
      autoCount++;
    }
    if (prov.acceptance.actor_id) {
      actorSet.add(prov.acceptance.actor_id);
    }
    if (prov.acceptance.method) {
      methodSet.add(prov.acceptance.method);
    }
    for (const link of extractSafeLinksFromProvenance(prov)) {
      if (!linkMap.has(link.href)) {
        linkMap.set(link.href, link);
      }
    }
  }

  return {
    hasHuman: humanCount > 0,
    hasAuto: autoCount > 0,
    humanCount,
    autoCount,
    actors: Array.from(actorSet).sort(),
    methods: Array.from(methodSet).sort(),
    totalProvenanceRecords: provenanceList.length,
    safeLinks: Array.from(linkMap.values()),
  };
}

export interface QueryDiagnostics {
  utf8Bytes: number;
  hasLeadingOrTrailingWhitespace: boolean;
  hasJoinersOrSoftHyphen: boolean;
  joinerLabels: string[];
}

/**
 * Inspects exact query properties for transparency without modifying the query.
 */
export function inspectExactQuery(query: string): QueryDiagnostics {
  const utf8Bytes = new TextEncoder().encode(query).length;
  const hasLeadingOrTrailingWhitespace =
    query.length > 0 && (query !== query.trim());
  const joinerLabels: string[] = [];
  if (query.includes(String.fromCodePoint(0x200d))) joinerLabels.push("ZWJ (U+200D)");
  if (query.includes(String.fromCodePoint(0x200c))) joinerLabels.push("ZWNJ (U+200C)");
  if (query.includes("\u00AD")) joinerLabels.push("SHY (U+00AD)");

  return {
    utf8Bytes,
    hasLeadingOrTrailingWhitespace,
    hasJoinersOrSoftHyphen: joinerLabels.length > 0,
    joinerLabels,
  };
}

export interface ContractTestPreset {
  id: string;
  label_ta: string;
  label_en: string;
  desc_ta: string;
  desc_en: string;
  query: string;
  /** If true, uses currently loaded packs from `lexicon_packs()`; otherwise uses explicit `packs`. */
  useAvailablePacks?: boolean;
  packs?: string[];
  region?: string;
  register?: string;
}

/**
 * Optional developer contract-test presets exercising boundary, empty/unknown/unavailable
 * pack, invalid filter, joiner/whitespace preservation, and NFD->NFC canonicalization.
 */
export const CONTRACT_TEST_PRESETS: readonly ContractTestPreset[] = [
  {
    id: "empty-query",
    label_ta: "வெற்று வினவல் (\"\")",
    label_en: "Empty query (\"\")",
    desc_ta: "காலி உள்ளீடு பிழையின்றி not_found அளிக்கிறது",
    desc_en: "Empty string is valid after pack validation and returns not_found",
    query: "",
    useAvailablePacks: true,
  },
  {
    id: "empty-packs",
    label_ta: "வெற்றுப் தொகுப்பு பட்டியல் (packs: [])",
    label_en: "Empty packs ([])",
    desc_ta: "packs: [] என்ற விருப்பம் சுருக்கப்படாமல் Rust பிழையைத் தர வேண்டும்",
    desc_en: "Preserves packs: [] to trigger 'lexicon: packs must be a nonempty string array'",
    query: "நன்றி",
    packs: [],
  },
  {
    id: "unknown-pack",
    label_ta: "அறியப்படாத தொகுப்பு (\"nonexistent\")",
    label_en: "Unknown pack",
    desc_ta: "அறியப்படாத தொகுப்புப் பெயருக்கான ஒப்பந்தப் பிழை",
    desc_en: "Requests an unknown pack ID ('nonexistent_pack')",
    query: "நன்றி",
    packs: ["nonexistent_pack"],
  },
  {
    id: "unavailable-terminology",
    label_ta: "கிடைக்காத தொகுப்பு (terminology)",
    label_en: "Unavailable pack (terminology)",
    desc_ta: "தொகுக்கப்படாத terminology தொகுப்புக்கான பிழைச் செய்தி",
    desc_en: "Requests 'terminology' to verify 'lexicon: pack unavailable'",
    query: "நன்றி",
    packs: ["terminology"],
  },
  {
    id: "invalid-region",
    label_ta: "தவறான பகுதி வடிகட்டி",
    label_en: "Invalid region filter",
    desc_ta: "வரையறையில் இல்லாத பகுதி குறியீட்டுக்கான பிழை",
    desc_en: "Sends 'UNKNOWN_REGION' to verify 'lexicon: unknown region'",
    query: "நன்றி",
    useAvailablePacks: true,
    region: "UNKNOWN_REGION",
  },
  {
    id: "invalid-register",
    label_ta: "தவறான நடை வடிகட்டி",
    label_en: "Invalid register filter",
    desc_ta: "வரையறையில் இல்லாத நடைக் குறியீட்டுக்கான பிழை",
    desc_en: "Sends 'invalid_register' to verify 'lexicon: unknown register'",
    query: "நன்றி",
    useAvailablePacks: true,
    register: "invalid_register",
  },
  {
    id: "empty-region-option",
    label_ta: "வெற்று பகுதி மதிப்பு (region: \"\")",
    label_en: "Empty region option (\"\")",
    desc_ta: "region: \"\" என்பது invalid options பிழையைத் தர வேண்டும்",
    desc_en: "Preserves region: \"\" to verify 'lexicon: invalid options'",
    query: "நன்றி",
    useAvailablePacks: true,
    region: "",
  },
  {
    id: "whitespace-joiner-preserved",
    label_ta: "இடைவெளி & ZWJ பாதுகாப்பு",
    label_en: "Whitespace & ZWJ preserved",
    desc_ta: String.fromCodePoint(0x22, 0x20, 0xba8, 0xba9, 0xbcd, 0xbb1, 0xbbf, 0x200d, 0x20, 0x22, 0x20, 0x2014, 0x20, 0xb87, 0xb9f, 0xbc8, 0xbb5, 0xbc6, 0xbb3, 0xbbf, 0xbaf, 0xbc1, 0xbae, 0xbcd, 0x20, 0x5a, 0x57, 0x4a, 0x2d, 0xb89, 0xbae, 0xbcd, 0x20, 0xba8, 0xbc0, 0xb95, 0xbcd, 0xb95, 0xbaa, 0xbcd, 0xbaa, 0xb9f, 0xbbe, 0xbae, 0xbb2, 0xbcd, 0x20, 0xb85, 0xba9, 0xbc1, 0xbaa, 0xbcd, 0xbaa, 0xbaa, 0xbcd, 0xbaa, 0xb9f, 0xbc1, 0xbae, 0xbcd),
    desc_en: String.fromCodePoint(0x53, 0x65, 0x6e, 0x64, 0x73, 0x20, 0x22, 0x20, 0xba8, 0xba9, 0xbcd, 0xbb1, 0xbbf, 0x5c, 0x75, 0x32, 0x30, 0x30, 0x44, 0x20, 0x22, 0x20, 0x76, 0x65, 0x72, 0x62, 0x61, 0x74, 0x69, 0x6d, 0x20, 0x77, 0x69, 0x74, 0x68, 0x6f, 0x75, 0x74, 0x20, 0x74, 0x72, 0x69, 0x6d, 0x6d, 0x69, 0x6e, 0x67, 0x20, 0x6f, 0x72, 0x20, 0x73, 0x74, 0x72, 0x69, 0x70, 0x70, 0x69, 0x6e, 0x67, 0x20, 0x6a, 0x6f, 0x69, 0x6e, 0x65, 0x72, 0x73),
    query: String.fromCodePoint(0x20, 0xba8, 0xba9, 0xbcd, 0xbb1, 0xbbf, 0x200d, 0x20),
    useAvailablePacks: true,
  },
  {
    id: "nfd-to-nfc",
    label_ta: String.fromCodePoint(0x4e, 0x46, 0x44, 0x20, 0x2192, 0x20, 0x4e, 0x46, 0x43, 0x20, 0xb92, 0xbaa, 0xbcd, 0xbaa, 0xbc0, 0xb9f, 0xbc1, 0x20, 0x28, 0xb95, 0xbc6, 0xbbe, 0x29),
    label_en: "NFD → NFC canonicalization",
    desc_ta: String.fromCodePoint(0xbaa, 0xbbf, 0xbb0, 0xbbf, 0xba8, 0xbcd, 0xba4, 0x20, 0x4e, 0x46, 0x44, 0x20, 0x28, 0x5c, 0x75, 0x30, 0x42, 0x39, 0x35, 0x5c, 0x75, 0x30, 0x42, 0x43, 0x36, 0x5c, 0x75, 0x30, 0x42, 0x42, 0x45, 0x29, 0x20, 0xb89, 0xbb3, 0xbcd, 0xbb3, 0xbc0, 0xb9f, 0xbcd, 0xb9f, 0xbc8, 0x20, 0x52, 0x75, 0x73, 0x74, 0x20, 0x4e, 0x46, 0x43, 0x20, 0x28, 0xb95, 0xbca, 0x29, 0x20, 0xb86, 0xb95, 0x20, 0xbae, 0xbbe, 0xbb1, 0xbcd, 0xbb1, 0xbc1, 0xbae, 0xbcd),
    desc_en: String.fromCodePoint(0x53, 0x65, 0x6e, 0x64, 0x73, 0x20, 0x4e, 0x46, 0x44, 0x20, 0x64, 0x65, 0x63, 0x6f, 0x6d, 0x70, 0x6f, 0x73, 0x65, 0x64, 0x20, 0x27, 0xb95, 0xbc6, 0xbbe, 0x27, 0x20, 0x61, 0x6e, 0x64, 0x20, 0x73, 0x68, 0x6f, 0x77, 0x73, 0x20, 0x52, 0x75, 0x73, 0x74, 0x20, 0x63, 0x61, 0x6e, 0x6f, 0x6e, 0x69, 0x63, 0x61, 0x6c, 0x5f, 0x71, 0x75, 0x65, 0x72, 0x79, 0x20, 0x27, 0xb95, 0xbca, 0x27),
    query: String.fromCodePoint(0xb95, 0xbc6, 0xbbe),
    useAvailablePacks: true,
  },
];

export type ExtendedPackId = tt.LexiconPackId | "ta_wiktionary";

export interface BrowseWordItem {
  word: string;
  letter: string;
  packs: ExtendedPackId[];
  pos: string[];
  regions: string[];
  gloss: string;
  glossLower: string;
}

export interface ExtendedLetterBucket {
  id: string;
  file: string;
  count: number;
}

export interface ExtendedManifest {
  version: number;
  total_words: number;
  embedded_words: number;
  tawiktionary_words: number;
  overlap_words: number;
  source_id: string;
  dump_sha256: string;
  license: string;
  letters: ExtendedLetterBucket[];
  pos: string[];
}

export interface ExtendedEntryDetail {
  pos: string | null;
  tam_defs: string[];
  eng_trans: string[];
  pageid: number;
  revid: number;
  timestamp: string;
  permalink: string;
  history_url: string;
  source_id: string;
  license: string;
}

export type RawExtendedLetterRow = [string, string[], string[], string[], string];

export function parseExtendedLetterRows(
  rows: RawExtendedLetterRow[],
  letter: string
): BrowseWordItem[] {
  return rows.map(([word, packs, pos, regions, gloss]) => ({
    word,
    letter,
    packs: packs as ExtendedPackId[],
    pos,
    regions,
    gloss,
    glossLower: gloss.toLowerCase(),
  }));
}

export function findExtendedLetterBucket(
  query: string,
  letters: readonly ExtendedLetterBucket[]
): ExtendedLetterBucket | null {
  const trimmed = query.trim().normalize("NFC");
  if (!trimmed) return null;
  const byId = new Map(letters.map((b) => [b.id, b]));
  for (const ch of trimmed) {
    const hit = byId.get(ch);
    if (hit) return hit;
  }
  return null;
}

export async function sha256PrefixHex(text: string): Promise<string> {
  const data = new TextEncoder().encode(text.normalize("NFC"));
  const digest = await crypto.subtle.digest("SHA-256", data);
  const firstByte = new Uint8Array(digest)[0];
  return firstByte.toString(16).padStart(2, "0");
}

export interface BrowseLetterBucket {
  id: string;
  count: number;
}

export interface BrowseIndexData {
  version: number;
  count: number;
  letters: BrowseLetterBucket[];
  pos: string[];
  items: BrowseWordItem[];
}

export interface RawBrowseIndexPayload {
  version: number;
  count: number;
  letters: BrowseLetterBucket[];
  pos: string[];
  items: [string, string, string[], string[], string[], string][];
}

export const POS_HUMAN_LABELS: Record<string, { en: string; ta: string }> = {
  NOUN: { en: "Noun", ta: "பெயர்ச்சொல்" },
  VERB: { en: "Verb", ta: "வினைச்சொல்" },
  ADJ: { en: "Adjective", ta: "பெயரடை" },
  ADV: { en: "Adverb", ta: "வினையடை" },
  PROPN: { en: "Proper Noun", ta: "சிறப்புப் பெயர்" },
  PRON: { en: "Pronoun", ta: "பிரதிப்பெயர்" },
  INTJ: { en: "Interjection", ta: "வியப்பிடைச்சொல்" },
  NUM: { en: "Numeral", ta: "எண்ணுப்பெயர்" },
  PART: { en: "Particle", ta: "இடைச்சொல்" },
  ADP: { en: "Postposition", ta: "வேற்றுமை உருபு" },
  CONJ: { en: "Conjunction", ta: "இணைப்புச்சொல்" },
  DET: { en: "Determiner", ta: "சுட்டுச்சொல்" },
};

export function parseBrowseIndex(raw: RawBrowseIndexPayload): BrowseIndexData {
  const items: BrowseWordItem[] = raw.items.map(([word, letter, packs, pos, regions, gloss]) => ({
    word,
    letter,
    packs: packs as tt.LexiconPackId[],
    pos,
    regions,
    gloss,
    glossLower: gloss.toLowerCase(),
  }));
  return {
    version: raw.version,
    count: raw.count,
    letters: raw.letters,
    pos: raw.pos,
    items,
  };
}

export interface BrowseFilterCriteria {
  query?: string;
  letter?: string;
  packs?: readonly string[];
  pos?: string;
  region?: string;
}

export function filterBrowseItems(
  items: readonly BrowseWordItem[],
  criteria: BrowseFilterCriteria
): BrowseWordItem[] {
  const q = (criteria.query ?? "").trim().normalize("NFC");
  const qLower = q.toLowerCase();
  const hasPackFilter = Boolean(criteria.packs && criteria.packs.length > 0);
  const packSet = hasPackFilter ? new Set(criteria.packs) : null;
  const letter = criteria.letter && criteria.letter !== "ALL" ? criteria.letter : "";
  const pos = criteria.pos && criteria.pos !== "ALL" ? criteria.pos : "";
  const region = criteria.region && criteria.region !== "ALL" ? criteria.region : "";

  const exact: BrowseWordItem[] = [];
  const prefix: BrowseWordItem[] = [];
  const containsWord: BrowseWordItem[] = [];
  const containsGloss: BrowseWordItem[] = [];

  for (const item of items) {
    if (letter && item.letter !== letter) continue;
    if (packSet && !item.packs.some((p) => packSet.has(p))) continue;
    if (pos && !item.pos.includes(pos)) continue;
    if (region && !item.regions.includes(region)) continue;

    if (!q) {
      exact.push(item);
      continue;
    }

    if (item.word === q) {
      exact.push(item);
    } else if (item.word.startsWith(q)) {
      prefix.push(item);
    } else if (item.word.includes(q)) {
      containsWord.push(item);
    } else if (item.glossLower.includes(qLower)) {
      containsGloss.push(item);
    }
  }

  return q ? [...exact, ...prefix, ...containsWord, ...containsGloss] : exact;
}
