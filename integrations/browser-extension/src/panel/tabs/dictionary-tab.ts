import { getBrowserApi } from "../../shared/browser-api.js";
import type { UiStrings } from "../../shared/i18n.js";
import type { LexiconMountProfile } from "../../shared/messages.js";
import {
  DEFAULT_LEXICON_MANIFEST_URL,
  getPreferences,
  updatePreferences,
} from "../../shared/storage.js";
import {
  lexiconClient,
  type LexiconFuzzySearchHit,
  type LexiconPrefixSearchHit,
  type LexiconStatsResult,
  type LexiconWordDefinition,
  type UnifiedSearchResult,
} from "../../engine/lexicon-client.js";

export interface DictionaryTabContext {
  strings: () => UiStrings;
  getActiveTabId: () => Promise<number | undefined>;
}

function escapeHtml(raw: string): string {
  return raw
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

export function mountDictionaryTab(
  container: HTMLElement,
  ctx: DictionaryTabContext
): {
  refresh: () => Promise<void>;
  rerenderLabels: () => void;
} {
  const api = getBrowserApi();
  let query = "";
  let profile: LexiconMountProfile = "open-lite";
  let manifestUrl = DEFAULT_LEXICON_MANIFEST_URL;
  let stats: LexiconStatsResult | null = null;
  let result: UnifiedSearchResult | null = null;
  let statusMessage = "";
  let statusKind: "ok" | "warn" | "muted" = "muted";
  let isMounting = false;
  let settingsOpen = false;
  let debounceTimer: number | null = null;

  function renderWordCard(def: LexiconWordDefinition): string {
    const s = ctx.strings();
    const posBadges = def.pos
      .map((p) => `<span class="badge accent">${escapeHtml(p)}</span>`)
      .join("");
    const domainBadges = def.domains
      .slice(0, 4)
      .map((d) => `<span class="badge">${escapeHtml(d)}</span>`)
      .join("");
    const regionBadges = def.regions
      .slice(0, 4)
      .map((r) => `<span class="badge">${escapeHtml(r)}</span>`)
      .join("");
    const packBadges = Array.from(new Set(def.sources.map((src) => src.pack_id)))
      .slice(0, 4)
      .map((pid) => `<span class="badge ok">${escapeHtml(pid)}</span>`)
      .join("");

    const ipaHtml =
      def.ipa && def.ipa.length > 0
        ? `<div class="dict-ipa">/${escapeHtml(def.ipa.slice(0, 2).join(", /"))}/</div>`
        : "";

    const pureTamilHtml =
      def.pure_tamil_equivalents.length > 0
        ? `<div class="row" style="justify-content:flex-start;flex-wrap:wrap;gap:6px">
            <span class="muted">${escapeHtml(s.dictPureTamil)}:</span>
            ${def.pure_tamil_equivalents
              .slice(0, 4)
              .map(
                (term) =>
                  `<button class="btn sm dict-insert-term" data-term="${escapeHtml(term)}" type="button">${escapeHtml(term)}</button>`
              )
              .join("")}
          </div>`
        : "";

    const enMeanings = def.meanings_en.slice(0, 6);
    const taMeanings = def.meanings_ta.slice(0, 4);
    const syns = def.relations.synonyms.slice(0, 6);

    return `
      <div class="card stack">
        <div class="row">
          <div>
            <div class="dict-headword">${escapeHtml(def.headword)}</div>
            ${ipaHtml}
          </div>
          <div class="row" style="gap:4px">
            <button class="btn sm primary dict-insert-term" data-term="${escapeHtml(def.headword)}" type="button">${escapeHtml(s.insertIntoPage)}</button>
            <button class="btn sm dict-copy-term" data-term="${escapeHtml(def.headword)}" type="button">${escapeHtml(s.copy)}</button>
          </div>
        </div>

        ${
          posBadges || domainBadges || regionBadges || packBadges
            ? `<div class="badge-row">${posBadges}${domainBadges}${regionBadges}${packBadges}</div>`
            : ""
        }

        ${pureTamilHtml}

        ${
          enMeanings.length > 0
            ? `<div>
                <div class="muted">${escapeHtml(s.dictMeaningsEn)}</div>
                <ol class="dict-meaning-list">
                  ${enMeanings
                    .map(
                      (m) =>
                        `<li>${escapeHtml(m.text)} <span class="muted">(${escapeHtml(m.pack_id)})</span></li>`
                    )
                    .join("")}
                </ol>
              </div>`
            : ""
        }

        ${
          taMeanings.length > 0
            ? `<div>
                <div class="muted">${escapeHtml(s.dictMeaningsTa)}</div>
                <ol class="dict-meaning-list">
                  ${taMeanings
                    .map(
                      (m) =>
                        `<li>${escapeHtml(m.text)} <span class="muted">(${escapeHtml(m.pack_id)})</span></li>`
                    )
                    .join("")}
                </ol>
              </div>`
            : ""
        }

        ${
          syns.length > 0
            ? `<div class="badge-row">
                <span class="muted">${escapeHtml(s.dictSynonyms)}:</span>
                ${syns
                  .map(
                    (syn) =>
                      `<button class="btn sm dict-pick-word" data-word="${escapeHtml(syn)}" type="button">${escapeHtml(syn)}</button>`
                  )
                  .join("")}
              </div>`
            : ""
        }

        ${
          def.examples.length > 0
            ? `<div>
                <div class="muted">${escapeHtml(s.dictExamples)}</div>
                <div class="muted" style="margin-top:2px">${escapeHtml(def.examples[0])}</div>
              </div>`
            : ""
        }
      </div>
    `;
  }

  function renderHitButtons(
    hits: readonly (LexiconPrefixSearchHit | LexiconFuzzySearchHit)[],
    activeHeadword?: string
  ): string {
    const filtered = hits.filter((h) => h.headword !== activeHeadword).slice(0, 10);
    if (filtered.length === 0) return "";
    const s = ctx.strings();
    return `
      <div class="card stack">
        <strong style="font-size:12px">${escapeHtml(s.dictMatchesHeading)}</strong>
        <div class="stack" style="gap:5px">
          ${filtered
            .map((h) => {
              const pos = h.pos.slice(0, 2).join(", ");
              const packTag = h.packs.slice(0, 2).join(", ");
              const meta = [pos, packTag].filter(Boolean).join(" \u00B7 ");
              return `
                <button class="dict-hit-btn dict-pick-word" data-word="${escapeHtml(h.headword)}" type="button">
                  <div class="row">
                    <strong>${escapeHtml(h.headword)}</strong>
                    ${meta ? `<span class="muted">${escapeHtml(meta)}</span>` : ""}
                  </div>
                  ${h.preview_gloss ? `<div class="muted">${escapeHtml(h.preview_gloss)}</div>` : ""}
                </button>
              `;
            })
            .join("")}
        </div>
      </div>
    `;
  }

  function renderResultsBody(): string {
    const s = ctx.strings();
    const packCount = stats?.pack_count ?? 0;

    if (packCount === 0 && !result?.definition) {
      return `<div class="card muted">${escapeHtml(s.dictNoPacksMounted)}</div>`;
    }
    if (!query.trim()) {
      return `<div class="card muted">${escapeHtml(s.dictSearchHint)}</div>`;
    }
    if (!result) return "";

    const parts: string[] = [];
    if (result.definition) {
      parts.push(renderWordCard(result.definition));
    }

    const hits =
      result.mode === "english"
        ? result.englishHits
        : result.prefixHits.length > 0
          ? result.prefixHits
          : result.fuzzyHits;
    const hitsHtml = renderHitButtons(hits, result.definition?.headword);
    if (hitsHtml) parts.push(hitsHtml);

    if (parts.length === 0) {
      return `<div class="card muted">${escapeHtml(s.dictNoResults)}</div>`;
    }
    return parts.join("");
  }

  function render(): void {
    const s = ctx.strings();
    const packCount = stats?.pack_count ?? 0;
    const totalWords =
      stats?.packs.reduce((sum, p) => sum + p.distinct_headwords, 0) ?? 0;
    const statsLabel = s.dictStatsSummary(packCount, totalWords);

    container.innerHTML = `
      <div class="card stack">
        <div class="dict-search-row">
          <input type="text" id="dict-query" value="${escapeHtml(query)}" placeholder="${escapeHtml(s.dictSearchPlaceholder)}" />
          <button class="btn sm primary" id="dict-search-btn" type="button">\uD83D\uDD0D</button>
        </div>
        <div class="row">
          <button class="btn sm" id="dict-selection-btn" type="button">${escapeHtml(s.dictLookupSelection)}</button>
          <span class="muted" id="dict-stats-badge">${escapeHtml(statsLabel)}</span>
        </div>
      </div>

      ${
        statusMessage
          ? `<div class="card ${statusKind === "ok" ? "ok-text" : statusKind === "warn" ? "warn-text" : "muted"}" style="font-size:12px">${escapeHtml(statusMessage)}</div>`
          : ""
      }

      <div id="dict-results" class="stack">
        ${renderResultsBody()}
      </div>

      <details class="card dict-details" id="dict-pack-details" ${settingsOpen ? "open" : ""}>
        <summary>${escapeHtml(s.dictPackSettings)} (${escapeHtml(statsLabel)})</summary>
        <div class="stack" style="margin-top:8px">
          <div>
            <label class="muted" for="dict-profile">${escapeHtml(s.dictProfileLabel)}</label>
            <select id="dict-profile">
              <option value="open-lite">open-lite (~2.9 MB \u00B7 core, names, regional)</option>
              <option value="open">open (~15.3 MB \u00B7 + ta_wiktionary)</option>
              <option value="full">full (~45.6 MB \u00B7 + local historical)</option>
            </select>
          </div>

          <div>
            <label class="muted" for="dict-manifest-url">${escapeHtml(s.dictManifestUrlLabel)}</label>
            <input type="url" id="dict-manifest-url" value="${escapeHtml(manifestUrl)}" />
          </div>

          <div class="row">
            <button class="btn sm primary" id="dict-mount-btn" type="button" ${isMounting ? "disabled" : ""}>
              ${escapeHtml(isMounting ? s.dictMounting : s.dictMountProfile)}
            </button>
            <button class="btn sm" id="dict-clear-btn" type="button" ${packCount === 0 || isMounting ? "disabled" : ""}>
              ${escapeHtml(s.dictClearPacks)}
            </button>
          </div>

          <div>
            <label class="muted" for="dict-local-files">${escapeHtml(s.dictLoadLocalFiles)}</label>
            <input type="file" id="dict-local-files" accept=".tlpack" multiple style="margin-top:4px;font-size:11.5px;width:100%" />
          </div>

          ${
            stats && stats.packs.length > 0
              ? `<div class="dict-pack-list">
                  ${stats.packs
                    .map(
                      (p) => `
                        <div class="dict-pack-item">
                          <span><strong>${escapeHtml(p.pack_id)}</strong> (${p.distinct_headwords.toLocaleString()})</span>
                          <button class="btn sm dict-unload-pack" data-pack="${escapeHtml(p.pack_id)}" type="button">\u2715</button>
                        </div>`
                    )
                    .join("")}
                </div>`
              : ""
          }
        </div>
      </details>
    `;

    wireEvents();
  }

  function wireEvents(): void {
    const s = ctx.strings();
    const queryEl = container.querySelector("#dict-query") as HTMLInputElement | null;
    const profileEl = container.querySelector("#dict-profile") as HTMLSelectElement | null;
    const manifestEl = container.querySelector("#dict-manifest-url") as HTMLInputElement | null;
    const detailsEl = container.querySelector("#dict-pack-details") as HTMLDetailsElement | null;

    if (profileEl) {
      profileEl.value = profile;
      profileEl.addEventListener("change", async () => {
        profile = profileEl.value as LexiconMountProfile;
        await updatePreferences({ lexiconProfile: profile });
      });
    }

    if (manifestEl) {
      manifestEl.addEventListener("change", async () => {
        const nextUrl = manifestEl.value.trim() || DEFAULT_LEXICON_MANIFEST_URL;
        manifestUrl = nextUrl;
        const saved = await updatePreferences({ lexiconManifestUrl: nextUrl });
        manifestUrl = saved.lexiconManifestUrl;
        manifestEl.value = manifestUrl;
      });
    }

    detailsEl?.addEventListener("toggle", () => {
      settingsOpen = detailsEl.open;
    });

    queryEl?.addEventListener("input", () => {
      query = queryEl.value;
      if (debounceTimer !== null) window.clearTimeout(debounceTimer);
      debounceTimer = window.setTimeout(() => {
        void runSearch();
      }, 160);
    });

    queryEl?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        if (debounceTimer !== null) window.clearTimeout(debounceTimer);
        void runSearch();
      }
    });

    container.querySelector("#dict-search-btn")?.addEventListener("click", () => {
      void runSearch();
    });

    container.querySelector("#dict-selection-btn")?.addEventListener("click", () => {
      void lookupSelectionFromPage();
    });

    container.querySelector("#dict-mount-btn")?.addEventListener("click", () => {
      void mountSelectedProfile();
    });

    container.querySelector("#dict-clear-btn")?.addEventListener("click", () => {
      try {
        lexiconClient.clearAllPacks();
        stats = lexiconClient.getStats();
        result = null;
        statusMessage = "";
        render();
      } catch (err) {
        statusMessage = err instanceof Error ? err.message : String(err);
        statusKind = "warn";
        render();
      }
    });

    const localInput = container.querySelector("#dict-local-files") as HTMLInputElement | null;
    localInput?.addEventListener("change", async () => {
      if (!localInput.files || localInput.files.length === 0) return;
      isMounting = true;
      statusMessage = s.dictMounting;
      statusKind = "muted";
      render();
      try {
        const batch = await lexiconClient.mountLocalFiles(localInput.files);
        stats = lexiconClient.getStats();
        if (batch.errors.length > 0) {
          statusMessage = batch.errors.map((e) => `${e.fileName}: ${e.message}`).join("; ");
          statusKind = "warn";
        } else {
          statusMessage = `Mounted ${batch.mounted.length} local pack(s).`;
          statusKind = "ok";
        }
        await runSearch(false);
      } catch (err) {
        statusMessage = err instanceof Error ? err.message : String(err);
        statusKind = "warn";
      } finally {
        isMounting = false;
        render();
      }
    });

    container.querySelectorAll(".dict-unload-pack").forEach((btn) => {
      btn.addEventListener("click", () => {
        const packId = (btn as HTMLElement).dataset.pack;
        if (!packId) return;
        lexiconClient.unloadPack(packId);
        stats = lexiconClient.getStats();
        void runSearch();
      });
    });

    container.querySelectorAll(".dict-pick-word").forEach((btn) => {
      btn.addEventListener("click", () => {
        const word = (btn as HTMLElement).dataset.word;
        if (!word) return;
        query = word;
        void runSearch();
      });
    });

    container.querySelectorAll(".dict-insert-term").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const term = (btn as HTMLElement).dataset.term;
        if (!term) return;
        const tabId = await ctx.getActiveTabId();
        await api.runtime
          .sendMessage({ type: "PANEL_INSERT_TAB_TEXT", tabId, text: term })
          .catch(() => undefined);
      });
    });

    container.querySelectorAll(".dict-copy-term").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const term = (btn as HTMLElement).dataset.term;
        if (!term) return;
        await navigator.clipboard.writeText(term);
        const button = btn as HTMLButtonElement;
        button.textContent = s.copied;
        window.setTimeout(() => {
          button.textContent = s.copy;
        }, 1200);
      });
    });
  }

  async function runSearch(rerender = true): Promise<void> {
    if (!query.trim()) {
      result = null;
      if (rerender) render();
      return;
    }
    try {
      await lexiconClient.ensureReady();
      stats = lexiconClient.getStats();
      result = lexiconClient.searchUnified(query, 12);
      if (rerender) {
        const resultsEl = container.querySelector("#dict-results");
        if (resultsEl) {
          resultsEl.innerHTML = renderResultsBody();
          wireEvents();
        } else {
          render();
        }
      }
    } catch (err) {
      statusMessage = err instanceof Error ? err.message : String(err);
      statusKind = "warn";
      if (rerender) render();
    }
  }

  async function lookupSelectionFromPage(): Promise<void> {
    const tabId = await ctx.getActiveTabId();
    try {
      const res = await api.runtime.sendMessage({
        type: "PANEL_GET_TAB_CONTEXT_TEXT",
        tabId,
        mode: "auto",
      });
      if (res?.ok && typeof res.text === "string" && res.text.trim()) {
        query = res.text.trim().split(/\s+/)[0] ?? "";
        render();
        await runSearch();
      }
    } catch {
      // Ignore on restricted pages
    }
  }

  async function mountSelectedProfile(): Promise<void> {
    const s = ctx.strings();
    isMounting = true;
    statusMessage = s.dictMounting;
    statusKind = "muted";
    render();
    try {
      const saved = await updatePreferences({
        lexiconProfile: profile,
        lexiconManifestUrl: manifestUrl,
      });
      manifestUrl = saved.lexiconManifestUrl;
      await lexiconClient.mountProfile(profile, manifestUrl, {
        onProgress: (p) => {
          statusMessage = p.done
            ? ""
            : `${s.dictMounting} (${p.loadedPacks}/${p.totalPacks}${p.lastPackId ? ` \u00B7 ${p.lastPackId}` : ""})`;
          const badge = container.querySelector("#dict-stats-badge");
          if (badge && statusMessage) badge.textContent = statusMessage;
        },
      });
      stats = lexiconClient.getStats();
      statusMessage = s.dictStatsSummary(
        stats.pack_count,
        stats.packs.reduce((sum, p) => sum + p.distinct_headwords, 0)
      );
      statusKind = "ok";
      await runSearch(false);
    } catch (err) {
      statusMessage = err instanceof Error ? err.message : String(err);
      statusKind = "warn";
    } finally {
      isMounting = false;
      render();
    }
  }

  async function refresh(): Promise<void> {
    const prefs = await getPreferences();
    profile = prefs.lexiconProfile;
    manifestUrl = prefs.lexiconManifestUrl;
    try {
      await lexiconClient.ensureReady();
      stats = lexiconClient.getStats();
    } catch (err) {
      statusMessage = err instanceof Error ? err.message : String(err);
      statusKind = "warn";
    }
    render();
  }

  render();

  return {
    refresh,
    rerenderLabels: render,
  };
}
