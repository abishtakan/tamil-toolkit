import { useRef, useState } from "react";
import type * as tt from "tamil-toolkit/web";
import type { LexiconCategory, LexiconV2Stats } from "../../../lib/engine";
import { useLanguage } from "../../../lib/i18n";
import { IS_PUBLIC_BETA } from "../../../lib/tools";
import {
  IS_OPEN_ONLY_CHANNEL,
  TlpackManifestEntry,
  formatPackBytes,
  getLexiconCategoryMeta,
} from "../../../lib/lexicon-v2";
import {
  CONTRACT_TEST_PRESETS,
  ContractTestPreset,
  ExtendedManifest,
  LEXICON_PACK_DISPLAY_ORDER,
  QueryDiagnostics,
  deriveFiniteScopeOptions,
  getPackNoticeLinks,
  verifyPackCatalogAlignment,
} from "../../../lib/lexicon";
import { Card } from "../../ui/card";
import { Button } from "../../ui/button";
import { Badge } from "../../ui/badge";
import { CopyButton } from "../../common/CopyButton";
import { PackTierBadge } from "./MergedWordDefinitionCard";
import {
  BookMarked,
  ChevronDown,
  ChevronUp,
  Database,
  Download,
  ExternalLink,
  FlaskConical,
  Info,
  Layers,
  Loader2,
  SlidersHorizontal,
  Trash2,
  Upload,
} from "lucide-react";

