import { useState } from "react";
import type * as tt from "tamil-toolkit/web";
import type {
  LexiconWordDefinition,
  LexiconWordMeaning,
} from "../../../lib/engine";
import { getLexiconCategoryMeta } from "../../../lib/lexicon-v2";
import {
  POS_HUMAN_LABELS,
  sanitizeSafeExternalUrl,
} from "../../../lib/lexicon";
import { Card } from "../../ui/card";
import { Badge } from "../../ui/badge";
import { CopyButton } from "../../common/CopyButton";
import {
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Link2,
  ShieldCheck,
} from "lucide-react";

export function formatPosLabel(
  pos: string | null | undefined,
  language: "ta" | "en"
): string {
  if (!pos) return "";
  const mapped = POS_HUMAN_LABELS[pos];
  if (!mapped) return pos;
  return language === "ta" ? `${mapped.ta} (${pos})` : mapped.en;
}

export function PackTierBadge({
  tier,
  language,
}: {
  tier: tt.LexiconPackTier;
  language: "ta" | "en";
}) {
  if (tier === "verified_open") {
    return (
      <Badge variant="terracotta" className="text-[10px]">
        {language === "ta"
          ? "சரிபார்க்கப்பட்ட திறந்த தரவு · CC-BY-SA-4.0"
          : "Verified Open · CC-BY-SA-4.0"}
      </Badge>
    );
  }
  return (
    <Badge variant="sandhanam" className="text-[10px]">
      {language === "ta"
        ? "உள்ளூர் காப்பகம் · உரிமம் தீர்க்கப்படவில்லை"
        : "Local Archive · Unresolved"}
    </Badge>
  );
}

function DefinitionRightsBadge({
  hasVerifiedOpen,
  hasLocalHistorical,
  language,
}: {
  hasVerifiedOpen: boolean;
  hasLocalHistorical: boolean;
  language: "ta" | "en";
}) {
  if (hasVerifiedOpen && hasLocalHistorical) {
    return (
      <Badge variant="sandhanam" className="text-[11px]">
        <ShieldCheck className="w-3 h-3 shrink-0" />
        <span>{language === "ta" ? "திறந்த + உள்ளூர்" : "Open + Local"}</span>
      </Badge>
    );
  }
  if (hasVerifiedOpen) {
    return (
      <Badge variant="terracotta" className="text-[11px]">
        <ShieldCheck className="w-3 h-3 shrink-0" />
        <span>
          {language === "ta"
            ? "சரிபார்க்கப்பட்ட திறந்த தரவு · CC-BY-SA-4.0"
            : "Verified Open · CC-BY-SA-4.0"}
        </span>
      </Badge>
    );
  }
  if (hasLocalHistorical) {
    return (
      <Badge variant="sandhanam" className="text-[11px]">
        <span>
          {language === "ta"
            ? "உள்ளூர் காப்பகம் · உரிமம் தீர்க்கப்படவில்லை"
            : "Local Archive · Unresolved"}
        </span>
      </Badge>
    );
  }
  return null;
}

function MeaningMetadataTags({
  meaning,
  language,
}: {
  meaning: LexiconWordMeaning;
  language: "ta" | "en";
}) {
  const hasMeta =
    meaning.pos ||
    meaning.domain ||
    meaning.region ||
    meaning.register ||
    meaning.pack_tier === "local_historical";
  if (!hasMeta) return null;

  return (
    <div className="flex flex-wrap items-center gap-1 pt-0.5">
      {meaning.pos && (
        <Badge variant="outline" className="text-[10px] font-mono-tamil">
          {formatPosLabel(meaning.pos, language)}
        </Badge>
      )}
      {meaning.domain && (
        <Badge variant="outline" className="text-[10px]">
          {meaning.domain}
        </Badge>
      )}
      {meaning.region && (
        <Badge variant="sandhanam" className="text-[10px]">
          {meaning.region}
        </Badge>
      )}
      {meaning.register && (
        <Badge variant="outline" className="text-[10px] capitalize">
          {meaning.register}
        </Badge>
      )}
      {meaning.pack_tier === "local_historical" && (
        <Badge
          variant="sandhanam"
          className="text-[10px]"
          title={`${meaning.pack_id} (${meaning.rights_status})`}
        >
          {language === "ta"
            ? `உள்ளூர் · ${meaning.pack_id}`
            : `Local Archive · ${meaning.pack_id}`}
        </Badge>
      )}
    </div>
  );
}

