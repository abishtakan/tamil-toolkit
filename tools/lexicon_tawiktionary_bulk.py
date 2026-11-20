"""Fail-closed Tamil Wiktionary (ta.wiktionary.org) dump parser and verified exporter.

Parses the official pinned Wikimedia XML dump (`tawiktionary-latest-pages-articles.xml.bz2`,
licensed under CC-BY-SA-4.0 / GFDL) into clean, provenance-backed Tamil lexical entries
with Tamil definitions (`tam`) and English translations (`eng`).
"""

from __future__ import annotations

import argparse
import bz2
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import unicodedata
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = ROOT / "data/sources/tawiktionary-tamil"
DEFAULT_DUMP_PATH = DEFAULT_SOURCE_DIR / "tawiktionary-latest-pages-articles.xml.bz2"
DEFAULT_OUTPUT_DIR = ROOT / "target/lexicon/tawiktionary-bulk"
DEFAULT_REPORT_PATH = ROOT / "target/lexicon/tawiktionary-bulk-report.json"
SOURCE_ID = "ta-wiktionary-dump-2026-11-01"

TAMIL_CHAR_RE = re.compile(r"[\u0b80-\u0bff]")
FORBIDDEN_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\ufeff\u200b-\u200f\u202a-\u202e]")
HEADING_RE = re.compile(r"^(={2,5})\s*(.+?)\s*\1\s*$")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
REF_TAG_RE = re.compile(r"<ref\b[^>]*>.*?</ref>|<ref\b[^>]*/>", re.I | re.S)
HTML_TAG_RE = re.compile(r"</?[a-zA-Z][^>]*>")
FILE_LINK_RE = re.compile(r"\[\[(?:File|Image|படிமம்|கோப்பு):[^\]]*\]\]", re.I)
CATEGORY_LINK_RE = re.compile(r"\[\[(?:Category|பகுப்பு):[^\]]*\]\]", re.I)
WIKILINK_RE = re.compile(r"\[\[([^|\]]+)\|([^\]]+)\]\]|\[\[([^\]]+)\]\]")
EXT_LINK_RE = re.compile(r"\[https?://[^\s\]]+(?:\s+([^\]]+))?\]")
SIMPLE_CITATION_TMPL_RE = re.compile(r"\(\s*\{\{[^{}]*\}\}[^{}()]*\)")
EMPTY_PARENS_RE = re.compile(r"\(\s*[,;:\s]*\)")
MULTISPACE_RE = re.compile(r"\s+")

POS_TEMPLATE_MAP: dict[str, str] = {
    "பெயர்ச்சொல்-பகுப்பு": "NOUN",
    "வினைச்சொல்-பகுப்பு": "VERB",
    "வினைசொல்-பகுப்பு": "VERB",
    "உரிச்சொல்-பகுப்பு": "ADJ",
    "உரிச்ச்சொல்-பகுப்பு": "ADJ",
    "வினையுரிச்சொல்-பகுப்பு": "ADV",
    "இடைச்சொல்-பகுப்பு": "PART",
    "பிரதிப்பெயர்-பகுப்பு": "PRON",
}

POS_HEADING_MAP: dict[str, str] = {
    "பெயர்ச்சொல்": "NOUN",
    "பெயர்ச்சொற்கள்": "NOUN",
    "வினைச்சொல்": "VERB",
    "வினைச்சொற்கள்": "VERB",
    "உரிச்சொல்": "ADJ",
    "பெயரடை": "ADJ",
    "வினையுரிச்சொல்": "ADV",
    "வினையடை": "ADV",
    "இடைச்சொல்": "PART",
    "பிரதிப்பெயர்": "PRON",
    "எண்ணுப்பெயர்": "NUM",
    "வியப்பிடைச்சொல்": "INTJ",
}

POS_TMPL_RE = re.compile(r"\{\{\s*([^|{}]+-பகுப்பு)\s*\|\s*ta\s*\}\}")


