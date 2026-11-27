"""Deterministic offline lexicon cleaning, deduplication, and organization pipeline.

Reads verified open Wiktionary sources and frozen historical CSV sources
read-only, verifies integrity hashes fail-closed, cleans and normalizes entries
and relations into deterministic per-pack JSONL/JSON artifacts, and writes a
complete machine-readable ``cleaning_audit.json`` proving exact row coverage.
"""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import gzip
import hashlib
import html
import json
from pathlib import Path
import re
import sys
import tomllib
from typing import Any
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "target/lexicon/organized"
DEFAULT_HISTORICAL_DIR = ROOT / "data/sources/tamil-lexicon"
DEFAULT_HISTORICAL_PIN = ROOT / "data/sources/tamil-lexicon.sha256.json"
DEFAULT_TAWIKT_MANIFEST = ROOT / "data/sources/tawiktionary-tamil/snapshots_manifest.json"
DEFAULT_TAWIKT_ENTRIES = ROOT / "target/lexicon/tawiktionary-bulk/entries.jsonl.gz"
DEFAULT_OPEN_PACKS = {
    "core": ROOT / "lexicon/dictionary",
    "names_taxa": ROOT / "lexicon/packs/names_taxa",
    "regional": ROOT / "lexicon/packs/regional",
}

DATASET_VERSION = "0.2.0"
SCHEMA_VERSION = 2
EXPECTED_HISTORICAL_TOTAL_ROWS = 307243

VALID_POS = frozenset({
    "NOUN",
    "VERB",
    "ADJ",
    "ADV",
    "PRON",
    "NUM",
    "INTJ",
    "CONJ",
    "ADP",
    "PART",
    "DET",
    "PROPN",
    "PHRASE",
})

POS_ALIASES = {
    "PROPER NOUN": "PROPN",
    "PROPER_NOUN": "PROPN",
    "ADJECTIVE": "ADJ",
    "ADVERB": "ADV",
    "PRONOUN": "PRON",
    "NUMERAL": "NUM",
    "NUMBER": "NUM",
    "INTERJECTION": "INTJ",
    "CONJUNCTION": "CONJ",
    "ADPOSITION": "ADP",
    "POSTPOSITION": "ADP",
    "PREPOSITION": "ADP",
    "PARTICLE": "PART",
    "DETERMINER": "DET",
    "MWE": "PHRASE",
}

DIALECT_REGION_MAP = {
    "kongu": "KONGU",
    "madras baashai": "CHENNAI",
    "chennai": "CHENNAI",
    "jaffna": "JAFFNA",
    "madurai": "MADURAI",
    "nellai": "NELLAI",
    "tirunelveli": "NELLAI",
    "general spoken": "SPOKEN",
    "spoken": "SPOKEN",
    "gen-z / cinema": "GEN_Z",
    "gen_z": "GEN_Z",
    "batticaloa": "BATTICALOA",
    "vanni": "VANNI",
    "up-country": "UP_COUNTRY",
    "up_country": "UP_COUNTRY",
    "trincomalee": "TRINCOMALEE",
    "thanjavur": "THANJAVUR",
    "kanyakumari": "KANYAKUMARI",
    "pudukkottai": "PUDUKKOTTAI",
}

_RE_CONSONANT_CENT = re.compile(r"([\u0b95-\u0bb9])\u00a2")
_RE_MOJIBAKE_SCAN = re.compile(r"[\u00a2\u00a3\u00e1\u00e2]")
_RE_MOJIBAKE_ANY = re.compile(r"[\u00a2\u00a3\u00a4\u00a6]")
_RE_EN_STRAY_CENT = re.compile(r"([A-Za-z0-9])\u00a2(?=$|\s|[,.;:!?)\]])")
_RE_TAWIKT_TRAILING_MOJIBAKE = re.compile(r"(?:,\s*|\s+)[\u00a2\u00a6]+$")
_RE_TAWIKT_BAD_HW = re.compile(r"[\u00a4\u00a6]")
_RE_TAMIL_SCRIPT = re.compile(r"[\u0b80-\u0bff]")
_RE_ASCII_ALPHA = re.compile(r"[A-Za-z]")
_RE_WORDNET_LEXNAME = re.compile(r"^(?:noun|verb|adj|adv)\.[A-Za-z_]+$", re.IGNORECASE)
_RE_HTML_COMMENT = re.compile(r"<!--+.*?(?:-->|$)", re.DOTALL)
_RE_NBSP_ENTITY = re.compile(r"&nbsp;?", re.IGNORECASE)

_DOMAIN_ACRONYMS = frozenset({"IT", "AI", "DNA", "ICT", "LGBTQ", "TV", "API", "UI", "OS", "CPU"})
_DOMAIN_SMALL_WORDS = frozenset({"and", "of", "the", "or", "in", "on", "for", "to", "a", "an"})
WORDNET_DOMAIN_MAP: dict[str, str | None] = {
    "noun.animal": "Zoology",
    "noun.plant": "Botany",
    "noun.body": "Anatomy",
    "noun.food": "Food & Cooking",
    "noun.artifact": "Artifacts & Tools",
    "noun.location": "Geography",
    "noun.time": "Time & Calendar",
    "noun.phenomenon": "Nature & Weather",
    "noun.substance": "Chemistry & Materials",
    "noun.cognition": "Mind & Knowledge",
    "noun.communication": "Language & Communication",
    "noun.group": "Society & Groups",
    "noun.person": "People & Roles",
    "noun.quantity": "Mathematics & Measures",
    "noun.feeling": "Emotion",
    "noun.tops": None,
    "noun.act": None,
    "noun.attribute": None,
    "noun.event": None,
    "noun.motive": None,
    "noun.object": None,
    "noun.possession": None,
    "noun.process": None,
    "noun.relation": None,
    "noun.shape": None,
    "noun.state": None,
}
_RE_LEADING_MOJIBAKE_A_HAT = re.compile(r"^\u00e2\s+")
_RE_KALAICHOL_PREFIX = re.compile(r"^\(\s*\u0baa\u0bc6\u0bb0\u0bc1\u0bae\u0bcd\u0baa\u0bbe\u0bb2\u0bc1\u0bae\u0bcd\s+\u0b95\u0bb2\u0bc8\u0b9a\u0bcd\u0b9a\u0bca\u0bb2\u0bcd\u0bb2\u0bbe\u0b95\s*\)\s*")
_RE_LEADING_SENSE_TAG = re.compile(
    r"^\(\s*(?:transitive|intransitive|transitive\s*,\s*intransitive|archaic|colloquial|"
    r"figurative|literary|dialectal|rare|obsolete|slang|informal|formal|dated|countable|"
    r"uncountable|idiomatic|pejorative|offensive|humorous|poetic|honorific|plural|singular)\s*\)\s*",
    re.IGNORECASE,
)
_RE_INFLECTED_FORM_GLOSS = re.compile(
    r"\b(?:"
    r"(?:vocative|accusative|dative|genitive|benefactive|locative|sociative|instrumental|ablative|nominative)\s+(?:singular\s+|plural\s+)?of"
    r"|(?:singular|plural)\s+of"
    r"|(?:present|past|future|negative|verbal|adjectival|adverbial)?\s*(?:adjectival|adverbial)?\s*participle\s+of"
    r"|(?:first|second|third)-person\s+[^()]*?\bof"
    r"|(?:plain\s+)?infinitive\s+of"
    r"|(?:form\s+two\s+)?gerund\s+of"
    r"|imperative\s+of"
    r"|conditional\s+of"
    r"|honorific\s+[^()]*?\bof"
    r"|(?:alternative|rare|archaic|colloquial|spoken\s+tamil|nonstandard|standard|obsolete|dialectal|emphatic|adjectival|short|dated|literary)\s+(?:form|spelling)\s+of"
    r"|adjectival\s+of"
    r"|abbreviation\s+of"
    r"|alphasyllabic\s+(?:combination|compound)\s+of"
    r")\b",
    re.IGNORECASE,
)
_RE_VARIANT_FORM_OF = re.compile(
    r"\b(?:alternative|rare|archaic|colloquial|spoken\s+tamil|nonstandard|standard|obsolete|dialectal)\s+(?:form|spelling)\s+of\b",
    re.IGNORECASE,
)
_RE_NUMBERED_SUBSENSE = re.compile(r"(?:^|\s)(\d+\.\s+)")
_RE_TRANSITIVITY_BOTH = ("\u0b87\u0bb0\u0bc1\u0bb5\u0bbf\u0ba9\u0bc8",)
_RE_TRANSITIVITY_INTRANS = ("\u0ba4\u0ba9\u0bcd\u0bb5\u0bbf\u0ba9\u0bc8",)
_RE_TRANSITIVITY_TRANS = ("\u0baa\u0bbf\u0bb1\u0bb5\u0bbf\u0ba9\u0bc8",)


def _clean_text_value(text: str, *, strip_leading_a_hat: bool = False) -> str:
    """Unescape HTML entities, strip HTML comments/NBSP, normalize curly quotes, collapse whitespace."""
    if not text:
        return ""
    s = _RE_HTML_COMMENT.sub(" ", text)
    s = _RE_NBSP_ENTITY.sub(" ", s)
    s = html.unescape(s)
    s = s.replace("\u00a0", " ")
    s = (
        s.replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
    )
    s = " ".join(s.split())
    if strip_leading_a_hat:
        s = _RE_LEADING_MOJIBAKE_A_HAT.sub("", s).strip()
    return s


def _balance_parens(text: str) -> tuple[str, bool]:
    """Safely fix unbalanced leading/trailing/unmatched parentheses without splitting valid glosses."""
    if not text or ("(" not in text and ")" not in text):
        return text, False
    stack: list[int] = []
    unmatched_close: set[int] = set()
    for idx, ch in enumerate(text):
        if ch == "(":
            stack.append(idx)
        elif ch == ")":
            if stack:
                stack.pop()
            else:
                unmatched_close.add(idx)
    if not stack and not unmatched_close:
        return text, False

    chars: list[str] = []
    for idx, ch in enumerate(text):
        if idx in unmatched_close:
            continue
        if idx in stack and idx == len(text) - 1:
            continue
        chars.append(ch)
    cleaned = " ".join("".join(chars).split()).strip()
    # Re-check remaining unclosed '(' with trailing text -> close them cleanly at end
    rem_stack: list[int] = []
    for idx, ch in enumerate(cleaned):
        if ch == "(":
            rem_stack.append(idx)
        elif ch == ")" and rem_stack:
            rem_stack.pop()
    if rem_stack:
        # Drop trailing empty '(' or append missing ')' if content follows
        if cleaned.endswith("("):
            cleaned = cleaned[:-1].strip()
        else:
            cleaned = cleaned + (")" * len(rem_stack))
    return cleaned, True


def _is_junk_non_tamil_gloss(text: str) -> bool:
    """Return True for stray Latin-1/symbol/mojibake artifacts without Tamil or ASCII words."""
    s = text.strip()
    if not s:
        return True
    if _RE_TAMIL_SCRIPT.search(s) or re.search(r"[A-Za-z0-9]", s):
        return False
    if _RE_MOJIBAKE_ANY.search(s) or _RE_MOJIBAKE_SCAN.search(s):
        return True
    return len(s) <= 2 and any(ord(ch) >= 0x80 for ch in s)


def _split_single_bilingual_segment(seg: str) -> tuple[str, str | None]:
    """Split one 'English, Tamil' / 'English; Tamil' / 'English - Tamil' segment at depth 0."""
    depth = 0
    n = len(seg)
    for i, ch in enumerate(seg):
        if ch in "([":
            depth += 1
        elif ch in ")]" and depth > 0:
            depth -= 1
        elif depth == 0:
            sep_len = 0
            if seg.startswith(", ", i) or seg.startswith("; ", i):
                sep_len = 2
            elif seg.startswith(" - ", i):
                sep_len = 3
            elif ch in ",;" and i + 1 < n and _RE_TAMIL_SCRIPT.match(seg[i + 1]):
                sep_len = 1
            if sep_len:
                rest = seg[i + sep_len :].lstrip()
                if re.match(r'^[\'"\-\s]*[\u0b80-\u0bff]', rest):
                    en_part = seg[:i].strip(" ,;-")
                    ta_part = rest.strip()
                    if en_part and _RE_ASCII_ALPHA.search(en_part):
                        return en_part, ta_part
    return seg, None


def _split_bilingual_en_ta(text: str) -> tuple[str, str | None]:
    """Split Madras-Lexicon bilingual English+Tamil text into (english, tamil).

    Purely Tamil strings (no Latin ASCII letters) return ("", text).
    """
    if not text:
        return "", None
    if not _RE_TAMIL_SCRIPT.search(text):
        return text, None
    if not _RE_ASCII_ALPHA.search(text):
        return "", text

    en_direct, ta_direct = _split_single_bilingual_segment(text)
    if ta_direct is None:
        return text, None

    # Handle numbered multi-sense entries like "1. Viṣṇu, திருமால். ... 2. Šiva, சிவன்."
    if re.search(r"\b\d+\.\s+[A-Za-z]", ta_direct):
        parts = _RE_NUMBERED_SUBSENSE.split(text)
        # parts alternates: [prefix, "1. ", body1, "2. ", body2, ...]
        if len(parts) >= 3:
            en_chunks: list[str] = []
            ta_chunks: list[str] = []
            if parts[0].strip():
                p_en, p_ta = _split_single_bilingual_segment(parts[0].strip())
                if p_en:
                    en_chunks.append(p_en)
                if p_ta:
                    ta_chunks.append(p_ta)
            for idx in range(1, len(parts), 2):
                marker = parts[idx].strip()
                body = parts[idx + 1].strip() if idx + 1 < len(parts) else ""
                b_en, b_ta = _split_single_bilingual_segment(body)
                if b_en:
                    en_chunks.append(f"{marker} {b_en}".strip())
                if b_ta:
                    ta_chunks.append(b_ta)
            if en_chunks and ta_chunks:
                return " ".join(en_chunks), "; ".join(ta_chunks)

    return en_direct, ta_direct


