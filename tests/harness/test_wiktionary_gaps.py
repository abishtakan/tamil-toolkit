"""Gap reconciliation keeps source absence separate from rejected source text."""

import hashlib

import pytest

from tools.lexicon_wiktionary_gaps import ROOT, fetch_missing, reconcile_records, stage_candidates, validate_supplemental_directory, verify_capture, verify_page, verify_raw_files


def page(title="sample", text="==Tamil==\n===Noun===\n# sample"):
    return {
        "title": title, "pageid": 1, "revid": 2,
        "wikitext": text,
        "wikitext_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "permalink_url": "https://en.wiktionary.org/w/index.php?oldid=2",
        "history_url": "https://en.wiktionary.org/w/index.php?action=history",
    }


def test_gap_accounting_and_source_presence_are_independent():
    candidates = [{"headword": s, "word_ids": [i]} for i, s in enumerate(("absent", "blocked", "recoverable"))]
    pages = {"blocked": page("blocked"), "recoverable": page("recoverable")}

    def parse(p, **kwargs):
        if p["title"] == "blocked":
            return {"entries": [], "exclusions": [{"reason_code": "UNSAFE"}]}
        return {"entries": [{"entry_id": "ent_test", "senses": [{"meaning_en": "sample"}]}], "exclusions": []}

    report = reconcile_records(candidates, pages, parser=parse)
    assert report["status_counts"] == {"missing_from_snapshot": 1, "recoverable_candidate": 1, "source_present_parser_blocked": 1}
    assert report["candidate_entries"][0]["entry_id"] == "ent_test"
    assert report["records"][1]["blocker_counts"] == {"UNSAFE": 1}
    assert all(row["historical_claims_approved"] is False for row in report["records"])


def test_source_digest_and_unsafe_attribution_fail_closed():
    p = page()
    verify_page(p)
    p["wikitext"] += " changed"
    with pytest.raises(ValueError, match="digest"):
        verify_page(p)
    p = page()
    p["permalink_url"] = "https://example.com/?oldid=2"
    with pytest.raises(ValueError, match="attribution"):
        verify_page(p)


def test_exact_spelling_matching_never_trims_or_follows_aliases():
    p = page("word")
    report = reconcile_records([{"headword": " word ", "word_ids": [1]}], {"word": p}, parser=lambda *a, **k: pytest.fail("must not parse"))
    assert report["records"][0]["status"] == "missing_from_snapshot"


def test_duplicate_candidates_and_mismatched_page_title_rejected():
    with pytest.raises(ValueError, match="Duplicate"):
        reconcile_records([{"headword": "x"}, {"headword": "x"}], {})
    with pytest.raises(ValueError, match="title"):
        reconcile_records([{"headword": "x"}], {"x": page("different")})


def test_missing_page_capture_is_explicit_cached_and_tamper_checked(tmp_path, monkeypatch):
    calls = []

    def api(params, **kwargs):
        calls.append(params)
        return {"query": {"pages": [{"title": "absent", "missing": True, "ns": 0}]}}

    monkeypatch.setattr("tools.lexicon_wiktionary_gaps._api_get_json", api)
    records, manifest = fetch_missing(["absent"], tmp_path)
    assert records == {}
    assert manifest["title_outcomes"] == {"absent": {"status": "api_page_missing"}}
    fetch_missing(["absent"], tmp_path)
    assert len(calls) == 1
    (tmp_path / "batch-000.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="digest"):
        fetch_missing(["absent"], tmp_path)


def test_api_errors_are_not_reported_as_missing_pages(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.lexicon_wiktionary_gaps._api_get_json", lambda *a, **k: {"error": {"code": "maxlag"}})
    with pytest.raises(ValueError, match="query failed"):
        fetch_missing(["not_proven_absent"], tmp_path)
    assert not (tmp_path / "manifest.json").exists()


def test_partial_capture_requires_hash_checkpoint_and_resumes(tmp_path, monkeypatch):
    titles = [f"word{i}" for i in range(26)]
    calls = []

    def api(params, **kwargs):
        calls.append(params["titles"])
        if len(calls) == 2:
            raise OSError("capture interrupted")
        return {"query": {"pages": [{"title": t, "missing": True} for t in params["titles"].split("|")]}}

    monkeypatch.setattr("tools.lexicon_wiktionary_gaps._api_get_json", api)
    with pytest.raises(OSError, match="interrupted"):
        fetch_missing(titles, tmp_path)
    assert (tmp_path / "capture-checkpoint.json").is_file()
    records, manifest = fetch_missing(titles, tmp_path)
    assert records == {} and len(manifest["title_outcomes"]) == 26
    assert len(calls) == 3  # The first 25 results were verified and reused.
    (tmp_path / "manifest.json").unlink()
    (tmp_path / "capture-checkpoint.json").unlink()
    with pytest.raises(ValueError, match="no manifest or checkpoint"):
        fetch_missing(titles, tmp_path)


def test_capture_rejects_compressed_tamper_and_extra_batches(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.lexicon_wiktionary_gaps._api_get_json", lambda *a, **k: {"query": {"pages": [{"title": "x", "missing": True}]}})
    fetch_missing(["x"], tmp_path)
    original = (tmp_path / "pages.jsonl.gz").read_bytes()
    (tmp_path / "pages.jsonl.gz").write_bytes(original + b"tamper")
    with pytest.raises(ValueError, match="compressed.*digest"):
        verify_capture(tmp_path)
    (tmp_path / "pages.jsonl.gz").write_bytes(original)
    (tmp_path / "batch-999.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="Unregistered"):
        verify_capture(tmp_path)


def test_stage_rejects_wrong_pack_normalization_and_foreign_snapshot(tmp_path, monkeypatch):
    source = tmp_path / "source"
    monkeypatch.setattr("tools.lexicon_wiktionary_gaps._api_get_json", lambda *a, **k: {"query": {"pages": [{"title": "x", "missing": True}]}})
    _, manifest = fetch_missing(["x"], source)
    for entry in ({"headword": "x", "pack_id": "regional"}, {"headword": "x", "pack_id": "core", "headword_nfc_normalized": True}):
        with pytest.raises(ValueError, match="only exact.*core"):
            stage_candidates({"candidate_entries": [entry], "supplemental_manifest": manifest}, source, tmp_path / "output")
    with pytest.raises(ValueError, match="outside this supplemental"):
        stage_candidates({"candidate_entries": [{"headword": "other", "pack_id": "core"}], "supplemental_manifest": manifest}, source, tmp_path / "output")
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("name", ["", ".", "..", "../batch-000.json", "other.json"])
def test_raw_capture_filename_confinement(tmp_path, name):
    with pytest.raises(ValueError, match="filename"):
        verify_raw_files(tmp_path, {name: {}})


def test_supplement_guard_always_protects_original_snapshots(tmp_path):
    for protected in (ROOT / "data/sources/enwiktionary-tamil", ROOT / "data/sources/tamil-lexicon"):
        with pytest.raises(ValueError, match="separate directory"):
            validate_supplemental_directory(protected, tmp_path / "custom-snapshot")
