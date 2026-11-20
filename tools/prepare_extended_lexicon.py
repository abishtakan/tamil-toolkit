"""Build the sharded extended verified dictionary index (~90k+ CC-BY-SA-4.0 Tamil words) for the Playground.

Combines:
1. Embedded Rust WASM packs (`core`, `names_taxa`, `regional` from `en.wiktionary.org`).
2. Verified `ta.wiktionary.org` bulk entries (`target/lexicon/tawiktionary-bulk/entries.jsonl.gz`).

Emits lazy-loaded letter buckets (`letters/*.json`) and 256 headword shards (`shards/*.json`)
under `playground/public/lexicon-extended/` so the browser stays fast and zero-bloat.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.prepare_playground import (  # noqa: E402
    TAMIL_LETTER_ORDER,
    TAMIL_LETTER_RANK,
    _truncate_gloss,
    build_artifacts,
    initial_letter_bucket,
)

TAWIKT_ENTRIES_PATH = ROOT / "target/lexicon/tawiktionary-bulk/entries.jsonl.gz"
TAWIKT_NOTICE_PATH = ROOT / "data/sources/tawiktionary-tamil/notices/ATTRIBUTION_AND_LICENSE.md"
TAWIKT_MANIFEST_PATH = ROOT / "data/sources/tawiktionary-tamil/snapshots_manifest.json"
EXTENDED_DIR = ROOT / "playground/public/lexicon-extended"


def shard_hex(word: str) -> str:
    return hashlib.sha256(word.encode("utf-8")).hexdigest()[:2]


def prepare_extended() -> dict[str, Any]:
    _catalog_data, embedded_browse = build_artifacts()

    merged: dict[str, dict[str, Any]] = {}
    all_pos: set[str] = set(embedded_browse["pos"])

    # 1. Seed with embedded Rust WASM words (9,410 words)
    for hw, letter, packs, pos_list, regions, gloss in embedded_browse["items"]:
        merged[hw] = {
            "letter": letter,
            "packs": set(packs),
            "pos": set(pos_list),
            "regions": set(regions),
            "gloss": gloss,
        }
    embedded_count = len(merged)

    # 2. Merge verified ta.wiktionary.org entries (~85,889 words)
    tawikt_count = 0
    overlap_count = 0
    shards: dict[str, dict[str, Any]] = {f"{i:02x}": {} for i in range(256)}
    source_id = "ta-wiktionary-dump-2026-11-01"
    dump_sha256 = ""

    if TAWIKT_MANIFEST_PATH.exists():
        m = json.loads(TAWIKT_MANIFEST_PATH.read_text(encoding="utf-8"))
        source_id = m.get("source_id", source_id)
        dump_sha256 = m.get("dump_sha256", "")

    if TAWIKT_ENTRIES_PATH.exists():
        with gzip.open(TAWIKT_ENTRIES_PATH, "rt", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                entry = json.loads(line)
                hw = entry["headword"]
                tawikt_count += 1
                pos = entry.get("pos")
                if pos:
                    all_pos.add(pos)

                # Store full ta.wiktionary.org details in 256 headword shards
                shards[shard_hex(hw)][hw] = {
                    "pos": pos,
                    "tam_defs": entry.get("tam_defs", []),
                    "eng_trans": entry.get("eng_trans", []),
                    "pageid": entry["pageid"],
                    "revid": entry["revid"],
                    "timestamp": entry.get("timestamp", ""),
                    "permalink": entry["permalink"],
                    "history_url": entry["history_url"],
                    "source_id": entry.get("source_id", source_id),
                    "license": entry.get("license", "CC-BY-SA-4.0"),
                }

                # Build concise preview gloss (prefer English translation, fallback to Tamil definition)
                preview_parts: list[str] = []
                if entry.get("eng_trans"):
                    preview_parts.extend(entry["eng_trans"][:2])
                if not preview_parts and entry.get("tam_defs"):
                    preview_parts.extend(entry["tam_defs"][:2])
                ta_preview = _truncate_gloss("; ".join(preview_parts), max_len=96)

                if hw in merged:
                    overlap_count += 1
                    rec = merged[hw]
                    rec["packs"].add("ta_wiktionary")
                    if pos:
                        rec["pos"].add(pos)
                    if not rec["gloss"] and ta_preview:
                        rec["gloss"] = ta_preview
                else:
                    merged[hw] = {
                        "letter": initial_letter_bucket(hw),
                        "packs": {"ta_wiktionary"},
                        "pos": {pos} if pos else set(),
                        "regions": set(),
                        "gloss": ta_preview,
                    }

    # 3. Group into Tamil alphabetical letter buckets
    by_letter: dict[str, list[list[Any]]] = {}
    for hw, rec in merged.items():
        by_letter.setdefault(rec["letter"], []).append([
            hw,
            sorted(rec["packs"]),
            sorted(rec["pos"]),
            sorted(rec["regions"]),
            rec["gloss"],
        ])

    letters_dir = EXTENDED_DIR / "letters"
    shards_dir = EXTENDED_DIR / "shards"
    letters_dir.mkdir(parents=True, exist_ok=True)
    shards_dir.mkdir(parents=True, exist_ok=True)

    letter_manifest: list[dict[str, Any]] = []
    ordered_letters = [*TAMIL_LETTER_ORDER, "#"]
    for idx, ch in enumerate(ordered_letters):
        rows = by_letter.get(ch)
        if not rows:
            continue
        rows.sort(key=lambda r: r[0])
        fname = f"{idx:02d}.json"
        (letters_dir / fname).write_text(
            json.dumps(rows, ensure_ascii=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        letter_manifest.append({"id": ch, "file": fname, "count": len(rows)})

    # 4. Write 256 entry detail shards
    for key, payload in shards.items():
        (shards_dir / f"{key}.json").write_text(
            json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    # 5. Copy attribution notice
    if TAWIKT_NOTICE_PATH.exists():
        (EXTENDED_DIR / "NOTICE.md").write_bytes(TAWIKT_NOTICE_PATH.read_bytes())

    manifest = {
        "version": 1,
        "total_words": len(merged),
        "embedded_words": embedded_count,
        "tawiktionary_words": tawikt_count,
        "overlap_words": overlap_count,
        "source_id": source_id,
        "dump_sha256": dump_sha256,
        "license": "CC-BY-SA-4.0",
        "letters": letter_manifest,
        "pos": sorted(all_pos),
    }
    (EXTENDED_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return {
        "total_words": len(merged),
        "embedded_words": embedded_count,
        "tawiktionary_words": tawikt_count,
        "overlap_words": overlap_count,
        "letter_buckets": len(letter_manifest),
        "shard_count": len(shards),
    }


def main() -> None:
    summary = prepare_extended()
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
