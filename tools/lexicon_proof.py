"""Reproducible full-intake accounting, payload equality, and clean-replay proof for Feature 021."""

from __future__ import annotations

import argparse
import csv
import hashlib
from itertools import zip_longest
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import tomllib

if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.lexicon import (
    LexiconError,
    NAMESPACE,
    ROOT,
    SOURCE,
    _checked_files,
    _checked_files_with_digests,
    _scalars,
    allocate_id,
    atomic_json,
    digest,
    inventory,
    json_text,
    native_batch_canonical_json_sha256,
    source_rows,
    stage,
    table_rows,
)


def _reject_constant(token):
    raise LexiconError(f"invalid JSON constant in assertion payload: {token}")


_STRICT_DECODER = json.JSONDecoder(parse_constant=_reject_constant)
_STRICT_SCAN_ONCE = _STRICT_DECODER.scan_once
_SQL_QUERY_CHUNK = 250
_SELECT_EXPECTED_PREFIX = "SELECT assertion_id, subject_id, property_code, row_sha256 FROM expected WHERE assertion_id IN ("
_SELECT_EXPECTED_FULL = _SELECT_EXPECTED_PREFIX + ",".join("?" * _SQL_QUERY_CHUNK) + ")"


def _iter_csv_columns(path, columns):
    """Yield projected tuples for selected CSV columns without per-row DictReader dicts."""
    with Path(path).open(encoding="utf-8", newline="", buffering=1024 * 1024) as handle:
        reader = csv.reader(handle, strict=True)
        header = next(reader, None)
        if header is None:
            return
        index = {name: pos for pos, name in enumerate(header)}
        cols = tuple(index[name] for name in columns)
        if not cols:
            for _row in reader:
                yield ()
            return
        max_col = max(cols)
        if len(cols) == 1:
            c0 = cols[0]
            for row in reader:
                yield (row[c0] if len(row) > max_col else None,)
            return
        for row in reader:
            if len(row) > max_col:
                yield tuple(row[c] for c in cols)
            else:
                yield tuple(row[c] if c < len(row) else None for c in cols)