def _clean_wikitext_line(raw: str) -> str | None:
    """Clean a single definition or translation line; fail closed on unexpanded templates/markup."""
    s = HTML_COMMENT_RE.sub("", raw)
    s = REF_TAG_RE.sub("", s)
    s = FILE_LINK_RE.sub("", s)
    s = CATEGORY_LINK_RE.sub("", s)
    s = SIMPLE_CITATION_TMPL_RE.sub("", s)
    # Remove simple inline citation/label templates with no nested braces when they are purely trailing or standalone
    s = re.sub(r"\{\{(?:மேற்கோள்-சொல்|எ\. ?கா\.|சிறு-மொழி|ஆதாரங்கள்-மொழி|PAGENAME)[^{}]*\}\}", "", s)
    # Unwrap wikilinks [[target|label]] -> label, [[word]] -> word
    def _replace_link(m: re.Match[str]) -> str:
        if m.group(2) is not None:
            return m.group(2)
        target = m.group(3) or ""
        if ":" in target:
            return ""
        return target

    s = WIKILINK_RE.sub(_replace_link, s)
    s = EXT_LINK_RE.sub(lambda m: m.group(1) or "", s)
    s = HTML_TAG_RE.sub(" ", s)
    s = s.replace("'''", "").replace("''", "")
    s = EMPTY_PARENS_RE.sub("", s)
    s = MULTISPACE_RE.sub(" ", s).strip(" \t\r\n-:;,.")

    if not s or len(s) < 2 or len(s) > 400:
        return None
    # Fail closed if unexpanded templates, tables, or magic markup remain
    if "{{" in s or "}}" in s or "{|" in s or "|}" in s or "[[" in s or "]]" in s:
        return None
    if FORBIDDEN_CONTROL_RE.search(s):
        s = FORBIDDEN_CONTROL_RE.sub("", s).strip()
        if not s:
            return None
    return unicodedata.normalize("NFC", s)