export function MergedWordDefinitionCard({
  definition,
  latencyMs,
  language,
  onSelectWord,
}: {
  definition: LexiconWordDefinition;
  latencyMs: number;
  language: "ta" | "en";
  onSelectWord: (nextWord: string) => void;
}) {
  const [showProv, setShowProv] = useState(false);

  const relationSections = [
    {
      key: "synonyms",
      label: language === "ta" ? "ஒத்த சொற்கள்" : "Synonyms",
      items: definition.relations.synonyms,
    },
    {
      key: "antonyms",
      label: language === "ta" ? "எதிர்ச்சொற்கள்" : "Antonyms",
      items: definition.relations.antonyms,
    },
    {
      key: "related",
      label: language === "ta" ? "தொடர்புடைய சொற்கள்" : "Related",
      items: definition.relations.related,
    },
    {
      key: "hypernyms",
      label: language === "ta" ? "மேல்வகைச் சொற்கள்" : "Hypernyms",
      items: definition.relations.hypernyms,
    },
  ].filter((sec) => sec.items.length > 0);

  const otherMatchedHeadwords =
    definition.folded && (definition.matched_headwords?.length ?? 0) > 1
      ? (definition.matched_headwords ?? []).filter(
          (hw) => hw !== definition.headword
        )
      : [];

  const ipaList = definition.ipa ?? [];
  const verbClasses = definition.verb_classes ?? [];
  const transitivity = definition.transitivity ?? [];
  const rootWords = definition.root_words ?? [];
  const etymologyTypes = definition.etymology_types ?? [];
  const dedrIds = definition.dedr_ids ?? [];
  const animacyGenders = definition.animacy_genders ?? [];
  const sandhiBehaviors = definition.sandhi_behaviors ?? [];
  const frequencyTiers = definition.frequency_tiers ?? [];

  const hasHeritageOrRegional =
    definition.variants.length > 0 ||
    definition.regions.length > 0 ||
    definition.standard_equivalents.length > 0 ||
    definition.pure_tamil_equivalents.length > 0 ||
    definition.origin_languages.length > 0 ||
    definition.scientific_names.length > 0 ||
    definition.literary_sources.length > 0 ||
    definition.domains.length > 0 ||
    definition.examples.length > 0 ||
    verbClasses.length > 0 ||
    transitivity.length > 0 ||
    rootWords.length > 0 ||
    etymologyTypes.length > 0 ||
    dedrIds.length > 0 ||
    animacyGenders.length > 0 ||
    sandhiBehaviors.length > 0 ||
    frequencyTiers.length > 0;

  return (
    <Card className="p-5 sm:p-7 space-y-6" data-testid="merged-word-card">
      {/* Headword Header */}
      <div className="flex flex-wrap items-start justify-between gap-3 pb-4 border-b border-[var(--border-line)]">
        <div className="space-y-2 min-w-0 flex-1">
          <div className="flex flex-wrap items-baseline gap-2.5">
            <h2 className="text-3xl sm:text-4xl font-tamil font-bold text-[var(--color-mai)] tracking-tight break-words">
              {definition.headword}
            </h2>
            {definition.folded && (
              <Badge variant="sandhanam" className="text-[11px]">
                {language === "ta" ? "மயங்கொலி மடிப்பு" : "Mayangoli Folded"}
              </Badge>
            )}
            {definition.canonical_query &&
              definition.canonical_query !== definition.query && (
                <Badge variant="mono" className="text-[10px]">
                  NFC: {definition.canonical_query}
                </Badge>
              )}
          </div>

          {ipaList.length > 0 && (
            <p className="text-sm font-mono-tamil text-[var(--color-muted)]">
              {ipaList
                .map((p) => (p.startsWith("/") || p.startsWith("[") ? p : `/${p}/`))
                .join(" · ")}
            </p>
          )}

          {otherMatchedHeadwords.length > 0 && (
            <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
              <span className="text-[11px] font-medium text-[var(--color-muted)]">
                {language === "ta" ? "மேலும் பொருந்தியவை:" : "Also matched:"}
              </span>
              {otherMatchedHeadwords.map((hw) => (
                <button
                  key={hw}
                  type="button"
                  onClick={() => onSelectWord(hw)}
                  className="inline-flex items-center px-2 py-0.5 rounded-full border border-[var(--color-sandhanam)]/60 bg-[var(--bg-canvas)] hover:border-[var(--color-semman)] hover:text-[var(--color-semman)] text-xs font-tamil text-[var(--color-mai)] transition-colors cursor-pointer"
                >
                  {hw}
                </button>
              ))}
            </div>
          )}

          <div className="flex flex-wrap items-center gap-1.5">
            {definition.pos.map((p) => (
              <Badge key={p} variant="default" className="text-[11px] font-tamil">
                {formatPosLabel(p, language)}
              </Badge>
            ))}
            {definition.categories.map((cat) => {
              const meta = getLexiconCategoryMeta(cat);
              return (
                <Badge key={cat} variant="outline" className="text-[11px]">
                  {language === "ta" ? meta.label_ta : meta.label_en}
                </Badge>
              );
            })}
            <DefinitionRightsBadge
              hasVerifiedOpen={definition.has_verified_open}
              hasLocalHistorical={definition.has_local_historical}
              language={language}
            />
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {latencyMs > 0 && (
            <Badge variant="mono" className="text-[10px]">
              {latencyMs.toFixed(2)} ms
            </Badge>
          )}
          <CopyButton text={definition.headword} size="sm" variant="outline" />
        </div>
      </div>

      {/* English Meanings */}
      {definition.meanings_en.length > 0 && (
        <section className="space-y-2.5">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--color-semman)]">
            {language === "ta" ? "ஆங்கிலப் பொருள்" : "English Meanings"}
          </h3>
          <ol className="space-y-2.5">
            {definition.meanings_en.map((m, idx) => (
              <li
                key={`en-${idx}-${m.pack_id}-${m.text.slice(0, 24)}`}
                className="flex items-baseline gap-2.5"
              >
                <span className="text-xs font-mono-tamil font-semibold text-[var(--color-muted)] w-5 text-right shrink-0">
                  {idx + 1}.
                </span>
                <div className="min-w-0 flex-1 space-y-1">
                  <p className="text-sm sm:text-[15px] text-[var(--color-mai)] leading-relaxed">
                    {m.text}
                  </p>
                  <MeaningMetadataTags meaning={m} language={language} />
                </div>
              </li>
            ))}
          </ol>
        </section>
      )}

      {/* Tamil Meanings */}
      {definition.meanings_ta.length > 0 && (
        <section
          className={`space-y-2.5 ${
            definition.meanings_en.length > 0
              ? "pt-4 border-t border-[var(--border-line)]"
              : ""
          }`}
        >
          <h3 className="text-sm font-tamil font-bold text-[var(--color-semman)]">
            {language === "ta" ? "தமிழ் பொருள்" : "Tamil Meanings (தமிழ் பொருள்)"}
          </h3>
          <ol className="space-y-2.5">
            {definition.meanings_ta.map((m, idx) => (
              <li
                key={`ta-${idx}-${m.pack_id}-${m.text.slice(0, 24)}`}
                className="flex items-baseline gap-2.5"
              >
                <span className="text-xs font-mono-tamil font-semibold text-[var(--color-muted)] w-5 text-right shrink-0">
                  {idx + 1}.
                </span>
                <div className="min-w-0 flex-1 space-y-1">
                  <p className="text-sm sm:text-[15px] font-tamil text-[var(--color-mai)] leading-relaxed">
                    {m.text}
                  </p>
                  <MeaningMetadataTags meaning={m} language={language} />
                </div>
              </li>
            ))}
          </ol>
        </section>
      )}

      {/* Semantic Relations Chips */}
      {relationSections.length > 0 && (
        <section className="rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] p-4 space-y-3">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-[var(--color-semman)]">
            <Link2 className="w-3.5 h-3.5 shrink-0" />
            <span>
              {language === "ta" ? "சொல் தொடர்புகள்" : "Word Relations"}
            </span>
          </div>
          <div className="space-y-2.5">
            {relationSections.map((sec) => (
              <div key={sec.key} className="space-y-1.5">
                <span className="text-[11px] font-semibold text-[var(--color-muted)] block">
                  {sec.label}
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {sec.items.map((relWord) => (
                    <button
                      key={`${sec.key}-${relWord}`}
                      type="button"
                      onClick={() => onSelectWord(relWord)}
                      className="inline-flex items-center px-2.5 py-1 rounded-full border border-[var(--border-line)] bg-[var(--bg-surface)] hover:border-[var(--color-semman)] hover:text-[var(--color-semman)] text-xs font-tamil text-[var(--color-mai)] transition-colors cursor-pointer"
                    >
                      {relWord}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Regional, Variants & Heritage */}
      {hasHeritageOrRegional && (
        <section className="rounded-xl border border-[var(--border-line)] bg-[var(--bg-raised)]/40 p-4 space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--color-muted)]">
            {language === "ta"
              ? "வட்டாரம், மாற்று வடிவங்கள் & மரபு"
              : "Regional, Variants & Heritage"}
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            {definition.variants.length > 0 && (
              <div className="space-y-1">
                <span className="font-semibold text-[var(--color-mai)] block">
                  {language === "ta" ? "மாற்று வடிவங்கள்" : "Variants"}
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {definition.variants.map((v) => (
                    <button
                      key={v}
                      type="button"
                      onClick={() => onSelectWord(v)}
                      className="px-2 py-0.5 rounded-md border border-[var(--border-line)] bg-[var(--bg-surface)] hover:border-[var(--color-semman)] font-tamil text-[var(--color-mai)] cursor-pointer"
                    >
                      {v}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {definition.regions.length > 0 && (
              <div className="space-y-1">
                <span className="font-semibold text-[var(--color-mai)] block">
                  {language === "ta" ? "வட்டாரங்கள்" : "Regions"}
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {definition.regions.map((r) => (
                    <Badge key={r} variant="sandhanam" className="text-[11px]">
                      {r}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {definition.standard_equivalents.length > 0 && (
              <div className="space-y-1">
                <span className="font-semibold text-[var(--color-mai)] block">
                  {language === "ta" ? "நியமச் சொற்கள்" : "Standard Equivalents"}
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {definition.standard_equivalents.map((eq) => (
                    <button
                      key={eq}
                      type="button"
                      onClick={() => onSelectWord(eq)}
                      className="px-2 py-0.5 rounded-md border border-[var(--border-line)] bg-[var(--bg-surface)] hover:border-[var(--color-semman)] font-tamil text-[var(--color-mai)] cursor-pointer"
                    >
                      {eq}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {definition.pure_tamil_equivalents.length > 0 && (
              <div className="space-y-1">
                <span className="font-semibold text-[var(--color-mai)] block">
                  {language === "ta" ? "தனித்தமிழ்ச் சொற்கள்" : "Pure Tamil Equivalents"}
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {definition.pure_tamil_equivalents.map((eq) => (
                    <button
                      key={eq}
                      type="button"
                      onClick={() => onSelectWord(eq)}
                      className="px-2 py-0.5 rounded-md border border-[var(--border-line)] bg-[var(--bg-surface)] hover:border-[var(--color-semman)] font-tamil text-[var(--color-mai)] cursor-pointer"
                    >
                      {eq}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {verbClasses.length > 0 && (
              <div className="space-y-1">
                <span className="font-semibold text-[var(--color-mai)] block">
                  {language === "ta" ? "வினை வகுப்பு" : "Verb Class"}
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {verbClasses.map((vc) => (
                    <Badge key={vc} variant="outline" className="text-[11px]">
                      {vc}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {transitivity.length > 0 && (
              <div className="space-y-1">
                <span className="font-semibold text-[var(--color-mai)] block">
                  {language === "ta" ? "செயப்படுபொருள் நிலை" : "Transitivity"}
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {transitivity.map((tr) => (
                    <Badge key={tr} variant="outline" className="text-[11px]">
                      {tr}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {rootWords.length > 0 && (
              <div className="space-y-1">
                <span className="font-semibold text-[var(--color-mai)] block">
                  {language === "ta" ? "வேர்ச்சொல்" : "Root Word"}
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {rootWords.map((rw) => (
                    <button
                      key={rw}
                      type="button"
                      onClick={() => onSelectWord(rw)}
                      className="px-2 py-0.5 rounded-md border border-[var(--border-line)] bg-[var(--bg-surface)] hover:border-[var(--color-semman)] font-tamil text-[var(--color-mai)] cursor-pointer"
                    >
                      {rw}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {etymologyTypes.length > 0 && (
              <div className="space-y-1">
                <span className="font-semibold text-[var(--color-mai)] block">
                  {language === "ta" ? "சொற்பிறப்பியல்" : "Etymology"}
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {etymologyTypes.map((et) => (
                    <Badge key={et} variant="outline" className="text-[11px]">
                      {et}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {dedrIds.length > 0 && (
              <div className="space-y-1">
                <span className="font-semibold text-[var(--color-mai)] block">
                  DEDR
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {dedrIds.map((id) => (
                    <Badge key={id} variant="mono" className="text-[11px]">
                      {id}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {animacyGenders.length > 0 && (
              <div className="space-y-1">
                <span className="font-semibold text-[var(--color-mai)] block">
                  {language === "ta" ? "திணை / பால்" : "Animacy / Gender"}
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {animacyGenders.map((ag) => (
                    <Badge key={ag} variant="outline" className="text-[11px]">
                      {ag}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {sandhiBehaviors.length > 0 && (
              <div className="space-y-1">
                <span className="font-semibold text-[var(--color-mai)] block">
                  {language === "ta" ? "புணர்ச்சி" : "Sandhi"}
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {sandhiBehaviors.map((sb) => (
                    <Badge key={sb} variant="outline" className="text-[11px]">
                      {sb}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {frequencyTiers.length > 0 && (
              <div className="space-y-1">
                <span className="font-semibold text-[var(--color-mai)] block">
                  {language === "ta" ? "பயன்பாட்டு அடுக்கு" : "Frequency Tier"}
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {frequencyTiers.map((ft) => (
                    <Badge key={ft} variant="sandhanam" className="text-[11px]">
                      {ft}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {definition.origin_languages.length > 0 && (
              <div className="space-y-1">
                <span className="font-semibold text-[var(--color-mai)] block">
                  {language === "ta" ? "மூல மொழிகள்" : "Origin Languages"}
                </span>
                <p className="text-[var(--color-muted)]">
                  {definition.origin_languages.join(" · ")}
                </p>
              </div>
            )}

            {definition.scientific_names.length > 0 && (
              <div className="space-y-1">
                <span className="font-semibold text-[var(--color-mai)] block">
                  {language === "ta" ? "அறிவியல் பெயர்கள்" : "Scientific Names"}
                </span>
                <p className="italic text-[var(--color-muted)]">
                  {definition.scientific_names.join(" · ")}
                </p>
              </div>
            )}

            {definition.literary_sources.length > 0 && (
              <div className="space-y-1">
                <span className="font-semibold text-[var(--color-mai)] block">
                  {language === "ta" ? "இலக்கிய மூலங்கள்" : "Literary Sources"}
                </span>
                <p className="font-tamil text-[var(--color-muted)]">
                  {definition.literary_sources.join(" · ")}
                </p>
              </div>
            )}

            {definition.domains.length > 0 && (
              <div className="space-y-1 sm:col-span-2">
                <span className="font-semibold text-[var(--color-mai)] block">
                  {language === "ta" ? "துறைகள்" : "Domains"}
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {definition.domains.slice(0, 12).map((d) => (
                    <Badge key={d} variant="outline" className="text-[10px]">
                      {d}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>

          {definition.examples.length > 0 && (
            <div className="pt-2 border-t border-[var(--border-line)]/60 space-y-1.5">
              <span className="text-xs font-semibold text-[var(--color-mai)] block">
                {language === "ta" ? "எடுத்துக்காட்டுகள்" : "Examples"}
              </span>
              <div className="space-y-1">
                {definition.examples.slice(0, 6).map((ex, idx) => (
                  <p
                    key={idx}
                    className="text-xs font-tamil text-[var(--color-muted)] pl-2.5 border-l-2 border-[var(--color-sandhanam)]/70"
                  >
                    “{ex}”
                  </p>
                ))}
              </div>
            </div>
          )}
        </section>
      )}

      {/* Collapsible Provenance & Sources Footer */}
      {definition.sources.length > 0 && (
        <div className="pt-3 border-t border-[var(--border-line)]">
          <button
            type="button"
            onClick={() => setShowProv((prev) => !prev)}
            aria-expanded={showProv}
            className="inline-flex items-center gap-1.5 text-xs font-medium text-[var(--color-muted)] hover:text-[var(--color-semman)] py-1 cursor-pointer"
          >
            {showProv ? (
              <ChevronUp className="w-3.5 h-3.5" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5" />
            )}
            <span>
              {language === "ta"
                ? `ஆதாரங்கள் & உரிமம் (${definition.sources.length})`
                : `Provenance & Sources (${definition.sources.length})`}
            </span>
          </button>

          {showProv && (
            <div className="mt-2.5 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] p-3.5 space-y-2 text-xs">
              {definition.sources.map((src, idx) => {
                const safePermalink = src.permalink
                  ? sanitizeSafeExternalUrl(src.permalink)
                  : null;
                return (
                  <div
                    key={`${src.pack_id}:${src.source_locator}:${idx}`}
                    className="flex flex-wrap items-center justify-between gap-2 pb-2 last:pb-0 border-b last:border-b-0 border-[var(--border-line)]/50"
                  >
                    <div className="min-w-0 flex-1 space-y-0.5">
                      <div className="flex flex-wrap items-center gap-1.5">
                        <Badge variant="mono" className="text-[10px]">
                          {src.pack_id}
                        </Badge>
                        <Badge variant="outline" className="text-[10px]">
                          {src.category}
                        </Badge>
                        <Badge
                          variant={
                            src.pack_tier === "verified_open"
                              ? "terracotta"
                              : "sandhanam"
                          }
                          className="text-[10px]"
                        >
                          {src.rights_status}
                        </Badge>
                      </div>
                      <p className="text-[11px] font-mono-tamil text-[var(--color-muted)] truncate">
                        {src.source_id} · {src.source_locator}
                      </p>
                    </div>
                    {safePermalink && (
                      <a
                        href={safePermalink}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border border-[var(--border-line)] bg-[var(--bg-surface)] text-[var(--color-semman)] hover:border-[var(--color-semman)] text-[11px] font-medium shrink-0"
                      >
                        <ExternalLink className="w-3 h-3" />
                        <span>Permalink</span>
                      </a>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </Card>
  );
}
