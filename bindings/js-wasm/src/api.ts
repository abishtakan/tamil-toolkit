export interface Uyirmei { mei: string; uyir: string }
export interface Request { op: string; input: unknown }
export interface Inspection {
  nfc: string; nfd: string; is_nfc: boolean; is_nfd: boolean;
  ezhuthu_count: number; grapheme_count: number;
  letters: { text: string; classification: string }[];
}

/** Serialization only. The Rust dispatcher owns every operation. */
export function createApi(nativeExecute: (request: string) => string) {
  const execute = (request: Request): unknown => JSON.parse(nativeExecute(JSON.stringify(request)));
  return {
    execute,
    get_letters: (text: string) => execute({ op: "get_letters", input: text }) as string[],
    normalize_nfc: (text: string) => execute({ op: "normalize_nfc", input: text }) as string,
    normalize_nfd: (text: string) => execute({ op: "normalize_nfd", input: text }) as string,
    split_uyirmei: (text: string) => execute({ op: "split_uyirmei", input: text }) as Uyirmei,
    compose_uyirmei: (mei: string, uyir: string) => execute({ op: "compose_uyirmei", input: { mei, uyir } }) as string,
    inspect_tamil_string: (text: string) => execute({ op: "inspect_tamil_string", input: text }) as Inspection,
    compare: (left: string, right: string) => execute({ op: "compare", input: { left, right } }) as -1 | 0 | 1,
    sort_words: (words: string[]) => execute({ op: "sort_words", input: words }) as string[],
    sort_key: (text: string) => execute({ op: "sort_key", input: text }) as number[],
    search_key: (text: string) => execute({ op: "search_key", input: text }) as number[],
  };
}
