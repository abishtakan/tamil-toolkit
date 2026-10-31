import { execute as nativeExecute } from "../pkg-node/tamil_toolkit.js";
import { createApi } from "./api.js";
export type { Uyirmei, Request, Inspection, Locale, Currency } from "./api.js";
export const { execute, get_letters, normalize_nfc, normalize_nfd, split_uyirmei, compose_uyirmei, inspect_tamil_string, compare, sort_words, sort_key, search_key, to_words, format_currency, currency_to_words } = createApi(nativeExecute);