def parse_tawiktionary_page(
    *,
    pageid: int,
    revid: int,
    timestamp: str,
    title: str,
    wikitext: str,
) -> tuple[dict[str, Any] | None, str | None]:
    """Parse one ta.wiktionary.org namespace-0 page into a clean entry or rejection reason."""
    headword = unicodedata.normalize("NFC", title.strip())
    if not headword or len(headword) > 120:
        return None, "TITLE_EMPTY_OR_TOO_LONG"
    if ":" in headword or "/" in headword or headword.startswith("-"):
        return None, "NON_LEMMA_TITLE"
    if not TAMIL_CHAR_RE.search(headword):
        return None, "NON_TAMIL_TITLE"
    if FORBIDDEN_CONTROL_RE.search(headword):
        return None, "FORBIDDEN_SCALAR_IN_TITLE"
    # Skip meta/main pages
    if headword in {"முதற் பக்கம்", "தமிழ்"} and "{{மொழி|ta}}" not in wikitext and "==பொருள்==" not in wikitext:
        return None, "META_PAGE"

    # Determine POS from templates first
    pos: str | None = None
    for m in POS_TMPL_RE.finditer(wikitext):
        key = m.group(1).strip()
        if key in POS_TEMPLATE_MAP:
            pos = POS_TEMPLATE_MAP[key]
            break

    tam_defs: list[str] = []
    eng_trans: list[str] = []

    section = "root"
    in_en_trans = False
    in_other_lang = False

    for raw_line in wikitext.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        hm = HEADING_RE.match(line)
        if hm:
            level = len(hm.group(1))
            heading = hm.group(2).strip().strip("=: ")
            # Detect non-Tamil language section (e.g. =={{மொழி|en}}==)
            if "{{மொழி|" in heading:
                if "{{மொழி|ta}}" in heading:
                    in_other_lang = False
                    section = "tamil"
                else:
                    in_other_lang = True
                    section = "other_lang"
                in_en_trans = False
                continue
            if heading in {"ஆங்கிலம்", "இந்தி", "மலையாளம்", "தெலுங்கு", "கன்னடம்", "சமஸ்கிருதம்"} and level == 2:
                in_other_lang = True
                section = "other_lang"
                in_en_trans = False
                continue
            if heading == "தமிழ்" and level == 2:
                in_other_lang = False
                section = "tamil"
                in_en_trans = False
                continue

            if in_other_lang:
                continue

            if heading in POS_HEADING_MAP:
                if pos is None:
                    pos = POS_HEADING_MAP[heading]
                section = "meaning"
                in_en_trans = False
            elif heading in {"பொருள்", "விளக்கம்"}:
                section = "meaning"
                in_en_trans = False
            elif heading in {"மொழிபெயர்ப்புகள்", "மொழிபெயர்ப்பு"}:
                section = "translations"
                in_en_trans = False
            else:
                section = "other"
                in_en_trans = False
            continue

        if in_other_lang:
            continue

        if section == "translations":
            if "{{சிறு-மொழி|en}}" in line or "{{மொழி|en}}" in line:
                in_en_trans = True
                continue
            if "{{சிறு-மொழி|" in line or "{{மொழி|" in line:
                in_en_trans = False
                continue
            if in_en_trans and line.startswith("#") and not line.startswith("#:") and not line.startswith("#*"):
                cleaned = _clean_wikitext_line(line.lstrip("# "))
                if cleaned and not TAMIL_CHAR_RE.search(cleaned) and cleaned not in eng_trans:
                    eng_trans.append(cleaned)
            elif line.startswith("*") and ("ஆங்கிலம்" in line or "English" in line):
                parts = re.split(r"[:\-–—]", line, maxsplit=1)
                if len(parts) == 2:
                    cleaned = _clean_wikitext_line(parts[1])
                    if cleaned and not TAMIL_CHAR_RE.search(cleaned) and cleaned not in eng_trans:
                        eng_trans.append(cleaned)
            continue

        if section in {"meaning", "root", "tamil"}:
            if line.startswith("#") and not line.startswith("#:") and not line.startswith("#*"):
                cleaned = _clean_wikitext_line(line.lstrip("# "))
                if cleaned and cleaned not in tam_defs:
                    tam_defs.append(cleaned)

    if not tam_defs and not eng_trans:
        return None, "NO_CLEAN_SENSES"

    # Cap per-entry senses cleanly to keep payloads bounded
    tam_defs = tam_defs[:12]
    eng_trans = eng_trans[:8]

    encoded_title = urllib.parse.quote(headword.replace(" ", "_"), safe="")
    entry = {
        "headword": headword,
        "pos": pos,
        "pos_attested": pos is not None,
        "tam_defs": tam_defs,
        "eng_trans": eng_trans,
        "source_id": SOURCE_ID,
        "license": "CC-BY-SA-4.0",
        "pageid": pageid,
        "revid": revid,
        "timestamp": timestamp,
        "permalink": f"https://ta.wiktionary.org/w/index.php?title={encoded_title}&oldid={revid}",
        "history_url": f"https://ta.wiktionary.org/w/index.php?title={encoded_title}&action=history",
    }
    return entry, None


