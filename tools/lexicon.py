"""Offline structural lexicon tooling. Linguistic inspection stays in Rust."""

from __future__ import annotations

import argparse
import csv
import functools
import hashlib
import heapq
import _json
import json
import os
from pathlib import Path
import pickle
import re
import shutil
import sys
import tempfile
import tomllib
import uuid

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SOURCE = ROOT / "data/sources/tamil-lexicon"
MANIFEST = ROOT / "data/sources/tamil-lexicon.sha256.json"
NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/abishtakan/tamil-toolkit/lexicon/intake-v1")
_DEFAULT_NAMESPACE_STR = str(NAMESPACE)
_DEFAULT_NAMESPACE_SHA1 = hashlib.sha1(NAMESPACE.bytes, usedforsecurity=False)
RECORD_FIELDS = ["record_id", "snapshot_id", "logical_ordinal", "line_start", "line_end", "legacy_key_json", "row_sha256"]
DEFAULT_SORT_BATCH_SIZE = 65536
_IO_BUFFER_BYTES = 1024 * 1024
_CHUNK_BUFFER_BYTES = 262144
_PICKLE_FRAME_ROWS = 1024

_ASCII_ENCODER = json.JSONEncoder(ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)
_UTF8_ENCODER = json.JSONEncoder(ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
_C_ENCODE_ASCII_STR = _json.encode_basestring_ascii
_C_ENCODE_UTF8_STR = _json.encode_basestring
_C_ITERENCODE_ASCII = _json.make_encoder(None, None, _C_ENCODE_ASCII_STR, None, ":", ",", True, False, False)
_C_ITERENCODE_UTF8 = _json.make_encoder(None, None, _C_ENCODE_UTF8_STR, None, ":", ",", True, False, False)
_KNOWN_ID_KINDS = frozenset({"rec", "ast", "ent", "sen", "rel", "frm", "txt", "snap", "src"})


class LexiconError(ValueError):
    def __init__(self, message, code=2):
        super().__init__(message)
        self.code = code


def digest(path):
    with Path(path).open("rb", buffering=_IO_BUFFER_BYTES) as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def json_text(value):
    t = type(value)
    if t is str:
        return _C_ENCODE_ASCII_STR(value)
    if value is None:
        return "null"
    if t is dict or t is list:
        try:
            return "".join(_C_ITERENCODE_ASCII(value, 0))
        except RecursionError:
            return _ASCII_ENCODER.encode(value)
    return _ASCII_ENCODER.encode(value)


_DATA_JSON_EXTRA_CPS = (0x00AD, 0x200C, 0x200D, 0x2028, 0x2029, 0xFEFF)
_DATA_JSON_TRANSLATE = str.maketrans(
    {cp: f"\\u{cp:04x}" for cp in (*range(0x7F, 0xA0), *_DATA_JSON_EXTRA_CPS)}
)
_DATA_JSON_AUDIT_RE = re.compile(
    "[" + chr(0x7F) + "-" + chr(0x9F) + "".join(chr(cp) for cp in _DATA_JSON_EXTRA_CPS) + "]"
)


def data_json(value):
    """Readable UTF-8 data cells; controls and audit-sensitive scalars stay visible.

    Hashing and exact scalar diagnostics use json_text instead, so this storage
    choice never changes Unicode content, claim revisions or stable identities.
    """
    if value is None:
        return "null"
    t = type(value)
    if t is str:
        text = _C_ENCODE_UTF8_STR(value)
    elif t is dict or t is list:
        try:
            text = "".join(_C_ITERENCODE_UTF8(value, 0))
        except RecursionError:
            text = _UTF8_ENCODER.encode(value)
    else:
        text = _UTF8_ENCODER.encode(value)
    if not text.isascii() or "\x7f" in text:
        return text.translate(_DATA_JSON_TRANSLATE) if _DATA_JSON_AUDIT_RE.search(text) else text
    return text


_SURROGATE_RE = re.compile("[" + chr(0xD800) + "-" + chr(0xDFFF) + "]")


def _scalars(text):
    if not text.isascii() and _SURROGATE_RE.search(text):
        raise LexiconError("invalid Unicode scalar: lone surrogate")
    return text


def encode_text(value):
    if not isinstance(value, str):
        raise LexiconError("text codec requires a string")
    return json_text(_scalars(value))


def decode_text(cell):
    if not isinstance(cell, str) or not cell.isascii():
        raise LexiconError("text cell must contain an ASCII JSON string literal")
    try:
        value = json.loads(cell)
    except (ValueError, TypeError) as error:
        raise LexiconError("invalid JSON string cell") from error
    if not isinstance(value, str):
        raise LexiconError("text cell must decode to a string")
    return _scalars(value)


@functools.lru_cache(maxsize=64)
def _namespace_sha1(namespace_key):
    try:
        ns_bytes = namespace_key.bytes if isinstance(namespace_key, uuid.UUID) else uuid.UUID(str(namespace_key)).bytes
    except ValueError as error:
        raise LexiconError("invalid identity namespace") from error
    return hashlib.sha1(ns_bytes, usedforsecurity=False)


def allocate_id(kind, namespace, allocation_key):
    if kind not in _KNOWN_ID_KINDS:
        if not isinstance(kind, str) or not kind or not kind.replace("_", "").isalnum() or not kind.isascii():
            raise LexiconError("invalid entity kind")
    if namespace is NAMESPACE or namespace == _DEFAULT_NAMESPACE_STR:
        base = _DEFAULT_NAMESPACE_SHA1
    else:
        try:
            base = _namespace_sha1(namespace)
        except TypeError:
            try:
                base = hashlib.sha1(uuid.UUID(str(namespace)).bytes, usedforsecurity=False)
            except ValueError as error:
                raise LexiconError("invalid identity namespace") from error
    h = base.copy()
    key_bytes = allocation_key.encode("utf-8") if type(allocation_key) is str else str(allocation_key).encode("utf-8")
    h.update(key_bytes)
    buf = bytearray(h.digest()[:16])
    buf[6] = (buf[6] & 0x0F) | 0x50
    buf[8] = (buf[8] & 0x3F) | 0x80
    hx = buf.hex()
    return f"{kind}_{hx[:8]}-{hx[8:12]}-{hx[12:16]}-{hx[16:20]}-{hx[20:]}"


def safe_output(path, source_root=None):
    path = Path(path).resolve()
    source = Path(source_root or SOURCE).resolve()
    if path == source or path.is_relative_to(source) or source.is_relative_to(path):
        raise LexiconError("output overlaps frozen source")
    return path


def atomic_json(path, obj, source_root=None):
    path = safe_output(path, source_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(obj, ensure_ascii=True, sort_keys=True, indent=2, allow_nan=False) + "\n"
    handle = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False)
    try:
        with handle:
            handle.write(content)
        os.replace(handle.name, path)
    finally:
        Path(handle.name).unlink(missing_ok=True)


def _iter_pickle_chunk(handle):
    load = pickle.load
    while True:
        try:
            block = load(handle)
        except EOFError:
            break
        yield from block


class _ExternalSortWriter:
    """Bounded-memory external sort CSV writer; cleans temp files unless finished."""

    def __init__(self, path, fields, source_root=None, batch_size=DEFAULT_SORT_BATCH_SIZE):
        self.path = safe_output(path, source_root)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fields = list(fields)
        self.batch_size = batch_size
        self._tempdir = tempfile.TemporaryDirectory(dir=self.path.parent, prefix=".lexicon-")
        self._temporary = Path(self._tempdir.name)
        self._chunks = []
        self._batch = []

    def add_tuple(self, row_tuple):
        self._batch.append(row_tuple)
        if len(self._batch) >= self.batch_size:
            self._flush()

    def _flush(self):
        filename = self._temporary / f"chunk-{len(self._chunks)}.pkl"
        self._batch.sort()
        with filename.open("wb", buffering=_CHUNK_BUFFER_BYTES) as handle:
            dump = pickle.dump
            batch = self._batch
            proto = pickle.HIGHEST_PROTOCOL
            for start in range(0, len(batch), _PICKLE_FRAME_ROWS):
                dump(batch[start : start + _PICKLE_FRAME_ROWS], handle, proto)
        self._chunks.append(filename)
        self._batch.clear()

    def finish(self):
        result = self._temporary / "table.csv"
        if not self._chunks:
            self._batch.sort()
            with result.open("w", encoding="utf-8", newline="", buffering=_IO_BUFFER_BYTES) as handle:
                writer = csv.writer(handle, lineterminator="\n")
                writer.writerow(self.fields)
                writer.writerows(self._batch)
            self._batch.clear()
        else:
            if self._batch:
                self._flush()
            handles = []
            try:
                for chunk in self._chunks:
                    handles.append(chunk.open("rb", buffering=_CHUNK_BUFFER_BYTES))
                with result.open("w", encoding="utf-8", newline="", buffering=_IO_BUFFER_BYTES) as handle:
                    writer = csv.writer(handle, lineterminator="\n")
                    writer.writerow(self.fields)
                    writer.writerows(heapq.merge(*(_iter_pickle_chunk(h) for h in handles)))
            finally:
                for handle in handles:
                    handle.close()
        os.replace(result, self.path)
        return self.path

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self._tempdir.cleanup()


def write_table(path, fields, rows, source_root=None):
    """Bounded-memory external sort; no partial replacement on generator failure."""
    with _ExternalSortWriter(path, fields, source_root=source_root) as writer:
        add_tuple = writer.add_tuple
        for row in rows:
            if isinstance(row, dict):
                add_tuple(tuple(str(row.get(f, "")) for f in fields))
            elif type(row) is tuple and all(type(x) is str for x in row):
                add_tuple(row)
            else:
                add_tuple(tuple(map(str, row)))
        writer.finish()


def table_rows(path):
    with Path(path).open(encoding="utf-8", newline="") as handle:
        yield from csv.DictReader(handle, strict=True)


class _SourceLines:
    def __init__(self, handle):
        self.handle, self.number, self.buffer = handle, 0, []

    def __iter__(self):
        return self

    def __next__(self):
        line = next(self.handle)
        self.number += 1
        self.buffer.append(line)
        return line


def _iter_source_rows(path, *, include_dict=True):
    """Yield logical ordinals, physical spans, exact row-byte hashes and fields or first key."""
    with Path(path).open(encoding="utf-8-sig", newline="", buffering=_IO_BUFFER_BYTES) as handle:
        lines = _SourceLines(handle)
        reader = csv.reader(lines, strict=True)
        try:
            header = next(reader)
            if not header or any(not h for h in header) or len(set(header)) != len(header):
                raise LexiconError(f"invalid or duplicate CSV header: {Path(path).name}")
            for h in header:
                _scalars(h)
            n_cols = len(header)
            ordinal = 1
            buf = lines.buffer
            while True:
                start = lines.number + 1
                buf.clear()
                row = next(reader, None)
                if row is None:
                    break
                ordinal += 1
                if len(row) != n_cols:
                    raise LexiconError(f"CSV record width mismatch: {Path(path).name}:{ordinal}")
                raw = buf[0] if len(buf) == 1 else "".join(buf)
                _scalars(raw)
                row_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
                yield ordinal, start, lines.number, row_hash, (dict(zip(header, row)) if include_dict else row[0])
        except (csv.Error, UnicodeError, StopIteration) as error:
            raise LexiconError(f"invalid UTF-8/CSV: {Path(path).name}: {error}") from error


def source_rows(path):
    """Yield logical ordinals, physical spans, exact row-byte hashes and fields."""
    return _iter_source_rows(path, include_dict=True)


def _checked_files_with_digests(source, manifest_path=None):
    source = Path(source).resolve()
    if not source.is_dir():
        raise LexiconError("source directory is unavailable")
    manifest_path = Path(manifest_path) if manifest_path else (MANIFEST if source == SOURCE.resolve() else None)
    verified = {}
    if manifest_path:
        declared = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        if {p.name for p in source.iterdir()} != {r["file"] for r in declared}:
            raise LexiconError("source inventory file set mismatch")
        for item in declared:
            name = item["file"]
            if Path(name).name != name or ".." in name or not (source / name).is_file():
                raise LexiconError("invalid source inventory path")
            size = (source / name).stat().st_size
            sha = digest(source / name)
            if size != item["bytes"] or sha != item["sha256"]:
                raise LexiconError(f"source hash mismatch: {name}")
            verified[name] = (size, sha)
    return source, sorted(source.iterdir()), verified


def _checked_files(source, manifest_path=None):
    source, paths, _ = _checked_files_with_digests(source, manifest_path)
    return source, paths


def inventory(source, output, manifest_path=None):
    source, paths, verified = _checked_files_with_digests(source, manifest_path)
    output = safe_output(output, source)
    metadata, total = [], 0
    # Build everything in a sibling directory before touching an existing inventory.
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent, prefix=".lexicon-inventory-") as tmp:
        tmp = Path(tmp)
        with _ExternalSortWriter(
            tmp / "source_records.csv", RECORD_FIELDS, source_root=source, batch_size=131072
        ) as writer:
            add_tuple = writer.add_tuple
            for path in paths:
                if path.name in verified:
                    byte_size, checksum = verified[path.name]
                else:
                    byte_size, checksum = path.stat().st_size, digest(path)
                snapshot = allocate_id("snap", NAMESPACE, checksum)
                count = 0
                if path.suffix == ".csv":
                    for ordinal, start, end, row_hash, key in _iter_source_rows(path, include_dict=False):
                        count += 1
                        record = allocate_id("rec", NAMESPACE, f"{checksum}:{ordinal}:{row_hash}")
                        add_tuple((record, snapshot, str(ordinal), str(start), str(end), encode_text(key), row_hash))
                metadata.append({"file": path.name, "bytes": byte_size, "sha256": checksum, "rows": count, "snapshot_id": snapshot,
                    "disposition": "quarantined" if path.suffix != ".csv" else "pending",
                    "reason_code": "UNREPRODUCIBLE_DERIVED_ARTIFACT" if path.suffix != ".csv" else "INTAKE_ONLY"})
                total += count
            writer.finish()
        result = {"schema_version": 1, "source_root": str(source), "files": metadata, "csv_records": total}
        atomic_json(tmp / "manifest.json", result, source)
        if output.exists():
            if not output.is_dir():
                raise LexiconError("inventory output is not a directory")
            for name in ["source_records.csv", "manifest.json"]:
                if not (output / name).is_file() or digest(output / name) != digest(tmp / name):
                    raise LexiconError("inventory output conflicts with existing content")
        else:
            output.mkdir()
            for name in ["source_records.csv", "manifest.json"]:
                os.replace(tmp / name, output / name)
        return result


