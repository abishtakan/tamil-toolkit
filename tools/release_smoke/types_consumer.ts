import { format_date, format_fraction, get_letters, lexicon_lookup, lexicon_packs, type DateStyle, type LexiconLookupOptions, type LexiconLookupResponse, type LexiconPackInfo, type Locale } from "tamil-toolkit";
import { init, to_words, lexicon_lookup as webLexiconLookup, lexicon_packs as webLexiconPacks } from "tamil-toolkit/web";

const locale: Locale = "SL";
const style: DateStyle = "full";
const date: string = format_date(2024, 2, 29, locale, style, "tamil");
const fraction: string = format_fraction(2, 4);
const letters: string[] = get_letters("\u0ba4\u0bae\u0bbf\u0bb4\u0bcd");
const ready: ReturnType<typeof init> = init();
const words: string = to_words(1025, locale);
const options: LexiconLookupOptions = { packs: ["core", "names_taxa", "regional"], region: "TN", register: "literary" };
const checkLexiconTypes = (run: boolean): void => {
  if (!run) return;
  const packs: LexiconPackInfo[] = lexicon_packs();
  const webPacks: LexiconPackInfo[] = webLexiconPacks();
  const hit: LexiconLookupResponse = lexicon_lookup("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", options);
  const webHit: LexiconLookupResponse = webLexiconLookup("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", options);
  void [packs, webPacks, hit, webHit];
};
void [date, fraction, letters, ready, words, checkLexiconTypes];