function downloadJsonFile(filename: string, content: string) {
  if (typeof document === "undefined" || typeof URL === "undefined") return;
  const blob = new Blob([content], { type: "application/json;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export interface LexiconPackDrawerProps {
  ready: boolean;
  v2Stats: LexiconV2Stats;
  v2MountedIds: Set<string>;
  v2LoadingAction: string | null;
  v2Error: string | null;
  v2OpenManifestPacks: TlpackManifestEntry[];
  v2LocalManifestPacks: TlpackManifestEntry[];
  v2ExtraMountedPacks: tt.LexiconCompactPackSummary[];
  groupedManifestPacks: [LexiconCategory, TlpackManifestEntry[]][];
  allOpenMounted: boolean;
  allLocalMounted: boolean;
  onLoadV2Tier: (tier: tt.LexiconPackTier) => void;
  onToggleV2ManifestPack: (entry: TlpackManifestEntry) => void;
  onLocalTlpackFiles: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onUnloadAllV2: () => void;
  onUnloadSingleV2Pack: (packId: string) => void;
  onOpenHistoricalMode: () => void;
  scopeOptions: ReturnType<typeof deriveFiniteScopeOptions>;
  selectedRegister: string;
  onChangeRegister: (nextRegister: string) => void;
  v2Domains: string[];
  v2Domain: string;
  onChangeV2Domain: (nextDomain: string) => void;
  queryDiagnostics: QueryDiagnostics;
  loadedTotals: { loadedPackIds: string[] };
  catalogAlignment: ReturnType<typeof verifyPackCatalogAlignment>;
  availablePackSet: Set<string>;
  selectedPacks: string[];
  onTogglePack: (packId: tt.LexiconPackId) => void;
  extendedManifest: ExtendedManifest | null;
  onPresetClick: (preset: ContractTestPreset) => void;
  lastRawRequest: string;
  lastRawResponse: string;
}

export function LexiconPackDrawer({
  ready,
  v2Stats,
  v2MountedIds,
  v2LoadingAction,
  v2Error,
  v2OpenManifestPacks,
  v2LocalManifestPacks,
  v2ExtraMountedPacks,
  groupedManifestPacks,
  allOpenMounted,
  allLocalMounted,
  onLoadV2Tier,
  onToggleV2ManifestPack,
  onLocalTlpackFiles,
  onUnloadAllV2,
  onUnloadSingleV2Pack,
  onOpenHistoricalMode,
  scopeOptions,
  selectedRegister,
  onChangeRegister,
  v2Domains,
  v2Domain,
  onChangeV2Domain,
  queryDiagnostics,
  loadedTotals,
  catalogAlignment,
  availablePackSet,
  selectedPacks,
  onTogglePack,
  extendedManifest,
  onPresetClick,
  lastRawRequest,
  lastRawResponse,
}: LexiconPackDrawerProps) {
  const { t, language } = useLanguage();
  const [devToolsOpen, setDevToolsOpen] = useState(false);
  const [showDataDetails, setShowDataDetails] = useState(false);
  const [showContractPresets, setShowContractPresets] = useState(false);
  const [showRawInspector, setShowRawInspector] = useState(false);
  const v2FileInputRef = useRef<HTMLInputElement>(null);

  return (
    <Card className="p-4 sm:p-5">
      <button
        type="button"
        onClick={() => setDevToolsOpen((prev) => !prev)}
        aria-expanded={devToolsOpen}
        className="w-full flex items-center justify-between gap-2 text-left min-h-[40px] cursor-pointer"
      >
        <div className="flex items-center gap-2.5">
          <SlidersHorizontal className="w-4 h-4 text-[var(--color-muted)] shrink-0" />
          <div>
            <span className="text-sm font-semibold text-[var(--color-mai)] block">
              {language === "ta"
                ? "தொகுப்பு மேலாண்மை & உருவாக்குநர் கருவிகள் (Manage Packs & Developer Tools)"
                : "Manage Packs & Developer Tools"}
            </span>
            <span className="text-xs text-[var(--color-muted)]">
              {language === "ta"
                ? ".tlpack தொகுப்புகள், தனிப்பயன் கோப்பு பதிவேற்றம், Raw JSON மற்றும் ஒப்பந்தச் சோதனைகள்"
                : "Per-pack mount table, custom .tlpack upload, domain/register filters, contract presets, and raw JSON"}
            </span>
          </div>
        </div>
        {devToolsOpen ? (
          <ChevronUp className="w-4 h-4 text-[var(--color-muted)] shrink-0" />
        ) : (
          <ChevronDown className="w-4 h-4 text-[var(--color-muted)] shrink-0" />
        )}
      </button>

      {devToolsOpen && (
        <div className="mt-4 pt-4 border-t border-[var(--border-line)] space-y-5">
          {/* Pack Engine v2 Quick Actions & Custom .tlpack File Uploader */}
          <div className="rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] p-3.5 space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex flex-wrap items-center gap-2">
                <Layers className="w-4 h-4 text-[var(--color-semman)] shrink-0" />
                <span className="text-xs font-semibold text-[var(--color-mai)]">
                  Pack Engine v2 (.tlpack)
                </span>
                <Badge
                  variant={v2Stats.pack_count > 0 ? "terracotta" : "mono"}
                  className="text-[11px]"
                >
                  {v2Stats.pack_count} mounted ·{" "}
                  {v2Stats.total_entries.toLocaleString()} entries ·{" "}
                  {formatPackBytes(v2Stats.total_bytes)}
                </Badge>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                {v2OpenManifestPacks.length > 0 && (
                  <Button
                    type="button"
                    size="sm"
                    variant={allOpenMounted ? "secondary" : "primary"}
                    disabled={!ready || v2LoadingAction !== null || allOpenMounted}
                    onClick={() => onLoadV2Tier("verified_open")}
                  >
                    {v2LoadingAction === "open" ? (
                      <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                    ) : (
                      <Download className="w-3.5 h-3.5 mr-1.5" />
                    )}
                    <span>Load Open Packs (90k)</span>
                  </Button>
                )}

                {!IS_OPEN_ONLY_CHANNEL && v2LocalManifestPacks.length > 0 && (
                  <Button
                    type="button"
                    size="sm"
                    variant={allLocalMounted ? "secondary" : "outline"}
                    disabled={
                      !ready || v2LoadingAction !== null || allLocalMounted
                    }
                    onClick={() => onLoadV2Tier("local_historical")}
                  >
                    {v2LoadingAction === "local" ? (
                      <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                    ) : (
                      <Database className="w-3.5 h-3.5 mr-1.5" />
                    )}
                    <span>Load Local Packs (241k)</span>
                  </Button>
                )}

                <input
                  ref={v2FileInputRef}
                  type="file"
                  accept=".tlpack"
                  multiple
                  aria-label="Load .tlpack file"
                  className="hidden"
                  onChange={onLocalTlpackFiles}
                />
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  disabled={!ready || v2LoadingAction !== null}
                  onClick={() => v2FileInputRef.current?.click()}
                >
                  {v2LoadingAction === "file" ? (
                    <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                  ) : (
                    <Upload className="w-3.5 h-3.5 mr-1.5" />
                  )}
                  <span>Load .tlpack File...</span>
                </Button>

                {v2Stats.pack_count > 0 && (
                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    disabled={!ready || v2LoadingAction !== null}
                    onClick={onUnloadAllV2}
                  >
                    <Trash2 className="w-3.5 h-3.5 mr-1" />
                    <span>Unload All</span>
                  </Button>
                )}

                {!IS_PUBLIC_BETA && (
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={onOpenHistoricalMode}
                  >
                    <Database className="w-3.5 h-3.5 mr-1.5" />
                    <span>307k CSV Source Explorer</span>
                  </Button>
                )}
              </div>
            </div>

            {v2Error && (
              <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-xs font-mono-tamil text-red-700 dark:text-red-300">
                {v2Error}
              </div>
            )}

            {/* Per-Pack Mount / Unmount Table grouped by Category */}
            {groupedManifestPacks.length > 0 && (
              <div className="overflow-x-auto rounded-lg border border-[var(--border-line)] bg-[var(--bg-surface)]">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-[var(--border-line)] bg-[var(--bg-raised)]/50 text-[var(--color-muted)]">
                    <tr>
                      <th className="px-3 py-2 font-semibold">Pack ID</th>
                      <th className="px-3 py-2 font-semibold">Category</th>
                      <th className="px-3 py-2 font-semibold">Tier / Rights</th>
                      <th className="px-3 py-2 font-semibold text-right">
                        Words / Rels
                      </th>
                      <th className="px-3 py-2 font-semibold text-right">
                        Size
                      </th>
                      <th className="px-3 py-2 font-semibold">SHA-256</th>
                      <th className="px-3 py-2 font-semibold text-right">
                        Action
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border-line)]/60">
                    {groupedManifestPacks.flatMap(([cat, entries]) =>
                      entries.map((entry) => {
                        const s = entry.summary;
                        const mounted = v2MountedIds.has(s.pack_id);
                        const busy = v2LoadingAction === s.pack_id;
                        const catMeta = getLexiconCategoryMeta(cat);
                        return (
                          <tr
                            key={s.pack_id}
                            className="hover:bg-[var(--bg-raised)]/30"
                          >
                            <td className="px-3 py-2 font-mono-tamil font-semibold text-[var(--color-mai)]">
                              {s.pack_id}
                            </td>
                            <td className="px-3 py-2 text-[var(--color-muted)]">
                              {language === "ta"
                                ? catMeta.label_ta
                                : catMeta.label_en}
                            </td>
                            <td className="px-3 py-2">
                              <PackTierBadge
                                tier={s.pack_tier}
                                language={language}
                              />
                            </td>
                            <td className="px-3 py-2 text-right font-mono-tamil text-[var(--color-muted)]">
                              {s.relation_count > 0
                                ? `${s.relation_count.toLocaleString()} rels`
                                : s.distinct_headwords.toLocaleString()}
                            </td>
                            <td className="px-3 py-2 text-right font-mono-tamil text-[var(--color-muted)]">
                              {formatPackBytes(s.byte_len)}
                            </td>
                            <td className="px-3 py-2 font-mono-tamil text-[11px] text-[var(--color-muted)]">
                              {s.checksum_sha256.slice(0, 12)}…
                            </td>
                            <td className="px-3 py-2 text-right">
                              <Button
                                type="button"
                                size="sm"
                                variant={mounted ? "outline" : "secondary"}
                                disabled={
                                  !ready ||
                                  busy ||
                                  v2LoadingAction === "open" ||
                                  v2LoadingAction === "local"
                                }
                                onClick={() => onToggleV2ManifestPack(entry)}
                              >
                                {busy && (
                                  <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                                )}
                                <span>{mounted ? "Unload" : "Mount"}</span>
                              </Button>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {v2ExtraMountedPacks.length > 0 && (
              <div className="space-y-2 pt-2">
                <span className="text-xs font-semibold text-[var(--color-mai)] block">
                  User-Loaded Local .tlpack Files
                </span>
                <div className="flex flex-wrap gap-2">
                  {v2ExtraMountedPacks.map((s) => (
                    <div
                      key={s.pack_id}
                      className="inline-flex items-center gap-2 rounded-lg border border-[var(--color-semman)] bg-[var(--bg-surface)] px-3 py-1.5 text-xs"
                    >
                      <span className="font-mono-tamil font-bold text-[var(--color-mai)]">
                        {s.pack_id}
                      </span>
                      <Badge variant="mono" className="text-[10px]">
                        {formatPackBytes(s.byte_len)}
                      </Badge>
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={() => onUnloadSingleV2Pack(s.pack_id)}
                      >
                        Unload
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Domain, Register & Query Diagnostics */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="space-y-1.5">
              <label
                htmlFor="lexicon-register-select"
                className="text-xs font-semibold text-[var(--color-mai)] block"
              >
                {t.tools.lexicon.registerFilterLabel} (
                {scopeOptions.registers.length})
              </label>
              <div className="relative">
                <select
                  id="lexicon-register-select"
                  value={selectedRegister}
                  onChange={(e) => onChangeRegister(e.target.value)}
                  className="appearance-none w-full min-h-[40px] pl-3 pr-9 py-2 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] text-xs font-mono-tamil text-[var(--color-mai)] cursor-pointer"
                >
                  <option value="">{t.tools.lexicon.allRegistersOption}</option>
                  {scopeOptions.registers.map((reg) => (
                    <option key={reg} value={reg}>
                      {reg}
                    </option>
                  ))}
                </select>
                <ChevronDown className="w-3.5 h-3.5 text-[var(--color-muted)] pointer-events-none absolute right-3 top-1/2 -translate-y-1/2" />
              </div>
            </div>

            {v2Domains.length > 0 && (
              <div className="space-y-1.5">
                <label
                  htmlFor="lexicon-v2-domain-select"
                  className="text-xs font-semibold text-[var(--color-mai)] block"
                >
                  {language === "ta"
                    ? `துறை வடிகட்டி (${v2Domains.length})`
                    : `Domain Filter (${v2Domains.length})`}
                </label>
                <div className="relative">
                  <select
                    id="lexicon-v2-domain-select"
                    value={v2Domain}
                    onChange={(e) => onChangeV2Domain(e.target.value)}
                    className="appearance-none w-full min-h-[40px] pl-3 pr-9 py-2 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] text-xs text-[var(--color-mai)] cursor-pointer"
                  >
                    <option value="ALL">
                      All domains ({v2Domains.length})
                    </option>
                    {v2Domains.map((dom) => (
                      <option key={dom} value={dom}>
                        {dom}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="w-3.5 h-3.5 text-[var(--color-muted)] pointer-events-none absolute right-3 top-1/2 -translate-y-1/2" />
                </div>
              </div>
            )}

            <div className="space-y-1.5">
              <span className="text-xs font-semibold text-[var(--color-mai)] block">
                Exact Query Diagnostics
              </span>
              <div className="flex flex-wrap items-center gap-1.5 pt-1">
                <Badge variant="mono" className="text-[10px]">
                  {queryDiagnostics.utf8Bytes} UTF-8 bytes
                </Badge>
                {queryDiagnostics.hasLeadingOrTrailingWhitespace && (
                  <Badge variant="sandhanam" className="text-[10px]">
                    whitespace preserved
                  </Badge>
                )}
                {queryDiagnostics.hasJoinersOrSoftHyphen && (
                  <Badge variant="terracotta" className="text-[10px]">
                    preserved: {queryDiagnostics.joinerLabels.join(", ")}
                  </Badge>
                )}
              </div>
            </div>
          </div>

          {/* Compiled v1 Pack Checkboxes & Attribution Notices (hidden in slim WASM builds with 0 embedded v1 packs) */}
          {availablePackSet.size > 0 && (
          <div className="space-y-2">
            <span className="text-xs font-semibold text-[var(--color-mai)] block">
              {t.tools.lexicon.packsLabel} (
              {loadedTotals.loadedPackIds.join(" + ") || "none"})
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
              {LEXICON_PACK_DISPLAY_ORDER.map((packId) => {
                const verification = catalogAlignment.byPack[packId];
                const isAvailableInBuild = availablePackSet.has(packId);
                const isChecked = selectedPacks.includes(packId);
                const noticeLinks = getPackNoticeLinks(packId);
                return (
                  <div
                    key={packId}
                    className={`p-3 rounded-xl border space-y-2 ${
                      isAvailableInBuild && isChecked
                        ? "border-[var(--color-semman)] bg-[var(--color-semman-light)]/30"
                        : "border-[var(--border-line)] bg-[var(--bg-canvas)]"
                    }`}
                  >
                    <label className="flex items-start gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={isChecked}
                        disabled={!isAvailableInBuild}
                        onChange={() => onTogglePack(packId)}
                        aria-label={packId}
                        className="mt-0.5 h-4 w-4 accent-[var(--color-semman)]"
                      />
                      <div className="min-w-0 flex-1">
                        <span className="text-xs font-mono-tamil font-bold text-[var(--color-mai)] block">
                          {packId}
                        </span>
                        <span className="text-[10px] font-mono-tamil text-[var(--color-muted)] block">
                          {verification.status === "verified" &&
                          verification.verifiedEntryCount !== null
                            ? `${verification.verifiedEntryCount.toLocaleString()} entries · ${(verification.verifiedSenseCount ?? 0).toLocaleString()} senses`
                            : t.tools.lexicon.packUnavailableBadge}
                        </span>
                      </div>
                    </label>
                    {noticeLinks.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 pt-1 border-t border-[var(--border-line)]/60">
                        {noticeLinks.slice(0, 2).map((nLink) => (
                          <a
                            key={nLink.href}
                            href={nLink.href}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-[10px] text-[var(--color-semman)] hover:underline"
                          >
                            <ExternalLink className="w-2.5 h-2.5 shrink-0" />
                            <span>
                              {language === "ta"
                                ? nLink.label_ta
                                : nLink.label_en}
                            </span>
                          </a>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
          )}

          {/* Data Coverage Summary Toggle */}
          <div className="rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] p-3 space-y-2">
            <button
              type="button"
              onClick={() => setShowDataDetails((prev) => !prev)}
              aria-expanded={showDataDetails}
              className="w-full flex items-center justify-between text-xs font-semibold text-[var(--color-mai)] cursor-pointer"
            >
              <span className="inline-flex items-center gap-1.5">
                <Info className="w-3.5 h-3.5 text-[var(--color-semman)]" />
                <span>{t.tools.lexicon.dataDetailsToggle}</span>
              </span>
              {showDataDetails ? (
                <ChevronUp className="w-3.5 h-3.5" />
              ) : (
                <ChevronDown className="w-3.5 h-3.5" />
              )}
            </button>
            {showDataDetails && (
              <div className="pt-2 border-t border-[var(--border-line)] space-y-2 text-xs text-[var(--color-muted)]">
                {availablePackSet.size > 0 ? (
                  <p>
                    Embedded WASM packs:{" "}
                    {catalogAlignment.verifiedLoadedEntries.toLocaleString()}{" "}
                    entries ·{" "}
                    {catalogAlignment.verifiedLoadedSenses.toLocaleString()}{" "}
                    senses ·{" "}
                    {(
                      catalogAlignment.verifiedDistinctHeadwords ?? 0
                    ).toLocaleString()}{" "}
                    distinct words.
                  </p>
                ) : (
                  <p>
                    Slim WASM build (0 embedded v1 bytes); dictionary data loads
                    progressively from .tlpack v2 packs ({v2Stats.pack_count}{" "}
                    mounted · {v2Stats.total_entries.toLocaleString()} entries).
                  </p>
                )}
                {extendedManifest && (
                  <p>
                    Extended verified dictionary (en.wiktionary.org +
                    ta.wiktionary.org, CC-BY-SA-4.0):{" "}
                    {extendedManifest.total_words.toLocaleString()} distinct
                    words (
                    {extendedManifest.tawiktionary_words.toLocaleString()} from
                    Tamil Wiktionary).
                  </p>
                )}
                {!IS_PUBLIC_BETA && (
                  <p>{t.tools.lexicon.historicalExclusionBody}</p>
                )}
              </div>
            )}
          </div>

          {/* Contract-Test Presets Toggle */}
          <div className="rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] p-3 space-y-2">
            <button
              type="button"
              onClick={() => setShowContractPresets((prev) => !prev)}
              aria-expanded={showContractPresets}
              className="w-full flex items-center justify-between text-xs font-semibold text-[var(--color-mai)] cursor-pointer"
            >
              <span className="inline-flex items-center gap-1.5">
                <FlaskConical className="w-3.5 h-3.5 text-[var(--color-sandhanam)]" />
                <span>{t.tools.lexicon.contractPresetsToggle}</span>
              </span>
              {showContractPresets ? (
                <ChevronUp className="w-3.5 h-3.5" />
              ) : (
                <ChevronDown className="w-3.5 h-3.5" />
              )}
            </button>
            {showContractPresets && (
              <div className="pt-2 border-t border-[var(--border-line)] grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                {CONTRACT_TEST_PRESETS.map((preset) => (
                  <button
                    key={preset.id}
                    type="button"
                    onClick={() => onPresetClick(preset)}
                    disabled={!ready}
                    className="p-2.5 rounded-lg border border-[var(--border-line)] bg-[var(--bg-surface)] hover:border-[var(--color-sandhanam)] text-left space-y-0.5 cursor-pointer disabled:opacity-50"
                  >
                    <div className="text-xs font-bold text-[var(--color-mai)]">
                      {language === "ta" ? preset.label_ta : preset.label_en}
                    </div>
                    <p className="text-[11px] text-[var(--color-muted)] leading-snug">
                      {language === "ta" ? preset.desc_ta : preset.desc_en}
                    </p>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Raw JSON Inspector Toggle (`define` / `lookup` payload) */}
          <div className="rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] p-3 space-y-2">
            <button
              type="button"
              onClick={() => setShowRawInspector((prev) => !prev)}
              aria-expanded={showRawInspector}
              className="w-full flex items-center justify-between text-xs font-semibold text-[var(--color-mai)] cursor-pointer"
            >
              <span className="inline-flex items-center gap-1.5">
                <BookMarked className="w-3.5 h-3.5 text-[var(--color-semman)]" />
                <span>{t.tools.lexicon.rawInspectorHeading}</span>
              </span>
              {showRawInspector ? (
                <ChevronUp className="w-3.5 h-3.5" />
              ) : (
                <ChevronDown className="w-3.5 h-3.5" />
              )}
            </button>
            {showRawInspector && (
              <div className="pt-2 border-t border-[var(--border-line)] grid grid-cols-1 lg:grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-semibold text-[var(--color-mai)]">
                      {t.tools.lexicon.rawRequestLabel}
                    </span>
                    <div className="flex items-center gap-1.5">
                      <CopyButton
                        text={lastRawRequest}
                        size="sm"
                        variant="outline"
                      />
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        disabled={!lastRawRequest}
                        onClick={() =>
                          downloadJsonFile(
                            "lexicon-request.json",
                            lastRawRequest
                          )
                        }
                      >
                        <Download className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  </div>
                  <pre className="text-[11px] font-mono-tamil bg-[var(--bg-surface)] border border-[var(--border-line)] rounded-lg p-2.5 max-h-64 overflow-auto text-[var(--color-mai)]">
                    {lastRawRequest || "{}"}
                  </pre>
                </div>
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-semibold text-[var(--color-mai)]">
                      {t.tools.lexicon.rawResponseLabel}
                    </span>
                    <div className="flex items-center gap-1.5">
                      <CopyButton
                        text={lastRawResponse}
                        size="sm"
                        variant="outline"
                      />
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        disabled={!lastRawResponse}
                        onClick={() =>
                          downloadJsonFile(
                            "lexicon-response.json",
                            lastRawResponse
                          )
                        }
                      >
                        <Download className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  </div>
                  <pre className="text-[11px] font-mono-tamil bg-[var(--bg-surface)] border border-[var(--border-line)] rounded-lg p-2.5 max-h-64 overflow-auto text-[var(--color-mai)]">
                    {lastRawResponse || "{}"}
                  </pre>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </Card>
  );
}
