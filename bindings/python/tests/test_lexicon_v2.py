"""Real-runtime Python parity & benchmark tests for tamil-lexicon v0.2 (TMLPACK2)."""

from __future__ import annotations

import hashlib
import http.server
import json
from pathlib import Path
import socketserver
import threading
import time
from typing import Any

import pytest
import tamil_toolkit as tt

ROOT = Path(__file__).resolve().parents[3]
GOLDEN_V02 = ROOT / "tests/golden/lexicon_v02_runtime.jsonl"
PACKS_DIR = ROOT / "dist/lexicon-packs"


def test_golden_lexicon_v02_runtime_vectors() -> None:
    tt.lexicon_unload_pack(None)
    for line in GOLDEN_V02.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        req = {"op": row["op"], "input": row["input"]}
        if "expected_error" in row:
            with pytest.raises(ValueError) as exc:
                tt.execute(req)
            assert str(exc.value) == row["expected_error"], row["id"]
        else:
            actual = tt.execute(req)
            assert actual == row["expected"], row["id"]


def test_python_runtime_all_12_compiled_packs_and_benchmark() -> None:
    if not (PACKS_DIR / "MANIFEST.json").is_file():
        pytest.skip("dist/lexicon-packs not compiled yet")

    tt.lexicon_unload_pack(None)
    try:
        # 1. Load one pack directly via raw binary bytes FFI (zero JSON array overhead)
        core_bytes = (PACKS_DIR / "open/core.tlpack").read_bytes()
        summary = tt.lexicon_load_pack_bytes(core_bytes)
        assert summary["pack_id"] == "core"
        assert summary["category"] == "dictionary"
        assert summary["pack_tier"] == "verified_open"
        assert summary["entry_count"] == 10343

        # 2. Load entire 12-pack directory (open + local)
        loaded = tt.lexicon_load_pack(str(PACKS_DIR))
        assert len(loaded["loaded"]) == 12
        by_pack = {p["pack_id"]: p["category"] for p in loaded["loaded"]}
        assert by_pack["core"] == "dictionary"
        assert by_pack["names_taxa"] == "names_taxa"
        assert by_pack["regional"] == "regional"
        assert by_pack["local_terminology"] == "terminology"
        assert by_pack["local_phrases"] == "phrases"
        assert by_pack["local_literary"] == "heritage"
        assert by_pack["local_relations"] == "relations"

        stats = tt.lexicon_stats()
        assert stats["pack_count"] == 12
        assert stats["total_entries"] == 274100
        assert stats["total_senses"] == 376308
        assert stats["total_relations"] == 30858

        # 3. Exact lookup across open + local
        q = tt.lexicon_query("\u0ba4\u0bae\u0bbf\u0bb4\u0bcd")
        assert q["status"] == "matched"
        assert q["total_entries"] >= 4
        pack_ids = {e["pack_id"] for e in q["entries"]}
        assert {"core", "ta_wiktionary", "local_core"} <= pack_ids

        # 3b. Category filtering on lexicon_query and lexicon_search
        q_dict = tt.lexicon_query("\u0ba4\u0bae\u0bbf\u0bb4\u0bcd", category="dictionary")
        assert q_dict["status"] == "matched"
        assert set(q_dict["searched_packs"]) == {"core", "local_core", "ta_wiktionary"}

        q_term = tt.lexicon_query("\u0b85\u0b95\u0bcd\u0b95\u0bc1\u0bb3\u0bcd \u0b95\u0bcb\u0b9f\u0bc1", category="terminology")
        assert q_term["status"] == "matched"
        assert q_term["searched_packs"] == ["local_terminology"]
        assert all(e["pack_id"] == "local_terminology" for e in q_term["entries"])

        s_dict = tt.lexicon_search("\u0ba4\u0bae\u0bbf\u0bb4\u0bcd", limit=5, category="dictionary")
        assert set(s_dict["searched_packs"]) == {"core", "local_core", "ta_wiktionary"}
        assert len(s_dict["hits"]) >= 1

        # 4. Mayangoli-folded open-only query
        fq = tt.lexicon_query("\u0ba4\u0bae\u0bbf\u0bb2\u0bcd", tier="open", folded=True)
        assert fq["status"] == "matched"
        assert all(e["pack_tier"] == "verified_open" for e in fq["entries"])
        assert any(e["entry"]["headword"] == "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd" for e in fq["entries"])

        # 5. Spaceless Sorkuvai variant lookup resolves to canonical TVA entry
        vq = tt.lexicon_query("\u0b85\u0b95\u0bcd\u0b95\u0bc1\u0bb3\u0bcd\u0b95\u0bcb\u0b9f\u0bc1")
        assert vq["status"] == "matched"
        assert vq["entries"][0]["entry"]["headword"] == "\u0b85\u0b95\u0bcd\u0b95\u0bc1\u0bb3\u0bcd \u0b95\u0bcb\u0b9f\u0bc1"

        # 6. FST prefix search & cursor pagination (after_key)
        s = tt.lexicon_search("\u0ba4\u0bae\u0bbf\u0bb4\u0bcd", limit=5)
        assert len(s["hits"]) == 5
        assert s["hits"][0]["headword"] == "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd"

        page1 = tt.lexicon_search("\u0ba4\u0bae\u0bbf\u0bb4\u0bcd", limit=2)
        assert len(page1["hits"]) == 2
        assert page1.get("has_more") is True
        assert page1.get("next_cursor")
        page2 = tt.lexicon_search(
            "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd",
            limit=2,
            after_key=page1["next_cursor"],
        )
        assert len(page2["hits"]) >= 1
        assert all(h["matched_key"] > page1["next_cursor"] for h in page2["hits"])

        # 6b. Bounded Damerau-Levenshtein fuzzy search & longest-prefix stemmer probes
        fuzzy = tt.lexicon_fuzzy_search("\u0ba4\u0bae\u0bbf\u0bb2\u0bcd", max_distance=1, limit=5)
        assert fuzzy["query"] == "\u0ba4\u0bae\u0bbf\u0bb2\u0bcd"
        assert fuzzy["canonical_query"] == "\u0ba4\u0bae\u0bbf\u0bb2\u0bcd"
        assert fuzzy["max_distance"] == 1
        assert any(
            h["headword"] == "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd" and h["distance"] == 1
            for h in fuzzy["hits"]
        )

        stems = tt.lexicon_longest_prefix("\u0ba4\u0bae\u0bbf\u0bb4\u0bcd\u0ba8\u0bbe\u0b9f\u0bc1")
        assert stems["query"] == "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd\u0ba8\u0bbe\u0b9f\u0bc1"
        assert "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd" in stems["prefixes"]
        assert [len(p) for p in stems["prefixes"]] == sorted(
            (len(p) for p in stems["prefixes"]),
            reverse=True,
        )

        # 7. Relations lookup (unfiltered, category-filtered, and folded)
        r = tt.lexicon_relations("\u0b85\u0ba9\u0bcd\u0baa\u0bc1")
        assert r["status"] == "matched"
        assert len(r["relations"]) >= 4

        r_cat = tt.lexicon_relations("\u0b85\u0ba9\u0bcd\u0baa\u0bc1", category="relations")
        assert r_cat["status"] == "matched"
        assert r_cat["searched_packs"] == ["local_relations"]
        assert len(r_cat["relations"]) >= 4

        r_folded = tt.lexicon_relations("\u0b85\u0ba3\u0bcd\u0baa\u0bc1", folded=True)
        assert r_folded["status"] == "matched"
        assert len(r_folded["relations"]) >= 4

        # 7b. Unified word definitions with merged meanings, relations, and provenance
        def_ta = tt.lexicon_define("\u0ba4\u0bae\u0bbf\u0bb4\u0bcd")
        assert def_ta["status"] == "matched"
        assert def_ta["headword"] == "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd"
        assert def_ta["has_verified_open"] is True
        assert def_ta["has_local_historical"] is True
        assert "dictionary" in def_ta["categories"]
        assert len(def_ta["meanings_en"]) >= 1
        assert def_ta["meanings_en"][0]["category"] in def_ta["categories"]
        assert len(def_ta["sources"]) >= 1
        assert def_ta["sources"][0]["source_id"]

        def_anbu = tt.lexicon_define("\u0b85\u0ba9\u0bcd\u0baa\u0bc1")
        assert def_anbu["status"] == "matched"
        assert def_anbu["headword"] == "\u0b85\u0ba9\u0bcd\u0baa\u0bc1"
        assert def_anbu["has_verified_open"] is True
        assert len(def_anbu["meanings_en"]) >= 1
        rels = def_anbu["relations"]
        assert any(rels[k] for k in ("synonyms", "antonyms", "related", "hypernyms"))
        assert len(def_anbu["sources"]) >= 1

        # 7c. Folded define prefers exact NFC headword (\u0b85\u0bb0\u0bc8 over \u0b85\u0bb1\u0bc8)
        def_arai = tt.lexicon_define("\u0b85\u0bb0\u0bc8", folded=True)
        assert def_arai["status"] == "matched"
        assert def_arai["folded"] is True
        assert def_arai["headword"] == "\u0b85\u0bb0\u0bc8"

        # 7d. Category-scoped define ("terminology") must not leak local_relations
        def_anbu_term = tt.lexicon_define("\u0b85\u0ba9\u0bcd\u0baa\u0bc1", category="terminology")
        assert def_anbu_term["searched_packs"] == ["local_terminology"]
        assert def_anbu_term["relations"] == {
            "synonyms": [],
            "antonyms": [],
            "related": [],
            "hypernyms": [],
        }
        assert all(s["pack_id"] != "local_relations" for s in def_anbu_term["sources"])

        # 8. Measure warmed lookup latency over 500 queries across all 274k entries
        sample_queries = [
            "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd",
            "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf",
            "\u0b85\u0ba9\u0bcd\u0baa\u0bc1",
            "\u0b85\u0b95\u0bcd\u0b95\u0bc1\u0bb3\u0bcd \u0b95\u0bcb\u0b9f\u0bc1",
            "\u0b95\u0bcb\u0bb3\u0bbe\u0bb1\u0bc1",
        ]
        latencies_ms: list[float] = []
        for i in range(500):
            w = sample_queries[i % len(sample_queries)]
            t0 = time.perf_counter()
            res = tt.lexicon_query(w)
            latencies_ms.append((time.perf_counter() - t0) * 1000.0)
            assert res["status"] == "matched"
        latencies_ms.sort()
        p95 = latencies_ms[int(len(latencies_ms) * 0.95)]
        assert p95 < 10.0, f"p95 lookup latency {p95:.3f} ms exceeded 10 ms budget"
    finally:
        tt.lexicon_unload_pack(None)