def _extract_transitivity(grammatical_subclass: str | None) -> str | None:
    """Extract canonical transitivity from Tamil/English grammatical_subclass."""
    if not grammatical_subclass:
        return None
    s = grammatical_subclass.strip()
    if not s:
        return None
    has_both = any(tok in s for tok in _RE_TRANSITIVITY_BOTH)
    has_intrans = any(tok in s for tok in _RE_TRANSITIVITY_INTRANS) or bool(re.search(r"\bintransitive\b", s, re.I))
    has_trans = any(tok in s for tok in _RE_TRANSITIVITY_TRANS) or bool(re.search(r"\btransitive\b", s, re.I))
    if has_both or (has_intrans and has_trans):
        return "ambitransitive"
    if has_intrans:
        return "intransitive"
    if has_trans:
        return "transitive"
    return None


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def _normalize_nfc(text: str) -> tuple[str, bool]:
    """Return NFC-normalized text and whether normalization changed it.

    Never removes ZWJ (U+200D) or ZWNJ (U+200C).
    """
    nfc = unicodedata.normalize("NFC", text)
    return nfc, nfc != text


def _strip_bom_logged(text: str) -> tuple[str, int]:
    """Strip U+FEFF BOM artifacts if present, returning cleaned text and count."""
    if "\ufeff" not in text:
        return text, 0
    count = text.count("\ufeff")
    return text.replace("\ufeff", ""), count


def normalize_pos(raw: str | None) -> str | None:
    """Normalize a POS label to uppercase canonical vocabulary or None."""
    if not raw:
        return None
    cleaned = " ".join(raw.strip().upper().split())
    if not cleaned:
        return None
    if cleaned in VALID_POS:
        return cleaned
    return POS_ALIASES.get(cleaned)


def _strip_stray_en_mojibake(text: str) -> str:
    """Strip stray cent-sign artifacts attached to ASCII words such as 'profile\u00a2'."""
    if not text or "\u00a2" not in text:
        return text
    return _RE_EN_STRAY_CENT.sub(r"\1", text)


def _strip_stray_quotes_and_parens(token: str) -> str:
    """Strip stray wrapping quotes and unbalanced/outer-wrapping parentheses from a token."""
    s = token.strip().strip("'\"").strip()
    if not s:
        return ""
    s, _ = _balance_parens(s)
    if s.startswith("(") and s.endswith(")"):
        depth = 0
        single_wrap = True
        for i, ch in enumerate(s):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0 and i < len(s) - 1:
                    single_wrap = False
                    break
        if single_wrap:
            s = s[1:-1].strip()
    return s.strip("'\"").strip()


def _title_case_domain_token(token: str) -> str:
    """Normalize a single atomic domain token to canonical Title Case while preserving acronyms."""
    s = " ".join(token.replace("_", " ").split())
    words = s.split(" ")
    out: list[str] = []
    for idx, word in enumerate(words):
        match = re.match(r"^([^A-Za-z0-9]*)([A-Za-z0-9]+)([^A-Za-z0-9]*)$", word)
        if not match:
            out.append(word)
            continue
        pre, core, post = match.groups()
        upper = core.upper()
        lower = core.lower()
        if upper in _DOMAIN_ACRONYMS:
            norm = upper
        elif idx > 0 and not pre and lower in _DOMAIN_SMALL_WORDS:
            norm = lower
        else:
            norm = lower.capitalize()
        out.append(f"{pre}{norm}{post}")
    return " ".join(out)


def _clean_domain_value(
    raw_domain: str | None,
) -> tuple[str | None, str | None, dict[str, Any]]:
    """Clean, split, map WordNet lexnames, and canonicalize a raw domain value.

    Returns ``(clean_domain, salvaged_tamil_gloss, metadata)``.
    If ``raw_domain`` contains Tamil script, starts with ``/`` or ``.``, or is
    sentence-like (contains ``...`` or an unsplit token longer than 48 chars),
    the domain is cleared to ``None`` and clean Tamil synonyms are salvaged.
    """
    meta: dict[str, Any] = {
        "corrupted": False,
        "typo_fixed": False,
        "ws_changed": False,
        "wn_mapped": 0,
        "wn_dropped": 0,
    }
    if not raw_domain:
        return None, None, meta

    cleaned = _clean_text_value(raw_domain)
    if not cleaned:
        return None, None, meta
    meta["ws_changed"] = cleaned != raw_domain.strip()

    is_corrupted_whole = (
        bool(_RE_TAMIL_SCRIPT.search(cleaned))
        or cleaned.startswith(("/", "."))
        or "..." in cleaned
        or ("," not in cleaned and ";" not in cleaned and len(cleaned) > 48)
    )
    if is_corrupted_whole:
        meta["corrupted"] = True
        salvaged_ta: str | None = None
        if not cleaned.startswith(".") and "..." not in cleaned:
            cand = cleaned.lstrip("/ ").strip()
            if (
                cand
                and _RE_TAMIL_SCRIPT.search(cand)
                and not _RE_MOJIBAKE_ANY.search(cand)
                and not _RE_MOJIBAKE_SCAN.search(cand)
            ):
                cand_bal, _ = _balance_parens(cand)
                cand_nfc, _ = _normalize_nfc(cand_bal)
                if cand_nfc and _RE_TAMIL_SCRIPT.search(cand_nfc):
                    salvaged_ta = cand_nfc
        return None, salvaged_ta, meta

    tokens: list[str] = []
    seen_lower: set[str] = set()
    for part in re.split(r"[,;]", cleaned):
        tok = _strip_stray_quotes_and_parens(part)
        if not tok:
            continue
        if (
            _RE_TAMIL_SCRIPT.search(tok)
            or tok.startswith(("/", "."))
            or "..." in tok
            or len(tok) > 48
        ):
            meta["corrupted"] = True
            continue
        if _RE_WORDNET_LEXNAME.match(tok):
            mapped = WORDNET_DOMAIN_MAP.get(tok.lower())
            if mapped:
                meta["wn_mapped"] += 1
                tok = mapped
            else:
                meta["wn_dropped"] += 1
                continue
        low = tok.lower()
        if low == "vetenary science":
            tok = "Veterinary Science"
            meta["typo_fixed"] = True
        elif low == "folk lore":
            tok = "Folklore"
        canonical = _title_case_domain_token(tok)
        key = canonical.lower()
        if canonical and key not in seen_lower:
            seen_lower.add(key)
            tokens.append(canonical)

    if not tokens:
        return None, None, meta
    return ", ".join(sorted(tokens)), None, meta


def normalize_domain(raw: str | None) -> tuple[str | None, bool, bool]:
    """Collapse repeated whitespace, split atomic domains, and fix known domain typos."""
    dom, _salvaged, meta = _clean_domain_value(raw)
    return dom, bool(meta["typo_fixed"]), bool(meta["ws_changed"])


def normalize_register(raw: str | None) -> str | None:
    """Split, deduplicate, and canonicalize register tags to lowercase snake_case."""
    if not raw:
        return None
    cleaned = _clean_text_value(raw)
    if not cleaned:
        return None
    tokens: list[str] = []
    seen: set[str] = set()
    for part in re.split(r"[,;]", cleaned):
        tok = _strip_stray_quotes_and_parens(part)
        if not tok or _RE_TAMIL_SCRIPT.search(tok):
            continue
        tok = re.sub(r"[\s\-/]+", "_", tok.lower())
        tok = re.sub(r"_+", "_", tok).strip("_")
        if tok and tok not in seen:
            seen.add(tok)
            tokens.append(tok)
    if not tokens:
        return None
    return ", ".join(sorted(tokens))


def normalize_dialect_region(raw: str | None) -> str | None:
    """Map raw regional dialect label to a normalized region code."""
    if not raw:
        return None
    key = " ".join(raw.strip().lower().split())
    if not key:
        return None
    if key in DIALECT_REGION_MAP:
        return DIALECT_REGION_MAP[key]
    return re.sub(r"[^A-Z0-9]+", "_", key.upper()).strip("_") or None


def repair_tamil_mojibake(text: str) -> tuple[str, str]:
    """Repair verified unambiguous Tamil TSCII/TAB mojibake artifacts.

    Returns ``(cleaned_text, status)`` where status is one of:
    ``"clean"``, ``"repaired"``, or ``"flagged_unrepaired"``.
    """
    if not _RE_MOJIBAKE_SCAN.search(text):
        return text, "clean"

    repaired = text
    # 1. Stray cent after pulli (e.g. பெருக்கல்¢, சுண்ணக்¢கட்டி)
    repaired = repaired.replace("\u0bcd\u00a2", "\u0bcd")
    # 2. Mis-OCR'd ர் as ா¢ (e.g. பணியாளா¢ -> பணியாளர், சுவா¢ -> சுவர்)
    repaired = repaired.replace("\u0bbe\u00a2", "\u0bb0\u0bcd")
    # 3. Missing pulli replaced by ¢ after consonant (e.g. ச¢ -> ச், ர¢ -> ர், ல¢ -> ல்)
    repaired = _RE_CONSONANT_CENT.sub("\\1\u0bcd", repaired)
    # 4. Lengthening hook £ after ு (e.g. து£ண்டல் -> தூண்டல்)
    repaired = repaired.replace("\u0bc1\u00a3", "\u0bc2")

    if _RE_MOJIBAKE_SCAN.search(repaired):
        # Still contains unmapped Latin-1/symbol artifacts (e.g. £...., á, â)
        return repaired, "repaired_partial" if repaired != text else "flagged_unrepaired"
    return repaired, "repaired"


def clean_technical_parens(text: str) -> tuple[str, str | None, bool]:
    """Clean unbalanced parentheses and split trailing parenthetical glosses.

    Returns ``(clean_headword, paren_note, had_unbalanced_parens)``.
    Guarantees a non-empty ``clean_headword`` whenever ``text.strip()`` is non-empty.
    """
    collapsed = " ".join(text.split())
    if not collapsed:
        return "", None, False

    had_unbalanced = False
    paren_note: str | None = None

    # Pass 1: stack-match parentheses to detect unbalanced '(' or ')'
    stack: list[int] = []
    unmatched_close: set[int] = set()
    for idx, ch in enumerate(collapsed):
        if ch == "(":
            stack.append(idx)
        elif ch == ")":
            if stack:
                stack.pop()
            else:
                unmatched_close.add(idx)

    if stack or unmatched_close:
        had_unbalanced = True
        # If there is an unclosed '(' with a non-empty prefix before it, split tail note
        if stack:
            first_unclosed = stack[0]
            prefix = "".join(
                ch
                for i, ch in enumerate(collapsed[:first_unclosed])
                if i not in unmatched_close
            )
            prefix = " ".join(prefix.split()).strip()
            tail = "".join(
                ch
                for i, ch in enumerate(collapsed[first_unclosed + 1 :], first_unclosed + 1)
                if i not in unmatched_close
            )
            tail = " ".join(tail.split()).strip()
            if prefix:
                collapsed = prefix
                if tail:
                    paren_note = tail
            else:
                # Unclosed '(' at position 0: drop unmatched '(' and unmatched ')'
                drop = set(stack) | unmatched_close
                collapsed = " ".join(
                    "".join(ch for i, ch in enumerate(collapsed) if i not in drop).split()
                )
        else:
            collapsed = " ".join(
                "".join(ch for i, ch in enumerate(collapsed) if i not in unmatched_close).split()
            )

    # Pass 2: handle balanced outer wrapping or trailing parenthetical gloss
    if collapsed.startswith("(") and collapsed.endswith(")"):
        depth = 0
        single_wrap = True
        for i, ch in enumerate(collapsed):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0 and i < len(collapsed) - 1:
                    single_wrap = False
                    break
        if single_wrap:
            inner = " ".join(collapsed[1:-1].split()).strip()
            if inner:
                collapsed = inner

    if collapsed.endswith(")"):
        # Find matching '(' for the final ')'
        depth = 0
        match_idx = -1
        for i in range(len(collapsed) - 1, -1, -1):
            ch = collapsed[i]
            if ch == ")":
                depth += 1
            elif ch == "(":
                depth -= 1
                if depth == 0:
                    match_idx = i
                    break
        if match_idx > 0:
            base = collapsed[:match_idx].strip()
            note = " ".join(collapsed[match_idx + 1 : -1].split()).strip()
            if base:
                collapsed = base
                if note:
                    paren_note = f"{note}; {paren_note}" if paren_note else note

    collapsed = " ".join(collapsed.split()).strip()
    if not collapsed:
        collapsed = " ".join(text.split())
    return collapsed, paren_note, had_unbalanced