def _native_module():
    wrapper = str(ROOT / "bindings/python/python")
    if wrapper not in sys.path:
        sys.path.insert(0, wrapper)
    try:
        from tamil_toolkit import _native
    except ImportError as error:
        raise LexiconError("native Rust adapter unavailable; rebuild bindings") from error
    return _native


def native_inspect(text):
    wrapper = str(ROOT / "bindings/python/python")
    if wrapper not in sys.path:
        sys.path.insert(0, wrapper)
    try:
        from tamil_toolkit import execute
    except ImportError as error:
        raise LexiconError("native Rust adapter unavailable; rebuild bindings") from error
    return execute({"op": "inspect_tamil_string", "input": text})


def native_audit_batch(texts):
    """Batch-audit text strings via host-only Rust `_native`, returning None per surrogate item."""
    if not texts:
        return []
    native = _native_module()
    batch_fn = getattr(native, "batch_audit_tamil_texts", None)
    if batch_fn is not None:
        return batch_fn(texts)
    # Fallback to single-call existing Rust dispatcher until root rebuilds _native.pyd.
    from tools.lexicon_tables import is_intentional_control
    cache = {}
    out = []
    for text in texts:
        cached = cache.get(text)
        if cached is not None or text in cache:
            out.append(cached)
            continue
        if not text.isascii() and _SURROGATE_RE.search(text):
            cache[text] = None
            out.append(None)
            continue
        report = native_inspect(text)
        ctrls = [(pos, ord(ch)) for pos, ch in enumerate(text) if is_intentional_control(ord(ch))]
        other_tamil = any(
            letter["classification"] == "other" and any(0x0B80 <= ord(c) <= 0x0BDF for c in letter["text"])
            for letter in report["letters"]
        )
        res = (bool(report["is_nfc"]), ctrls, bool(other_tamil))
        cache[text] = res
        out.append(res)
    return out


