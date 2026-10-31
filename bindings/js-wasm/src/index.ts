import { execute as nativeExecute } from "../pkg-node/tamil_toolkit.js";
import { createApi } from "./api.js";
export type { Uyirmei, Request, Inspection, Locale, Currency, CodecErrorPolicy, DigitStyle, DateStyle } from "./api.js";
export const { execute, get_letters, normalize_nfc, normalize_nfd, split_uyirmei, compose_uyirmei, inspect_tamil_string, compare, sort_words, sort_key, search_key, to_words, format_currency, currency_to_words, bamini_to_unicode, unicode_to_bamini, tam_bytes_to_unicode, unicode_to_tam_bytes, tab_bytes_to_unicode, unicode_to_tab_bytes, tscii_bytes_to_unicode, unicode_to_tscii_bytes, format_fraction, fraction_to_words, fraction_symbol, format_date } = createApi(nativeExecute);
