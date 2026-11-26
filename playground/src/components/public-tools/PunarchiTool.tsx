import { useState, useMemo, useCallback } from "react";
import { getLetters, isEngineReady, tt } from "../../lib/engine";
import { useLanguage } from "../../lib/i18n";
import { ToolHeader } from "../common/ToolHeader";
import { CopyButton } from "../common/CopyButton";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Card } from "../ui/card";
import { Textarea } from "../ui/textarea";
import punarchiReviewRaw from "../../generated/punarchi-review-data.json";
import {
  AlertCircle,
  ArrowLeftRight,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Code2,
  ExternalLink,
  FlaskConical,
  GitMerge,
  HelpCircle,
  Layers,
  Play,
  RotateCcw,
  Scissors,
  Search,
  SlidersHorizontal,
  Sparkles,
  XCircle,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Review Catalog Types (compiled by tools/prepare_playground.py)
// ---------------------------------------------------------------------------

interface DeclarativeRuleMeta {
  id: string;
  sutra: number;
  chapter: string;
  stage: number;
  substage: string;
  priority: number;
  transform: string;
  relation: string;
  left_match: string;
  right_match: string;
  action: string;
  optional: boolean;
  poetic: boolean;
  reversible: boolean;
  evidence_layer: string;
}

interface ClosedClassMeta {
  id: string;
  sutra: number;
  stems: string[];
  oblique_map: Record<string, string[]>;
  notes: string;
}

interface GoldenVectorRow {
  id: string;
  op: "punarchi_join" | "punarchi_split_candidates" | "punarchi_rules";
  input: Record<string, unknown>;
  expected?: unknown;
  expected_error?: string;
  dialect: string;
  tags: string[];
  source: string;
}

interface SutraCrosswalkNote {
  summary_ta: string;
  wikisource_pages: number[];
  tolkappiyam_sutras: number[];
}

interface PunarchiReviewCatalog {
  profile: string;
  rule_count: number;
  closed_class_count: number;
  golden_count: number;
  wikisource_page_base?: string;
  sutra_notes?: Record<string, SutraCrosswalkNote>;
  rules: DeclarativeRuleMeta[];
  closed_classes: ClosedClassMeta[];
  chariyais: Array<{
    id: string;
    form: string;
    sutra: number;
    attach_classes: string[];
    post_um: boolean;
    suppress_205: boolean;
  }>;
  case_suffixes: Array<{
    case_number: number;
    form: string;
    sutra: number;
    force_165: boolean;
  }>;
  golden_vectors: GoldenVectorRow[];
}

const REVIEW_DATA = punarchiReviewRaw as unknown as PunarchiReviewCatalog;

function getSutraCrosswalk(sutraNum: number): SutraCrosswalkNote | undefined {
  return REVIEW_DATA.sutra_notes?.[String(sutraNum)];
}

// ---------------------------------------------------------------------------
// Exported Presets (everyday featured + full chapter presets for deep review)
// ---------------------------------------------------------------------------

export interface PunarchiJoinPreset {
  id: string;
  category: string;
  featured?: boolean;
  labelEn: string;
  labelTa: string;
  hintEn: string;
  hintTa: string;
  first: string;
  second: string;
  context?: tt.PunarchiContext;
}

export const PUNARCHI_JOIN_PRESETS: readonly PunarchiJoinPreset[] = [
  {
    id: "uyireeru_162",
    category: "Everyday",
    featured: true,
    labelEn: "மணி + அடி",
    labelTa: "மணி + அடி",
    hintEn: "Glide added (மணியடி)",
    hintTa: "உடம்படுமெய் (மணியடி)",
    first: "மணி",
    second: "அடி",
  },
  {
    id: "urupu_252_maram",
    category: "Everyday",
    featured: true,
    labelEn: "மரம் + ஐ",
    labelTa: "மரம் + ஐ",
    hintEn: "Case suffix (மரத்தை)",
    hintTa: "வேற்றுமை (மரத்தை)",
    first: "மரம்",
    second: "ஐ",
    context: { relation: "vetrumai", subtype: "case_2" },
  },
  {
    id: "panpuppeyar_136",
    category: "Everyday",
    featured: true,
    labelEn: "செம்மை + தாமரை",
    labelTa: "செம்மை + தாமரை",
    hintEn: "Adjective compound (செந்தாமரை)",
    hintTa: "பண்புத்தொகை (செந்தாமரை)",
    first: "செம்மை",
    second: "தாமரை",
    context: { relation: "alvazhi", subtype: "panputhogai" },
  },
  {
    id: "meyyeeru_237_kal",
    category: "Everyday",
    featured: true,
    labelEn: "கல் + தீது",
    labelTa: "கல் + தீது",
    hintEn: "Consonant change (கற்றீது)",
    hintTa: "மெய்யீறு (கற்றீது)",
    first: "கல்",
    second: "தீது",
    context: { relation: "alvazhi" },
  },
  {
    id: "ambiguity_209_pon",
    category: "Everyday",
    featured: true,
    labelEn: "பொன் + தகடு",
    labelTa: "பொன் + தகடு",
    hintEn: "Two meanings (பொன்தகடு / பொற்றகடு)",
    hintTa: "இரு வடிவம் (பொன்தகடு / பொற்றகடு)",
    first: "பொன்",
    second: "தகடு",
    context: { relation: "unspecified" },
  },
  {
    id: "urupu_245_ellaam",
    category: "Everyday",
    featured: true,
    labelEn: "எல்லாம் + ஐ",
    labelTa: "எல்லாம் + ஐ",
    hintEn: "Multi-step (எல்லாவற்றையும்)",
    hintTa: "சாரியை + உம் (எல்லாவற்றையும்)",
    first: "எல்லாம்",
    second: "ஐ",
    context: { relation: "vetrumai", subtype: "case_2", lexical_class: "non_rational_noun" },
  },
  {
    id: "kurriyalugaram_183",
    category: "Uyireeru",
    labelEn: "நாடு + பற்று (183)",
    labelTa: "நாடு + பற்று (183)",
    hintEn: "நாட்டுப்பற்று",
    hintTa: "நாட்டுப்பற்று",
    first: "நாடு",
    second: "பற்று",
    context: { relation: "vetrumai" },
  },
  {
    id: "panpuppeyar_pasumai",
    category: "Padaviyal",
    labelEn: "பசுமை + தமிழ் (136)",
    labelTa: "பசுமை + தமிழ் (136)",
    hintEn: "பைந்தமிழ்",
    hintTa: "பைந்தமிழ்",
    first: "பசுமை",
    second: "தமிழ்",
    context: { relation: "alvazhi", subtype: "panputhogai" },
  },
  {
    id: "urupu_254_filter",
    category: "Urupu",
    labelEn: "நாடு + இன் (254)",
    labelTa: "நாடு + இன் (254)",
    hintEn: "நாட்டின் (blocks *நாட்டினின்)",
    hintTa: "நாட்டின் (*நாட்டினின் தவிர்ப்பு)",
    first: "நாடு",
    second: "இன்",
    context: { relation: "vetrumai", subtype: "case_5" },
  },
  {
    id: "numeral_194",
    category: "Numerals",
    labelEn: "ஒன்பது + பத்து (194)",
    labelTa: "ஒன்பது + பத்து (194)",
    hintEn: "தொண்ணூறு",
    hintTa: "தொண்ணூறு",
    first: "ஒன்பது",
    second: "பத்து",
  },
  {
    id: "poetic_172",
    category: "Poetic",
    labelEn: "நிலா + வந்தது (172 Poetic)",
    labelTa: "நிலா + வந்தது (172 செய்யுள்)",
    hintEn: "Verse shortening",
    hintTa: "செய்யுள் குறுக்கம்",
    first: "நிலா",
    second: "வந்தது",
    context: { relation: "alvazhi", poetic: true },
  },
  {
    id: "poetic_180",
    category: "Poetic",
    labelEn: "அது + அன்று (180 Poetic)",
    labelTa: "அது + அன்று (180 செய்யுள்)",
    hintEn: "அதான்று",
    hintTa: "அதான்று",
    first: "அது",
    second: "அன்று",
    context: { relation: "alvazhi", poetic: true },
  },
  {
    id: "sutra_256_passive",
    category: "Urupu",
    labelEn: "பேய் + கோட்பட்டான் (256)",
    labelTa: "பேய் + கோட்பட்டான் (256)",
    hintEn: "Case-3 passive",
    hintTa: "செயப்பாட்டு வினை",
    first: "பேய்",
    second: "கோட்பட்டான்",
    context: {
      relation: "vetrumai",
      subtype: "case_3",
      lexical_class: "passive_action_compound",
    },
  },
  {
    id: "zwnj_barrier",
    category: "Unicode",
    labelEn: "கல் + ZWNJ + தீது (153)",
    labelTa: "கல் + ZWNJ + தீது (153)",
    hintEn: "Preserves invisible joiner",
    hintTa: "மறை எழுத்து பாதுகாப்பு",
    first: "கல்",
    second: "\u200Cதீது",
  },
];

export const PUNARCHI_SPLIT_PRESETS: readonly {
  surface: string;
  featured?: boolean;
  labelEn: string;
  labelTa: string;
  poetic?: boolean;
}[] = [
  { surface: "மரத்தை", featured: true, labelEn: "மரத்தை", labelTa: "மரத்தை" },
  { surface: "செந்தாமரை", featured: true, labelEn: "செந்தாமரை", labelTa: "செந்தாமரை" },
  { surface: "தொண்ணூறு", featured: true, labelEn: "தொண்ணூறு", labelTa: "தொண்ணூறு" },
  { surface: "பன்னிரண்டு", featured: true, labelEn: "பன்னிரண்டு", labelTa: "பன்னிரண்டு" },
  { surface: "அஃறிணை", featured: true, labelEn: "அஃறிணை", labelTa: "அஃறிணை" },
  { surface: "எல்லாவற்றையும்", featured: true, labelEn: "எல்லாவற்றையும்", labelTa: "எல்லாவற்றையும்" },
  { surface: "கற்றீது", labelEn: "கற்றீது", labelTa: "கற்றீது" },
  { surface: "நாட்டின்கண்", labelEn: "நாட்டின்கண்", labelTa: "நாட்டின்கண்" },
  { surface: "ஸ்ரீராமன்", labelEn: "ஸ்ரீராமன் (Ligature)", labelTa: "ஸ்ரீராமன் (கூட்டெழுத்து)" },
  { surface: "அதான்று", labelEn: "அதான்று (Poetic)", labelTa: "அதான்று (செய்யுள்)", poetic: true },
];

const VETRUMAI_SUBTYPES = [
  { value: "case_2", en: "2nd Case — Object (ஐ)", ta: "இரண்டாம் வேற்றுமை (ஐ)" },
  { value: "case_3", en: "3rd Case — By / With (ஆல் / ஒடு)", ta: "மூன்றாம் வேற்றுமை (ஆல் / ஒடு)" },
  { value: "case_4", en: "4th Case — To / For (கு)", ta: "நான்காம் வேற்றுமை (கு)" },
  { value: "case_5", en: "5th Case — From / Than (இன்)", ta: "ஐந்தாம் வேற்றுமை (இன்)" },
  { value: "case_6", en: "6th Case — Of (அது / ஆது)", ta: "ஆறாம் வேற்றுமை (அது / ஆது)" },
  { value: "case_7", en: "7th Case — In / At (கண்)", ta: "ஏழாம் வேற்றுமை (கண்)" },
] as const;

const ALVAZHI_SUBTYPES = [
  { value: "panputhogai", en: "Quality Compound (பண்புத்தொகை)", ta: "பண்புத்தொகை (செந்தாமரை)" },
  { value: "vinaithogai", en: "Verb Compound (வினைத்தொகை)", ta: "வினைத்தொகை (சுடுசோறு)" },
  { value: "uvamaithogai", en: "Simile Compound (உவமைத்தொகை)", ta: "உவமைத்தொகை (மதிமுகம்)" },
  { value: "ummaithogai", en: "And-Compound (உம்மைத்தொகை)", ta: "உம்மைத்தொகை (இரவுபகல்)" },
  { value: "anmozhi", en: "Metonymic Compound (அன்மொழித்தொகை)", ta: "அன்மொழித்தொகை" },
  { value: "ezhuvai", en: "Subject Phrase (எழுவாய்த்தொடர்)", ta: "எழுவாய்த்தொடர்" },
  { value: "vili", en: "Vocative / Calling (விளித்தொடர்)", ta: "விளித்தொடர்" },
  { value: "peyarecham", en: "Relative Participle (பெயரெச்சம்)", ta: "பெயரெச்சம்" },
  { value: "vinaiyecham", en: "Adverbial Participle (வினையெச்சம்)", ta: "வினையெச்சம்" },
  { value: "vinai_mutru", en: "Finite Verb (வினைமுற்று)", ta: "வினைமுற்று" },
  { value: "kurippu_vinai_mutru", en: "Appellative Verb (குறிப்பு வினைமுற்று)", ta: "குறிப்பு வினைமுற்று" },
  { value: "idaiccol", en: "Particle Phrase (இடைச்சொல்)", ta: "இடைச்சொல் தொடர்" },
  { value: "uriccol", en: "Intensifier Phrase (உரிச்சொல்)", ta: "உரிச்சொல் தொடர்" },
  { value: "adukkuthodar", en: "Reduplication (அடுக்குத்தொடர்)", ta: "அடுக்குத்தொடர்" },
  { value: "imperative", en: "Command / Imperative (ஏவல்)", ta: "ஏவல் வினை" },
  { value: "second_person_verb", en: "Second-Person Verb (முன்னிலை வினை)", ta: "முன்னிலை வினை" },
  { value: "viyankol", en: "Optative / Blessing (வியங்கோள்)", ta: "வியங்கோள் (வாழ்க)" },
  { value: "distributive", en: "Distributive Number (அடுக்கு எண்)", ta: "அடுக்கு எண் (ஒவ்வொன்று)" },
  { value: "ilakkanappoli", en: "Idiom / Inversion (இலக்கணப்போலி)", ta: "இலக்கணப்போலி" },
] as const;

const LEXICAL_CLASSES: readonly { value: string; en: string; ta: string }[] = [
  { value: "rational_noun", en: "Person / Rational Noun (உயர்திணை)", ta: "உயர்திணைப் பெயர்" },
  { value: "non_rational_noun", en: "Thing / Non-Rational Noun (அஃறிணை)", ta: "அஃறிணைப் பெயர்" },
  { value: "common_noun", en: "Common Noun (பொதுப்பெயர்)", ta: "பொதுப்பெயர்" },
  { value: "tree_name", en: "Tree Name (மரப்பெயர் — மா, விளா)", ta: "மரப்பெயர் (மா, விளா)" },
  { value: "taste_puli", en: "Sour Taste 'புளி' (சுவை புளி)", ta: "சுவைப் புளி" },
  { value: "measure_word", en: "Measure Word (அளவுப்பெயர்)", ta: "அளவுப்பெயர்" },
  { value: "quantity_word", en: "Quantity Word (எண்ணளவை)", ta: "எண்ணளவை" },
  { value: "number_word", en: "Number Word (எண்ணுப்பெயர்)", ta: "எண்ணுப்பெயர்" },
  { value: "direction_word", en: "Direction Word (திசைப்பெயர்)", ta: "திசைப்பெயர்" },
  { value: "pronoun", en: "Pronoun (மூவிடப்பெயர்)", ta: "மூவிடப்பெயர்" },
  { value: "demonstrative", en: "Demonstrative (சுட்டு — அ, இ, உ)", ta: "சுட்டுச் சொல்" },
  { value: "interrogative", en: "Question Word (வினா)", ta: "வினாச் சொல்" },
  { value: "branch_name", en: "Clan / Branch Name (கிளைப்பெயர்)", ta: "கிளைப்பெயர்" },
  { value: "quality_noun", en: "Quality / Adjective Noun (பண்புப்பெயர்)", ta: "பண்புப்பெயர் (-மை)" },
  { value: "verbal_noun_root", en: "Root Verbal Noun (முதனிலைத் தொழிற்பெயர்)", ta: "முதனிலைத் தொழிற்பெயர்" },
  { value: "verbal_noun_derived", en: "Derived Verbal Noun (ஆடல், பாடல்)", ta: "விகுதித் தொழிற்பெயர்" },
  { value: "negation_stem", en: "Negation Stem 'இல்' (இல்பொருள்)", ta: "இல் எதிர்மறை" },
  { value: "clitic_particle", en: "Clitic Particle (ஏ, ஓ, அம்ம)", ta: "இடைச்சொல் (ஏ, ஓ, அம்ம)" },
  { value: "locative_particle", en: "Place Particle (அங்கு, இங்கு, எங்கு)", ta: "இடப்பெயர் (அங்கு, இங்கு)" },
  { value: "temporal_particle", en: "Time Particle (ஆண்டு, யாண்டு)", ta: "காலப்பெயர்" },
  { value: "negative_plural_verb", en: "Negative Plural Verb (உண்ணா)", ta: "எதிர்மறைப் பன்மை வினை" },
  { value: "passive_action_compound", en: "Passive Compound (கோட்பட்டான்)", ta: "செயப்பாட்டு வினை" },
  { value: "food_sesame", en: "Sesame Food 'எண்' (எள்)", ta: "உணவுப் பொருள் (எண்)" },
  { value: "swan_ekin", en: "Swan 'எகின்' (அன்னம்)", ta: "எகின் (அன்னம்)" },
  { value: "dice_val", en: "Dice / Board 'வல்' (சூதாட்டம்)", ta: "வல் (சூதாட்டம்)" },
  { value: "cloud_sel", en: "Cloud 'செல்' (மேகம்)", ta: "செல் (மேகம்)" },
  { value: "smith_kol", en: "Blacksmith 'கொல்' (தொழில்)", ta: "கொல் (தொழில்)" },
];

const TRANSFORM_BADGE_STYLES: Record<tt.PunarchiAlterationKind, string> = {
  iyalbu: "bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 border-emerald-500/35",
  thonral: "bg-sky-500/15 text-sky-800 dark:text-sky-300 border-sky-500/35",
  thirithal: "bg-amber-500/15 text-amber-800 dark:text-amber-300 border-amber-500/35",
  keduthal: "bg-rose-500/15 text-rose-800 dark:text-rose-300 border-rose-500/35",
};

const TRANSFORM_LABELS: Record<tt.PunarchiAlterationKind, { en: string; ta: string; descEn: string; descTa: string }> = {
  iyalbu: {
    en: "No Change (Iyalbu)",
    ta: "இயல்பு (மாற்றமில்லை)",
    descEn: "Words join directly without adding, changing, or dropping any letter.",
    descTa: "எந்த எழுத்தும் மாறாமல் இயல்பாக இணையும் (எ.கா: வாழை + மரம் → வாழைமரம்).",
  },
  thonral: {
    en: "Letter Added (Thonral)",
    ta: "தோன்றல் (புதிய எழுத்து)",
    descEn: "A glide, doubled stop, or connecting syllable appears between the words.",
    descTa: "இரு சொற்களுக்கு இடையே புதிய எழுத்து தோன்றும் (எ.கா: மணி + அடி → மணியடி).",
  },
  thirithal: {
    en: "Letter Changed (Thirithal)",
    ta: "திரிதல் (எழுத்து மாற்றம்)",
    descEn: "One or more boundary letters transform into another letter.",
    descTa: "ஓர் எழுத்து வேறோர் எழுத்தாக மாறும் (எ.கா: கல் + தீது → கற்றீது).",
  },
  keduthal: {
    en: "Letter Dropped (Keduthal)",
    ta: "கெடுதல் (எழுத்து நீக்கம்)",
    descEn: "A vowel or consonant at the boundary drops cleanly during joining.",
    descTa: "இணையும்போது ஓர் எழுத்து மறையும் (எ.கா: மரம் + வேர் → மரவேர்).",
  },
};

const CHAPTER_LABELS: Record<tt.PunarchiChapter, { en: string; ta: string; range: string }> = {
  ezhuttiyal: { en: "Sound Rules", ta: "எழுத்தியல்", range: "93–94, 102–108" },
  padaviyal: { en: "Quality Nouns", ta: "பதவியல்", range: "136" },
  uyireeru: { en: "Vowel-Ending", ta: "உயிரீறு", range: "151–203" },
  meyyeeru: { en: "Consonant-Ending", ta: "மெய்யீறு", range: "204–239" },
  urupu: { en: "Case Suffixes", ta: "உருபு புணரியல்", range: "240–257" },
};

const PIPELINE_STAGES = [
  { stage: "1A", title: "Panpuppeyar -மை Cascade (136)", detail: "8-op cascade: ஈறு போதல், இடையுகரம் இ, ஆதி நீடல், அடிஅகரம் ஐ, தன்னொற்று இரட்டல், மெய் திரிதல், இனமிகல்.", file: "closed_class.rs" },
  { stage: "1B", title: "Closed-Class Reductions", detail: "Numerals (188–199), Directions (186–187), Pronouns (247/238), Named stems (168–170, 172–174, 177, 180, 203, 222, 233).", file: "closed_class.rs" },
  { stage: "1C", title: "Kurriyalugaram Pre-Elision (183–185)", detail: "டு/று → ட்டு/ற்று (183), Menthodar → Vanthodar (184), பண்டு/இன்று + ஐ (185).", file: "uyireeru.rs" },
  { stage: "2", title: "Urupu Chariyai Staging (240–257)", detail: "Stages [Stem, Chariyai_1..k, Suffix, (+உம்)] & enforces Sutra 254 (no இன் before இன்).", file: "urupu.rs" },
  { stage: "3A", title: "Pre-Glide Overrides (252, 163, 106)", detail: "Runs before 162: அத்து drops அ after அ (252), deictics அ/இ/உ/எ (163) & ஙனம் (106).", file: "uyireeru.rs" },
  { stage: "3B", title: "Sutra 237 த/ந Pre-Mutation", detail: "ன்/ல்/ண்/ள் + த/ந → ற/ன/ட/ண before left-final rules so *ல்த/*ள்த never occur.", file: "meyyeeru.rs" },
  { stage: "3C", title: "Disjoint Core Vowel / Consonant Rules", detail: "Meyyeeru (206–235) vs Uyireeru (93, 158–182, 200–201).", file: "uyireeru.rs / meyyeeru.rs" },
  { stage: "3D", title: "Thanikkuril Otru (205)", detail: "Short monosyllable + single Mei doubles coda before vowels unless suppress_205.", file: "meyyeeru.rs" },
  { stage: "4", title: "Udalmel Uyir Fusion (204) + NFC", detail: "Fuses pure native Mei + independent Uyir, normalizes NFC, ranks primary + alternates.", file: "pipeline.rs" },
] as const;

const BOUNDARY_FLAGS_REF = [
  { flag: "block_165", role: "Suppresses Vallinam doubling in 165 & 224", setters: "167, 168, 170, 173, 174, 177, 179, 186, 188, 189" },
  { flag: "force_165", role: "Overrides 159 & forces Vallinam doubling", setters: "183, 184, 197, 242.2 (கு), Chariyais உ/அ/அற்று" },
  { flag: "suppress_205", role: "Prevents Thanikkuril coda doubling before vowels", setters: "247.5 (4th/6th case pronouns), 250.3 (அவ்+அற்று), 164.3" },
  { flag: "force_205", role: "Forces coda doubling on appended short Chariyais", setters: "245 (எல்லாநம்), 246 (எல்லார்தம், எல்லீர்நும்)" },
  { flag: "is_short_chariyai_m", role: "Retains ம் instead of Sutra 219 deletion", setters: "202 (அம்), 223 (ஈம்/கம்/உரும்), 245, 246" },
  { flag: "block_209_stop", role: "Keeps ன் natural before content words", setters: "212, 238, 247, 248, 251, 254" },
  { flag: "is_chariyai_attu", role: "Routes அத்து to Stage 3A Sutra 252 before 162", setters: "244 (மரம் + அத்து, மக + அத்து)" },
  { flag: "triggered_237", role: "Passes (left_final, orig_right) from 3B to 3C", setters: "237 (ன்/ல்/ண்/ள் + த/ந)" },
  { flag: "block_229", role: "Retains ற் instead of Sutra 229 deletion", setters: "186 (மேற்கு + திசை → மேற்றிசை)" },
] as const;

const SUTRA_237_MATRIX = [
  { left: "பொன் + தீது", alvazhi: "பொன்றீது", vetrumai: "பொற்றீது", sutras: "237 + 209" },
  { left: "பொன் + நன்று", alvazhi: "பொன்னன்று", vetrumai: "பொன்னன்று", sutras: "237 + 209" },
  { left: "மான் + நன்று", alvazhi: "மானன்று", vetrumai: "மானன்று", sutras: "237 + 210" },
  { left: "மண் + தீது", alvazhi: "மண்டீது", vetrumai: "மட்டீது", sutras: "237 + 209" },
  { left: "தூண் + நன்று", alvazhi: "தூணன்று", vetrumai: "தூணன்று", sutras: "237 + 210" },
  { left: "கல் + தீது", alvazhi: "கற்றீது / கஃறீது", vetrumai: "கற்றீது", sutras: "237 + 227/228" },
  { left: "பால் + தீது", alvazhi: "பாறீது", vetrumai: "பாற்றீது", sutras: "237 + 229/227" },
  { left: "பால் + நன்று", alvazhi: "பானன்று", vetrumai: "பானன்று", sutras: "237 + 229" },
  { left: "முள் + தீது", alvazhi: "முட்டீது / முஃடீது", vetrumai: "முட்டீது", sutras: "237 + 227/228" },
  { left: "வாள் + நன்று", alvazhi: "வாணன்று", vetrumai: "வாணன்று", sutras: "237 + 229" },
] as const;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function deepEqual(a: unknown, b: unknown): boolean {
  if (a === b) return true;
  if (a === null || b === null || typeof a !== "object" || typeof b !== "object") return false;
  if (Array.isArray(a) || Array.isArray(b)) {
    if (!Array.isArray(a) || !Array.isArray(b) || a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) if (!deepEqual(a[i], b[i])) return false;
    return true;
  }
  const objA = a as Record<string, unknown>;
  const objB = b as Record<string, unknown>;
  const keysA = Object.keys(objA);
  if (keysA.length !== Object.keys(objB).length) return false;
  for (const key of keysA) {
    if (!Object.prototype.hasOwnProperty.call(objB, key) || !deepEqual(objA[key], objB[key])) {
      return false;
    }
  }
  return true;
}

function utf8ByteLength(str: string): number {
  return new TextEncoder().encode(str).length;
}

function friendlyContextHint(req: string, lang: "ta" | "en"): string {
  if (req === "vetrumai") return lang === "ta" ? "வேற்றுமைப் பொருளில் (Case)" : "When used as a case/possessive compound (Vetrumai)";
  if (req === "alvazhi") return lang === "ta" ? "அல்வழிப் பொருளில் (Descriptive)" : "When used as a descriptive phrase (Alvazhi)";
  if (req === "rational_noun") return lang === "ta" ? "உயர்திணைப் பொருளில் (மனிதர்கள்)" : "When referring to people (Rational noun)";
  if (req === "panputhogai") return lang === "ta" ? "பண்புத்தொகையாக" : "As a quality compound (Panputhogai)";
  return req;
}

type PunarchiTab = "join" | "split" | "sutras" | "notes";

interface GoldenRunItem {
  row: GoldenVectorRow;
  passed: boolean;
  actual?: unknown;
  error?: string;
}

interface PunarchiToolProps {
  engineReady?: boolean;
}

export function PunarchiTool({ engineReady }: PunarchiToolProps) {
  const { language, t } = useLanguage();
  const ready = engineReady ?? isEngineReady();
  const isTa = language === "ta";

  const [activeTab, setActiveTab] = useState<PunarchiTab>("join");

  // --- Join Lab state ---
  const [first, setFirst] = useState("மரம்");
  const [second, setSecond] = useState("ஐ");
  const [relation, setRelation] = useState<tt.PunarchiRelation>("vetrumai");
  const [subtype, setSubtype] = useState<string>("case_2");
  const [lexicalClass, setLexicalClass] = useState<string>("");
  const [poetic, setPoetic] = useState<boolean>(false);
  const [showAdvancedJoin, setShowAdvancedJoin] = useState<boolean>(false);
  const [showDevDetails, setShowDevDetails] = useState<boolean>(false);
  const [allowInvalidCombo, setAllowInvalidCombo] = useState<boolean>(false);
  const [showJoinJson, setShowJoinJson] = useState<boolean>(false);
  const [expandedAltIdx, setExpandedAltIdx] = useState<number | null>(null);
  const [showBatchTester, setShowBatchTester] = useState<boolean>(false);
  const [batchText, setBatchText] = useState<string>(
    "மணி + அடி\nபொன் + தகடு\nகல் + தீது\nசெம்மை + தாமரை\nஎல்லாம் + ஐ\nநாடு + இன்"
  );

  // --- Split Lab state ---
  const [splitSurface, setSplitSurface] = useState("மரத்தை");
  const [splitPoetic, setSplitPoetic] = useState(false);
  const [showSplitTech, setShowSplitTech] = useState(false);
  const [expandedSplitIdx, setExpandedSplitIdx] = useState<number | null>(null);

  // --- 117-Sutra Explorer state ---
  const [sutraChapter, setSutraChapter] = useState<string>("all");
  const [onlyEditionNotes, setOnlyEditionNotes] = useState<boolean>(false);
  const [sutraSearch, setSutraSearch] = useState<string>("");
  const [selectedSutraNum, setSelectedSutraNum] = useState<number>(252);
  const [showSutraDevSpecs, setShowSutraDevSpecs] = useState<boolean>(false);

  // --- Notes & Dev Verification state ---
  const [showDevArchitecture, setShowDevArchitecture] = useState<boolean>(false);
  const [goldenRun, setGoldenRun] = useState<{
    elapsedMs: number;
    passed: number;
    failed: number;
    items: GoldenRunItem[];
  } | null>(null);
  const [goldenFilterTag, setGoldenFilterTag] = useState<string>("all");
  const [goldenOnlyFailed, setGoldenOnlyFailed] = useState<boolean>(false);

  // --- Live 117-Sutra Inventory from WASM ---
  const allSutras = useMemo<tt.PunarchiSutraInventoryEntry[]>(() => {
    if (!ready) return [];
    try {
      return tt.punarchi_rules({ profile: "nannool-v1" });
    } catch {
      return [];
    }
  }, [ready]);

  const sutraByNum = useMemo(() => {
    const map = new Map<number, tt.PunarchiSutraInventoryEntry>();
    for (const s of allSutras) map.set(s.sutra, s);
    return map;
  }, [allSutras]);

  // --- Derived Indexes from Review Catalog ---
  const rulesBySutra = useMemo(() => {
    const map = new Map<number, DeclarativeRuleMeta[]>();
    for (const r of REVIEW_DATA.rules) {
      const list = map.get(r.sutra) ?? [];
      list.push(r);
      map.set(r.sutra, list);
    }
    return map;
  }, []);

  const closedClassesBySutra = useMemo(() => {
    const map = new Map<number, ClosedClassMeta[]>();
    for (const cc of REVIEW_DATA.closed_classes) {
      const list = map.get(cc.sutra) ?? [];
      list.push(cc);
      map.set(cc.sutra, list);
    }
    return map;
  }, []);

  const witnessesBySutra = useMemo(() => {
    const map = new Map<number, GoldenVectorRow[]>();
    for (const row of REVIEW_DATA.golden_vectors) {
      if (row.op !== "punarchi_join" || !row.expected || typeof row.expected !== "object") continue;
      const exp = row.expected as tt.PunarchiJoinResult;
      const sutras = new Set<number>();
      for (const st of exp.steps ?? []) sutras.add(st.sutra);
      for (const alt of exp.alternatives ?? []) {
        for (const st of alt.steps ?? []) sutras.add(st.sutra);
      }
      for (const s of sutras) {
        const list = map.get(s) ?? [];
        list.push(row);
        map.set(s, list);
      }
    }
    return map;
  }, []);

  const availableSubtypes = useMemo(() => {
    if (allowInvalidCombo || relation === "unspecified") {
      return [...VETRUMAI_SUBTYPES, ...ALVAZHI_SUBTYPES];
    }
    return relation === "vetrumai" ? [...VETRUMAI_SUBTYPES] : [...ALVAZHI_SUBTYPES];
  }, [relation, allowInvalidCombo]);

  const handleRelationChange = (nextRel: tt.PunarchiRelation) => {
    setRelation(nextRel);
    if (!allowInvalidCombo && subtype) {
      const isVetSub = VETRUMAI_SUBTYPES.some((s) => s.value === subtype);
      if (nextRel === "vetrumai" && !isVetSub) setSubtype("");
      if (nextRel === "alvazhi" && isVetSub) setSubtype("");
    }
  };

  const activeContext = useMemo<tt.PunarchiContext>(() => {
    const ctx: tt.PunarchiContext = {};
    if (relation !== "unspecified") ctx.relation = relation;
    if (subtype) ctx.subtype = subtype;
    if (lexicalClass) ctx.lexical_class = lexicalClass;
    if (poetic) ctx.poetic = true;
    return ctx;
  }, [relation, subtype, lexicalClass, poetic]);

  const activeAdvancedCount = (subtype ? 1 : 0) + (lexicalClass ? 1 : 0);

  // --- Live Join Evaluation ---
  const joinEval = useMemo(() => {
    if (!ready) return { result: null as tt.PunarchiJoinResult | null, error: null as string | null };
    try {
      const result = tt.punarchi_join(first, second, {
        context: activeContext,
        profile: "nannool-v1",
      });
      return { result, error: null };
    } catch (err) {
      return { result: null, error: err instanceof Error ? err.message : String(err) };
    }
  }, [ready, first, second, activeContext]);

  const batchResults = useMemo(() => {
    if (!ready || !showBatchTester) return [];
    return batchText
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const parts = line.split("+").map((p) => p.trim());
        if (parts.length !== 2) {
          return { line, first: line, second: "", result: null, error: "Format: word1 + word2" };
        }
        try {
          const result = tt.punarchi_join(parts[0], parts[1], {
            context: activeContext,
            profile: "nannool-v1",
          });
          return { line, first: parts[0], second: parts[1], result, error: null };
        } catch (err) {
          return {
            line,
            first: parts[0],
            second: parts[1],
            result: null,
            error: err instanceof Error ? err.message : String(err),
          };
        }
      });
  }, [ready, showBatchTester, batchText, activeContext]);

  // --- Live Split Evaluation ---
  const splitByteLen = useMemo(() => utf8ByteLength(splitSurface), [splitSurface]);
  const splitUnits = useMemo(() => (ready ? getLetters(splitSurface) : []), [ready, splitSurface]);
  const splitEval = useMemo(() => {
    if (!ready) return { candidates: [] as tt.PunarchiSplitCandidate[], error: null as string | null };
    try {
      const candidates = tt.punarchi_split_candidates(splitSurface, {
        profile: "nannool-v1",
        poetic: splitPoetic,
      });
      return { candidates, error: null };
    } catch (err) {
      return { candidates: [], error: err instanceof Error ? err.message : String(err) };
    }
  }, [ready, splitSurface, splitPoetic]);

  // --- Filtered Sutras ---
  const filteredSutras = useMemo(() => {
    const q = sutraSearch.trim().toLowerCase();
    return allSutras.filter((entry) => {
      if (sutraChapter === "prereqs") {
        if (entry.chapter !== "ezhuttiyal" && entry.chapter !== "padaviyal") return false;
      } else if (sutraChapter !== "all" && entry.chapter !== sutraChapter) {
        return false;
      }
      if (onlyEditionNotes && !entry.edition_note) return false;
      if (!q) return true;
      if (String(entry.sutra).includes(q)) return true;
      if (entry.summary.toLowerCase().includes(q)) return true;
      if (entry.edition_note?.toLowerCase().includes(q)) return true;
      const cw = getSutraCrosswalk(entry.sutra);
      if (cw?.summary_ta?.toLowerCase().includes(q)) return true;
      if (cw?.tolkappiyam_sutras?.some((n) => String(n).includes(q))) return true;
      const mappedRules = rulesBySutra.get(entry.sutra) ?? [];
      if (mappedRules.some((r) => r.id.toLowerCase().includes(q))) return true;
      const mappedClasses = closedClassesBySutra.get(entry.sutra) ?? [];
      if (
        mappedClasses.some(
          (cc) => cc.id.toLowerCase().includes(q) || cc.stems.some((st) => st.toLowerCase().includes(q))
        )
      ) {
        return true;
      }
      const mappedW = witnessesBySutra.get(entry.sutra) ?? [];
      if (
        mappedW.some((w) => {
          const inp = w.input as { first?: string; second?: string };
          return (
            inp.first?.toLowerCase().includes(q) || inp.second?.toLowerCase().includes(q)
          );
        })
      ) {
        return true;
      }
      return false;
    });
  }, [allSutras, sutraChapter, onlyEditionNotes, sutraSearch, rulesBySutra, closedClassesBySutra, witnessesBySutra]);

  const selectedSutraEntry = useMemo(
    () => allSutras.find((e) => e.sutra === selectedSutraNum) ?? filteredSutras[0] ?? null,
    [allSutras, selectedSutraNum, filteredSutras]
  );

  // --- Cross-Tab Helpers ---
  const jumpToSutra = useCallback((sutraNum: number) => {
    setSelectedSutraNum(sutraNum);
    setSutraChapter("all");
    setOnlyEditionNotes(false);
    setSutraSearch("");
    setActiveTab("sutras");
  }, []);

  const loadIntoJoinLab = useCallback(
    (nextFirst: string, nextSecond: string, ctx?: tt.PunarchiContext) => {
      setFirst(nextFirst);
      setSecond(nextSecond);
      setRelation(ctx?.relation ?? "unspecified");
      setSubtype(ctx?.subtype ?? "");
      setLexicalClass(ctx?.lexical_class ?? "");
      setPoetic(Boolean(ctx?.poetic));
      setExpandedAltIdx(null);
      setActiveTab("join");
    },
    []
  );

  const applyRequiredContext = useCallback((req: string) => {
    if (req === "vetrumai" || req === "alvazhi") {
      setRelation(req);
      setSubtype("");
    } else if (VETRUMAI_SUBTYPES.some((s) => s.value === req)) {
      setRelation("vetrumai");
      setSubtype(req);
    } else if (ALVAZHI_SUBTYPES.some((s) => s.value === req)) {
      setRelation("alvazhi");
      setSubtype(req);
    } else if (LEXICAL_CLASSES.some((c) => c.value === req)) {
      setLexicalClass(req);
    }
  }, []);

  const runBrowserGoldenSuite = useCallback(() => {
    if (!ready) return;
    const t0 = performance.now();
    let passed = 0;
    let failed = 0;
    const items: GoldenRunItem[] = [];
    for (const row of REVIEW_DATA.golden_vectors) {
      try {
        const actual = tt.execute({ op: row.op, input: row.input });
        if (row.expected_error) {
          failed += 1;
          items.push({ row, passed: false, actual, error: `Expected error: ${row.expected_error}` });
        } else {
          const ok = deepEqual(actual, row.expected);
          if (ok) passed += 1;
          else failed += 1;
          items.push({ row, passed: ok, actual });
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        if (row.expected_error) {
          const ok = msg === row.expected_error;
          if (ok) passed += 1;
          else failed += 1;
          items.push({ row, passed: ok, error: msg });
        } else {
          failed += 1;
          items.push({ row, passed: false, error: msg });
        }
      }
    }
    setGoldenRun({ elapsedMs: performance.now() - t0, passed, failed, items });
  }, [ready]);

  const editionNoteCount = useMemo(
    () => allSutras.filter((s) => Boolean(s.edition_note)).length,
    [allSutras]
  );

  const goldenTags = useMemo(() => {
    const s = new Set<string>();
    for (const row of REVIEW_DATA.golden_vectors) for (const tag of row.tags) s.add(tag);
    return ["all", ...Array.from(s).sort()];
  }, []);

  const filteredGoldenItems = useMemo(() => {
    if (!goldenRun) return [];
    return goldenRun.items.filter((it) => {
      if (goldenOnlyFailed && it.passed) return false;
      if (goldenFilterTag !== "all" && !it.row.tags.includes(goldenFilterTag)) return false;
      return true;
    });
  }, [goldenRun, goldenFilterTag, goldenOnlyFailed]);

  const renderTransformBadge = (kind: tt.PunarchiAlterationKind) => (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${TRANSFORM_BADGE_STYLES[kind]}`}
    >
      {isTa ? TRANSFORM_LABELS[kind].ta : TRANSFORM_LABELS[kind].en}
    </span>
  );

  // Friendly, plain-language step trace (hides raw rule_id unless showDevDetails is ON)
  const renderFriendlySteps = (steps: tt.PunarchiDerivationStep[], showRawIds: boolean) => (
    <ol className="space-y-2.5">
      {steps.map((st, idx) => {
        const sutraMeta = sutraByNum.get(st.sutra);
        const sutraNote = getSutraCrosswalk(st.sutra);
        const stepSummary = isTa
          ? sutraNote?.summary_ta || sutraMeta?.summary
          : sutraMeta?.summary;
        return (
          <li
            key={`${st.sutra}-${st.rule_id}-${idx}`}
            className="p-3 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] space-y-1.5"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2 font-tamil text-base">
                <span className="w-5 h-5 rounded-full bg-[var(--bg-raised)] border border-[var(--border-line)] text-[11px] font-semibold text-[var(--color-muted)] inline-flex items-center justify-center shrink-0">
                  {idx + 1}
                </span>
                <span className="text-[var(--color-muted)]">{st.before}</span>
                <ArrowRight className="w-4 h-4 text-[var(--color-semman)] shrink-0" />
                <span className="font-bold text-[var(--color-mai)]">{st.after}</span>
              </div>

              <div className="flex flex-wrap items-center gap-1.5">
                {renderTransformBadge(st.transform)}
                <button
                  type="button"
                  onClick={() => jumpToSutra(st.sutra)}
                  className="px-2.5 py-0.5 rounded-full bg-[var(--color-semman-light)] text-[var(--color-semman)] text-[11px] font-semibold hover:underline cursor-pointer"
                  title={isTa ? "இந்த நூற்பாவைப் படிக்க" : "Read this Nannūl rule"}
                >
                  {isTa ? `நன்னூல் ${st.sutra} →` : `Nannūl ${st.sutra} →`}
                </button>
              </div>
            </div>

            {stepSummary && (
              <p className="text-xs text-[var(--color-muted)] pl-7 leading-relaxed font-tamil">
                {stepSummary}
              </p>
            )}

            {showRawIds && (
              <div className="pl-7 flex flex-wrap items-center gap-2 text-[11px] font-mono text-[var(--color-muted)]">
                <span>Stage {st.stage}</span>
                <span>·</span>
                <code>{st.rule_id}</code>
              </div>
            )}
          </li>
        );
      })}
    </ol>
  );

  const featuredJoinPresets = useMemo(
    () => PUNARCHI_JOIN_PRESETS.filter((p) => p.featured),
    []
  );
  const extraJoinPresets = useMemo(
    () => PUNARCHI_JOIN_PRESETS.filter((p) => !p.featured),
    []
  );
  const featuredSplitPresets = useMemo(
    () => PUNARCHI_SPLIT_PRESETS.filter((p) => p.featured),
    []
  );
  const extraSplitPresets = useMemo(
    () => PUNARCHI_SPLIT_PRESETS.filter((p) => !p.featured),
    []
  );

  return (
    <div className="space-y-6">
      <ToolHeader title={t.tools.punarchi.title} description={t.tools.punarchi.desc} />

      {/* Clean 4-Tab Bar */}
      <div className="inline-flex flex-wrap items-center gap-1 p-1 rounded-xl bg-[var(--bg-raised)] border border-[var(--border-line)]">
        {(
          [
            { id: "join", icon: GitMerge, label: t.tools.punarchi.tabJoin },
            { id: "split", icon: Scissors, label: t.tools.punarchi.tabSplit },
            { id: "sutras", icon: BookOpen, label: t.tools.punarchi.tabSutras },
            { id: "notes", icon: HelpCircle, label: t.tools.punarchi.tabNotes },
          ] as const
        ).map(({ id, icon: Icon, label }) => (
          <button
            key={id}
            type="button"
            onClick={() => setActiveTab(id)}
            className={`px-4 py-2 min-h-[40px] rounded-lg text-xs sm:text-sm font-medium inline-flex items-center gap-1.5 transition-colors cursor-pointer ${
              activeTab === id
                ? "bg-[var(--bg-surface)] text-[var(--color-semman)] font-semibold shadow-xs"
                : "text-[var(--color-muted)] hover:text-[var(--color-mai)]"
            }`}
          >
            <Icon className="w-4 h-4" />
            <span>{label}</span>
          </button>
        ))}
      </div>

      {/* ================================================================= */}
      {/* TAB 1: JOIN WORDS (Simple First, Power Options One Click Away)    */}
      {/* ================================================================= */}
      {activeTab === "join" && (
        <div className="space-y-5">
          {/* Main Hero Input Card */}
          <Card className="p-5 sm:p-6 space-y-5">
            {/* Two Big Friendly Word Inputs */}
            <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr] gap-3 items-end">
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-[var(--color-mai)]">
                  {t.tools.punarchi.firstLabel}
                </label>
                <input
                  type="text"
                  value={first}
                  onChange={(e) => setFirst(e.target.value)}
                  placeholder="மரம்"
                  className="w-full px-4 py-3 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] font-tamil text-lg sm:text-xl text-[var(--color-mai)] focus:outline-none focus:border-[var(--color-semman)]"
                />
              </div>

              <div className="flex items-center justify-center md:pb-2 gap-2">
                <span className="text-xl font-bold text-[var(--color-semman)]">+</span>
                <button
                  type="button"
                  onClick={() => {
                    setFirst(second);
                    setSecond(first);
                  }}
                  title={isTa ? "சொற்களை இடமாற்று" : "Swap words"}
                  className="p-1.5 rounded-lg border border-[var(--border-line)] text-[var(--color-muted)] hover:text-[var(--color-semman)] hover:border-[var(--color-semman)] cursor-pointer"
                >
                  <ArrowLeftRight className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-[var(--color-mai)]">
                  {t.tools.punarchi.secondLabel}
                </label>
                <input
                  type="text"
                  value={second}
                  onChange={(e) => setSecond(e.target.value)}
                  placeholder="ஐ"
                  className="w-full px-4 py-3 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] font-tamil text-lg sm:text-xl text-[var(--color-mai)] focus:outline-none focus:border-[var(--color-semman)]"
                />
              </div>
            </div>

            {/* Everyday Quick Try Chips */}
            <div className="space-y-2">
              <div className="text-xs font-medium text-[var(--color-muted)]">
                {t.tools.punarchi.presetsLabel}
              </div>
              <div className="flex flex-wrap gap-2">
                {featuredJoinPresets.map((preset) => {
                  const isCurrent = first === preset.first && second === preset.second;
                  return (
                    <button
                      key={preset.id}
                      type="button"
                      onClick={() => loadIntoJoinLab(preset.first, preset.second, preset.context)}
                      className={`px-3 py-1.5 rounded-xl text-xs border transition-colors cursor-pointer font-tamil flex items-center gap-1.5 ${
                        isCurrent
                          ? "bg-[var(--color-semman-light)] border-[var(--color-semman)] text-[var(--color-semman)] font-semibold"
                          : "bg-[var(--bg-canvas)] border-[var(--border-line)] text-[var(--color-mai)] hover:border-[var(--color-semman)]"
                      }`}
                    >
                      <span>{isTa ? preset.labelTa : preset.labelEn}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Simple Meaning Selector (3 plain pills + Poetry toggle) */}
            <div className="pt-3 border-t border-[var(--border-line)] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs font-semibold text-[var(--color-muted)] mr-1">
                  {t.tools.punarchi.relationLabel}:
                </span>
                {(
                  [
                    {
                      id: "unspecified" as const,
                      en: "Auto",
                      ta: "தானாக",
                      tip: isTa ? "பொருத்தமான அனைத்தையும் காட்டு" : "Show best & alternate forms",
                    },
                    {
                      id: "vetrumai" as const,
                      en: "Case / Of (வேற்றுமை)",
                      ta: "வேற்றுமை",
                      tip: isTa ? "ஐ, ஆல், கு, இன், அது, கண்" : "Case suffix or possessive relation",
                    },
                    {
                      id: "alvazhi" as const,
                      en: "Phrase / Compound (அல்வழி)",
                      ta: "அல்வழி",
                      tip: isTa ? "பண்புத்தொகை, வினைத்தொகை, தொடர்" : "Descriptive phrase or compound",
                    },
                  ] as const
                ).map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    title={opt.tip}
                    onClick={() => handleRelationChange(opt.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors cursor-pointer ${
                      relation === opt.id
                        ? "bg-[var(--color-semman)] text-[#faf7f2] border-[var(--color-semman)] font-semibold"
                        : "bg-[var(--bg-canvas)] border-[var(--border-line)] text-[var(--color-mai)] hover:border-[var(--color-semman)]"
                    }`}
                  >
                    {isTa ? opt.ta : opt.en}
                  </button>
                ))}

                <button
                  type="button"
                  onClick={() => setPoetic((v) => !v)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border inline-flex items-center gap-1.5 transition-colors cursor-pointer ${
                    poetic
                      ? "bg-amber-500/20 text-amber-900 dark:text-amber-200 border-amber-500/50 font-semibold"
                      : "bg-[var(--bg-canvas)] border-[var(--border-line)] text-[var(--color-muted)] hover:text-[var(--color-mai)]"
                  }`}
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>{t.tools.punarchi.poeticLabel}</span>
                </button>
              </div>

              <button
                type="button"
                onClick={() => setShowAdvancedJoin((v) => !v)}
                className="text-xs font-medium text-[var(--color-semman)] hover:underline inline-flex items-center gap-1.5 cursor-pointer self-start sm:self-auto"
              >
                <SlidersHorizontal className="w-3.5 h-3.5" />
                <span>
                  {isTa ? "மேம்பட்ட இலக்கணத் தேர்வுகள்" : "Advanced Grammar Options"}
                  {activeAdvancedCount > 0 ? ` (${activeAdvancedCount})` : ""}
                </span>
                {showAdvancedJoin ? (
                  <ChevronDown className="w-3.5 h-3.5" />
                ) : (
                  <ChevronRight className="w-3.5 h-3.5" />
                )}
              </button>
            </div>

            {/* Collapsible Advanced Grammar & Testing Controls */}
            {showAdvancedJoin && (
              <div className="p-4 rounded-xl bg-[var(--bg-raised)]/50 border border-[var(--border-line)] space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <label className="block text-xs font-semibold text-[var(--color-muted)]">
                      {t.tools.punarchi.subtypeLabel}
                    </label>
                    <select
                      value={subtype}
                      onChange={(e) => setSubtype(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg bg-[var(--bg-canvas)] border border-[var(--border-line)] text-xs text-[var(--color-mai)]"
                    >
                      <option value="">
                        {isTa ? "(குறிப்பிடப்படவில்லை — இயல்பு)" : "(Any / Not specified)"}
                      </option>
                      {availableSubtypes.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {isTa ? opt.ta : opt.en}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="space-y-1.5">
                    <label className="block text-xs font-semibold text-[var(--color-muted)]">
                      {t.tools.punarchi.lexicalClassLabel}
                    </label>
                    <select
                      value={lexicalClass}
                      onChange={(e) => setLexicalClass(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg bg-[var(--bg-canvas)] border border-[var(--border-line)] text-xs text-[var(--color-mai)]"
                    >
                      <option value="">
                        {isTa ? "(பொதுச் சொல் — சிறப்பு இல்லை)" : "(General word — none)"}
                      </option>
                      {LEXICAL_CLASSES.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {isTa ? opt.ta : opt.en}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Extra Chapter & Edge-Case Presets */}
                <div className="space-y-1.5">
                  <div className="text-[11px] font-semibold uppercase tracking-wide text-[var(--color-muted)]">
                    {isTa ? "கூடுதல் சிறப்பு எடுத்துக்காட்டுகள்" : "More Nannūl Chapter & Edge-Case Presets"}
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {extraJoinPresets.map((preset) => (
                      <button
                        key={preset.id}
                        type="button"
                        onClick={() => loadIntoJoinLab(preset.first, preset.second, preset.context)}
                        className="px-2.5 py-1 rounded-lg text-xs border border-[var(--border-line)] bg-[var(--bg-canvas)] text-[var(--color-mai)] hover:border-[var(--color-semman)] cursor-pointer font-tamil"
                      >
                        {isTa ? preset.labelTa : preset.labelEn}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Utility & Dev Toggles */}
                <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-[var(--border-line)] text-xs">
                  <div className="flex flex-wrap items-center gap-4">
                    <label className="inline-flex items-center gap-1.5 text-[var(--color-muted)] cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={showDevDetails}
                        onChange={(e) => setShowDevDetails(e.target.checked)}
                        className="rounded accent-[var(--color-semman)]"
                      />
                      <span>{isTa ? "தொழில்நுட்ப விதி ID காட்டு" : "Show rule IDs & stages"}</span>
                    </label>
                    <label className="inline-flex items-center gap-1.5 text-[var(--color-muted)] cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={allowInvalidCombo}
                        onChange={(e) => setAllowInvalidCombo(e.target.checked)}
                        className="rounded accent-[var(--color-semman)]"
                      />
                      <span>
                        {isTa ? "தவறான இணைப்பைச் சோதி" : "Allow invalid combo (error test)"}
                      </span>
                    </label>
                  </div>

                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => setShowBatchTester((v) => !v)}
                      className="text-[var(--color-semman)] hover:underline inline-flex items-center gap-1 cursor-pointer"
                    >
                      <FlaskConical className="w-3.5 h-3.5" />
                      <span>
                        {showBatchTester
                          ? isTa
                            ? "தொகுதி சோதனையை மறை"
                            : "Hide Batch Tester"
                          : isTa
                            ? "பல சொற்களை ஒரே நேரத்தில் சோதி"
                            : "Test Multiple Pairs"}
                      </span>
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setRelation("unspecified");
                        setSubtype("");
                        setLexicalClass("");
                        setPoetic(false);
                        setAllowInvalidCombo(false);
                      }}
                      className="text-[var(--color-muted)] hover:text-[var(--color-semman)] inline-flex items-center gap-1 cursor-pointer"
                    >
                      <RotateCcw className="w-3 h-3" />
                      <span>{t.tools.punarchi.resetContext}</span>
                    </button>
                  </div>
                </div>
              </div>
            )}
          </Card>

          {/* Join Result Hero Card */}
          {joinEval.error ? (
            <Card className="p-4 border-rose-500/40 bg-rose-500/10 flex items-start gap-2.5 text-sm text-rose-800 dark:text-rose-200">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <div>
                <div className="font-semibold">
                  {isTa ? "சரிபார்க்க வேண்டிய உள்ளீடு" : "Please check your selection"}
                </div>
                <p className="text-xs mt-0.5">{joinEval.error}</p>
              </div>
            </Card>
          ) : (
            joinEval.result && (
              <Card className="p-5 sm:p-6 space-y-5">
                {/* Result Banner */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[var(--border-line)]">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs font-medium text-[var(--color-muted)]">
                        {t.tools.punarchi.primaryOutput}
                      </span>
                      {renderTransformBadge(joinEval.result.transform)}
                    </div>
                    <div className="font-tamil text-3xl sm:text-4xl font-bold text-[var(--color-mai)] tracking-wide">
                      {joinEval.result.surface}
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-2">
                    <CopyButton text={joinEval.result.surface} size="sm" variant="outline" />
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setSplitSurface(joinEval.result!.surface);
                        setSplitPoetic(poetic);
                        setExpandedSplitIdx(null);
                        setActiveTab("split");
                      }}
                    >
                      <Scissors className="w-3.5 h-3.5 mr-1.5" />
                      {t.tools.punarchi.sendToSplit}
                    </Button>
                    {showDevDetails && (
                      <Button size="sm" variant="ghost" onClick={() => setShowJoinJson((v) => !v)}>
                        <Code2 className="w-3.5 h-3.5 mr-1" />
                        JSON
                      </Button>
                    )}
                  </div>
                </div>

                {/* Friendly Step-by-Step Explanation */}
                <div className="space-y-2.5">
                  <div className="text-xs font-semibold text-[var(--color-muted)]">
                    {t.tools.punarchi.derivationSteps}
                  </div>
                  {renderFriendlySteps(joinEval.result.steps, showDevDetails)}
                </div>

                {/* Other Valid Forms */}
                {joinEval.result.alternatives.length > 0 && (
                  <div className="space-y-2.5 pt-3 border-t border-[var(--border-line)]">
                    <div className="text-xs font-semibold text-[var(--color-muted)]">
                      {t.tools.punarchi.alternativesHeading} ({joinEval.result.alternatives.length})
                    </div>
                    <div className="space-y-2">
                      {joinEval.result.alternatives.map((alt, idx) => {
                        const isOpen = expandedAltIdx === idx;
                        return (
                          <div
                            key={`${alt.surface}-${idx}`}
                            className="rounded-xl border border-[var(--border-line)] bg-[var(--bg-raised)]/35 overflow-hidden"
                          >
                            <div className="p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
                              <button
                                type="button"
                                onClick={() => setExpandedAltIdx(isOpen ? null : idx)}
                                className="flex flex-wrap items-center gap-2 text-left cursor-pointer"
                              >
                                {isOpen ? (
                                  <ChevronDown className="w-4 h-4 text-[var(--color-muted)]" />
                                ) : (
                                  <ChevronRight className="w-4 h-4 text-[var(--color-muted)]" />
                                )}
                                <span className="font-tamil text-xl font-bold text-[var(--color-mai)]">
                                  {alt.surface}
                                </span>
                                {renderTransformBadge(alt.transform)}
                                {alt.required_context && (
                                  <span className="text-xs text-[var(--color-muted)]">
                                    — {friendlyContextHint(alt.required_context, language)}
                                  </span>
                                )}
                                {!alt.required_context && alt.poetic && (
                                  <Badge variant="sandhanam" className="text-[11px]">
                                    {isTa ? "செய்யுள் வடிவம்" : "Poetic variant"}
                                  </Badge>
                                )}
                                {!alt.required_context && !alt.poetic && alt.optional_variant && (
                                  <Badge variant="outline" className="text-[11px]">
                                    {isTa ? "மாற்று வடிவம்" : "Optional variant"}
                                  </Badge>
                                )}
                              </button>

                              <div className="flex items-center gap-1.5">
                                {alt.required_context && (
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => applyRequiredContext(alt.required_context!)}
                                  >
                                    {isTa ? "இதைப் பயன்படுத்து" : "Use this meaning"}
                                  </Button>
                                )}
                                <CopyButton text={alt.surface} size="sm" variant="ghost" />
                              </div>
                            </div>

                            {isOpen && (
                              <div className="px-3.5 pb-3.5 pt-2 border-t border-[var(--border-line)]/60">
                                {renderFriendlySteps(alt.steps, showDevDetails)}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {showDevDetails && showJoinJson && (
                  <div className="pt-2 border-t border-[var(--border-line)] space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-[var(--color-muted)]">
                        Raw Engine JSON
                      </span>
                      <CopyButton
                        text={JSON.stringify(joinEval.result, null, 2)}
                        size="sm"
                        variant="outline"
                      />
                    </div>
                    <pre className="p-3 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] text-xs font-mono-tamil overflow-x-auto max-h-80">
                      <code>{JSON.stringify(joinEval.result, null, 2)}</code>
                    </pre>
                  </div>
                )}
              </Card>
            )
          )}

          {/* Optional Batch Pair Tester */}
          {showBatchTester && (
            <Card className="p-5 space-y-3">
              <div className="flex items-center justify-between gap-2">
                <h3 className="text-sm font-semibold text-[var(--color-mai)]">
                  {isTa
                    ? "பல சொற்களை ஒரே நேரத்தில் சோதி (ஒரு வரிக்கு சொல்1 + சொல்2)"
                    : "Test Multiple Word Pairs (one `word1 + word2` per line)"}
                </h3>
                <Badge variant="outline">{batchResults.length}</Badge>
              </div>
              <Textarea
                rows={4}
                value={batchText}
                onChange={(e) => setBatchText(e.target.value)}
                className="font-tamil text-sm"
              />
              <div className="overflow-x-auto">
                <table className="w-full text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-[var(--border-line)] text-left text-[var(--color-muted)]">
                      <th className="py-1.5 pr-3">{isTa ? "உள்ளீடு" : "Input"}</th>
                      <th className="py-1.5 pr-3">{isTa ? "விடை" : "Joined Word"}</th>
                      <th className="py-1.5 pr-3">{isTa ? "நூற்பா" : "Nannūl"}</th>
                      <th className="py-1.5 pr-3">{isTa ? "மாற்று" : "Alternates"}</th>
                      <th className="py-1.5" />
                    </tr>
                  </thead>
                  <tbody>
                    {batchResults.map((row, idx) => (
                      <tr key={`${row.line}-${idx}`} className="border-b border-[var(--border-line)]/50">
                        <td className="py-2 pr-3 font-tamil">{row.line}</td>
                        <td className="py-2 pr-3 font-tamil font-semibold text-[var(--color-mai)]">
                          {row.error ? <span className="text-rose-600">{row.error}</span> : row.result?.surface}
                        </td>
                        <td className="py-2 pr-3 font-mono text-[11px]">
                          {row.result?.steps.map((s) => s.sutra).join(" → ") ?? "—"}
                        </td>
                        <td className="py-2 pr-3 font-tamil text-[var(--color-muted)]">
                          {row.result?.alternatives.map((a) => a.surface).join(", ") || "—"}
                        </td>
                        <td className="py-2">
                          {!row.error && (
                            <button
                              type="button"
                              onClick={() => loadIntoJoinLab(row.first, row.second, activeContext)}
                              className="text-[var(--color-semman)] hover:underline cursor-pointer"
                            >
                              {isTa ? "பார்" : "Open"}
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </div>
      )}

      {/* ================================================================= */}
      {/* TAB 2: SPLIT WORD (Clean Everyday View + Optional Tech Drawer)    */}
      {/* ================================================================= */}
      {activeTab === "split" && (
        <div className="space-y-5">
          <Card className="p-5 sm:p-6 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-end gap-3">
              <div className="flex-1 space-y-1.5">
                <label className="block text-xs font-semibold text-[var(--color-mai)]">
                  {t.tools.punarchi.splitInputLabel}
                </label>
                <input
                  type="text"
                  value={splitSurface}
                  onChange={(e) => {
                    setSplitSurface(e.target.value);
                    setExpandedSplitIdx(null);
                  }}
                  placeholder="மரத்தை"
                  className="w-full px-4 py-3 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] font-tamil text-xl text-[var(--color-mai)] focus:outline-none focus:border-[var(--color-semman)]"
                />
              </div>

              <div className="flex items-center gap-2 pb-1">
                <button
                  type="button"
                  onClick={() => setSplitPoetic((v) => !v)}
                  className={`px-3 py-2 rounded-lg text-xs font-medium border inline-flex items-center gap-1.5 cursor-pointer ${
                    splitPoetic
                      ? "bg-amber-500/20 text-amber-900 dark:text-amber-200 border-amber-500/50 font-semibold"
                      : "bg-[var(--bg-canvas)] border-[var(--border-line)] text-[var(--color-muted)]"
                  }`}
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>{t.tools.punarchi.poeticLabel}</span>
                </button>
              </div>
            </div>

            {/* Friendly Example Chips */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs text-[var(--color-muted)]">
                  {t.tools.punarchi.splitPresetsLabel}
                </span>
                <button
                  type="button"
                  onClick={() => setShowSplitTech((v) => !v)}
                  className="text-xs text-[var(--color-semman)] hover:underline inline-flex items-center gap-1 cursor-pointer"
                >
                  <SlidersHorizontal className="w-3 h-3" />
                  <span>
                    {showSplitTech
                      ? isTa
                        ? "தொழில்நுட்ப விவரங்களை மறை"
                        : "Hide technical details"
                      : isTa
                        ? "தொழில்நுட்ப விவரங்கள்"
                        : "Show technical details"}
                  </span>
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {featuredSplitPresets.map((preset) => (
                  <button
                    key={preset.surface}
                    type="button"
                    onClick={() => {
                      setSplitSurface(preset.surface);
                      setSplitPoetic(Boolean(preset.poetic));
                      setExpandedSplitIdx(null);
                    }}
                    className={`px-3 py-1.5 rounded-xl text-xs border cursor-pointer font-tamil ${
                      splitSurface === preset.surface
                        ? "bg-[var(--color-semman-light)] border-[var(--color-semman)] text-[var(--color-semman)] font-semibold"
                        : "bg-[var(--bg-canvas)] border-[var(--border-line)] text-[var(--color-mai)] hover:border-[var(--color-semman)]"
                    }`}
                  >
                    {isTa ? preset.labelTa : preset.labelEn}
                  </button>
                ))}
                {showSplitTech &&
                  extraSplitPresets.map((preset) => (
                    <button
                      key={preset.surface}
                      type="button"
                      onClick={() => {
                        setSplitSurface(preset.surface);
                        setSplitPoetic(Boolean(preset.poetic));
                        setExpandedSplitIdx(null);
                      }}
                      className="px-2.5 py-1.5 rounded-xl text-xs border border-[var(--border-line)] bg-[var(--bg-raised)] text-[var(--color-mai)] hover:border-[var(--color-semman)] cursor-pointer font-tamil"
                    >
                      {isTa ? preset.labelTa : preset.labelEn}
                    </button>
                  ))}
              </div>
            </div>

            {showSplitTech && splitUnits.length > 0 && (
              <div className="pt-3 border-t border-[var(--border-line)] space-y-2">
                <div className="flex items-center justify-between text-[11px] font-mono text-[var(--color-muted)]">
                  <span>Written Units ({splitUnits.length}) — Atomic Boundaries</span>
                  <span className={splitByteLen > 256 ? "text-rose-600 font-bold" : ""}>
                    {splitByteLen} / 256 UTF-8 bytes
                  </span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {splitUnits.map((unit, idx) => (
                    <span
                      key={`${unit}-${idx}`}
                      className="inline-flex flex-col items-center px-2 py-1 rounded-lg bg-[var(--bg-raised)] border border-[var(--border-line)]"
                    >
                      <span className="font-tamil text-sm font-semibold text-[var(--color-mai)]">
                        {unit}
                      </span>
                      <span className="text-[10px] font-mono text-[var(--color-muted)]">{idx}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </Card>

          {splitEval.error ? (
            <Card className="p-4 border-rose-500/40 bg-rose-500/10 flex items-start gap-2.5 text-sm text-rose-800 dark:text-rose-200">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <div>
                <div className="font-semibold">
                  {isTa ? "சொல் நீளம் மிக அதிகம்" : "Word cannot be split"}
                </div>
                <p className="text-xs mt-0.5">{splitEval.error}</p>
              </div>
            </Card>
          ) : (
            <Card className="p-5 space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-xs font-semibold text-[var(--color-muted)]">
                  {t.tools.punarchi.candidatesHeading} ({splitEval.candidates.length})
                </span>
                <span className="text-xs text-[var(--color-muted)]">
                  {isTa
                    ? "ஒவ்வொரு பிரிப்பும் நன்னூல் விதிகளால் சரிபார்க்கப்பட்டது"
                    : "Every split below is verified to rejoin into your word"}
                </span>
              </div>

              {splitEval.candidates.length === 0 ? (
                <div className="py-6 text-center text-sm text-[var(--color-muted)]">
                  {t.tools.punarchi.noCandidates}
                </div>
              ) : (
                <div className="space-y-2.5">
                  {splitEval.candidates.map((cand, idx) => {
                    const isOpen = expandedSplitIdx === idx;
                    return (
                      <div
                        key={`${cand.first}-${cand.second}-${cand.rule_id}-${idx}`}
                        className="rounded-xl border border-[var(--border-line)] bg-[var(--bg-raised)]/35 overflow-hidden"
                      >
                        <div className="p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
                          <button
                            type="button"
                            onClick={() => setExpandedSplitIdx(isOpen ? null : idx)}
                            className="flex flex-wrap items-center gap-2 text-left cursor-pointer"
                          >
                            {isOpen ? (
                              <ChevronDown className="w-4 h-4 text-[var(--color-muted)]" />
                            ) : (
                              <ChevronRight className="w-4 h-4 text-[var(--color-muted)]" />
                            )}
                            <span className="font-tamil text-xl font-bold text-[var(--color-mai)]">
                              {cand.first} <span className="text-[var(--color-semman)]">+</span>{" "}
                              {cand.second}
                            </span>
                            {renderTransformBadge(cand.transform)}
                            <span
                              role="button"
                              tabIndex={0}
                              onClick={(e) => {
                                e.stopPropagation();
                                jumpToSutra(cand.sutra);
                              }}
                              onKeyDown={(e) => {
                                if (e.key === "Enter") {
                                  e.stopPropagation();
                                  jumpToSutra(cand.sutra);
                                }
                              }}
                              className="px-2.5 py-0.5 rounded-full bg-[var(--color-semman-light)] text-[var(--color-semman)] text-[11px] font-semibold hover:underline"
                            >
                              {isTa ? `நன்னூல் ${cand.sutra} →` : `Nannūl ${cand.sutra} →`}
                            </span>
                            {showSplitTech && (
                              <span className="text-[11px] font-mono text-[var(--color-muted)]">
                                unit={cand.split_unit} · byte={cand.split_byte}
                              </span>
                            )}
                          </button>

                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() =>
                              loadIntoJoinLab(
                                cand.first,
                                cand.second,
                                splitPoetic ? { poetic: true } : undefined
                              )
                            }
                          >
                            <GitMerge className="w-3.5 h-3.5 mr-1.5" />
                            {t.tools.punarchi.verifyInJoin}
                          </Button>
                        </div>

                        {isOpen && (
                          <div className="px-3.5 pb-3.5 pt-2 border-t border-[var(--border-line)]/60">
                            {renderFriendlySteps(cand.steps, showSplitTech)}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {showSplitTech && (
                <pre className="p-3 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] text-xs font-mono-tamil overflow-x-auto max-h-72">
                  <code>{JSON.stringify(splitEval.candidates, null, 2)}</code>
                </pre>
              )}
            </Card>
          )}
        </div>
      )}

      {/* ================================================================= */}
      {/* TAB 3: NANNOOL 117-SUTRA READER (Clear Guide + Collapsible Specs) */}
      {/* ================================================================= */}
      {activeTab === "sutras" && (
        <div className="space-y-4">
          <Card className="p-4 space-y-3">
            {/* Clean Chapter Pills */}
            <div className="flex flex-wrap items-center gap-1.5">
              {(
                [
                  { id: "all", label: isTa ? "அனைத்தும் (117)" : "All Rules (117)" },
                  { id: "prereqs", label: isTa ? "அடிப்படை (10)" : "Foundations (10)" },
                  { id: "uyireeru", label: isTa ? "உயிரீறு (53)" : "Vowel-Ending (53)" },
                  { id: "meyyeeru", label: isTa ? "மெய்யீறு (36)" : "Consonant-Ending (36)" },
                  { id: "urupu", label: isTa ? "உருபு புணரியல் (18)" : "Case Suffixes (18)" },
                ] as const
              ).map((ch) => (
                <button
                  key={ch.id}
                  type="button"
                  onClick={() => setSutraChapter(ch.id)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border cursor-pointer transition-colors ${
                    sutraChapter === ch.id
                      ? "bg-[var(--color-semman)] text-[#faf7f2] border-[var(--color-semman)] font-semibold"
                      : "bg-[var(--bg-canvas)] border-[var(--border-line)] text-[var(--color-mai)] hover:border-[var(--color-semman)]"
                  }`}
                >
                  {ch.label}
                </button>
              ))}

              <button
                type="button"
                onClick={() => setOnlyEditionNotes((v) => !v)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium border cursor-pointer transition-colors ${
                  onlyEditionNotes
                    ? "bg-amber-500/20 text-amber-900 dark:text-amber-200 border-amber-500/50 font-semibold"
                    : "bg-[var(--bg-canvas)] border-[var(--border-line)] text-[var(--color-muted)]"
                }`}
              >
                {isTa
                  ? `பதிப்பு வேறுபாடுகள் (${editionNoteCount})`
                  : `Edition Notes (${editionNoteCount})`}
              </button>
            </div>

            {/* Search Input */}
            <div className="flex items-center gap-3">
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-[var(--color-muted)] absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={sutraSearch}
                  onChange={(e) => setSutraSearch(e.target.value)}
                  placeholder={
                    isTa
                      ? "நூற்பா எண் (எ.கா: 252) அல்லது தமிழ் சொல் (எ.கா: மரம், எல்லாம்) தேடுக..."
                      : "Search by sūtra number (e.g. 252) or Tamil word (e.g. மரம், எல்லாம்)..."
                  }
                  className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] text-sm font-tamil text-[var(--color-mai)] focus:outline-none focus:border-[var(--color-semman)]"
                />
              </div>
              <span className="text-xs text-[var(--color-muted)] shrink-0">
                {filteredSutras.length} / {allSutras.length}
              </span>
            </div>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-[310px_1fr] gap-4 items-start">
            {/* Scrollable Sutra List */}
            <Card className="p-2 max-h-[620px] overflow-y-auto space-y-1">
              {filteredSutras.map((entry) => {
                const isSelected = selectedSutraEntry?.sutra === entry.sutra;
                const witnessCount = witnessesBySutra.get(entry.sutra)?.length ?? 0;
                const cw = getSutraCrosswalk(entry.sutra);
                return (
                  <button
                    key={entry.sutra}
                    type="button"
                    onClick={() => setSelectedSutraNum(entry.sutra)}
                    className={`w-full text-left p-3 rounded-xl border transition-colors cursor-pointer ${
                      isSelected
                        ? "bg-[var(--color-semman-light)] border-[var(--color-semman)]"
                        : "bg-transparent border-transparent hover:bg-[var(--bg-raised)]"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-bold text-xs text-[var(--color-mai)]">
                        {isTa ? `நூற்பா ${entry.sutra}` : `Sūtra ${entry.sutra}`}
                      </span>
                      <div className="flex items-center gap-1.5">
                        {cw && cw.tolkappiyam_sutras.length > 0 && (
                          <span className="px-1.5 py-0.5 rounded text-[10px] bg-sky-500/15 text-sky-800 dark:text-sky-300 font-semibold">
                            {isTa ? "தொல்." : "Tol."}
                          </span>
                        )}
                        {entry.edition_note && (
                          <span className="px-1.5 py-0.5 rounded text-[10px] bg-amber-500/20 text-amber-800 dark:text-amber-300 font-semibold">
                            {isTa ? "பதிப்பு" : "edition"}
                          </span>
                        )}
                        {witnessCount > 0 && (
                          <span className="text-[10px] text-[var(--color-muted)]">
                            {witnessCount} {isTa ? "எ.கா" : "ex"}
                          </span>
                        )}
                      </div>
                    </div>
                    <p className="text-xs text-[var(--color-muted)] line-clamp-2 mt-1 font-tamil leading-snug">
                      {isTa ? cw?.summary_ta || entry.summary : entry.summary}
                    </p>
                  </button>
                );
              })}
            </Card>

            {/* Clean Sutra Detail Reader */}
            {selectedSutraEntry ? (
              <Card className="p-5 sm:p-6 space-y-5">
                <div className="space-y-2.5 pb-4 border-b border-[var(--border-line)]">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-xl font-bold text-[var(--color-mai)]">
                      {isTa
                        ? `நன்னூல் நூற்பா ${selectedSutraEntry.sutra}`
                        : `Nannūl Sūtra ${selectedSutraEntry.sutra}`}
                    </h3>
                    <Badge variant="outline">
                      {isTa
                        ? CHAPTER_LABELS[selectedSutraEntry.chapter].ta
                        : CHAPTER_LABELS[selectedSutraEntry.chapter].en}
                    </Badge>
                    {!selectedSutraEntry.executable && (
                      <Badge variant="sandhanam">
                        {isTa ? "விளக்க நூற்பா" : "Definition / Overview"}
                      </Badge>
                    )}
                  </div>

                  <p className="text-sm sm:text-base font-tamil text-[var(--color-mai)] leading-relaxed">
                    {isTa
                      ? getSutraCrosswalk(selectedSutraEntry.sutra)?.summary_ta ||
                        selectedSutraEntry.summary
                      : selectedSutraEntry.summary}
                  </p>

                  {(() => {
                    const cw = getSutraCrosswalk(selectedSutraEntry.sutra);
                    const secondary = isTa ? selectedSutraEntry.summary : cw?.summary_ta;
                    if (!secondary) return null;
                    return (
                      <p className="text-xs font-tamil text-[var(--color-muted)] leading-relaxed">
                        {secondary}
                      </p>
                    );
                  })()}

                  <div className="text-xs text-[var(--color-muted)]">
                    {isTa
                      ? `முதன்மை ஆதாரம்: தமிழ் இணையக் கல்விக் கழக விருத்தியுரை பக். ${selectedSutraEntry.tva_page} · காண்டிகையுரை நூற்பா ${selectedSutraEntry.kandigai_sutra}`
                      : `Primary Source: TVA Viruttiyurai p.${selectedSutraEntry.tva_page} · Kandigaiyurai #${selectedSutraEntry.kandigai_sutra}`}
                  </div>
                </div>

                {/* Tolkāppiyam Cross-Reference & Wikisource CC0 Scan */}
                {(() => {
                  const cw = getSutraCrosswalk(selectedSutraEntry.sutra);
                  if (!cw || (cw.tolkappiyam_sutras.length === 0 && cw.wikisource_pages.length === 0)) {
                    return null;
                  }
                  const baseUrl = REVIEW_DATA.wikisource_page_base || "";
                  return (
                    <div className="p-3.5 rounded-xl bg-sky-500/10 border border-sky-500/30 text-xs space-y-2">
                      <div className="font-semibold text-sky-900 dark:text-sky-300">
                        {isTa
                          ? "தொல்காப்பிய ஒப்பீடு & விக்கிமூல மூலப்பக்கம் (பேரா. க. வெள்ளைவாரணனார் · CC0)"
                          : "Tolkāppiyam Cross-Reference & Wikisource Scan (Prof. K. Vellaivaranar · CC0)"}
                      </div>
                      <div className="flex flex-wrap items-center gap-1.5">
                        {cw.tolkappiyam_sutras.map((tNum) => (
                          <span
                            key={`tol-${tNum}`}
                            className="px-2 py-0.5 rounded-md bg-[var(--bg-canvas)] border border-sky-500/30 font-tamil font-semibold text-[var(--color-mai)]"
                          >
                            {isTa ? `தொல்காப்பியம் ${tNum}` : `Tolkāppiyam ${tNum}`}
                          </span>
                        ))}
                        {baseUrl &&
                          cw.wikisource_pages.map((pno) => (
                            <a
                              key={`ws-${pno}`}
                              href={`${baseUrl}${pno}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-[var(--bg-canvas)] border border-[var(--border-line)] text-[var(--color-semman)] font-medium hover:border-[var(--color-semman)] hover:underline"
                            >
                              <span>{isTa ? `விக்கிமூலம் பக். ${pno}` : `Wikisource p.${pno}`}</span>
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          ))}
                      </div>
                    </div>
                  );
                })()}

                {/* Highlighted Edition Note */}
                {selectedSutraEntry.edition_note && (
                  <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/35 text-xs space-y-1">
                    <div className="font-semibold text-amber-900 dark:text-amber-300">
                      {isTa ? "பதிப்பு வேறுபாட்டுக் குறிப்பு" : "Edition Comparison Note"}
                    </div>
                    <p className="text-[var(--color-mai)] font-tamil leading-relaxed">
                      {selectedSutraEntry.edition_note}
                    </p>
                  </div>
                )}

                {/* Try Live Examples FIRST (most helpful for learners & reviewers!) */}
                <div className="space-y-2.5">
                  <div className="text-xs font-semibold text-[var(--color-muted)]">
                    {isTa ? "எடுத்துக்காட்டுகளை நேரில் சோதித்துப் பாருங்கள்" : "Try Real Examples Live"}
                  </div>
                  {(witnessesBySutra.get(selectedSutraEntry.sutra) ?? []).length === 0 ? (
                    <div className="p-3 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] text-xs text-[var(--color-muted)]">
                      {selectedSutraEntry.executable
                        ? isTa
                          ? "இந்த நூற்பா எழுத்து வகைப்பாடு / தடுப்பு விதியாக மற்ற புணர்ச்சிகளின் பின்னணியில் செயல்படுகிறது."
                          : "This rule acts as a sound classifier or guard behind other joins (verified in the core test suite)."
                        : isTa
                          ? "இது இலக்கண வரையறை கூறும் நூற்பா; நேரடி சொல் மாற்றம் செய்யாது."
                          : "This is a definitional / scope sūtra rather than a direct letter-change rule."}
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {(witnessesBySutra.get(selectedSutraEntry.sutra) ?? []).map((w) => {
                        const inp = w.input as {
                          first: string;
                          second: string;
                          context?: tt.PunarchiContext;
                        };
                        const exp = w.expected as tt.PunarchiJoinResult;
                        return (
                          <div
                            key={w.id}
                            className="p-3 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] flex flex-col sm:flex-row sm:items-center justify-between gap-2"
                          >
                            <div className="font-tamil text-base font-semibold text-[var(--color-mai)]">
                              {inp.first} <span className="text-[var(--color-semman)]">+</span>{" "}
                              {inp.second} <span className="text-[var(--color-muted)]">→</span>{" "}
                              {exp.surface}
                            </div>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => loadIntoJoinLab(inp.first, inp.second, inp.context)}
                            >
                              <Play className="w-3 h-3 mr-1" />
                              {isTa ? "இணைத்துப் பார்" : "Try Live"}
                            </Button>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Special Word Lists (when relevant) */}
                {(closedClassesBySutra.get(selectedSutraEntry.sutra) ?? []).length > 0 && (
                  <div className="space-y-2">
                    <div className="text-xs font-semibold text-[var(--color-muted)]">
                      {isTa ? "இந்த நூற்பாவுக்குரிய சிறப்புச் சொற்கள்" : "Special Word List for This Rule"}
                    </div>
                    {(closedClassesBySutra.get(selectedSutraEntry.sutra) ?? []).map((cc) => (
                      <div
                        key={cc.id}
                        className="p-3 rounded-xl bg-[var(--bg-raised)]/40 border border-[var(--border-line)] space-y-2"
                      >
                        <div className="flex flex-wrap gap-1.5 font-tamil text-sm">
                          {cc.stems.map((st) => (
                            <span
                              key={st}
                              className="px-2.5 py-0.5 rounded-lg bg-[var(--bg-canvas)] border border-[var(--border-line)] text-[var(--color-mai)]"
                            >
                              {st}
                            </span>
                          ))}
                        </div>
                        {Object.keys(cc.oblique_map).length > 0 && (
                          <div className="text-xs font-tamil text-[var(--color-muted)]">
                            {isTa ? "திரிபு வடிவங்கள்: " : "Stem changes: "}
                            {Object.entries(cc.oblique_map)
                              .map(([k, vals]) => `${k} → ${vals.join(" / ")}`)
                              .join(" · ")}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Collapsible Engine / Developer Spec Accordion */}
                <div className="pt-2 border-t border-[var(--border-line)]">
                  <button
                    type="button"
                    onClick={() => setShowSutraDevSpecs((v) => !v)}
                    className="text-xs font-medium text-[var(--color-muted)] hover:text-[var(--color-semman)] inline-flex items-center gap-1.5 cursor-pointer"
                  >
                    {showSutraDevSpecs ? (
                      <ChevronDown className="w-3.5 h-3.5" />
                    ) : (
                      <ChevronRight className="w-3.5 h-3.5" />
                    )}
                    <Code2 className="w-3.5 h-3.5" />
                    <span>
                      {isTa
                        ? `பொறி விதி விவரங்கள் (Developer / TOML: ${(rulesBySutra.get(selectedSutraEntry.sutra) ?? []).length})`
                        : `Engine Rule Specs (Developer / TOML: ${(rulesBySutra.get(selectedSutraEntry.sutra) ?? []).length})`}
                    </span>
                  </button>

                  {showSutraDevSpecs && (
                    <div className="mt-3 space-y-2">
                      {(rulesBySutra.get(selectedSutraEntry.sutra) ?? []).map((rule) => (
                        <div
                          key={rule.id}
                          className="p-3 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] text-xs space-y-1"
                        >
                          <div className="flex flex-wrap items-center gap-1.5">
                            <code className="font-bold text-[var(--color-semman)]">{rule.id}</code>
                            <Badge variant="outline" className="text-[10px]">
                              Stage {rule.stage}
                              {rule.substage ? ` (${rule.substage})` : ""} · prio {rule.priority}
                            </Badge>
                            <Badge variant="outline" className="text-[10px]">
                              rel: {rule.relation}
                            </Badge>
                            {rule.optional && <Badge variant="sandhanam">optional</Badge>}
                            {rule.poetic && <Badge variant="sandhanam">poetic</Badge>}
                          </div>
                          <div className="font-mono text-[11px] text-[var(--color-muted)]">
                            {rule.left_match} + {rule.right_match} → {rule.action} (
                            {rule.evidence_layer})
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </Card>
            ) : (
              <Card className="p-6 text-center text-sm text-[var(--color-muted)]">
                {isTa ? "பொருந்தும் நூற்பா எதுவும் இல்லை." : "No rules match your search."}
              </Card>
            )}
          </div>
        </div>
      )}

      {/* ================================================================= */}
      {/* TAB 4: PLAIN-LANGUAGE GUIDE + COLLAPSIBLE DEVELOPER VERIFICATION  */}
      {/* ================================================================= */}
      {activeTab === "notes" && (
        <div className="space-y-5">
          {/* Plain-Language Guide: The 4 Types of Punarchi */}
          <Card className="p-5 sm:p-6 space-y-4">
            <div>
              <h3 className="text-base font-bold text-[var(--color-mai)]">
                {isTa
                  ? "புணர்ச்சி என்றால் என்ன? — 4 அடிப்படை வகைகள்"
                  : "What is Tamil Punarchi? — The 4 Simple Change Types"}
              </h3>
              <p className="text-xs sm:text-sm text-[var(--color-muted)] mt-1 leading-relaxed">
                {isTa
                  ? "இரண்டு தமிழ் சொற்கள் இணையும்போது (நிலைமொழி + வருமொழி), நன்னூல் இலக்கணத்தின்படி நான்கு விதமான மாற்றங்களில் ஒன்று நிகழும்:"
                  : "When two Tamil words join together, Nannūl groups every sound change into four simple categories:"}
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {(["iyalbu", "thonral", "thirithal", "keduthal"] as const).map((kind) => (
                <div
                  key={kind}
                  className="p-3.5 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] space-y-1.5"
                >
                  {renderTransformBadge(kind)}
                  <p className="text-xs text-[var(--color-mai)] font-tamil leading-relaxed">
                    {isTa ? TRANSFORM_LABELS[kind].descTa : TRANSFORM_LABELS[kind].descEn}
                  </p>
                </div>
              ))}
            </div>
          </Card>

          {/* Easy-to-Read Sutra 237 Comparison Table */}
          <Card className="p-5 sm:p-6 space-y-3">
            <h3 className="text-sm font-bold text-[var(--color-mai)]">
              {isTa
                ? "நன்னூல் 237 — ன், ல், ண், ள் + த / ந மாற்ற அட்டவணை"
                : "Common Consonant Changes (Nannūl Sūtra 237: ன், ல், ண், ள் + த / ந)"}
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-xs sm:text-sm border-collapse font-tamil">
                <thead>
                  <tr className="border-b border-[var(--border-line)] text-left text-[var(--color-muted)] text-xs">
                    <th className="py-2 pr-3">{isTa ? "சொற்கள்" : "Words"}</th>
                    <th className="py-2 pr-3">{isTa ? "அல்வழி (தொடர்)" : "Phrase (Alvazhi)"}</th>
                    <th className="py-2 pr-3">{isTa ? "வேற்றுமை" : "Case (Vetrumai)"}</th>
                    <th className="py-2">{isTa ? "நூற்பா" : "Sūtras"}</th>
                  </tr>
                </thead>
                <tbody>
                  {SUTRA_237_MATRIX.map((row, i) => (
                    <tr key={i} className="border-b border-[var(--border-line)]/50">
                      <td className="py-2 pr-3">{row.left}</td>
                      <td className="py-2 pr-3 font-semibold text-[var(--color-mai)]">{row.alvazhi}</td>
                      <td className="py-2 pr-3 font-semibold text-[var(--color-mai)]">{row.vetrumai}</td>
                      <td className="py-2 font-mono text-xs text-[var(--color-muted)]">{row.sutras}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Developer Architecture & In-Browser 261-Test Suite (Collapsible) */}
          <Card className="p-5 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-bold text-[var(--color-mai)] inline-flex items-center gap-1.5">
                  <Layers className="w-4 h-4 text-[var(--color-semman)]" />
                  <span>
                    {isTa
                      ? `நன்னூல் பொறி ஆய்வு & ${REVIEW_DATA.golden_count} சோதனைத் தொகுப்பு`
                      : `Nannūl Engine Verification & Developer Architecture (${REVIEW_DATA.golden_count} Tests)`}
                  </span>
                </h3>
                <p className="text-xs text-[var(--color-muted)] mt-0.5">
                  {isTa
                    ? "அனைத்து 261 நன்னூல் சோதனைகளையும் உங்கள் உலாவியிலேயே நேரடியாக இயக்கிச் சரிபார்க்கலாம்."
                    : "Run all 261 canonical Nannūl test cases live in your browser, or inspect the 4-stage engine pipeline."}
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Button size="sm" onClick={runBrowserGoldenSuite} disabled={!ready}>
                  <Play className="w-3.5 h-3.5 mr-1.5" />
                  {isTa
                    ? `${REVIEW_DATA.golden_count} சோதனைகளை இயக்கு`
                    : `Run ${REVIEW_DATA.golden_count} Tests`}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setShowDevArchitecture((v) => !v)}
                >
                  <Code2 className="w-3.5 h-3.5 mr-1.5" />
                  {showDevArchitecture
                    ? isTa
                      ? "பொறி கட்டமைப்பை மறை"
                      : "Hide Engine Pipeline"
                    : isTa
                      ? "பொறி கட்டமைப்பைக் காட்டு"
                      : "Show Engine Pipeline"}
                </Button>
              </div>
            </div>

            {goldenRun && (
              <div className="space-y-3 pt-3 border-t border-[var(--border-line)]">
                <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 font-semibold">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      {goldenRun.passed} passed
                    </span>
                    {goldenRun.failed > 0 && (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-rose-500/15 text-rose-700 dark:text-rose-300 font-semibold">
                        <XCircle className="w-3.5 h-3.5" />
                        {goldenRun.failed} failed
                      </span>
                    )}
                    <span className="font-mono text-[var(--color-muted)]">
                      {goldenRun.elapsedMs.toFixed(1)} ms
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <select
                      value={goldenFilterTag}
                      onChange={(e) => setGoldenFilterTag(e.target.value)}
                      className="px-2.5 py-1 rounded-lg bg-[var(--bg-canvas)] border border-[var(--border-line)] text-xs"
                    >
                      {goldenTags.map((tg) => (
                        <option key={tg} value={tg}>
                          tag: {tg}
                        </option>
                      ))}
                    </select>
                    <label className="inline-flex items-center gap-1 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={goldenOnlyFailed}
                        onChange={(e) => setGoldenOnlyFailed(e.target.checked)}
                      />
                      <span>Failed only</span>
                    </label>
                  </div>
                </div>

                <div className="max-h-72 overflow-y-auto border border-[var(--border-line)] rounded-xl divide-y divide-[var(--border-line)]/60">
                  {filteredGoldenItems.map((it) => (
                    <div
                      key={it.row.id}
                      className="px-3 py-2 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs bg-[var(--bg-canvas)]"
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        {it.passed ? (
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                        ) : (
                          <XCircle className="w-3.5 h-3.5 text-rose-500 shrink-0" />
                        )}
                        <code className="truncate font-semibold text-[var(--color-mai)]">
                          {it.row.id}
                        </code>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        {it.row.op === "punarchi_join" && !it.row.expected_error && (
                          <button
                            type="button"
                            onClick={() => {
                              const inp = it.row.input as {
                                first: string;
                                second: string;
                                context?: tt.PunarchiContext;
                              };
                              loadIntoJoinLab(inp.first, inp.second, inp.context);
                            }}
                            className="text-[var(--color-semman)] hover:underline cursor-pointer"
                          >
                            {isTa ? "இணைப்பில் திற" : "Open in Join"}
                          </button>
                        )}
                        {it.row.op === "punarchi_split_candidates" && !it.row.expected_error && (
                          <button
                            type="button"
                            onClick={() => {
                              const inp = it.row.input as { surface: string; poetic?: boolean };
                              setSplitSurface(inp.surface);
                              setSplitPoetic(Boolean(inp.poetic));
                              setActiveTab("split");
                            }}
                            className="text-[var(--color-semman)] hover:underline cursor-pointer"
                          >
                            {isTa ? "பிரிப்பில் திற" : "Open in Split"}
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {showDevArchitecture && (
              <div className="space-y-4 pt-3 border-t border-[var(--border-line)]">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
                  {PIPELINE_STAGES.map((st) => (
                    <div
                      key={st.stage}
                      className="p-3 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] space-y-1"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="px-2 py-0.5 rounded bg-[var(--color-semman-light)] text-[var(--color-semman)] font-mono text-[11px] font-bold">
                          Stage {st.stage}
                        </span>
                        <code className="text-[10px] text-[var(--color-muted)]">{st.file}</code>
                      </div>
                      <div className="text-xs font-semibold text-[var(--color-mai)]">{st.title}</div>
                      <p className="text-[11px] text-[var(--color-muted)] font-tamil leading-relaxed">
                        {st.detail}
                      </p>
                    </div>
                  ))}
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-[var(--border-line)] text-left text-[var(--color-muted)]">
                        <th className="py-1.5 pr-2">BoundaryFlag</th>
                        <th className="py-1.5 pr-2">Purpose</th>
                        <th className="py-1.5">Set By</th>
                      </tr>
                    </thead>
                    <tbody>
                      {BOUNDARY_FLAGS_REF.map((row) => (
                        <tr key={row.flag} className="border-b border-[var(--border-line)]/50">
                          <td className="py-1.5 pr-2 font-mono text-[11px] text-[var(--color-semman)]">
                            {row.flag}
                          </td>
                          <td className="py-1.5 pr-2 text-[var(--color-mai)]">{row.role}</td>
                          <td className="py-1.5 font-tamil text-[11px] text-[var(--color-muted)]">
                            {row.setters}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
