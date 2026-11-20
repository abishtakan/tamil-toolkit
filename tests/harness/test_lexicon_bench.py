"""Fast unit and plumbing tests for Feature 021 benchmark runner (tools/lexicon_bench.py).

These tests verify path isolation, RSS/latency plumbing, fail-closed guards,
canonical pack/query generation, and report contract separation. They use small
synthetic inputs or explicit unit-test dispatch fixtures and never substitute
for or run the real post-integration full-corpus / native measurements.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tools.lexicon import ROOT, LexiconError
from tools import lexicon_bench as bench


def _fake_clock_factory(step: float = 0.25):
    state = {"t": 100.0}

    def clock() -> float:
        val = state["t"]
        state["t"] += step
        return val

    return clock


def _write_synthetic_source_csv(source_dir: Path) -> Path:
    source_dir.mkdir(parents=True, exist_ok=True)
    csv_path = source_dir / "tiny_sample.csv"
    csv_path.write_text(
        "headword,gloss\n"
        "\u0b85\u0b9f\u0b9f\u0bbe,exclamation of surprise\n"
        "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf,gratitude\n",
        encoding="utf-8",
    )
    return csv_path


def _stub_prov(suffix: str = "000000000001") -> list[dict[str, Any]]:
    return [
        {
            "assertion_id": f"ast_00000000-0000-5000-8000-{suffix}",
            "revision_sha256": "1" * 64,
            "source_id": "src_00000000-0000-5000-8000-000000000001",
            "locator": "unit-fixture",
            "acceptance": {
                "decision_id": f"dec_00000000-0000-5000-8000-{suffix}",
                "kind": "accepted_human",
                "actor_id": "unit",
                "method": "unit-fixture-v1",
                "decided_on": "2026-11-14",
            },
        }
    ]


def _make_stub_entry(headword: str, *, entry_id: str, senses: int) -> dict[str, Any]:
    return {
        "entry_id": entry_id,
        "revision": "0" * 64,
        "headword": headword,
        "language_id": "tam",
        "part_of_speech": {
            "availability": "available",
            "value": "NOUN",
            "convention": None,
            "provenance": _stub_prov("000000000001"),
        },
        "forms": [
            {
                "form_id": f"frm_00000000-0000-5000-8000-{i:012d}",
                "representation": "written",
                "role": "canonical",
                "text": headword,
                "convention": None,
                "provenance": _stub_prov(f"0000000000{i + 1:02d}"),
            }
            for i in range(1)
        ],
        "senses": [
            {
                "sense_id": f"sen_00000000-0000-5000-8000-{i + 1:012d}",
                "display_order": i + 1,
                "parent_sense_id": None,
                "components": [
                    {
                        "text_id": f"txt_00000000-0000-5000-8000-{i + 1:012d}",
                        "kind": "definition",
                        "language_id": "eng",
                        "text": f"sense-{i + 1}",
                        "provenance": _stub_prov(f"0000000001{i + 1:02d}"),
                    }
                ],
                "examples": [],
                "relations": [],
                "region": {"state": "unknown", "codes": [], "provenance": []},
                "register": {
                    "availability": "unknown",
                    "value": None,
                    "convention": None,
                    "provenance": [],
                },
                "annotations": [],
                "provenance": _stub_prov(f"0000000002{i + 1:02d}"),
            }
            for i in range(senses)
        ],
        "region": {"state": "unknown", "codes": [], "provenance": []},
        "register": {
            "availability": "unknown",
            "value": None,
            "convention": None,
            "provenance": [],
        },
        "annotations": [],
        "provenance": _stub_prov("000000000099"),
    }


def _make_stub_dispatcher(canonical_spec: dict[str, Any], *, truncate_entries: bool = False):
    pack_info = {
        "id": canonical_spec["pack_id"],
        "dataset_version": canonical_spec["dataset_version"],
        "schema_version": canonical_spec["schema_version"],
        "index_format_version": canonical_spec["index_format_version"],
        "manifest_sha256": canonical_spec["manifest_sha256"],
        "available": True,
        "coverage": canonical_spec["coverage"],
    }
    by_hw: dict[str, list[dict[str, Any]]] = {}
    for item in canonical_spec["headword_specs"]:
        hw = item["headword"]
        eids = item["entry_ids"]
        total_senses = int(item["sense_count"])
        entries: list[dict[str, Any]] = []
        remaining = total_senses
        for idx, eid in enumerate(eids):
            if idx == len(eids) - 1:
                scount = remaining
            else:
                scount = max(1, total_senses // len(eids))
                remaining -= scount
            entries.append(_make_stub_entry(hw, entry_id=eid, senses=scount))
        by_hw[hw] = entries

    import unicodedata

    def execute_dict(req: dict[str, Any]) -> dict[str, Any]:
        op = req.get("op")
        if op == "lexicon_packs":
            return [pack_info]
        if op == "lexicon_lookup":
            raw = str(req["input"])
            canonical_query = unicodedata.normalize("NFC", raw)
            matched = by_hw.get(canonical_query)
            if matched and not truncate_entries:
                return {
                    "schema_version": 1,
                    "status": "matched",
                    "canonical_query": canonical_query,
                    "packs": [pack_info],
                    "entries": matched,
                }
            if matched and truncate_entries:
                broken = json.loads(json.dumps(matched))
                broken[0]["senses"] = broken[0]["senses"][:0]
                return {
                    "schema_version": 1,
                    "status": "matched",
                    "canonical_query": canonical_query,
                    "packs": [pack_info],
                    "entries": broken,
                }
            return {
                "schema_version": 1,
                "status": "not_found",
                "canonical_query": canonical_query,
                "packs": [pack_info],
                "entries": [],
            }
        raise ValueError(f"unsupported op: {op}")

    def execute_native_json(raw_json: str) -> str:
        return json.dumps(execute_dict(json.loads(raw_json)), ensure_ascii=False)

    return execute_native_json, execute_dict


def test_safe_bench_paths_reject_protected_repo_locations(tmp_path: Path) -> None:
    for unsafe in (
        ROOT,
        ROOT / "data" / "sources",
        ROOT / "lexicon" / "dictionary",
        ROOT / "crates" / "tamil-toolkit",
        ROOT / "tools" / "benchmarks.json",
        ROOT / "tests" / "harness" / "out.json",
    ):
        with pytest.raises(LexiconError):
            bench.check_safe_bench_path(unsafe, label="output")

    src = tmp_path / "source"
    src.mkdir()
    with pytest.raises(LexiconError):
        bench.check_safe_scratch_dir(src / "sub", source_root=src)

    assert bench.check_safe_output_path(bench.DEFAULT_OUTPUT) == bench.DEFAULT_OUTPUT.resolve()


def test_memory_sampler_and_stat_helpers() -> None:
    rss_sequence = iter([100_000, 350_000, 220_000, 220_000])
    sampler = bench.ProcessTreeMemorySampler(
        root_pid=12345,
        interval_ms=5.0,
        rss_reader=lambda _pid: next(rss_sequence, 220_000),
        clock=_fake_clock_factory(0.75),
    )
    sampler.start()
    sampler.sample_once()
    metrics = sampler.stop()
    assert metrics["peak_rss_bytes"] == 350_000
    assert metrics["sample_count"] >= 3
    assert metrics["elapsed_s"] == pytest.approx(0.75)

    with pytest.raises(LexiconError):
        bench.ProcessTreeMemorySampler(root_pid=1, interval_ms=0.0)

    lat = bench.compute_latency_stats_ms([1_000_000 * i for i in range(1, 101)])
    assert lat["min_ms"] == pytest.approx(1.0)
    assert lat["p50_ms"] == pytest.approx(50.0)
    assert lat["p95_ms"] == pytest.approx(95.0)
    assert lat["p99_ms"] == pytest.approx(99.0)
    assert lat["max_ms"] == pytest.approx(100.0)


def test_canonical_pack_spec_and_seeded_query_corpus() -> None:
    spec = bench.load_canonical_core_pack_spec()
    assert spec["pack_id"] == "core"
    assert spec["manifest_sha256"] == bench.CANONICAL_PACK_MANIFEST_SHA256
    assert spec["entry_count"] == sum(len(item["entry_ids"]) for item in spec["headword_specs"])
    assert spec["sense_count"] == sum(item["sense_count"] for item in spec["headword_specs"])
    assert spec["entry_count"] >= 6 and spec["sense_count"] >= 19

    by_hw = {item["headword"]: item for item in spec["headword_specs"]}
    assert by_hw["\u0b9a\u0bc6\u0baa\u0bcd\u0baa\u0bae\u0bcd"]["sense_count"] == 9  # செப்பம்
    assert len(by_hw["\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf"]["entry_ids"]) == 2  # நன்றி homographs

    q1, hash1 = bench.build_lookup_queries(spec["headword_specs"], count=200, seed=42)
    q2, hash2 = bench.build_lookup_queries(spec["headword_specs"], count=200, seed=42)
    _, hash3 = bench.build_lookup_queries(spec["headword_specs"], count=200, seed=43)
    assert hash1 == hash2
    assert hash1 != hash3
    assert len(q1) == 200
    max_input_bytes = max(len(item["input"].encode("utf-8")) for item in q1)
    assert max_input_bytes == bench.MAX_LOOKUP_QUERY_UTF8_BYTES
    kinds = {item["kind"] for item in q1}
    assert {"matched_canonical", "matched_nfd", "not_found", "not_found_max_65536_bytes"} <= kinds


def test_structural_benchmark_rejects_pilot_or_small_corpus_by_default(tmp_path: Path) -> None:
    src = tmp_path / "small_source"
    _write_synthetic_source_csv(src)
    scratch = tmp_path / "scratch"

    def fake_stage_runner(**kwargs: Any) -> dict[str, Any]:
        return bench._default_subprocess_stage_runner(**kwargs)

    with pytest.raises(LexiconError, match="canonical counts"):
        bench.run_structural_benchmark(
            source_root=src,
            manifest_path=None,
            scratch_base=scratch,
            allow_noncanonical_counts=False,
            stage_runner=fake_stage_runner,
        )


def test_structural_benchmark_synthetic_pipeline_and_budget_separation(tmp_path: Path) -> None:
    src = tmp_path / "synthetic_source"
    _write_synthetic_source_csv(src)
    scratch = tmp_path / "scratch"

    def in_process_stage_runner(**kwargs: Any) -> dict[str, Any]:
        details = bench.execute_structural_stage_worker(
            stage_name=kwargs["stage_name"],
            source_root=kwargs["source_root"],
            manifest_path=kwargs["manifest_path"],
            inventory_path=kwargs["inventory_path"],
            workspace=kwargs["workspace"],
            proof_out=kwargs["proof_out"],
            allow_noncanonical_counts=kwargs["allow_noncanonical_counts"],
        )
        return {
            "elapsed_s": 0.02,
            "peak_rss_bytes": 12_345_678,
            "sample_count": 2,
            "sampling_interval_ms": kwargs["sampling_interval_ms"],
            "details": details,
        }

    ok_result = bench.run_structural_benchmark(
        source_root=src,
        manifest_path=None,
        scratch_base=scratch,
        allow_noncanonical_counts=True,
        stage_runner=in_process_stage_runner,
    )
    assert ok_result["measurement_completed"] is True
    assert ok_result["full_corpus_verified"] is False
    assert ok_result["canonical_counts_enforced"] is False
    assert ok_result["pilot_substituted"] is False
    assert ok_result["budget_met"] is True
    assert ok_result["input_identity"]["csv_records"] == 2
    assert set(ok_result["stages"]) == {
        bench.STAGE_INVENTORY,
        bench.STAGE_STAGE,
        bench.STAGE_VALIDATION,
    }
    assert list(scratch.glob("run-*")) == []

    missed_rss = bench.run_structural_benchmark(
        source_root=src,
        manifest_path=None,
        scratch_base=scratch,
        allow_noncanonical_counts=True,
        stage_runner=in_process_stage_runner,
        rss_budget_bytes=1024,
    )
    assert missed_rss["measurement_completed"] is True
    assert missed_rss["rss_budget_met"] is False
    assert missed_rss["wall_budget_met"] is True
    assert missed_rss["budget_met"] is False


def test_lookup_fail_closed_guards_for_missing_old_empty_mismatch_and_truncated() -> None:
    spec = bench.load_canonical_core_pack_spec()

    # Old binding without lexicon_packs
    with pytest.raises(LexiconError, match="old binding"):
        bench.verify_runtime_core_pack(
            lambda _req: (_ for _ in ()).throw(ValueError("unsupported op: lexicon_packs")),
            spec,
        )

    # No-data build
    with pytest.raises(LexiconError, match="no-data build"):
        bench.verify_runtime_core_pack(lambda _req: [], spec)

    # Unavailable pack
    with pytest.raises(LexiconError, match="not available"):
        bench.verify_runtime_core_pack(
            lambda _req: [{"id": "core", "available": False}],
            spec,
        )

    # Manifest mismatch
    with pytest.raises(LexiconError, match="PackInfo mismatch"):
        bench.verify_runtime_core_pack(
            lambda _req: [
                    {
                        "id": "core",
                        "dataset_version": spec["dataset_version"],
                        "schema_version": spec["schema_version"],
                        "index_format_version": spec["index_format_version"],
                        "manifest_sha256": "deadbeef" * 8,
                        "available": True,
                        "coverage": spec["coverage"],
                    }
                ],
            spec,
        )

    # Truncated lookup response inside stub workload fails closed
    truncated_loader = lambda: _make_stub_dispatcher(spec, truncate_entries=True)
    with pytest.raises(LexiconError, match="sense count mismatch"):
        bench.run_lookup_benchmark(
            queries=30,
            warmup=2,
            seed=7,
            dispatcher_loader=truncated_loader,
            cold_start_runner=lambda **_kw: {"status": "matched"},
            runtime_mode_label="unit_fixture_stub",
        )


def test_lookup_plumbing_fixture_and_report_schema_contract() -> None:
    spec = bench.load_canonical_core_pack_spec()
    stub_loader = lambda: _make_stub_dispatcher(spec, truncate_entries=False)

    def fake_cold_start(*, query: str, expected_manifest_sha256: str, sampling_interval_ms: float) -> dict[str, Any]:
        largest = max(spec["headword_specs"], key=lambda item: item["sense_count"])
        assert query == largest["headword"]
        assert expected_manifest_sha256 == spec["manifest_sha256"]
        return {
            "total_process_wall_ms": 18.5,
            "import_ms": 11.2,
            "first_lookup_ms": 0.45,
            "child_total_ms": 11.65,
            "peak_rss_bytes": 32_000_000,
            "peak_rss_mib": 30.52,
            "sample_count": 2,
            "sampling_interval_ms": sampling_interval_ms,
            "response_utf8_bytes": 4096,
            "status": "matched",
            "entry_count": len(largest["entry_ids"]),
            "sense_count": largest["sense_count"],
        }

    lookup_res = bench.run_lookup_benchmark(
        queries=40,
        warmup=5,
        seed=123,
        dispatcher_loader=stub_loader,
        cold_start_runner=fake_cold_start,
        runtime_mode_label="unit_fixture_stub",
    )
    assert lookup_res["measurement_completed"] is True
    assert lookup_res["warm_p95_budget_met"] is True
    assert lookup_res["budget_met"] is True
    assert lookup_res["pack_info"]["pack_bytes"]["default_build_payload_bytes"] == 0
    assert lookup_res["warm"]["query_count"] == 40
    assert lookup_res["warm"]["verification"]["truncated_responses"] == 0
    assert lookup_res["warm"]["verification"]["schema_validated_unique_responses"] >= 4
    assert "not claim ~263k/307k large-corpus lookup coverage" in lookup_res["corpus_coverage_note"]

    # Budget miss still records completed measurement while marking budget_met False
    missed = bench.run_lookup_benchmark(
        queries=25,
        warmup=2,
        seed=123,
        dispatcher_loader=stub_loader,
        cold_start_runner=fake_cold_start,
        warm_p95_budget_ms=0.0,
        runtime_mode_label="unit_fixture_stub",
    )
    assert missed["measurement_completed"] is True
    assert missed["warm_p95_budget_met"] is False
    assert missed["budget_met"] is False

    report = bench.assemble_benchmark_report(workloads={"lookup": missed})
    assert report["schema_version"] == 1
    assert report["measurement_completed"] is True
    assert report["budget_met"] is False
    assert report["environment"]["measurement_method"]["sampling_interval_ms"] == bench.DEFAULT_SAMPLING_INTERVAL_MS


def test_cli_enforce_budgets_exit_1_vs_missing_runtime_exit_2(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    out_file = tmp_path / "bench.json"

    # Deterministic missing-runtime error handling; this is not native parity evidence.
    def unavailable_dispatcher():
        raise LexiconError("native adapter unavailable in unit fixture", code=2)
    with monkeypatch.context() as isolated:
        isolated.setattr(bench, "load_native_dispatcher", unavailable_dispatcher)
        code_missing = bench.main(["lookup", "--output", str(out_file), "--queries", "10", "--warmup", "1"])
    assert code_missing == 2
    assert not out_file.exists()

    # Simulated completed measurement failing budget returns exit 1 cleanly when --enforce-budgets is set
    src = tmp_path / "src_cli"
    _write_synthetic_source_csv(src)
    scratch = tmp_path / "scratch_cli"
    monkeypatch.setattr(bench, "STRUCTURAL_RSS_BUDGET_BYTES", 1)
    code_budget = bench.main(
        [
            "structural",
            "--source-root",
            str(src),
            "--no-manifest",
            "--scratch-dir",
            str(scratch),
            "--output",
            str(out_file),
            "--allow-noncanonical-counts",
            "--enforce-budgets",
        ]
    )
    assert code_budget == 1
    assert out_file.is_file()
    written = json.loads(out_file.read_text(encoding="utf-8"))
    assert written["measurement_completed"] is True
    assert written["budget_met"] is False
    captured = capsys.readouterr()
    stdout_doc = json.loads(captured.out)
    assert stdout_doc["measurement_completed"] is True
    assert stdout_doc["budget_met"] is False


def test_pack_probe_uses_actual_golden_dispatcher_contract() -> None:
    golden = Path("tests/golden/lexicon_lookup.jsonl")
    row = next(json.loads(line) for line in golden.read_text(encoding="ascii").splitlines()
               if json.loads(line)["id"] == "lexicon_packs_core_043")
    calls = []
    def execute(request):
        calls.append(request)
        assert request == {"op": "lexicon_packs", "input": None}
        return row["expected"]
    actual = bench.verify_runtime_core_pack(execute, bench.load_canonical_core_pack_spec())
    assert actual == row["expected"][0]
    assert len(calls) == 1


def test_query_expectations_preserve_spaces_controls_and_exact_nfc() -> None:
    import unicodedata

    spec = bench.load_canonical_core_pack_spec()
    queries, _ = bench.build_lookup_queries(spec["headword_specs"], count=1000, seed=123)
    approved = {item["headword"] for item in spec["headword_specs"]}
    for query in queries:
        canonical = unicodedata.normalize("NFC", query["input"])
        assert query["expected_canonical"] == canonical
        assert query["expected_status"] == ("matched" if canonical in approved else "not_found")
    assert any(q["input"].strip() in approved and q["expected_status"] == "not_found" for q in queries)