def test_python_lexicon_init_profiles() -> None:
    if not (PACKS_DIR / "MANIFEST.json").is_file():
        pytest.skip("dist/lexicon-packs not compiled yet")

    tt.lexicon_unload_pack(None)
    try:
        lite = tt.lexicon_init(profile="open-lite", path=PACKS_DIR)
        assert lite["profile"] == "open-lite"
        assert lite["pack_count"] == 3
        assert len(lite["loaded"]) == 3
        lite_cats = {p["pack_id"]: p["category"] for p in lite["loaded"]}
        assert lite_cats == {
            "core": "dictionary",
            "names_taxa": "names_taxa",
            "regional": "regional",
        }
        assert tt.lexicon_stats()["pack_count"] == 3

        full = tt.lexicon_init(profile="full", path=PACKS_DIR)
        assert full["profile"] == "full"
        assert full["pack_count"] == 12
        assert full["total_entries"] == 274100
        assert len(full["loaded"]) == 12
        assert tt.lexicon_stats()["pack_count"] == 12
    finally:
        tt.lexicon_unload_pack(None)


def _sample_manifest_and_files(base_dir: Path) -> tuple[dict[str, Any], dict[str, bytes]]:
    blobs = {
        "open/core.tlpack": b"TMLPACK2-CORE-MOCK",
        "open/names_taxa.tlpack": b"TMLPACK2-NAMES-MOCK",
        "open/regional.tlpack": b"TMLPACK2-REGIONAL-MOCK",
        "open/ta_wiktionary.tlpack": b"TMLPACK2-TAWIKI-MOCK",
        "local/local_core.tlpack": b"TMLPACK2-LOCAL-MOCK",
    }
    pack_specs = [
        ("core", "open/core.tlpack", "verified_open", "dictionary"),
        ("names_taxa", "open/names_taxa.tlpack", "verified_open", "names_taxa"),
        ("regional", "open/regional.tlpack", "verified_open", "regional"),
        ("ta_wiktionary", "open/ta_wiktionary.tlpack", "verified_open", "dictionary"),
        ("local_core", "local/local_core.tlpack", "local_historical", "dictionary"),
    ]
    manifest_packs = []
    for pack_id, rel_file, tier, category in pack_specs:
        raw = blobs[rel_file]
        file_path = base_dir / rel_file
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(raw)
        manifest_packs.append({
            "file": rel_file,
            "summary": {
                "pack_id": pack_id,
                "category": category,
                "index_format_version": 2,
                "schema_version": 2,
                "pack_tier": tier,
                "rights_status": "CC-BY-SA-4.0" if tier == "verified_open" else "unresolved",
                "license": "CC-BY-SA-4.0" if tier == "verified_open" else "UNRESOLVED_LOCAL_ONLY",
                "dataset_version": "0.2.0",
                "description": f"Mock {pack_id}",
                "entry_count": 1,
                "sense_count": 1,
                "relation_count": 0,
                "distinct_headwords": 1,
                "byte_len": len(raw),
                "checksum_sha256": hashlib.sha256(raw).hexdigest(),
                "has_folded_index": True,
                "has_relations": False,
                "has_english_index": True,
                "source_ids": ["mock"],
                "attribution_notice": "mock",
                "domains": [],
                "regions": [],
                "registers": [],
            },
        })
    manifest = {"schema_version": 2, "pack_count": len(manifest_packs), "packs": manifest_packs}
    (base_dir / "MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
    return manifest, blobs


def test_python_lexicon_search_english_and_stats_facets_dispatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[dict[str, Any]] = []

    def fake_execute(req: dict[str, Any]) -> Any:
        captured.append(req)
        if req["op"] == "lexicon_search_english":
            return {
                "prefix": req["input"]["query"],
                "canonical_prefix": req["input"]["query"].lower(),
                "folded": False,
                "searched_packs": ["core"],
                "hits": [
                    {
                        "headword": "\u0ba8\u0bc0\u0bb0\u0bcd",
                        "matched_key": "water",
                        "packs": ["core"],
                        "pack_tiers": ["verified_open"],
                        "pos": ["noun"],
                        "preview_gloss": "water",
                        "entry_count": 1,
                    }
                ],
                "has_more": False,
            }
        if req["op"] == "lexicon_stats":
            return {
                "pack_count": 1,
                "total_entries": 10,
                "total_senses": 12,
                "total_relations": 0,
                "total_bytes": 1024,
                "packs": [{"pack_id": "core", "has_english_index": True}],
                "category_counts": {"dictionary": 10},
                "pos_counts": {"noun": 6, "verb": 4},
                "domain_counts": {"Nature": 3},
                "region_counts": {"TN": 2},
                "register_counts": {"standard": 8},
                "has_english_index": True,
            }
        raise AssertionError(f"Unexpected op: {req}")

    monkeypatch.setattr(tt, "execute", fake_execute)

    res = tt.lexicon_search_english(
        "water",
        category="dictionary",
        pos="noun",
        domain="Nature",
        region="TN",
        register="standard",
        limit=10,
    )
    assert captured[0] == {
        "op": "lexicon_search_english",
        "input": {
            "query": "water",
            "limit": 10,
            "category": "dictionary",
            "pos": "noun",
            "domain": "Nature",
            "region": "TN",
            "register": "standard",
        },
    }
    assert res["hits"][0]["headword"] == "\u0ba8\u0bc0\u0bb0\u0bcd"

    stats = tt.lexicon_stats()
    assert stats["has_english_index"] is True
    assert stats["category_counts"] == {"dictionary": 10}
    assert stats["pos_counts"] == {"noun": 6, "verb": 4}
    assert stats["domain_counts"] == {"Nature": 3}
    assert stats["region_counts"] == {"TN": 2}
    assert stats["register_counts"] == {"standard": 8}


def test_python_lexicon_download_offline_http_and_file(tmp_path: Path) -> None:
    serve_dir = tmp_path / "server"
    _sample_manifest_and_files(serve_dir)

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, directory=str(serve_dir), **kwargs)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            return

    with socketserver.TCPServer(("127.0.0.1", 0), QuietHandler) as httpd:
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            manifest_url = f"http://127.0.0.1:{port}/MANIFEST.json"
            dest_lite = tmp_path / "dl_lite"
            res1 = tt.lexicon_download("open-lite", dest=dest_lite, manifest_url=manifest_url)
            assert res1["downloaded"] == ["core", "names_taxa", "regional"]
            assert res1["skipped"] == []
            assert (dest_lite / "open/core.tlpack").is_file()
            assert (dest_lite / "MANIFEST.json").is_file()
            assert not (dest_lite / "open/ta_wiktionary.tlpack").exists()

            # Second run skips unchanged SHA-256 files
            res2 = tt.lexicon_download("open-lite", dest=dest_lite, manifest_url=manifest_url)
            assert res2["downloaded"] == []
            assert res2["skipped"] == ["core", "names_taxa", "regional"]

            # force=True re-downloads
            res3 = tt.lexicon_download(
                "open-lite", dest=dest_lite, manifest_url=manifest_url, force=True
            )
            assert res3["downloaded"] == ["core", "names_taxa", "regional"]
            assert res3["skipped"] == []

            # Explicit packs & local profile via file:// URI
            file_manifest_url = (serve_dir / "MANIFEST.json").as_uri()
            dest_local = tmp_path / "dl_local"
            res_local = tt.lexicon_download("local", dest=dest_local, manifest_url=file_manifest_url)
            assert res_local["downloaded"] == ["local_core"]
            assert (dest_local / "local/local_core.tlpack").is_file()

            # SHA-256 mismatch aborts cleanly without leaving .tmp or target file
            bad_manifest = json.loads((serve_dir / "MANIFEST.json").read_text(encoding="utf-8"))
            bad_manifest["packs"][0]["summary"]["checksum_sha256"] = "0" * 64
            bad_manifest_path = serve_dir / "BAD_MANIFEST.json"
            bad_manifest_path.write_text(json.dumps(bad_manifest), encoding="utf-8")
            dest_bad = tmp_path / "dl_bad"
            with pytest.raises(ValueError, match="SHA-256 mismatch"):
                tt.lexicon_download(
                    packs=["core"],
                    dest=dest_bad,
                    manifest_url=f"http://127.0.0.1:{port}/BAD_MANIFEST.json",
                )
            assert not (dest_bad / "open/core.tlpack").exists()
            assert not (dest_bad / "open/core.tlpack.tmp").exists()
        finally:
            httpd.shutdown()