def _check_scalars(value):
    if isinstance(value, str):
        _scalars(value)
    elif isinstance(value, list):
        for item in value:
            _check_scalars(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            _scalars(key)
            _check_scalars(item)


def _verify_source_payloads_impl(workspace, source=SOURCE, manifest_path=None, *, _prechecked=None):
    workspace = Path(workspace)
    if _prechecked is None:
        _, paths, verified = _checked_files_with_digests(source, manifest_path)
    else:
        paths, verified = _prechecked
    config_path = workspace / "dataset.toml"
    config = tomllib.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    if config and (config.get("schema_version") != 1 or config.get("text_codec") != "json-string-utf8-v1"):
        raise LexiconError("unsupported dataset schema or codec")
    namespace = config.get("id_namespace", str(NAMESPACE))
    if namespace == str(NAMESPACE):
        namespace = NAMESPACE
    assertions_path = workspace / "assertions.csv"
    if not assertions_path.is_file():
        raise LexiconError("missing assertions.csv in workspace")

    target_dir = ROOT / "target/lexicon"
    target_dir.mkdir(parents=True, exist_ok=True)
    hashes_verified = 0
    expected_records = 0
    master_records = 0
    matching_assertions = 0
    duplicates = 0
    unexpected = 0
    subject_mismatches = 0
    property_mismatches = 0
    content_mismatches = 0

    with tempfile.TemporaryDirectory(dir=target_dir, prefix=".source-payload-proof-") as temporary:
        db_path = Path(temporary) / "payload-proof.sqlite3"
        conn = sqlite3.connect(db_path)
        try:
            conn.execute("PRAGMA journal_mode = OFF")
            conn.execute("PRAGMA synchronous = OFF")
            conn.execute("PRAGMA temp_store = MEMORY")
            # This disposable index is roughly 100 MiB for the frozen intake.
            # Bound its page cache to 128 MiB to avoid repeated random disk reads.
            conn.execute("PRAGMA cache_size = -131072")
            conn.execute(
                """
                CREATE TABLE expected (
                    assertion_id TEXT PRIMARY KEY,
                    subject_id TEXT NOT NULL,
                    property_code TEXT NOT NULL,
                    row_sha256 TEXT NOT NULL
                ) WITHOUT ROWID
                """
            )

            batch = []
            meta_batch = []
            raw_row_batch = []

            def flush_batch():
                if not meta_batch and not batch:
                    return
                if meta_batch:
                    shas = native_batch_canonical_json_sha256(raw_row_batch)
                    for (ast, subject, expected_prop_val), row_sha in zip(meta_batch, shas):
                        batch.append((ast, subject, expected_prop_val, row_sha))
                    meta_batch.clear()
                    raw_row_batch.clear()
                if not batch:
                    return
                try:
                    conn.executemany(
                        "INSERT INTO expected (assertion_id, subject_id, property_code, row_sha256) VALUES (?, ?, ?, ?)",
                        batch,
                    )
                except sqlite3.IntegrityError as error:
                    raise LexiconError(f"duplicate expected source assertion ID during payload indexing: {error}") from error
                batch.clear()

            primary_subjects: dict[str, str] = {}
            with conn:
                for path in paths:
                    checksum = verified[path.name][1] if path.name in verified else digest(path)
                    hashes_verified += 1
                    if path.suffix != ".csv":
                        continue
                    expected_prop = (
                        "imported_master_fields"
                        if path.name.startswith("unified_master")
                        else "unparsed_source_record"
                    )
                    is_primary_lemmas = path.name == "primary_lemmas.csv"
                    is_master_table = path.name == "unified_master_30col.csv"
                    is_primary_or_master = is_primary_lemmas or is_master_table
                    if not is_primary_or_master:
                        kind = (
                            "sen"
                            if path.name == "primary_meanings.csv"
                            else "rel"
                            if path.name == "primary_relationships.csv"
                            else "ent"
                        )
                        key_prefix = path.stem + ":legacy:"
                    checked_header = False
                    for ordinal, _start, _end, row_hash, row in source_rows(path):
                        legacy = next(iter(row.values()))
                        if not legacy:
                            raise LexiconError(f"missing legacy key: {path.name}:{ordinal}")
                        rec = allocate_id("rec", NAMESPACE, f"{checksum}:{ordinal}:{row_hash}")
                        ast = allocate_id("ast", namespace, rec + ":unparsed")
                        if is_primary_lemmas:
                            subject = allocate_id("ent", namespace, "primary:word:" + legacy)
                            primary_subjects[legacy] = subject
                        elif is_master_table:
                            master_records += 1
                            subject = primary_subjects.get(legacy)
                            if subject is None:
                                subject = allocate_id("ent", namespace, "primary:word:" + legacy)
                        else:
                            subject = allocate_id(kind, namespace, key_prefix + legacy)
                        if not checked_header:
                            for key_name in row:
                                _scalars(key_name)
                            checked_header = True
                        meta_batch.append((ast, subject, expected_prop))
                        raw_row_batch.append(row)
                        expected_records += 1
                        if len(meta_batch) >= 4096:
                            flush_batch()
                flush_batch()

            required_cols = {"assertion_id", "subject_id", "property_code", "value_state", "value_json"}
            unparsed_props = {"unparsed_source_record", "imported_master_fields"}
            decode_strict = _STRICT_DECODER.decode
            scan_strict = _STRICT_SCAN_ONCE
            seen_aids: set[str] = set()

            def process_chunk(chunk):
                nonlocal matching_assertions, duplicates, unexpected, subject_mismatches, property_mismatches, content_mismatches
                if not chunk:
                    return
                query_aids = list({item[0] for item in chunk})
                sql = (
                    _SELECT_EXPECTED_FULL
                    if len(query_aids) == _SQL_QUERY_CHUNK
                    else _SELECT_EXPECTED_PREFIX + ",".join("?" * len(query_aids)) + ")"
                )
                expected_map = {r[0]: (r[1], r[2], r[3]) for r in conn.execute(sql, query_aids)}
                decoded_inner_items = []
                for aid, subj, prop, state, raw_vjson in chunk:
                    found = expected_map.get(aid)
                    if found is None:
                        unexpected += 1
                        continue
                    exp_subject, exp_prop, exp_row_sha = found
                    already_seen = aid in seen_aids
                    if already_seen:
                        duplicates += 1
                    else:
                        seen_aids.add(aid)
                    if state != "known":
                        content_mismatches += 1
                        continue
                    try:
                        if raw_vjson and raw_vjson[0] not in " \t\n\r":
                            try:
                                outer, end = scan_strict(raw_vjson, 0)
                            except StopIteration:
                                outer = decode_strict(raw_vjson)
                            else:
                                if end != len(raw_vjson):
                                    outer = decode_strict(raw_vjson)
                        else:
                            outer = decode_strict(raw_vjson)
                    except (ValueError, TypeError) as error:
                        raise LexiconError(f"invalid outer value_json cell for {aid}: {error}") from error
                    if not isinstance(outer, str):
                        raise LexiconError(f"unparsed assertion value_json must decode to JSON string document for {aid}")
                    if "\\u" in raw_vjson:
                        _scalars(outer)
                    try:
                        if outer and outer[0] not in " \t\n\r":
                            try:
                                inner, end = scan_strict(outer, 0)
                            except StopIteration:
                                inner = decode_strict(outer)
                            else:
                                if end != len(outer):
                                    inner = decode_strict(outer)
                        else:
                            inner = decode_strict(outer)
                    except (ValueError, TypeError) as error:
                        raise LexiconError(f"invalid inner raw-row JSON document for {aid}: {error}") from error
                    if not isinstance(inner, dict):
                        raise LexiconError(f"inner raw-row JSON document must decode to object for {aid}")
                    if "\\u" in outer:
                        _check_scalars(inner)
                    decoded_inner_items.append((aid, subj, prop, exp_subject, exp_prop, exp_row_sha, already_seen, inner))
                if decoded_inner_items:
                    inner_shas = native_batch_canonical_json_sha256([item[7] for item in decoded_inner_items])
                    for (_aid, subj, prop, exp_subject, exp_prop, exp_row_sha, already_seen, _inner), actual_row_sha in zip(decoded_inner_items, inner_shas):
                        if subj != exp_subject:
                            subject_mismatches += 1
                        if prop != exp_prop:
                            property_mismatches += 1
                        if actual_row_sha != exp_row_sha:
                            content_mismatches += 1
                        if (
                            not already_seen
                            and subj == exp_subject
                            and prop == exp_prop
                            and actual_row_sha == exp_row_sha
                        ):
                            matching_assertions += 1
                chunk.clear()

            with assertions_path.open(encoding="utf-8", newline="", buffering=1024 * 1024) as handle:
                reader = csv.reader(handle, strict=True)
                header = next(reader, None) or ()
                fieldnames = set(header)
                if not required_cols.issubset(fieldnames):
                    raise LexiconError(f"assertions.csv missing required columns: {sorted(required_cols - fieldnames)}")
                col_idx = {name: pos for pos, name in enumerate(header)}
                aid_i = col_idx["assertion_id"]
                subj_i = col_idx["subject_id"]
                prop_i = col_idx["property_code"]
                state_i = col_idx["value_state"]
                vjson_i = col_idx["value_json"]
                max_req_i = max(aid_i, subj_i, prop_i, state_i, vjson_i)
                chunk = []
                for row in reader:
                    len_row = len(row)
                    if len_row > max_req_i:
                        prop = row[prop_i]
                        if prop not in unparsed_props:
                            continue
                        chunk.append((row[aid_i], row[subj_i], prop, row[state_i], row[vjson_i]))
                    else:
                        prop = row[prop_i] if prop_i < len_row else None
                        if prop not in unparsed_props:
                            continue
                        chunk.append((
                            row[aid_i] if aid_i < len_row else None,
                            row[subj_i] if subj_i < len_row else None,
                            prop,
                            row[state_i] if state_i < len_row else None,
                            row[vjson_i] if vjson_i < len_row else None,
                        ))
                    if len(chunk) >= _SQL_QUERY_CHUNK:
                        process_chunk(chunk)
                process_chunk(chunk)

            missing = expected_records - len(seen_aids)
        finally:
            conn.close()

    if missing or duplicates or unexpected or subject_mismatches or property_mismatches or content_mismatches:
        raise LexiconError(
            "source payload verification failed: "
            f"missing={missing}, duplicates={duplicates}, unexpected={unexpected}, "
            f"subject_mismatches={subject_mismatches}, property_mismatches={property_mismatches}, "
            f"content_mismatches={content_mismatches}"
        )

    return {
        "schema_version": 1,
        "codec": "json-string-utf8-v1",
        "source_hashes_verified": hashes_verified,
        "source_records": expected_records,
        "master_records": master_records,
        "matching_raw_assertions": matching_assertions,
        "missing_or_duplicate_assertions": 0,
        "exact_decoded_source_fields_and_scalars": True,
        "subject_ids_match_immutable_allocations": True,
        "assertions_sha256": digest(assertions_path),
        "l2_structural_accepted": False,
        "l3_pack_eligible": False,
        "runtime_verified": None,
    }


def verify_source_payloads(workspace, source=SOURCE, manifest_path=None):
    """Prove 1:1 decoded payload and subject equality between source CSVs and workspace assertions.

    Uses a bounded-memory SQLite index in a temporary directory under target/lexicon
    and leaves no retained raw copies on disk.
    """
    return _verify_source_payloads_impl(workspace, source, manifest_path)


_ORIG_VERIFY_SOURCE_PAYLOADS = verify_source_payloads


def prove(workspace, inventory_path, output, replay=False, verify_payloads=True):
    workspace, inventory_path = Path(workspace), Path(inventory_path)
    _, src_paths, verified_src = _checked_files_with_digests(SOURCE)
    snapshots = {r["snapshot_id"]:r for r in table_rows(workspace / "snapshots.csv")}
    if len(snapshots) != 12:
        raise LexiconError("full intake must account for exactly 12 snapshots")
    counted, last = 0, ""
    ws_sr_cols = ("record_id", "snapshot_id", "ordinal", "physical_line_start", "physical_line_end", "legacy_key_json", "raw_row_sha256")
    inv_sr_cols = ("record_id", "snapshot_id", "logical_ordinal", "line_start", "line_end", "legacy_key_json", "row_sha256")
    disp_cols = ("record_id", "structural_state", "disposition", "reason_code")
    for actual, original, disposition in zip_longest(
        _iter_csv_columns(workspace / "source_records.csv", ws_sr_cols),
        _iter_csv_columns(inventory_path / "source_records.csv", inv_sr_cols),
        _iter_csv_columns(workspace / "dispositions.csv", disp_cols),
    ):
        if actual is None or original is None or disposition is None:
            raise LexiconError("full intake accounting cardinality failed")
        if actual != original:
            raise LexiconError("inventory locator or source row digest differs")
        rid = actual[0]
        if rid <= last or rid != allocate_id("rec", NAMESPACE, f"{snapshots[actual[1]]['sha256']}:{actual[2]}:{actual[6]}"):
            raise LexiconError("duplicate or unstable source-record identity")
        if disposition[0] != rid or disposition[1] != "validated" or disposition[2] != "quarantined" or not disposition[3]:
            raise LexiconError("record lacks its unique validated quarantine disposition")
        counted += 1
        last = rid
    if counted != 307243:
        raise LexiconError("full intake record count differs from the frozen audit")
    identities, last = 0, ""
    prefixes = {"entry":"ent","sense":"sen","relation":"rel","form":"frm","text":"txt"}
    for entity_id, kind, allocation_key in _iter_csv_columns(workspace / "identities.csv", ("entity_id", "kind", "allocation_key")):
        if entity_id <= last or entity_id != allocate_id(prefixes[kind], NAMESPACE, allocation_key):
            raise LexiconError("duplicate or conflicting lexical identity allocation")
        identities += 1
        last = entity_id
    masters = sum(prop == "imported_master_fields" for (prop,) in _iter_csv_columns(workspace / "assertions.csv", ("property_code",)))
    if masters != 44229 or identities != 263014:
        raise LexiconError("master reconciliation or initial identity accounting failed")
    if verify_payloads:
        if verify_source_payloads is _ORIG_VERIFY_SOURCE_PAYLOADS:
            payload_proof = _verify_source_payloads_impl(workspace, SOURCE, _prechecked=(src_paths, verified_src))
        else:
            payload_proof = verify_source_payloads(workspace, SOURCE)
    else:
        payload_proof = None
    files = sorted(workspace.glob("*.csv"))
    hashes = {
        p.name: (payload_proof["assertions_sha256"] if payload_proof is not None and p.name == "assertions.csv" else digest(p))
        for p in files
    }
    sizes = {p.name:p.stat().st_size for p in files}
    baseline_path = ROOT / "target/lexicon/escaped-storage-baseline.json"
    baseline = json.loads(baseline_path.read_text(encoding="ascii")) if baseline_path.exists() else None
    repeated = False
    if replay:
        with tempfile.TemporaryDirectory(dir=ROOT / "target/lexicon",prefix=".clean-replay-") as temporary:
            temporary = Path(temporary)
            inventory(SOURCE,temporary / "inventory")
            for name in ["manifest.json","source_records.csv"]:
                if digest(inventory_path / name) != digest(temporary / "inventory" / name):
                    raise LexiconError("clean inventory replay differs")
            second = temporary / "workspace"
            second.mkdir()
            shutil.copy2(workspace / "dataset.toml",second / "dataset.toml")
            stage(temporary / "inventory",second)
            if hashes != {p.name:digest(p) for p in second.glob("*.csv")}:
                raise LexiconError("clean UTF-8 staging replay differs")
            repeated = True
    report = {"schema_version":1,"command":"prove-intake","codec":"json-string-utf8-v1","source_hashes_verified":12,
        "source_records":counted,"validated_quarantined_dispositions":counted,"identities":identities,"master_records_retained":masters,
        "table_sha256":hashes,"table_bytes":sizes,"total_csv_bytes":sum(sizes.values()),"clean_inventory_and_stage_replay_identical":repeated,
        "legacy_csv_byte_baseline":baseline["total_bytes"] if baseline else None,
        "comparison_scope":"Same full intake rows before pilot projection; payload duplication remains in both representations.",
        "eligible_assertions":0,"l2_structural_accepted":False,"l3_pack_eligible":False,"runtime_verified":None}
    if payload_proof is not None:
        report["source_payload_proof"] = payload_proof
    atomic_json(output,report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace",type=Path,required=True)
    parser.add_argument("--inventory",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--replay",action="store_true")
    parser.add_argument("--payloads-only",action="store_true")
    parser.add_argument("--source",type=Path,default=SOURCE)
    parser.add_argument("--manifest",type=Path,default=None)
    args = parser.parse_args()
    if args.payloads_only:
        payload_report = verify_source_payloads(args.workspace, args.source, args.manifest)
        atomic_json(args.output, payload_report, args.source)
        print(json.dumps(payload_report, ensure_ascii=True, sort_keys=True))
    else:
        if args.inventory is None:
            parser.error("--inventory is required unless --payloads-only is specified")
        print(json.dumps(prove(args.workspace,args.inventory,args.output,args.replay),ensure_ascii=True,sort_keys=True))