def native_batch_canonical_json_sha256(values):
    """Compute SHA-256 of canonical ASCII JSON for a batch, preserving Python edge fallbacks."""
    if not values:
        return []
    native = _native_module()
    batch_fn = getattr(native, "batch_canonical_json_sha256", None)
    # CPython's C encoder beats unoptimized Rust tree traversal. Release
    # builds use the measured faster native batch; both paths retain parity.
    if batch_fn is not None and getattr(native, "HOST_BATCH_OPTIMIZED", False):
        results = batch_fn(values)
        for idx, digest_hex in enumerate(results):
            if digest_hex is None:
                results[idx] = hashlib.sha256(json_text(values[idx]).encode("ascii")).hexdigest()
        return results
    return [hashlib.sha256(json_text(v).encode("ascii")).hexdigest() for v in values]


def native_batch_data_json(values):
    """Serialize values to control-escaped UTF-8 data JSON in batch, preserving Python fallbacks."""
    if not values:
        return []
    native = _native_module()
    batch_fn = getattr(native, "batch_data_json", None)
    if batch_fn is not None and getattr(native, "HOST_BATCH_OPTIMIZED", False):
        results = batch_fn(values)
        for idx, encoded in enumerate(results):
            if encoded is None:
                results[idx] = data_json(values[idx])
        return results
    return [data_json(v) for v in values]