def test_python_lexicon_init_auto_download(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    empty_dir = tmp_path / "empty_packs"
    download_calls: list[dict[str, Any]] = []

    def fake_download(
        profile: str = "open",
        *,
        packs: list[str] | None = None,
        dest: str | Path | None = None,
        manifest_url: str | None = None,
        force: bool = False,
    ) -> dict[str, Any]:
        download_calls.append({"profile": profile, "dest": dest, "manifest_url": manifest_url})
        return {
            "dest": str(dest or empty_dir),
            "downloaded": ["core"],
            "skipped": [],
            "manifest_url": manifest_url or tt.DEFAULT_LEXICON_MANIFEST_URL,
        }

    calls = {"count": 0}

    def fake_execute(req: dict[str, Any]) -> Any:
        assert req["op"] == "lexicon_init"
        calls["count"] += 1
        if calls["count"] == 1:
            raise ValueError(f"lexicon: pack directory not found: '{empty_dir}'")
        return {
            "directory": str(empty_dir),
            "profile": req["input"]["profile"],
            "pack_count": 1,
            "total_entries": 1,
            "total_senses": 1,
            "total_relations": 0,
            "total_bytes": 100,
            "loaded": [],
        }

    monkeypatch.setattr(tt, "lexicon_download", fake_download)
    monkeypatch.setattr(tt, "execute", fake_execute)

    res = tt.lexicon_init(
        profile="open-lite",
        path=empty_dir,
        auto_download=True,
        manifest_url="https://example.invalid/MANIFEST.json",
    )
    assert len(download_calls) == 1
    assert download_calls[0]["profile"] == "open-lite"
    assert res["pack_count"] == 1


def test_python_runtime_english_search_and_facet_stats() -> None:
    if not (PACKS_DIR / "open/core.tlpack").is_file():
        pytest.skip("dist/lexicon-packs not compiled yet")

    tt.lexicon_unload_pack(None)
    try:
        try:
            tt.lexicon_load_pack(str(PACKS_DIR / "open/core.tlpack"))
        except ValueError as err:
            if "unsupported flags" in str(err):
                pytest.skip("native binary not rebuilt for TMLPACK2 English index flags yet")
            raise
        stats = tt.lexicon_stats()
        if "has_english_index" not in stats:
            pytest.skip("native binary not rebuilt with lexicon_stats facet counts yet")
        assert stats["has_english_index"] is True
        assert isinstance(stats["category_counts"], dict)
        assert stats["category_counts"].get("dictionary", 0) > 0
        assert isinstance(stats["pos_counts"], dict)

        try:
            en = tt.lexicon_search_english("water", limit=10)
        except ValueError as err:
            if "unsupported operation: lexicon_search_english" in str(err):
                pytest.skip("native binary not rebuilt with lexicon_search_english yet")
            raise
        assert en["hits"]
    finally:
        tt.lexicon_unload_pack(None)