def verify_historical_sources(
    historical_dir: Path = DEFAULT_HISTORICAL_DIR,
    pin_path: Path = DEFAULT_HISTORICAL_PIN,
) -> list[dict[str, Any]]:
    """Verify all frozen files in data/sources/tamil-lexicon/ against SHA-256 pin."""
    if not pin_path.is_file():
        raise ValueError(f"Missing historical SHA-256 pin file: {pin_path}")
    expected_files = json.loads(pin_path.read_text(encoding="utf-8"))
    if len(expected_files) != 12:
        raise ValueError(f"Expected 12 pinned historical files, found {len(expected_files)}")
    for item in expected_files:
        fpath = historical_dir / item["file"]
        if not fpath.is_file():
            raise ValueError(f"Missing frozen historical file: {fpath}")
        actual_size = fpath.stat().st_size
        actual_sha = _sha256_file(fpath)
        if actual_size != item["bytes"] or actual_sha != item["sha256"]:
            # Git on Linux checks out LF while the frozen pin recorded CRLF CSV sizes.
            if fpath.suffix.lower() == ".csv":
                raw = fpath.read_bytes()
                if b"\r\n" not in raw:
                    crlf = raw.replace(b"\n", b"\r\n")
                    crlf_sha = hashlib.sha256(crlf).hexdigest()
                    if len(crlf) == item["bytes"] and crlf_sha == item["sha256"]:
                        continue
            if actual_size != item["bytes"]:
                raise ValueError(
                    f"Frozen historical file size mismatch for {item['file']}: "
                    f"expected {item['bytes']}, got {actual_size}"
                )
            raise ValueError(
                f"Frozen historical file SHA-256 mismatch for {item['file']}: "
                f"expected {item['sha256']}, got {actual_sha}"
            )
    return expected_files


