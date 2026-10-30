import { execute as nativeExecute } from "../pkg-node/tamil_toolkit.js";
import { createApi } from "./api.js";
export type { Uyirmei, Request, Inspection } from "./api.js";
export const { execute, get_letters, normalize_nfc, normalize_nfd, split_uyirmei, compose_uyirmei, inspect_tamil_string } = createApi(nativeExecute);