def run_extract(dump_path: Path, output_dir: Path, report_path: Path, source_dir: Path) -> dict[str, Any]:
    if not dump_path.exists():
        raise FileNotFoundError(f"Missing dump file: {dump_path}")

    # Compute dump sha256 once for pinned manifest
    h = hashlib.sha256()
    with dump_path.open("rb") as fh:
        while True:
            chunk = fh.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    dump_sha256 = h.hexdigest()
    dump_bytes = dump_path.stat().st_size

    output_dir.mkdir(parents=True, exist_ok=True)
    entries_path = output_dir / "entries.jsonl.gz"

    stats: Counter[str] = Counter()
    pos_counts: Counter[str] = Counter()
    exclusions: Counter[str] = Counter()
    seen_headwords: set[str] = set()
    kept_entries: list[dict[str, Any]] = []

    with bz2.open(dump_path, "rb") as fh:
        for _event, elem in ET.iterparse(fh, events=("end",)):
            tag = elem.tag.rsplit("}", 1)[-1]
            if tag == "page":
                ns = elem.findtext("{*}ns")
                redirect = elem.find("{*}redirect")
                if ns == "0" and redirect is None:
                    stats["ns0_pages"] += 1
                    title = elem.findtext("{*}title") or ""
                    if TAMIL_CHAR_RE.search(title):
                        stats["tamil_title_pages"] += 1
                        pid_txt = elem.findtext("{*}id") or "0"
                        rid_txt = elem.findtext("{*}revision/{*}id") or "0"
                        ts = elem.findtext("{*}revision/{*}timestamp") or ""
                        wikitext = elem.findtext("{*}revision/{*}text") or ""
                        entry, reason = parse_tawiktionary_page(
                            pageid=int(pid_txt),
                            revid=int(rid_txt),
                            timestamp=ts,
                            title=title,
                            wikitext=wikitext,
                        )
                        if entry is None:
                            exclusions[reason or "UNKNOWN"] += 1
                        else:
                            hw = entry["headword"]
                            if hw in seen_headwords:
                                exclusions["DUPLICATE_NFC_HEADWORD"] += 1
                            else:
                                seen_headwords.add(hw)
                                kept_entries.append(entry)
                                stats["kept_entries"] += 1
                                stats["kept_tam_defs"] += len(entry["tam_defs"])
                                stats["kept_eng_trans"] += len(entry["eng_trans"])
                                if entry["tam_defs"] and entry["eng_trans"]:
                                    stats["bilingual_entries"] += 1
                                pos_counts[entry["pos"] or "UNKNOWN"] += 1
                elem.clear()

    kept_entries.sort(key=lambda e: e["headword"])
    with gzip.open(entries_path, "wt", encoding="utf-8", newline="\n") as out:
        for entry in kept_entries:
            out.write(json.dumps(entry, ensure_ascii=True, separators=(",", ":")) + "\n")

    # Write pinned source manifest & license notice
    manifest_path = source_dir / "snapshots_manifest.json"
    manifest_data = {
        "source_id": SOURCE_ID,
        "site": "https://ta.wiktionary.org",
        "dump_url": "https://dumps.wikimedia.org/tawiktionary/latest/tawiktionary-latest-pages-articles.xml.bz2",
        "dump_filename": dump_path.name,
        "dump_bytes": dump_bytes,
        "dump_sha256": dump_sha256,
        "license": "CC-BY-SA-4.0 AND GFDL",
        "extracted_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "kept_entries": stats["kept_entries"],
    }
    manifest_path.write_text(json.dumps(manifest_data, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")

    notice_dir = source_dir / "notices"
    notice_dir.mkdir(parents=True, exist_ok=True)
    notice_path = notice_dir / "ATTRIBUTION_AND_LICENSE.md"
    notice_path.write_text(
        "# Tamil Wiktionary (`ta.wiktionary.org`) Attribution & License\n\n"
        "- **Source**: Tamil Wiktionary (`https://ta.wiktionary.org`), official Wikimedia dump "
        "`tawiktionary-latest-pages-articles.xml.bz2`.\n"
        f"- **Dump SHA-256**: `{dump_sha256}` ({dump_bytes:,} bytes).\n"
        "- **License**: Creative Commons Attribution-ShareAlike 4.0 International (`CC-BY-SA-4.0`) "
        "and GNU Free Documentation License (`GFDL`), per Wikimedia Terms of Use.\n"
        "- **Attribution**: Each extracted entry retains its exact `pageid`, `revid`, `permalink`, "
        "and `history_url` linking back to the contributors on `ta.wiktionary.org`.\n",
        encoding="utf-8",
        newline="\n",
    )

    report = {
        "source_id": SOURCE_ID,
        "dump_sha256": dump_sha256,
        "dump_bytes": dump_bytes,
        "stats": dict(stats),
        "pos_counts": dict(pos_counts.most_common()),
        "exclusions": dict(exclusions.most_common()),
        "entries_path": str(entries_path.relative_to(ROOT)).replace("\\", "/"),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump", type=Path, default=DEFAULT_DUMP_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    args = parser.parse_args()
    report = run_extract(args.dump, args.output_dir, args.report, args.source_dir)
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