def verify_tawiktionary_sources(
    manifest_path: Path = DEFAULT_TAWIKT_MANIFEST,
    entries_path: Path = DEFAULT_TAWIKT_ENTRIES,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Verify ta.wiktionary manifest, optional raw dump archive, and bulk JSONL.gz."""
    if not manifest_path.is_file():
        raise ValueError(f"Missing ta.wiktionary manifest: {manifest_path}")
    if not entries_path.is_file():
        raise ValueError(f"Missing ta.wiktionary bulk entries: {entries_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for key in ("source_id", "dump_filename", "dump_bytes", "dump_sha256", "kept_entries"):
        if key not in manifest:
            raise ValueError(f"Missing required key {key!r} in {manifest_path}")

    dump_path = manifest_path.parent / manifest["dump_filename"]
    if dump_path.is_file():
        if dump_path.stat().st_size != manifest["dump_bytes"]:
            raise ValueError(
                f"ta.wiktionary dump byte mismatch: expected {manifest['dump_bytes']}, "
                f"got {dump_path.stat().st_size}"
            )
        actual_sha = _sha256_file(dump_path)
        if actual_sha != manifest["dump_sha256"]:
            raise ValueError(
                f"ta.wiktionary dump SHA-256 mismatch: expected {manifest['dump_sha256']}, "
                f"got {actual_sha}"
            )

    rows: list[dict[str, Any]] = []
    with gzip.open(entries_path, "rt", encoding="utf-8") as handle:
        for line in handle:
            s = line.strip()
            if not s:
                continue
            rows.append(json.loads(s))
    if len(rows) != int(manifest["kept_entries"]):
        raise ValueError(
            f"ta.wiktionary entry count mismatch: manifest kept_entries={manifest['kept_entries']}, "
            f"observed={len(rows)}"
        )
    return manifest, rows


def _make_entry(
    *,
    entry_id: str,
    headword: str,
    pos: str | None,
    forms: list[dict[str, str]],
    senses: list[dict[str, Any]],
    domain: str | None = None,
    region: str | None = None,
    register: str | None = None,
    origin_language: str | None = None,
    pure_tamil_equivalent: str | None = None,
    standard_equivalent: str | None = None,
    scientific_name: str | None = None,
    literary_source: str | None = None,
    verb_class: str | None = None,
    transitivity: str | None = None,
    root_word: str | None = None,
    etymology_type: str | None = None,
    dedr_id: str | None = None,
    sandhi_behavior: str | None = None,
    animacy_gender: str | None = None,
    frequency_tier: str | None = None,
    source_id: str,
    source_locator: str,
    rights_status: str,
    permalink: str | None = None,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "entry_id": entry_id,
        "headword": headword,
        "pos": pos,
        "forms": forms,
        "senses": senses,
        "domain": domain,
        "region": region,
        "register": register,
        "origin_language": origin_language,
        "pure_tamil_equivalent": pure_tamil_equivalent,
        "standard_equivalent": standard_equivalent,
        "scientific_name": scientific_name,
        "literary_source": literary_source,
        "source_id": source_id,
        "source_locator": source_locator,
        "rights_status": rights_status,
        "permalink": permalink,
    }
    optional_morph = (
        ("verb_class", verb_class),
        ("transitivity", transitivity),
        ("root_word", root_word),
        ("etymology_type", etymology_type),
        ("dedr_id", dedr_id),
        ("sandhi_behavior", sandhi_behavior),
        ("animacy_gender", animacy_gender),
        ("frequency_tier", frequency_tier),
    )
    for k, v in optional_morph:
        if v:
            entry[k] = v
    return entry


def _make_sense(
    *,
    gloss_ta: str | None = None,
    gloss_en: str | None = None,
    definition_ta: str | None = None,
    definition_en: str | None = None,
    examples: list[str] | None = None,
    domain: str | None = None,
    region: str | None = None,
    register: str | None = None,
) -> dict[str, Any]:
    return {
        "gloss_ta": gloss_ta,
        "gloss_en": gloss_en,
        "definition_ta": definition_ta,
        "definition_en": definition_en,
        "examples": examples or [],
        "domain": domain,
        "region": region,
        "register": register,
    }


def _write_pack(
    pack_dir: Path,
    *,
    pack_id: str,
    pack_tier: str,
    rights_status: str,
    license_id: str,
    description: str,
    attribution_notice: str,
    entries: list[dict[str, Any]],
    relations: list[dict[str, Any]],
    fallback_source_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Write deterministic manifest.json, entries.jsonl, and relations.jsonl."""
    pack_dir.mkdir(parents=True, exist_ok=True)
    sorted_entries = sorted(entries, key=lambda e: (e["headword"], e["entry_id"]))
    sorted_relations = sorted(
        relations,
        key=lambda r: (
            r["source_headword"],
            r["relation_code"],
            r["target_headword"],
            r["source_locator"],
        ),
    )

    seen_ids: set[str] = set()
    entries_path = pack_dir / "entries.jsonl"
    with entries_path.open("w", encoding="utf-8", newline="\n") as fh:
        for ent in sorted_entries:
            eid = ent["entry_id"]
            if eid in seen_ids:
                raise ValueError(f"Duplicate entry_id {eid!r} in pack {pack_id}")
            seen_ids.add(eid)
            if not ent["headword"]:
                raise ValueError(f"Empty headword in pack {pack_id} entry {eid}")
            fh.write(json.dumps(ent, ensure_ascii=False) + "\n")

    relations_path = pack_dir / "relations.jsonl"
    with relations_path.open("w", encoding="utf-8", newline="\n") as fh:
        for rel in sorted_relations:
            fh.write(json.dumps(rel, ensure_ascii=False) + "\n")

    source_ids = sorted(
        {e["source_id"] for e in sorted_entries}
        | {r["source_id"] for r in sorted_relations}
    )
    if not source_ids and fallback_source_ids:
        source_ids = sorted(fallback_source_ids)

    sense_count = sum(len(e["senses"]) for e in sorted_entries)
    distinct_headwords = len({e["headword"] for e in sorted_entries})

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "pack_id": pack_id,
        "pack_tier": pack_tier,
        "rights_status": rights_status,
        "license": license_id,
        "dataset_version": DATASET_VERSION,
        "description": description,
        "source_ids": source_ids,
        "attribution_notice": attribution_notice,
        "entry_count": len(sorted_entries),
        "sense_count": sense_count,
        "relation_count": len(sorted_relations),
        "distinct_headwords": distinct_headwords,
    }
    (pack_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest


def _parse_open_canonical_pack(
    pack_id: str,
    pack_dir: Path,
    nfc_records: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Read a canonical json-string-utf8-v1 pack directory."""
    meta = tomllib.loads((pack_dir / "packs.toml").read_text(encoding="utf-8"))
    with (pack_dir / "assertions.csv").open(encoding="utf-8", newline="") as fh:
        assertions = {
            r["assertion_id"]: json.loads(r["value_json"])
            for r in csv.DictReader(fh)
        }
    with (pack_dir / "sources.csv").open(encoding="utf-8", newline="") as fh:
        sources = {r["source_id"]: r for r in csv.DictReader(fh)}
    with (pack_dir / "evidence.csv").open(encoding="utf-8", newline="") as fh:
        evidence: dict[str, dict[str, str]] = {}
        for r in csv.DictReader(fh):
            evidence.setdefault(r["assertion_id"], r)

    forms_by_id: dict[str, dict[str, str]] = {}
    forms_by_entry: dict[str, list[dict[str, str]]] = {}
    with (pack_dir / "forms.csv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            forms_by_id[r["form_id"]] = r
            forms_by_entry.setdefault(r["entry_id"], []).append(r)

    senses_by_entry: dict[str, list[dict[str, str]]] = {}
    with (pack_dir / "senses.csv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            senses_by_entry.setdefault(r["entry_id"], []).append(r)

    texts_by_sense: dict[str, list[dict[str, str]]] = {}
    with (pack_dir / "texts.csv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["owner_kind"] == "sense":
                texts_by_sense.setdefault(r["owner_id"], []).append(r)

    entry_scopes: dict[str, dict[str, set[str]]] = {}
    sense_scopes: dict[str, dict[str, set[str]]] = {}
    with (pack_dir / "scopes.csv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["state"] != "attested":
                continue
            dim = r["dimension"]
            code = (r.get("label_code") or "").strip()
            if not code or dim not in ("domain", "region", "register"):
                continue
            target = (
                entry_scopes.setdefault(r["subject_id"], {})
                if r["subject_kind"] == "entry"
                else sense_scopes.setdefault(r["subject_id"], {})
            )
            target.setdefault(dim, set()).add(code)

    entries_out: list[dict[str, Any]] = []
    with (pack_dir / "entries.csv").open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            eid = row["entry_id"]
            canon_form = forms_by_id[row["canonical_form_id"]]
            hw_aid = canon_form["text_assertion_id"]
            raw_hw = str(assertions[hw_aid])
            hw_nfc, was_norm = _normalize_nfc(raw_hw)
            forms_list: list[dict[str, str]] = []
            if was_norm:
                nfc_records.append({"pack": pack_id, "raw": raw_hw, "nfc": hw_nfc})
                forms_list.append({"role": "raw_source", "text": raw_hw})
            for f in forms_by_entry.get(eid, []):
                if f["form_id"] == row["canonical_form_id"]:
                    continue
                ftext = assertions.get(f["text_assertion_id"])
                if isinstance(ftext, str) and ftext:
                    forms_list.append({"role": f["role"] or "variant", "text": ftext})

            pos_raw = assertions.get(row["pos_assertion_id"]) if row.get("pos_assertion_id") else None
            pos = normalize_pos(pos_raw if isinstance(pos_raw, str) else None)

            ev = evidence.get(hw_aid)
            source_id = ev["source_id"] if ev else sorted(sources)[0]
            permalink: str | None = None
            source_locator = f"enwiktionary:entry={eid}"
            if ev and ev.get("locator_json"):
                loc = json.loads(ev["locator_json"])
                if isinstance(loc, dict):
                    permalink = loc.get("permalink")
                    pid = loc.get("pageid")
                    rid = loc.get("revid")
                    if pid is not None and rid is not None:
                        source_locator = f"enwiktionary:pageid={pid},oldid={rid}"
                    elif rid is not None:
                        source_locator = f"enwiktionary:oldid={rid}"
                elif isinstance(loc, str) and loc:
                    source_locator = f"enwiktionary:{loc}"
                    if source_id in sources:
                        permalink = json.loads(sources[source_id]["url_json"])
            elif source_id in sources:
                permalink = json.loads(sources[source_id]["url_json"])

            raw_senses = sorted(
                senses_by_entry.get(eid, []),
                key=lambda s: (int(s["display_order"]) if s.get("display_order") else 0, s["sense_id"]),
            )
            senses_out: list[dict[str, Any]] = []
            e_doms = set(entry_scopes.get(eid, {}).get("domain", ()))
            e_regs = set(entry_scopes.get(eid, {}).get("region", ()))
            e_rgst = set(entry_scopes.get(eid, {}).get("register", ()))

            for srow in raw_senses:
                sid = srow["sense_id"]
                gloss_ta: str | None = None
                gloss_en: str | None = None
                def_ta: str | None = None
                def_en: str | None = None
                for trow in texts_by_sense.get(sid, []):
                    val = assertions.get(trow["text_assertion_id"])
                    if not isinstance(val, str) or not val.strip():
                        continue
                    val = _clean_text_value(val)
                    if not val:
                        continue
                    comp = trow["component"]
                    lang = trow["language_id"]
                    if lang == "eng":
                        if comp == "definition" and def_en is None:
                            def_en = val
                        elif comp in ("gloss", "translation") and gloss_en is None:
                            gloss_en = val
                    elif lang == "tam":
                        if comp == "definition" and def_ta is None:
                            def_ta = val
                        elif comp in ("gloss", "translation") and gloss_ta is None:
                            gloss_ta = val
                s_sc = sense_scopes.get(sid, {})
                s_dom = _clean_domain_value(", ".join(sorted(s_sc["domain"])))[0] if s_sc.get("domain") else None
                s_reg = ", ".join(sorted(s_sc["region"])) if s_sc.get("region") else None
                s_rgst = normalize_register(", ".join(sorted(s_sc["register"]))) if s_sc.get("register") else None
                if s_sc.get("domain"):
                    e_doms.update(s_sc["domain"])
                if s_sc.get("region"):
                    e_regs.update(s_sc["region"])
                if s_sc.get("register"):
                    e_rgst.update(s_sc["register"])
                senses_out.append(
                    _make_sense(
                        gloss_ta=gloss_ta,
                        gloss_en=gloss_en,
                        definition_ta=def_ta,
                        definition_en=def_en,
                        domain=s_dom,
                        region=s_reg,
                        register=s_rgst,
                    )
                )

            entries_out.append(
                _make_entry(
                    entry_id=eid,
                    headword=hw_nfc,
                    pos=pos,
                    forms=forms_list,
                    senses=senses_out,
                    domain=_clean_domain_value(", ".join(sorted(e_doms)))[0] if e_doms else None,
                    region=", ".join(sorted(e_regs)) if e_regs else None,
                    register=normalize_register(", ".join(sorted(e_rgst))) if e_rgst else None,
                    source_id=source_id,
                    source_locator=source_locator,
                    rights_status="CC-BY-SA-4.0",
                    permalink=permalink,
                )
            )

    return entries_out, [], {"description": meta.get("description", f"Verified open {pack_id} pack")}


def build_open_track(
    out_dir: Path,
    *,
    open_packs: dict[str, Path] = DEFAULT_OPEN_PACKS,
    tawikt_manifest_path: Path = DEFAULT_TAWIKT_MANIFEST,
    tawikt_entries_path: Path = DEFAULT_TAWIKT_ENTRIES,
) -> tuple[dict[str, Any], set[str], dict[str, set[str]]]:
    """Build all 4 verified_open packs under <out_dir>/open/."""
    tawikt_manifest, tawikt_rows = verify_tawiktionary_sources(
        tawikt_manifest_path, tawikt_entries_path
    )
    open_root = out_dir / "open"
    nfc_records: list[dict[str, str]] = []
    pack_manifests: dict[str, Any] = {}
    pack_headwords: dict[str, set[str]] = {}
    all_headwords: set[str] = set()

    for pack_id, pack_dir in open_packs.items():
        if not (pack_dir / "entries.csv").is_file():
            raise ValueError(f"Missing canonical pack {pack_id} at {pack_dir}")
        entries, relations, info = _parse_open_canonical_pack(pack_id, pack_dir, nfc_records)
        manifest = _write_pack(
            open_root / pack_id,
            pack_id=pack_id,
            pack_tier="verified_open",
            rights_status="CC-BY-SA-4.0",
            license_id="CC-BY-SA-4.0",
            description=info["description"],
            attribution_notice=(
                "English Wiktionary contributors, verified Tamil snapshot, licensed CC-BY-SA-4.0 "
                "(dual-licensed CC-BY-SA-4.0/GFDL upstream)."
            ),
            entries=entries,
            relations=relations,
        )
        pack_manifests[pack_id] = manifest
        hws = {e["headword"] for e in entries}
        pack_headwords[pack_id] = hws
        all_headwords.update(hws)

    # ta_wiktionary pack
    ta_entries: list[dict[str, Any]] = []
    quarantined_mojibake: list[dict[str, Any]] = []
    quarantined_mojibake_defs: list[dict[str, Any]] = []
    routed_ascii_defs = 0
    unbalanced_parens_fixed_tawikt = 0
    default_src_id = tawikt_manifest["source_id"]
    for idx, rec in enumerate(tawikt_rows, 1):
        raw_hw = rec["headword"]
        if _RE_TAWIKT_BAD_HW.search(raw_hw):
            quarantined_mojibake.append({
                "index": idx,
                "pageid": rec.get("pageid"),
                "revid": rec.get("revid"),
                "headword": raw_hw,
                "reason": "tscii_mojibake_headword",
            })
            continue

        hw_clean = _clean_text_value(raw_hw)
        hw_clean, hw_par_fixed = _balance_parens(hw_clean)
        if hw_par_fixed:
            unbalanced_parens_fixed_tawikt += 1
        hw_nfc, was_norm = _normalize_nfc(hw_clean)
        forms_list: list[dict[str, str]] = []
        if was_norm or hw_clean != raw_hw:
            nfc_records.append({"pack": "ta_wiktionary", "raw": raw_hw, "nfc": hw_nfc})
            forms_list.append({"role": "raw_source", "text": raw_hw})

        tam_defs_raw: list[str] = []
        routed_from_tam: list[str] = []
        for d in rec.get("tam_defs") or []:
            if not isinstance(d, str):
                continue
            cleaned = _clean_text_value(d)
            if not cleaned:
                continue
            cleaned = _RE_TAWIKT_TRAILING_MOJIBAKE.sub("", cleaned).strip()
            if not cleaned:
                continue
            if _RE_MOJIBAKE_ANY.search(cleaned):
                quarantined_mojibake_defs.append({
                    "index": idx,
                    "pageid": rec.get("pageid"),
                    "revid": rec.get("revid"),
                    "headword": hw_nfc,
                    "raw_def": d,
                    "reason": "tscii_mojibake_definition",
                })
                continue
            cleaned, par_fixed = _balance_parens(cleaned)
            if par_fixed:
                unbalanced_parens_fixed_tawikt += 1
            cleaned_nfc, _ = _normalize_nfc(cleaned)
            if not _RE_TAMIL_SCRIPT.search(cleaned_nfc) and _RE_ASCII_ALPHA.search(cleaned_nfc):
                routed_from_tam.append(cleaned_nfc)
                routed_ascii_defs += 1
            else:
                tam_defs_raw.append(cleaned_nfc)

        eng_raw: list[str] = []
        for t in rec.get("eng_trans") or []:
            if not isinstance(t, str):
                continue
            cleaned = _strip_stray_en_mojibake(_clean_text_value(t))
            if not cleaned or _RE_MOJIBAKE_ANY.search(cleaned):
                continue
            cleaned, par_fixed = _balance_parens(cleaned)
            if par_fixed:
                unbalanced_parens_fixed_tawikt += 1
            cleaned_nfc, _ = _normalize_nfc(cleaned)
            eng_raw.append(cleaned_nfc)

        tam_defs: list[str] = []
        seen_tam: set[str] = set()
        for td in tam_defs_raw:
            k = td.casefold()
            if k not in seen_tam:
                seen_tam.add(k)
                tam_defs.append(td)

        eng_trans: list[str] = []
        seen_eng: set[str] = set()
        for et in [*eng_raw, *routed_from_tam]:
            k = et.casefold()
            if k not in seen_eng:
                seen_eng.add(k)
                eng_trans.append(et)

        senses: list[dict[str, Any]] = []
        if len(tam_defs) == 1 and len(eng_trans) == 1:
            senses.append(_make_sense(gloss_en=eng_trans[0], definition_ta=tam_defs[0]))
        else:
            for td in tam_defs:
                senses.append(_make_sense(definition_ta=td))
            for et in eng_trans:
                senses.append(_make_sense(gloss_en=et))

        if not senses and (rec.get("tam_defs") or rec.get("eng_trans")):
            quarantined_mojibake.append({
                "index": idx,
                "pageid": rec.get("pageid"),
                "revid": rec.get("revid"),
                "headword": raw_hw,
                "reason": "tscii_mojibake_all_senses_quarantined",
            })
            continue

        pageid = rec["pageid"]
        revid = rec["revid"]
        ta_entries.append(
            _make_entry(
                entry_id=f"tawikt:{pageid}:{revid}:{idx}",
                headword=hw_nfc,
                pos=normalize_pos(rec.get("pos")),
                forms=forms_list,
                senses=senses,
                source_id=rec.get("source_id") or default_src_id,
                source_locator=f"tawiktionary:pageid={pageid},revid={revid}",
                rights_status="CC-BY-SA-4.0",
                permalink=rec.get("permalink"),
            )
        )

    ta_manifest = _write_pack(
        open_root / "ta_wiktionary",
        pack_id="ta_wiktionary",
        pack_tier="verified_open",
        rights_status="CC-BY-SA-4.0",
        license_id="CC-BY-SA-4.0",
        description="Verified Tamil Wiktionary (ta.wiktionary.org) bulk dictionary pack",
        attribution_notice=(
            "Tamil Wiktionary contributors (https://ta.wiktionary.org), official dump "
            f"{tawikt_manifest['dump_filename']}, licensed CC-BY-SA-4.0 / GFDL."
        ),
        entries=ta_entries,
        relations=[],
        fallback_source_ids=[default_src_id],
    )
    pack_manifests["ta_wiktionary"] = ta_manifest
    ta_hws = {e["headword"] for e in ta_entries}
    pack_headwords["ta_wiktionary"] = ta_hws
    all_headwords.update(ta_hws)

    audit = {
        "tawiktionary_kept_entries": len(tawikt_rows),
        "tawiktionary_emitted_entries": len(ta_entries),
        "tawiktionary_quarantined_mojibake_count": len(quarantined_mojibake),
        "tawiktionary_quarantined_mojibake": quarantined_mojibake,
        "tawiktionary_quarantined_mojibake_defs_count": len(quarantined_mojibake_defs),
        "tawiktionary_quarantined_mojibake_defs": quarantined_mojibake_defs,
        "tawiktionary_routed_ascii_defs": routed_ascii_defs,
        "tawiktionary_unbalanced_parens_fixed": unbalanced_parens_fixed_tawikt,
        "packs": pack_manifests,
        "total_entries": sum(m["entry_count"] for m in pack_manifests.values()),
        "total_senses": sum(m["sense_count"] for m in pack_manifests.values()),
        "total_distinct_headwords": len(all_headwords),
        "nfc_normalized_headwords_count": len(nfc_records),
        "nfc_normalized_headwords": nfc_records,
    }
    return audit, all_headwords, pack_headwords


def _read_historical_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _build_local_core(
    hist_dir: Path,
    local_root: Path,
    nfc_records: list[dict[str, str]],
) -> tuple[dict[str, Any], dict[str, int], dict[str, Any], set[str], dict[str, dict[str, str | None]]]:
    pl_rows = _read_historical_csv(hist_dir / "primary_lemmas.csv")
    um_rows = _read_historical_csv(hist_dir / "unified_master_30col.csv")
    pm_rows = _read_historical_csv(hist_dir / "primary_meanings.csv")

    pl_by_id: dict[str, tuple[int, dict[str, str]]] = {}
    for idx, row in enumerate(pl_rows, 1):
        pl_by_id[row["word_id"]] = (idx, row)

    um_by_id: dict[str, tuple[int, dict[str, str]]] = {}
    for idx, row in enumerate(um_rows, 1):
        um_by_id[row["word_id"]] = (idx, row)

    if set(pl_by_id) != set(um_by_id):
        raise ValueError("word_id mismatch between primary_lemmas.csv and unified_master_30col.csv")

    pm_by_id: dict[str, list[dict[str, str]]] = {}
    for row in pm_rows:
        wid = row["word_id"]
        if wid not in pl_by_id:
            raise ValueError(f"primary_meanings.csv references unknown word_id={wid!r}")
        pm_by_id.setdefault(wid, []).append(row)

    excluded_placeholder_meanings = 0
    dropped_empty_senses = 0
    filtered_cross_lemma_senses = 0
    filtered_inflected_senses = 0
    deduped_within_entry_senses = 0
    bilingual_glosses_split = 0
    pure_ta_moved_from_en = 0
    kalaichol_prefix_stripped = 0
    unbalanced_parens_fixed = 0
    bom_stripped_count = 0
    example_sentences_attached = 0
    corrupted_domains_cleared = 0
    corrupted_entry_domains_cleared = 0
    salvaged_tamil_domains_to_gloss = 0
    wordnet_domains_mapped = 0
    wordnet_domains_dropped = 0
    etymology_counts: Counter[str] = Counter()
    dedr_non_empty = 0

    for _um_idx, urow in um_by_id.values():
        et = urow.get("etymology_type", "").strip()
        if et:
            etymology_counts[et] += 1
        if urow.get("dedr_id", "").strip():
            dedr_non_empty += 1

    hw_counter: Counter[str] = Counter()
    entries: list[dict[str, Any]] = []
    core_lookup: dict[str, dict[str, str | None]] = {}

    for wid, (pl_row_num, prow) in pl_by_id.items():
        _um_row_num, urow = um_by_id[wid]
        raw_hw = prow["headword_ta"].strip()
        hw_clean, b_cnt = _strip_bom_logged(raw_hw)
        bom_stripped_count += b_cnt
        hw_clean = _clean_text_value(hw_clean)
        hw_clean, hw_par = _balance_parens(hw_clean)
        if hw_par:
            unbalanced_parens_fixed += 1
        hw_nfc, was_norm = _normalize_nfc(hw_clean)
        hw_counter[hw_nfc] += 1

        forms: list[dict[str, str]] = []
        if was_norm or b_cnt or hw_clean != raw_hw:
            nfc_records.append({"pack": "local_core", "raw": raw_hw, "nfc": hw_nfc})
            forms.append({"role": "raw_source", "text": raw_hw})
        translit = _clean_text_value(prow.get("transliteration", ""))
        if translit:
            forms.append({"role": "transliteration", "text": translit})
        ipa = _clean_text_value(prow.get("pronunciation_ipa", "") or urow.get("pronunciation_ipa", ""))
        if ipa:
            ipa_nfc, _ = _normalize_nfc(ipa)
            forms.append({"role": "ipa", "text": ipa_nfc})
        um_norm = _clean_text_value(urow.get("headword_normalized", ""))
        if um_norm:
            um_norm_nfc, _ = _normalize_nfc(um_norm)
            if um_norm_nfc != hw_nfc:
                forms.append({"role": "variant", "text": um_norm_nfc})

        pos = normalize_pos(prow.get("part_of_speech"))
        register = normalize_register(prow.get("register"))
        entry_domain, _, entry_dom_meta = _clean_domain_value(urow.get("domain"))
        if entry_dom_meta["corrupted"]:
            corrupted_entry_domains_cleared += 1
        wordnet_domains_mapped += int(entry_dom_meta["wn_mapped"])
        wordnet_domains_dropped += int(entry_dom_meta["wn_dropped"])

        verb_class = prow.get("verb_class", "").strip() or None
        subclass_raw = prow.get("grammatical_subclass", "").strip() or urow.get("grammatical_subclass", "").strip()
        transitivity = _extract_transitivity(subclass_raw)
        root_raw = _clean_text_value(prow.get("root_word", "") or urow.get("root_word", ""))
        root_word = _normalize_nfc(root_raw)[0] if root_raw else None
        etymology_type = _normalize_nfc(_clean_text_value(urow.get("etymology_type", "")))[0] or None
        dedr_id = urow.get("dedr_id", "").strip() or None
        sandhi_raw = _clean_text_value(urow.get("sandhi_behavior", ""))
        sandhi_behavior = _normalize_nfc(sandhi_raw)[0] if sandhi_raw else None
        animacy_raw = _clean_text_value(prow.get("animacy_gender", "") or urow.get("animacy_gender", ""))
        animacy_gender = _normalize_nfc(animacy_raw)[0] if animacy_raw else None
        frequency_tier = _clean_text_value(urow.get("corpus_frequency_tier", "")) or None

        raw_meanings = sorted(
            pm_by_id.get(wid, []),
            key=lambda m: (int(m["sense_number"]) if m.get("sense_number", "").isdigit() else 0, int(m["meaning_id"])),
        )

        # Pre-scan raw_meanings to detect cross-lemma join corruption & inflected-form noise.
        placeholder = f"{hw_nfc} (கலைச்சொல்)"
        raw_placeholder = f"{raw_hw} (கலைச்சொல்)"
        mt_counts: Counter[str] = Counter()
        has_empty_mt = False
        for mrow in raw_meanings:
            mt_scan = _normalize_nfc(mrow.get("meaning_ta", "").strip())[0]
            if not mt_scan or mt_scan in (placeholder, raw_placeholder):
                has_empty_mt = True
            elif mt_scan != hw_nfc:
                mt_counts[mt_scan] += 1

        senses: list[dict[str, Any]] = []
        seen_senses: set[tuple[str, str, str, str]] = set()
        seen_en_idx: dict[str, int] = {}
        seen_forms = {(f["role"], f["text"]) for f in forms}

        for mrow in raw_meanings:
            m_ta, c1 = _strip_bom_logged(mrow.get("meaning_ta", "").strip())
            m_en, c2 = _strip_bom_logged(mrow.get("meaning_en", "").strip())
            d_ta, c3 = _strip_bom_logged(mrow.get("definition_ta", "").strip())
            d_en, c4 = _strip_bom_logged(mrow.get("definition_en", "").strip())
            bom_stripped_count += c1 + c2 + c3 + c4

            m_ta, n1 = _normalize_nfc(m_ta)
            d_ta, n2 = _normalize_nfc(d_ta)
            if n1:
                nfc_records.append({"pack": "local_core", "raw": mrow.get("meaning_ta", ""), "nfc": m_ta})
            if n2:
                nfc_records.append({"pack": "local_core", "raw": mrow.get("definition_ta", ""), "nfc": d_ta})

            is_placeholder = False
            if m_ta in (placeholder, raw_placeholder):
                m_ta = ""
                is_placeholder = True
            if d_ta in (placeholder, raw_placeholder):
                d_ta = ""
                is_placeholder = True
            if is_placeholder:
                excluded_placeholder_meanings += 1

            # C2: filter cross-lemma joined blocks & inflected-form noise when native senses exist
            if has_empty_mt and m_ta and m_ta != hw_nfc:
                if m_ta == d_ta and mt_counts[m_ta] >= 2:
                    filtered_cross_lemma_senses += 1
                    continue
                if " " not in m_ta and _RE_INFLECTED_FORM_GLOSS.search(m_en):
                    if _RE_VARIANT_FORM_OF.search(m_en) and hw_nfc in m_en:
                        if ("variant", m_ta) not in seen_forms:
                            seen_forms.add(("variant", m_ta))
                            forms.append({"role": "variant", "text": m_ta})
                    filtered_inflected_senses += 1
                    continue

            # C2: strip remaining (பெரும்பாலும் கலைச்சொல்லாக) prefix notes
            if m_ta:
                m_ta_stripped = _RE_KALAICHOL_PREFIX.sub("", m_ta).strip()
                if m_ta_stripped != m_ta:
                    kalaichol_prefix_stripped += 1
                    m_ta = m_ta_stripped
            if d_ta:
                d_ta_stripped = _RE_KALAICHOL_PREFIX.sub("", d_ta).strip()
                if d_ta_stripped != d_ta:
                    kalaichol_prefix_stripped += 1
                    d_ta = d_ta_stripped

            # H3/M1: HTML unescape, curly quote normalization, stray English cent artifact
            m_ta = _clean_text_value(m_ta)
            m_en = _strip_stray_en_mojibake(_clean_text_value(m_en))
            d_ta = _clean_text_value(d_ta)
            d_en = _strip_stray_en_mojibake(_clean_text_value(d_en))

            # D1/D3: clean sense domain and salvage corrupted Tamil synonym/gloss if gloss_ta is empty
            s_dom, salvaged_dom_ta, s_dom_meta = _clean_domain_value(mrow.get("domain"))
            if s_dom_meta["corrupted"]:
                corrupted_domains_cleared += 1
            wordnet_domains_mapped += int(s_dom_meta["wn_mapped"])
            wordnet_domains_dropped += int(s_dom_meta["wn_dropped"])
            if (
                salvaged_dom_ta
                and not m_ta
                and salvaged_dom_ta.casefold() != hw_nfc.casefold()
                and salvaged_dom_ta.casefold() not in d_ta.casefold()
            ):
                m_ta = salvaged_dom_ta
                salvaged_tamil_domains_to_gloss += 1

            # C2: split Madras-Lexicon bilingual gloss_en / definition_en
            if m_en:
                en_part, ta_part = _split_bilingual_en_ta(m_en)
                if ta_part is not None:
                    ta_part_nfc, _ = _normalize_nfc(ta_part)
                    if not en_part:
                        pure_ta_moved_from_en += 1
                        if not m_ta:
                            m_ta = ta_part_nfc
                        elif ta_part_nfc.casefold() not in m_ta.casefold():
                            m_ta = f"{m_ta}; {ta_part_nfc}"
                        m_en = ""
                    else:
                        bilingual_glosses_split += 1
                        m_en = en_part
                        if not m_ta:
                            m_ta = ta_part_nfc
                        elif ta_part_nfc.casefold() not in m_ta.casefold():
                            m_ta = f"{m_ta}; {ta_part_nfc}"

            if d_en:
                en_part, ta_part = _split_bilingual_en_ta(d_en)
                if ta_part is not None:
                    ta_part_nfc, _ = _normalize_nfc(ta_part)
                    if not en_part:
                        pure_ta_moved_from_en += 1
                        if not d_ta:
                            d_ta = ta_part_nfc
                        elif ta_part_nfc.casefold() not in d_ta.casefold():
                            d_ta = f"{d_ta}; {ta_part_nfc}"
                        d_en = ""
                    else:
                        bilingual_glosses_split += 1
                        d_en = en_part
                        if not d_ta:
                            d_ta = ta_part_nfc
                        elif ta_part_nfc.casefold() not in d_ta.casefold():
                            d_ta = f"{d_ta}; {ta_part_nfc}"

            # M1: fix unbalanced parens after bilingual splitting
            if m_ta:
                m_ta, changed = _balance_parens(m_ta)
                if changed:
                    unbalanced_parens_fixed += 1
            if m_en:
                m_en, changed = _balance_parens(m_en)
                if changed:
                    unbalanced_parens_fixed += 1
            if d_ta:
                d_ta, changed = _balance_parens(d_ta)
                if changed:
                    unbalanced_parens_fixed += 1
            if d_en:
                d_en, changed = _balance_parens(d_en)
                if changed:
                    unbalanced_parens_fixed += 1

            m_ta = _normalize_nfc(m_ta)[0] if m_ta else ""
            d_ta = _normalize_nfc(d_ta)[0] if d_ta else ""

            if not (m_ta or m_en or d_ta or d_en):
                dropped_empty_senses += 1
                continue

            # C2: within-entry sense deduplication
            gt_key = " ".join(m_ta.split()).casefold()
            ge_key = _RE_LEADING_SENSE_TAG.sub("", " ".join(m_en.split())).strip().casefold()
            dt_key = " ".join(d_ta.split()).casefold()
            de_key = _RE_LEADING_SENSE_TAG.sub("", " ".join(d_en.split())).strip().casefold()
            sense_key = (gt_key, ge_key, dt_key, de_key)
            if sense_key in seen_senses:
                deduped_within_entry_senses += 1
                continue
            if ge_key and ge_key in seen_en_idx:
                prev_idx = seen_en_idx[ge_key]
                prev = senses[prev_idx]
                prev_gt = " ".join((prev["gloss_ta"] or "").split()).casefold()
                prev_de = _RE_LEADING_SENSE_TAG.sub("", " ".join((prev["definition_en"] or "").split())).strip().casefold()
                if (not gt_key or gt_key == prev_gt) and (not de_key or de_key == ge_key or de_key == prev_de):
                    deduped_within_entry_senses += 1
                    continue
                if gt_key and not prev_gt and (not de_key or de_key == ge_key or de_key == prev_de):
                    prev["gloss_ta"] = m_ta
                    if d_ta and not prev["definition_ta"]:
                        prev["definition_ta"] = d_ta
                    deduped_within_entry_senses += 1
                    continue

            seen_senses.add(sense_key)
            if ge_key and ge_key not in seen_en_idx:
                seen_en_idx[ge_key] = len(senses)

            s_reg = normalize_register(mrow.get("register"))
            senses.append(
                _make_sense(
                    gloss_ta=m_ta or None,
                    gloss_en=m_en or None,
                    definition_ta=d_ta or None,
                    definition_en=d_en or None,
                    domain=s_dom,
                    register=s_reg,
                )
            )

        example = urow.get("example_sentence_ta", "").strip()
        if example:
            example_clean, c5 = _strip_bom_logged(example)
            bom_stripped_count += c5
            example_clean = _clean_text_value(example_clean)
            example_nfc, _ = _normalize_nfc(example_clean)
            if example_nfc:
                if senses:
                    if example_nfc not in senses[0]["examples"]:
                        senses[0]["examples"].append(example_nfc)
                        example_sentences_attached += 1
                else:
                    senses.append(_make_sense(examples=[example_nfc], domain=entry_domain, register=register))
                    example_sentences_attached += 1

        if hw_nfc not in core_lookup:
            for s in senses:
                if s["gloss_ta"] or s["gloss_en"] or s["definition_ta"] or s["definition_en"]:
                    core_lookup[hw_nfc] = {
                        "gloss_ta": s["gloss_ta"],
                        "gloss_en": s["gloss_en"],
                        "definition_ta": s["definition_ta"],
                        "definition_en": s["definition_en"],
                    }
                    break

        entries.append(
            _make_entry(
                entry_id=f"loc_core:{wid}",
                headword=hw_nfc,
                pos=pos,
                forms=forms,
                senses=senses,
                domain=entry_domain,
                register=register,
                verb_class=verb_class,
                transitivity=transitivity,
                root_word=root_word,
                etymology_type=etymology_type,
                dedr_id=dedr_id,
                sandhi_behavior=sandhi_behavior,
                animacy_gender=animacy_gender,
                frequency_tier=frequency_tier,
                source_id="historical_tamil_lexicon_core",
                source_locator=f"primary_lemmas.csv:{pl_row_num}",
                rights_status="unresolved",
                permalink=None,
            )
        )

    manifest = _write_pack(
        local_root / "local_core",
        pack_id="local_core",
        pack_tier="local_historical",
        rights_status="unresolved",
        license_id="UNRESOLVED_LOCAL_ONLY",
        description="Local historical core lexicon (primary_lemmas + primary_meanings + unified_master_30col)",
        attribution_notice="Owner-supplied local historical Tamil lexicon files; rights status unresolved, local/self-hosted only.",
        entries=entries,
        relations=[],
    )
    accounted = {
        "primary_lemmas.csv": len(pl_rows),
        "unified_master_30col.csv": len(um_rows),
        "primary_meanings.csv": len(pm_rows),
    }
    homograph_headwords = sum(1 for v in hw_counter.values() if v > 1)
    homograph_entries = sum(v for v in hw_counter.values() if v > 1)
    stats = {
        "primary_lemmas_rows": len(pl_rows),
        "unified_master_rows": len(um_rows),
        "primary_meanings_rows": len(pm_rows),
        "excluded_placeholder_meanings": excluded_placeholder_meanings,
        "dropped_empty_senses": dropped_empty_senses,
        "filtered_cross_lemma_senses": filtered_cross_lemma_senses,
        "filtered_inflected_senses": filtered_inflected_senses,
        "deduped_within_entry_senses": deduped_within_entry_senses,
        "bilingual_glosses_split": bilingual_glosses_split,
        "pure_ta_moved_from_en": pure_ta_moved_from_en,
        "kalaichol_prefix_stripped": kalaichol_prefix_stripped,
        "unbalanced_parens_fixed": unbalanced_parens_fixed,
        "bom_stripped_count": bom_stripped_count,
        "example_sentences_attached": example_sentences_attached,
        "corrupted_domains_cleared": corrupted_domains_cleared,
        "corrupted_entry_domains_cleared": corrupted_entry_domains_cleared,
        "salvaged_tamil_domains_to_gloss": salvaged_tamil_domains_to_gloss,
        "wordnet_domains_mapped": wordnet_domains_mapped,
        "wordnet_domains_dropped": wordnet_domains_dropped,
        "homograph_headwords_count": homograph_headwords,
        "homograph_entries_count": homograph_entries,
        "unified_master_metadata": {
            "dedr_id_non_empty": dedr_non_empty,
            "etymology_types": dict(sorted(etymology_counts.items())),
        },
    }
    return manifest, accounted, stats, set(hw_counter), core_lookup


def _build_local_terminology(
    hist_dir: Path,
    local_root: Path,
    nfc_records: list[dict[str, str]],
) -> tuple[dict[str, Any], dict[str, int], dict[str, Any], set[str]]:
    rows = _read_historical_csv(hist_dir / "secondary_specialized_technical_terms.csv")

    mojibake_rows: list[dict[str, str]] = []
    mojibake_repaired_count = 0
    mojibake_flagged_count = 0
    mojibake_quarantined_count = 0
    domain_typos_fixed = 0
    domain_ws_collapsed = 0
    unbalanced_parens_fixed = 0
    parenthetical_notes_split = 0
    deduped_sorkuvai_merged = 0
    dropped_junk_glosses_count = 0

    tva_entries: list[dict[str, Any]] = []
    tva_index: dict[tuple[str, str], dict[str, Any]] = {}
    sork_rows: list[tuple[int, dict[str, str]]] = []

    _re_beta_astronomy = re.compile(r"(?<=[\(\s])\u00e2(?=-|\s+orionis\b)", re.IGNORECASE)

    def _process_row(row_num: int, row: dict[str, str]) -> dict[str, Any] | None:
        nonlocal mojibake_repaired_count, mojibake_flagged_count, mojibake_quarantined_count
        nonlocal domain_typos_fixed, domain_ws_collapsed
        nonlocal unbalanced_parens_fixed, parenthetical_notes_split, dropped_junk_glosses_count

        raw_term = row["term_ta"]
        term_pre = _clean_text_value(raw_term, strip_leading_a_hat=True)
        term_pre_beta = _re_beta_astronomy.sub("\u03b2", term_pre)
        beta_repaired = term_pre_beta != term_pre
        term_repaired, m_status = repair_tamil_mojibake(term_pre_beta)

        clean_hw, paren_note, had_unbal = clean_technical_parens(term_repaired)
        if had_unbal:
            unbalanced_parens_fixed += 1
        if paren_note:
            paren_note = _clean_text_value(paren_note, strip_leading_a_hat=True)
            if _is_junk_non_tamil_gloss(paren_note):
                paren_note = None
                dropped_junk_glosses_count += 1
            else:
                parenthetical_notes_split += 1

        hw_nfc, was_norm = _normalize_nfc(clean_hw)
        if was_norm:
            nfc_records.append({"pack": "local_terminology", "raw": clean_hw, "nfc": hw_nfc})

        forms: list[dict[str, str]] = []
        if hw_nfc != raw_term.strip():
            forms.append({"role": "raw_source", "text": raw_term.strip()})
        translit = _clean_text_value(row.get("transliteration", ""))
        if translit:
            forms.append({"role": "transliteration", "text": translit})

        dom, _, dom_meta = _clean_domain_value(row.get("domain_field"))
        if dom_meta["typo_fixed"]:
            domain_typos_fixed += 1
        if dom_meta["ws_changed"]:
            domain_ws_collapsed += 1

        eng_term = _strip_stray_en_mojibake(
            _clean_text_value(row.get("english_term", ""), strip_leading_a_hat=True)
        )
        if eng_term:
            eng_term_beta = _re_beta_astronomy.sub("\u03b2", eng_term)
            if eng_term_beta != eng_term:
                beta_repaired = True
                eng_term = eng_term_beta
            eng_term, eng_par = _balance_parens(eng_term)
            if eng_par:
                unbalanced_parens_fixed += 1
        def_ta = _clean_text_value(row.get("definition_ta", ""), strip_leading_a_hat=True)
        if def_ta:
            def_ta, dta_par = _balance_parens(def_ta)
            if dta_par:
                unbalanced_parens_fixed += 1
            def_ta = _normalize_nfc(def_ta)[0]
        def_en = _strip_stray_en_mojibake(
            _clean_text_value(row.get("definition_en", ""), strip_leading_a_hat=True)
        )
        if def_en:
            def_en, den_par = _balance_parens(def_en)
            if den_par:
                unbalanced_parens_fixed += 1

        emitted_texts = [t for t in (hw_nfc, paren_note, eng_term, def_ta, def_en) if t]
        still_dirty = any(
            _RE_MOJIBAKE_ANY.search(t) or _RE_MOJIBAKE_SCAN.search(t)
            for t in emitted_texts
        )

        if still_dirty:
            mojibake_rows.append({
                "term_id": row["term_id"],
                "row": str(row_num),
                "raw": raw_term,
                "cleaned": hw_nfc,
                "action": "quarantined_unrepaired",
            })
            mojibake_flagged_count += 1
            mojibake_quarantined_count += 1
            return None

        if m_status != "clean" or beta_repaired:
            action = (
                "repaired_greek_beta"
                if beta_repaired
                else ("repaired_post_paren" if m_status == "flagged_unrepaired" else m_status)
            )
            mojibake_rows.append({
                "term_id": row["term_id"],
                "row": str(row_num),
                "raw": raw_term,
                "cleaned": hw_nfc,
                "action": action,
            })
            mojibake_repaired_count += 1

        return _make_entry(
            entry_id=f"loc_term:{row['term_id']}",
            headword=hw_nfc,
            pos=None,
            forms=forms,
            senses=[
                _make_sense(
                    gloss_ta=paren_note,
                    gloss_en=eng_term or None,
                    definition_ta=def_ta or None,
                    definition_en=def_en or None,
                    domain=dom,
                )
            ],
            domain=dom,
            source_id=row.get("source_code", "").strip() or "secondary_specialized_technical_terms",
            source_locator=f"secondary_specialized_technical_terms.csv:{row_num}",
            rights_status="unresolved",
            permalink=None,
        )

    for row_num, row in enumerate(rows, 1):
        if row.get("source_code", "").strip() == "sorkuvai_technical":
            sork_rows.append((row_num, row))
            continue
        ent = _process_row(row_num, row)
        if ent is None:
            continue
        tva_entries.append(ent)
        eng_key = _clean_text_value(row.get("english_term") or "").lower()
        tva_index.setdefault((ent["headword"].replace(" ", ""), eng_key), ent)

    extra_sork_entries: list[dict[str, Any]] = []
    for row_num, row in sork_rows:
        s_hw_clean = _clean_text_value(row["term_ta"], strip_leading_a_hat=True)
        s_hw_nfc, _ = _normalize_nfc(s_hw_clean)
        eng_key = _clean_text_value(row.get("english_term") or "").lower()
        target = tva_index.get((s_hw_nfc.replace(" ", ""), eng_key))
        if target is not None:
            if s_hw_nfc != target["headword"]:
                existing = {(f["role"], f["text"]) for f in target["forms"]}
                if ("variant", s_hw_nfc) not in existing:
                    target["forms"].append({"role": "variant", "text": s_hw_nfc})
            deduped_sorkuvai_merged += 1
        else:
            ent = _process_row(row_num, row)
            if ent is not None:
                extra_sork_entries.append(ent)

    all_entries = tva_entries + extra_sork_entries
    manifest = _write_pack(
        local_root / "local_terminology",
        pack_id="local_terminology",
        pack_tier="local_historical",
        rights_status="unresolved",
        license_id="UNRESOLVED_LOCAL_ONLY",
        description="Local historical specialized technical terminology pack (TVA + Sorkuvai)",
        attribution_notice="Owner-supplied local historical Tamil terminology records; rights status unresolved, local/self-hosted only.",
        entries=all_entries,
        relations=[],
    )
    stats = {
        "input_rows": len(rows),
        "emitted_entries": len(all_entries),
        "deduped_sorkuvai_merged": deduped_sorkuvai_merged,
        "mojibake_repaired_count": mojibake_repaired_count,
        "mojibake_flagged_unrepaired_count": mojibake_flagged_count,
        "mojibake_quarantined_count": mojibake_quarantined_count,
        "mojibake_rows": mojibake_rows,
        "domain_typos_fixed": domain_typos_fixed,
        "domain_whitespace_collapsed": domain_ws_collapsed,
        "unbalanced_parens_fixed": unbalanced_parens_fixed,
        "parenthetical_notes_split": parenthetical_notes_split,
        "dropped_junk_glosses_count": dropped_junk_glosses_count,
    }
    return (
        manifest,
        {"secondary_specialized_technical_terms.csv": len(rows)},
        stats,
        {e["headword"] for e in all_entries},
    )


def _build_local_phrases(
    hist_dir: Path,
    local_root: Path,
    nfc_records: list[dict[str, str]],
    *,
    dialect_lookup: dict[str, dict[str, str | None]] | None = None,
    core_lookup: dict[str, dict[str, str | None]] | None = None,
) -> tuple[dict[str, Any], dict[str, int], dict[str, Any], set[str]]:
    rows = _read_historical_csv(hist_dir / "secondary_phrases_mwes.csv")
    entries: list[dict[str, Any]] = []
    tamil_domains_reclassified = 0
    backfilled_glosses = 0
    quarantined_empty_senses = 0
    wordnet_domains_mapped = 0
    wordnet_domains_dropped = 0
    corrupted_domains_cleared = 0
    quarantined_ids: list[str] = []

    for row_num, row in enumerate(rows, 1):
        raw_hw = _clean_text_value(row["phrase_ta"])
        hw_nfc, was_norm = _normalize_nfc(raw_hw)
        forms: list[dict[str, str]] = []
        if was_norm:
            nfc_records.append({"pack": "local_phrases", "raw": raw_hw, "nfc": hw_nfc})
            forms.append({"role": "raw_source", "text": raw_hw})
        translit = _clean_text_value(row.get("transliteration", ""))
        if translit:
            forms.append({"role": "transliteration", "text": translit})

        raw_dom = _clean_text_value(row.get("domain_category", ""))
        gloss_en = _clean_text_value(row.get("english_gloss", "")) or None
        gloss_ta: str | None = None
        def_ta: str | None = None
        def_en: str | None = None
        dom: str | None = None

        if raw_dom and _RE_TAMIL_SCRIPT.search(raw_dom):
            tamil_domains_reclassified += 1
            dom = None
            eq_parts = [_normalize_nfc(p.strip())[0] for p in raw_dom.split(";") if p.strip()]
            existing_forms = {(f["role"], f["text"]) for f in forms}
            for eq in eq_parts:
                if eq != hw_nfc and ("variant", eq) not in existing_forms:
                    existing_forms.add(("variant", eq))
                    forms.append({"role": "variant", "text": eq})
            if eq_parts:
                gloss_ta = "; ".join(eq_parts)
        else:
            dom, _, dom_meta = _clean_domain_value(raw_dom)
            wordnet_domains_mapped += int(dom_meta["wn_mapped"])
            wordnet_domains_dropped += int(dom_meta["wn_dropped"])
            if dom_meta["corrupted"]:
                corrupted_domains_cleared += 1

        if not (gloss_ta or gloss_en or def_ta or def_en):
            ref = None
            if dialect_lookup and hw_nfc in dialect_lookup:
                ref = dialect_lookup[hw_nfc]
            elif core_lookup and hw_nfc in core_lookup:
                ref = core_lookup[hw_nfc]
            if ref:
                gloss_ta = ref.get("gloss_ta")
                gloss_en = ref.get("gloss_en")
                def_ta = ref.get("definition_ta")
                def_en = ref.get("definition_en")
                if gloss_ta or gloss_en or def_ta or def_en:
                    backfilled_glosses += 1

        if not (gloss_ta or gloss_en or def_ta or def_en):
            quarantined_empty_senses += 1
            quarantined_ids.append(row["phrase_id"])
            continue

        entries.append(
            _make_entry(
                entry_id=f"loc_phr:{row['phrase_id']}",
                headword=hw_nfc,
                pos="PHRASE",
                forms=forms,
                senses=[
                    _make_sense(
                        gloss_ta=gloss_ta,
                        gloss_en=gloss_en,
                        definition_ta=def_ta,
                        definition_en=def_en,
                        domain=dom,
                    )
                ],
                domain=dom,
                source_id=row.get("source_code", "").strip() or "secondary_phrases_mwes",
                source_locator=f"secondary_phrases_mwes.csv:{row_num}",
                rights_status="unresolved",
                permalink=None,
            )
        )
    manifest = _write_pack(
        local_root / "local_phrases",
        pack_id="local_phrases",
        pack_tier="local_historical",
        rights_status="unresolved",
        license_id="UNRESOLVED_LOCAL_ONLY",
        description="Local historical phrases and multi-word expressions (MWEs)",
        attribution_notice="Owner-supplied local historical Tamil MWE records; rights status unresolved, local/self-hosted only.",
        entries=entries,
        relations=[],
    )
    stats = {
        "input_rows": len(rows),
        "emitted_entries": len(entries),
        "tamil_domains_reclassified": tamil_domains_reclassified,
        "backfilled_glosses": backfilled_glosses,
        "quarantined_empty_senses": quarantined_empty_senses,
        "wordnet_domains_mapped": wordnet_domains_mapped,
        "wordnet_domains_dropped": wordnet_domains_dropped,
        "corrupted_domains_cleared": corrupted_domains_cleared,
    }
    return manifest, {"secondary_phrases_mwes.csv": len(rows)}, stats, {e["headword"] for e in entries}


def _build_local_dialect(
    hist_dir: Path,
    local_root: Path,
    nfc_records: list[dict[str, str]],
) -> tuple[dict[str, Any], dict[str, int], set[str], dict[str, dict[str, str | None]]]:
    rows = _read_historical_csv(hist_dir / "secondary_dialect_colloquialisms.csv")
    entries: list[dict[str, Any]] = []
    dialect_lookup: dict[str, dict[str, str | None]] = {}
    for row_num, row in enumerate(rows, 1):
        raw_hw = _clean_text_value(row["term_ta"])
        hw_nfc, was_norm = _normalize_nfc(raw_hw)
        forms: list[dict[str, str]] = []
        if was_norm:
            nfc_records.append({"pack": "local_dialect", "raw": raw_hw, "nfc": hw_nfc})
            forms.append({"role": "raw_source", "text": raw_hw})
        translit = _clean_text_value(row.get("transliteration", ""))
        if translit:
            forms.append({"role": "transliteration", "text": translit})
        ipa = _clean_text_value(row.get("pronunciation_ipa", ""))
        if ipa:
            forms.append({"role": "ipa", "text": _normalize_nfc(ipa)[0]})

        raw_region = _clean_text_value(row.get("region_dialect", ""))
        mapped_region = normalize_dialect_region(raw_region)
        if mapped_region == "SPOKEN":
            region = None
            register = normalize_register("spoken")
        elif mapped_region == "GEN_Z":
            region = None
            register = normalize_register("slang")
        else:
            region = mapped_region
            register = normalize_register("colloquial")

        std_eq_raw = _clean_text_value(row.get("standard_equivalent", ""))
        std_eq = _normalize_nfc(std_eq_raw)[0] if std_eq_raw else None
        meaning_ta_clean = _clean_text_value(row.get("meaning_ta", ""))
        meaning_ta = _normalize_nfc(meaning_ta_clean)[0] if meaning_ta_clean else None
        notes_clean = _clean_text_value(row.get("notes", ""))
        notes = _normalize_nfc(notes_clean)[0] if notes_clean else None

        gloss_ta_val = meaning_ta
        gloss_en_val: str | None = None
        if meaning_ta and not _RE_TAMIL_SCRIPT.search(meaning_ta) and _RE_ASCII_ALPHA.search(meaning_ta):
            gloss_en_val = meaning_ta
            gloss_ta_val = None

        if hw_nfc not in dialect_lookup and (gloss_ta_val or gloss_en_val or std_eq):
            dialect_lookup[hw_nfc] = {
                "gloss_ta": gloss_ta_val or std_eq,
                "gloss_en": gloss_en_val,
                "definition_ta": notes,
                "definition_en": None,
            }

        entries.append(
            _make_entry(
                entry_id=f"loc_dial:{row['colloquial_id']}",
                headword=hw_nfc,
                pos=None,
                forms=forms,
                senses=[
                    _make_sense(
                        gloss_ta=gloss_ta_val,
                        gloss_en=gloss_en_val,
                        definition_ta=notes,
                        domain=None,
                        region=region,
                        register=register,
                    )
                ],
                domain=None,
                region=region,
                register=register,
                standard_equivalent=std_eq,
                source_id="secondary_dialect_colloquialisms",
                source_locator=f"secondary_dialect_colloquialisms.csv:{row_num}",
                rights_status="unresolved",
                permalink=None,
            )
        )
    manifest = _write_pack(
        local_root / "local_dialect",
        pack_id="local_dialect",
        pack_tier="local_historical",
        rights_status="unresolved",
        license_id="UNRESOLVED_LOCAL_ONLY",
        description="Local historical regional dialect and colloquialism terms",
        attribution_notice="Owner-supplied local historical Tamil dialect records; rights status unresolved, local/self-hosted only.",
        entries=entries,
        relations=[],
    )
    return manifest, {"secondary_dialect_colloquialisms.csv": len(rows)}, {e["headword"] for e in entries}, dialect_lookup


def _build_local_literary(
    hist_dir: Path,
    local_root: Path,
    nfc_records: list[dict[str, str]],
) -> tuple[dict[str, Any], dict[str, int], set[str]]:
    rows = _read_historical_csv(hist_dir / "secondary_archaic_literary_terms.csv")
    entries: list[dict[str, Any]] = []
    for row_num, row in enumerate(rows, 1):
        raw_hw = row["term_ta"].strip()
        hw_nfc, was_norm = _normalize_nfc(raw_hw)
        forms: list[dict[str, str]] = []
        if was_norm:
            nfc_records.append({"pack": "local_literary", "raw": raw_hw, "nfc": hw_nfc})
            forms.append({"role": "raw_source", "text": raw_hw})
        translit = row.get("transliteration", "").strip()
        if translit:
            forms.append({"role": "transliteration", "text": translit})

        lit_src = _clean_text_value(row.get("literary_source", "")) or None
        period, _, _ = _clean_domain_value(row.get("period_era"))
        lit_reg = normalize_register("literary")
        meaning_ta = _clean_text_value(row.get("meaning_ta", "")) or None
        meaning_en = _clean_text_value(row.get("meaning_en", "")) or None
        entries.append(
            _make_entry(
                entry_id=f"loc_lit:{row['archaic_id']}",
                headword=hw_nfc,
                pos=None,
                forms=forms,
                senses=[
                    _make_sense(
                        definition_ta=meaning_ta,
                        definition_en=meaning_en,
                        domain=period,
                        register=lit_reg,
                    )
                ],
                domain=period,
                register=lit_reg,
                literary_source=lit_src,
                source_id="secondary_archaic_literary_terms",
                source_locator=f"secondary_archaic_literary_terms.csv:{row_num}",
                rights_status="unresolved",
                permalink=None,
            )
        )
    manifest = _write_pack(
        local_root / "local_literary",
        pack_id="local_literary",
        pack_tier="local_historical",
        rights_status="unresolved",
        license_id="UNRESOLVED_LOCAL_ONLY",
        description="Local historical archaic and classical literary terms",
        attribution_notice="Owner-supplied local historical Tamil literary records; rights status unresolved, local/self-hosted only.",
        entries=entries,
        relations=[],
    )
    return manifest, {"secondary_archaic_literary_terms.csv": len(rows)}, {e["headword"] for e in entries}


def _build_local_names_taxa(
    hist_dir: Path,
    local_root: Path,
    nfc_records: list[dict[str, str]],
) -> tuple[dict[str, Any], dict[str, int], set[str]]:
    prop_rows = _read_historical_csv(hist_dir / "secondary_proper_names_toponyms.csv")
    taxa_rows = _read_historical_csv(hist_dir / "secondary_scientific_taxa.csv")
    entries: list[dict[str, Any]] = []

    for row_num, row in enumerate(prop_rows, 1):
        raw_hw = row["name_ta"].strip()
        hw_nfc, was_norm = _normalize_nfc(raw_hw)
        forms: list[dict[str, str]] = []
        if was_norm:
            nfc_records.append({"pack": "local_names_taxa", "raw": raw_hw, "nfc": hw_nfc})
            forms.append({"role": "raw_source", "text": raw_hw})
        translit = row.get("transliteration", "").strip()
        if translit:
            forms.append({"role": "transliteration", "text": translit})
        dom, _, _ = _clean_domain_value(row.get("name_type"))
        gloss_en = _clean_text_value(row.get("english_name", "")) or None
        notes = _clean_text_value(row.get("notes", "")) or None
        entries.append(
            _make_entry(
                entry_id=f"loc_prop:{row['proper_id']}",
                headword=hw_nfc,
                pos="PROPN",
                forms=forms,
                senses=[_make_sense(gloss_en=gloss_en, definition_en=notes, domain=dom)],
                domain=dom,
                source_id="secondary_proper_names_toponyms",
                source_locator=f"secondary_proper_names_toponyms.csv:{row_num}",
                rights_status="unresolved",
                permalink=None,
            )
        )

    for row_num, row in enumerate(taxa_rows, 1):
        raw_hw = row["tamil_name"].strip()
        hw_nfc, was_norm = _normalize_nfc(raw_hw)
        forms = []
        if was_norm:
            nfc_records.append({"pack": "local_names_taxa", "raw": raw_hw, "nfc": hw_nfc})
            forms.append({"role": "raw_source", "text": raw_hw})
        translit = row.get("transliteration", "").strip()
        if translit:
            forms.append({"role": "transliteration", "text": translit})
        sci = _clean_text_value(row.get("scientific_name", "")) or None
        dom, _, _ = _clean_domain_value(row.get("taxonomic_rank"))
        kingdom = _clean_text_value(row.get("kingdom_phylum", ""))
        notes = _clean_text_value(row.get("notes", ""))
        def_en = " | ".join(p for p in (kingdom, notes) if p) or None
        entries.append(
            _make_entry(
                entry_id=f"loc_taxa:{row['taxa_id']}",
                headword=hw_nfc,
                pos="NOUN",
                forms=forms,
                senses=[_make_sense(gloss_en=sci, definition_en=def_en, domain=dom)],
                domain=dom,
                scientific_name=sci,
                source_id="secondary_scientific_taxa",
                source_locator=f"secondary_scientific_taxa.csv:{row_num}",
                rights_status="unresolved",
                permalink=None,
            )
        )

    manifest = _write_pack(
        local_root / "local_names_taxa",
        pack_id="local_names_taxa",
        pack_tier="local_historical",
        rights_status="unresolved",
        license_id="UNRESOLVED_LOCAL_ONLY",
        description="Local historical proper names, toponyms, and scientific taxa",
        attribution_notice="Owner-supplied local historical Tamil proper names and taxa records; rights status unresolved, local/self-hosted only.",
        entries=entries,
        relations=[],
    )
    accounted = {
        "secondary_proper_names_toponyms.csv": len(prop_rows),
        "secondary_scientific_taxa.csv": len(taxa_rows),
    }
    return manifest, accounted, {e["headword"] for e in entries}


def _build_local_loans(
    hist_dir: Path,
    local_root: Path,
    nfc_records: list[dict[str, str]],
) -> tuple[dict[str, Any], dict[str, int], set[str]]:
    rows = _read_historical_csv(hist_dir / "secondary_transliterations_loanwords.csv")
    entries: list[dict[str, Any]] = []
    for row_num, row in enumerate(rows, 1):
        raw_hw = row["transliterated_ta"].strip()
        hw_nfc, was_norm = _normalize_nfc(raw_hw)
        forms: list[dict[str, str]] = []
        if was_norm:
            nfc_records.append({"pack": "local_loans", "raw": raw_hw, "nfc": hw_nfc})
            forms.append({"role": "raw_source", "text": raw_hw})
        translit = row.get("transliteration", "").strip()
        if translit:
            forms.append({"role": "transliteration", "text": translit})
        origin = _clean_text_value(row.get("origin_language", "")) or None
        pure_raw = _clean_text_value(row.get("pure_tamil_equivalent", ""))
        pure = _normalize_nfc(pure_raw)[0] if pure_raw else None
        gloss_en = _clean_text_value(row.get("source_word_en", "")) or None
        dom, _, _ = _clean_domain_value(row.get("domain"))
        entries.append(
            _make_entry(
                entry_id=f"loc_loan:{row['loanword_id']}",
                headword=hw_nfc,
                pos=None,
                forms=forms,
                senses=[_make_sense(gloss_ta=pure, gloss_en=gloss_en, domain=dom)],
                domain=dom,
                origin_language=origin,
                pure_tamil_equivalent=pure,
                source_id="secondary_transliterations_loanwords",
                source_locator=f"secondary_transliterations_loanwords.csv:{row_num}",
                rights_status="unresolved",
                permalink=None,
            )
        )
    manifest = _write_pack(
        local_root / "local_loans",
        pack_id="local_loans",
        pack_tier="local_historical",
        rights_status="unresolved",
        license_id="UNRESOLVED_LOCAL_ONLY",
        description="Local historical transliterated loanwords and pure Tamil equivalents",
        attribution_notice="Owner-supplied local historical Tamil loanword records; rights status unresolved, local/self-hosted only.",
        entries=entries,
        relations=[],
    )
    return manifest, {"secondary_transliterations_loanwords.csv": len(rows)}, {e["headword"] for e in entries}


def _build_local_relations(
    hist_dir: Path,
    local_root: Path,
    nfc_records: list[dict[str, str]],
) -> tuple[dict[str, Any], dict[str, int], dict[str, Any]]:
    rows = _read_historical_csv(hist_dir / "primary_relationships.csv")
    relations: list[dict[str, Any]] = []
    invalid_rows: list[dict[str, str]] = []
    seen_edges: set[tuple[str, str, str]] = set()
    symmetric_candidates: list[tuple[str, str, str, str]] = []
    deduplicated_relations = 0
    expanded_symmetric_edges = 0

    for row_num, row in enumerate(rows, 1):
        src_raw = _clean_text_value(row.get("source_headword_ta", ""))
        tgt_raw = _clean_text_value(row.get("target_headword_ta", ""))
        code = row.get("relation_code", "").strip().upper()
        if not src_raw or not tgt_raw or not code or src_raw == tgt_raw:
            invalid_rows.append({
                "row": str(row_num),
                "relationship_id": row.get("relationship_id", ""),
                "source_headword": src_raw,
                "target_headword": tgt_raw,
                "relation_code": code,
            })
            continue

        src_nfc, src_norm = _normalize_nfc(src_raw)
        tgt_nfc, tgt_norm = _normalize_nfc(tgt_raw)
        if src_norm:
            nfc_records.append({"pack": "local_relations", "raw": src_raw, "nfc": src_nfc})
        if tgt_norm:
            nfc_records.append({"pack": "local_relations", "raw": tgt_raw, "nfc": tgt_nfc})

        if src_nfc == tgt_nfc:
            invalid_rows.append({
                "row": str(row_num),
                "relationship_id": row.get("relationship_id", ""),
                "source_headword": src_nfc,
                "target_headword": tgt_nfc,
                "relation_code": code,
            })
            continue

        raw_dir = row.get("directionality", "").strip().lower()
        is_symmetric = raw_dir in ("symmetric", "bidirectional") or code in ("SYNONYM", "ANTONYM")
        directionality = "symmetric" if is_symmetric else "directed"

        edge_key = (src_nfc, tgt_nfc, code)
        if edge_key in seen_edges:
            deduplicated_relations += 1
            continue
        seen_edges.add(edge_key)

        locator = f"primary_relationships.csv:{row_num}"
        relations.append({
            "source_headword": src_nfc,
            "target_headword": tgt_nfc,
            "relation_code": code,
            "directionality": directionality,
            "source_id": "primary_relationships",
            "source_locator": locator,
        })
        if is_symmetric:
            symmetric_candidates.append((tgt_nfc, src_nfc, code, locator))

    for rev_src, rev_tgt, code, locator in symmetric_candidates:
        if rev_src == rev_tgt:
            continue
        rev_key = (rev_src, rev_tgt, code)
        if rev_key in seen_edges:
            continue
        seen_edges.add(rev_key)
        expanded_symmetric_edges += 1
        relations.append({
            "source_headword": rev_src,
            "target_headword": rev_tgt,
            "relation_code": code,
            "directionality": "symmetric",
            "source_id": "primary_relationships",
            "source_locator": locator,
        })

    manifest = _write_pack(
        local_root / "local_relations",
        pack_id="local_relations",
        pack_tier="local_historical",
        rights_status="unresolved",
        license_id="UNRESOLVED_LOCAL_ONLY",
        description="Local historical lexical semantic relations",
        attribution_notice="Owner-supplied local historical Tamil relation records; rights status unresolved, local/self-hosted only.",
        entries=[],
        relations=relations,
        fallback_source_ids=["primary_relationships"],
    )
    stats = {
        "input_rows": len(rows),
        "valid_relations": len(relations),
        "deduplicated_relations": deduplicated_relations,
        "expanded_symmetric_edges": expanded_symmetric_edges,
        "invalid_or_self_rows": len(invalid_rows),
        "invalid_rows": invalid_rows,
    }
    return manifest, {"primary_relationships.csv": len(rows)}, stats


def build_local_track(
    out_dir: Path,
    *,
    historical_dir: Path = DEFAULT_HISTORICAL_DIR,
    historical_pin: Path = DEFAULT_HISTORICAL_PIN,
    expected_total_rows: int = EXPECTED_HISTORICAL_TOTAL_ROWS,
) -> tuple[dict[str, Any], set[str], dict[str, set[str]]]:
    """Verify and build all 8 local_historical packs under <out_dir>/local/."""
    verify_historical_sources(historical_dir, historical_pin)
    local_root = out_dir / "local"
    nfc_records: list[dict[str, str]] = []

    pack_manifests: dict[str, Any] = {}
    pack_headwords: dict[str, set[str]] = {}
    per_file_accounted: dict[str, int] = {}

    m_core, acc_core, core_stats, hw_core, core_lookup = _build_local_core(historical_dir, local_root, nfc_records)
    pack_manifests["local_core"] = m_core
    pack_headwords["local_core"] = hw_core
    per_file_accounted.update(acc_core)

    m_term, acc_term, term_stats, hw_term = _build_local_terminology(historical_dir, local_root, nfc_records)
    pack_manifests["local_terminology"] = m_term
    pack_headwords["local_terminology"] = hw_term
    per_file_accounted.update(acc_term)

    m_dial, acc_dial, hw_dial, dialect_lookup = _build_local_dialect(historical_dir, local_root, nfc_records)
    pack_manifests["local_dialect"] = m_dial
    pack_headwords["local_dialect"] = hw_dial
    per_file_accounted.update(acc_dial)

    m_phr, acc_phr, phr_stats, hw_phr = _build_local_phrases(
        historical_dir,
        local_root,
        nfc_records,
        dialect_lookup=dialect_lookup,
        core_lookup=core_lookup,
    )
    pack_manifests["local_phrases"] = m_phr
    pack_headwords["local_phrases"] = hw_phr
    per_file_accounted.update(acc_phr)

    m_lit, acc_lit, hw_lit = _build_local_literary(historical_dir, local_root, nfc_records)
    pack_manifests["local_literary"] = m_lit
    pack_headwords["local_literary"] = hw_lit
    per_file_accounted.update(acc_lit)

    m_nt, acc_nt, hw_nt = _build_local_names_taxa(historical_dir, local_root, nfc_records)
    pack_manifests["local_names_taxa"] = m_nt
    pack_headwords["local_names_taxa"] = hw_nt
    per_file_accounted.update(acc_nt)

    m_loan, acc_loan, hw_loan = _build_local_loans(historical_dir, local_root, nfc_records)
    pack_manifests["local_loans"] = m_loan
    pack_headwords["local_loans"] = hw_loan
    per_file_accounted.update(acc_loan)

    m_rel, acc_rel, rel_stats = _build_local_relations(historical_dir, local_root, nfc_records)
    pack_manifests["local_relations"] = m_rel
    pack_headwords["local_relations"] = set()
    per_file_accounted.update(acc_rel)

    total_accounted = sum(per_file_accounted.values())
    if total_accounted != expected_total_rows:
        raise ValueError(
            f"Historical CSV row accounting mismatch: expected {expected_total_rows}, "
            f"got {total_accounted} ({per_file_accounted})"
        )

    all_headwords: set[str] = set()
    for hws in pack_headwords.values():
        all_headwords.update(hws)

    audit = {
        "historical_sha256_verified": True,
        "historical_files_verified": 12,
        "expected_historical_csv_rows": expected_total_rows,
        "total_accounted_rows": total_accounted,
        "accounting_exact": total_accounted == expected_total_rows,
        "per_file_accounted_rows": dict(sorted(per_file_accounted.items())),
        "packs": pack_manifests,
        "total_entries": sum(m["entry_count"] for m in pack_manifests.values()),
        "total_senses": sum(m["sense_count"] for m in pack_manifests.values()),
        "total_relations": sum(m["relation_count"] for m in pack_manifests.values()),
        "total_distinct_headwords": len(all_headwords),
        "local_core": core_stats,
        "local_terminology": term_stats,
        "local_phrases": phr_stats,
        "local_relations": rel_stats,
        "nfc_normalized_strings_count": len(nfc_records),
        "nfc_normalized_strings": nfc_records,
    }
    return audit, all_headwords, pack_headwords


def organize_lexicon(
    out_dir: Path = DEFAULT_OUT_DIR,
    *,
    track: str = "all",
    historical_dir: Path = DEFAULT_HISTORICAL_DIR,
    historical_pin: Path = DEFAULT_HISTORICAL_PIN,
    open_packs: dict[str, Path] = DEFAULT_OPEN_PACKS,
    tawikt_manifest_path: Path = DEFAULT_TAWIKT_MANIFEST,
    tawikt_entries_path: Path = DEFAULT_TAWIKT_ENTRIES,
    expected_historical_rows: int = EXPECTED_HISTORICAL_TOTAL_ROWS,
) -> dict[str, Any]:
    """Run read-only verification, organize requested tracks, and write cleaning_audit.json."""
    if track not in ("all", "open", "local"):
        raise ValueError(f"Unsupported track {track!r}; expected 'all', 'open', or 'local'")

    out_dir.mkdir(parents=True, exist_ok=True)
    tracks_run = ["open", "local"] if track == "all" else [track]

    audit: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "dataset_version": DATASET_VERSION,
        "tracks": tracks_run,
    }

    open_hws: set[str] = set()
    open_pack_hws: dict[str, set[str]] = {}
    local_hws: set[str] = set()
    local_pack_hws: dict[str, set[str]] = {}

    if track in ("all", "open"):
        open_audit, open_hws, open_pack_hws = build_open_track(
            out_dir,
            open_packs=open_packs,
            tawikt_manifest_path=tawikt_manifest_path,
            tawikt_entries_path=tawikt_entries_path,
        )
        audit["open"] = open_audit

    if track in ("all", "local"):
        local_audit, local_hws, local_pack_hws = build_local_track(
            out_dir,
            historical_dir=historical_dir,
            historical_pin=historical_pin,
            expected_total_rows=expected_historical_rows,
        )
        audit["local"] = local_audit

    if track == "all":
        by_pack = {
            op_id: {
                loc_id: len(op_set & loc_set)
                for loc_id, loc_set in sorted(local_pack_hws.items())
            }
            for op_id, op_set in sorted(open_pack_hws.items())
        }
        audit["cross_track_overlap"] = {
            "open_distinct_headwords": len(open_hws),
            "local_distinct_headwords": len(local_hws),
            "overlap_distinct_headwords": len(open_hws & local_hws),
            "union_distinct_headwords": len(open_hws | local_hws),
            "by_pack": by_pack,
        }

    (out_dir / "cleaning_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return audit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Output directory (default: target/lexicon/organized)",
    )
    parser.add_argument(
        "--track",
        choices=("all", "open", "local"),
        default="all",
        help="Which track(s) to build (default: all)",
    )
    args = parser.parse_args(argv)
    audit = organize_lexicon(args.out, track=args.track)
    summary: dict[str, Any] = {"out": str(args.out), "tracks": audit["tracks"]}
    if "open" in audit:
        summary["open_entries"] = audit["open"]["total_entries"]
        summary["open_senses"] = audit["open"]["total_senses"]
        summary["open_distinct_headwords"] = audit["open"]["total_distinct_headwords"]
    if "local" in audit:
        summary["local_accounted_rows"] = audit["local"]["total_accounted_rows"]
        summary["local_entries"] = audit["local"]["total_entries"]
        summary["local_senses"] = audit["local"]["total_senses"]
        summary["local_relations"] = audit["local"]["total_relations"]
        summary["local_distinct_headwords"] = audit["local"]["total_distinct_headwords"]
    if "cross_track_overlap" in audit:
        summary["cross_track_overlap_headwords"] = audit["cross_track_overlap"]["overlap_distinct_headwords"]
    print(json.dumps(summary, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