def native_batch_check_no_surrogates(rows):
    """Validate no lone surrogates in a batch via _native; return list[bool] or None if unbuilt."""
    if not rows:
        return []
    native = _native_module()
    batch_fn = getattr(native, "batch_check_no_surrogates", None)
    if batch_fn is None or not getattr(native, "HOST_BATCH_OPTIMIZED", False):
        return None
    try:
        return batch_fn(rows)
    except ValueError as error:
        raise LexiconError(str(error)) from error


def stage(inventory_path, workspace):
    from tools.lexicon_stage import stage as run
    return run(inventory_path, workspace)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    inv = subs.add_parser("inventory")
    inv.add_argument("--source", type=Path, default=SOURCE)
    inv.add_argument("--output", type=Path, required=True)
    inv.add_argument("--manifest", type=Path)
    staged = subs.add_parser("stage")
    staged.add_argument("--inventory", type=Path, required=True)
    staged.add_argument("--workspace", type=Path, required=True)
    selection = subs.add_parser("select-pilot")
    selection.add_argument("--source", type=Path, default=SOURCE)
    selection.add_argument("--selection", type=Path, required=True)
    curated = subs.add_parser("curate")
    curated.add_argument("--workspace", type=Path, required=True)
    curated.add_argument("--selection", type=Path, required=True)
    curated.add_argument("--source", type=Path, default=SOURCE)
    reviewed = subs.add_parser("review-ingest")
    reviewed.add_argument("--workspace", type=Path, required=True)
    reviewed.add_argument(
        "--table",
        choices=[
            "sources",
            "evidence",
            "decisions",
            "pack_members",
            "scopes",
            "labels",
            "unicode_exceptions",
            "changes",
            "successors",
        ],
        required=True,
    )
    reviewed.add_argument("--input", type=Path, required=True)
    promoted = subs.add_parser("promote")
    promoted.add_argument("--workspace", type=Path, required=True)
    promoted.add_argument("--pack", default="core")
    promoted.add_argument("--output", type=Path)
    promoted.add_argument("--report", type=Path)
    cldf = subs.add_parser("export-cldf", help="Export promoted canonical pack to offline CLDF 1.3")
    cldf.add_argument("--canonical", required=True)
    cldf.add_argument("--pack", required=True, choices=["core", "terminology", "names_taxa", "regional"])
    cldf.add_argument("--output", required=True)
    cldf.add_argument("--check", action="store_true")
    cldf.add_argument("--report-output")
    for name in ["pilot", "validate"]:
        command = subs.add_parser(name)
        command.add_argument("--workspace", type=Path, required=True)
        command.add_argument("--selection", type=Path)
        command.add_argument("--output", type=Path, required=True)
        command.add_argument("--source", type=Path, default=SOURCE)
        if name == "validate":
            command.add_argument("--mode", choices=["structural", "release"], required=True)
            command.add_argument("--pack", default="core")
    args = parser.parse_args(argv)
    try:
        if args.command == "inventory":
            result = inventory(args.source, args.output, args.manifest)
            # The stored inventory is a manifest; the CLI emits an explicit
            # operation report without implying a later acceptance milestone.
            result = dict(result, command="inventory", mode="intake", dataset_version=None,
                input_sha256=hashlib.sha256(json_text(result["files"]).encode("ascii")).hexdigest(),
                l2_structural_accepted=False, l3_pack_eligible=False, runtime_verified=None, findings=[])
        elif args.command == "stage":
            result = stage(args.inventory, args.workspace)
        elif args.command == "select-pilot":
            from tools.lexicon_pilot import select_pilot, write_selection
            result = select_pilot(args.source)
            write_selection(args.selection, result, args.source)
        elif args.command == "curate":
            from tools.lexicon_curate import project
            selected = tomllib.loads(args.selection.read_text(encoding="ascii"))
            result = project(args.workspace, {r["record_id"] for r in selected["records"]}, args.source)
        elif args.command == "review-ingest":
            from tools.lexicon_ingest import ingest
            result = ingest(args.workspace, args.table, args.input)
        elif args.command == "promote":
            from tools.lexicon_packs import promote
            result = promote(args.workspace, pack=args.pack, output=args.output, report_output=args.report)
        elif args.command == "export-cldf":
            from tools.lexicon_cldf import main as cldf_main
            cldf_argv = ["--canonical", str(args.canonical), "--pack", args.pack, "--output", str(args.output)]
            if args.check:
                cldf_argv.append("--check")
            if args.report_output:
                cldf_argv.extend(["--report-output", str(args.report_output)])
            return cldf_main(cldf_argv)
        else:
            from tools.lexicon_pilot import pilot, release_guard
            if args.command == "validate" and args.mode == "release":
                result = release_guard(args.workspace, args.pack)
            else:
                if not args.selection:
                    raise LexiconError("structural mode requires --selection")
                result = pilot(args.workspace, args.selection, source=args.source)
                if args.command == "validate":
                    from tools.lexicon_validate import validate_projection
                    result["findings"].extend(validate_projection(args.workspace))
                    result["findings"].sort(key=json_text)
                    result["l2_structural_accepted"] = not any(f["severity"] == "error" for f in result["findings"])
            if args.command == "validate":
                result["command"] = "validate"
            # Reuse the pilot report's overlap checks for this destination.
            from tools.lexicon_pilot import _report_output
            atomic_json(_report_output(args.workspace, args.output, [args.selection]), result, args.source)
        print(json_text(result))
        if args.command in {"pilot", "validate"}:
            return int(not (result["l3_pack_eligible"] if args.command == "validate" and args.mode == "release" else result["l2_structural_accepted"]))
        return 0
    except (LexiconError, OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return error.code if isinstance(error, LexiconError) else 2


if __name__ == "__main__":
    raise SystemExit(main())
