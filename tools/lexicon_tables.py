"""Schema-driven CSV table I/O and semantic relation validation for curation."""

from __future__ import annotations

import csv
from dataclasses import dataclass
import datetime
import functools
import hashlib
import json
import math
from pathlib import Path
import re

import jsonschema
import jsonschema_rs
import referencing
from referencing.jsonschema import DRAFT202012

from tools.lexicon import (
    DEFAULT_SORT_BATCH_SIZE,
    LexiconError,
    ROOT,
    _ExternalSortWriter,
    data_json,
    json_text,
    native_batch_check_no_surrogates,
    native_inspect,
    write_table,
)

SCHEMA_DIR = ROOT / "schemas/lexicon"
SCHEMA_FILES = ("intake.schema.json", "lexical.schema.json", "review.schema.json")
SCHEMA_BASE_URI = "https://schemas.tamil-toolkit.invalid/lexicon/"
INT_RE = re.compile(r"^-?(?:0|[1-9][0-9]*)$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$", re.ASCII)
SURROGATE_RE = re.compile("[" + chr(0xD800) + "-" + chr(0xDFFF) + "]")
ACCEPTED_OUTCOMES = frozenset({"accepted_auto_source", "accepted_human"})
AUDIT_CONTROL_EXTRA_CPS = frozenset({0x00AD, 0x200C, 0x200D, 0x2028, 0x2029, 0xFEFF})
RAW_JSON_CONTROL_RE = re.compile(
    "[\x00-\x1f\x7f-\x9f" + "".join(chr(cp) for cp in sorted(AUDIT_CONTROL_EXTRA_CPS)) + "]"
)


def is_intentional_control(cp: int) -> bool:
    """Return True when codepoint is a C0/C1 control or audit-sensitive format scalar."""
    return cp in AUDIT_CONTROL_EXTRA_CPS or cp < 32 or 0x7F <= cp <= 0x9F
ENTITY_TABLE_FOR_KIND = {
    "entry": "entries",
    "form": "forms",
    "sense": "senses",
    "text": "texts",
    "relation": "relations",
    "assertion": "assertions",
}
PRIMARY_ID_COLS = {
    "snapshots": "snapshot_id",
    "sources": "source_id",
    "source_records": "record_id",
    "dispositions": "record_id",
    "entries": "entry_id",
    "forms": "form_id",
    "senses": "sense_id",
    "texts": "text_id",
    "relations": "relation_id",
    "assertions": "assertion_id",
    "decisions": "decision_id",
    "changes": "change_id",
    "findings": "finding_id",
}


@dataclass(frozen=True)
class ColumnSpec:
    kind: str  # "json", "int", or "str"
    nullable: bool
    is_array: bool = False


@dataclass(frozen=True)
class TableMeta:
    name: str
    fields: list[str]
    columns: dict[str, ColumnSpec]
    col_specs: tuple[tuple[str, ColumnSpec], ...]
    expected_keys: frozenset[str]
    validator: jsonschema.Draft202012Validator
    fast_validator: jsonschema_rs.Draft202012Validator
    field_tuple: tuple[str, ...]
    n_fields: int
    col_modes: tuple[tuple[int, str, int], ...]
    opt_str_cols: tuple[tuple[int, str], ...]
    int_cols: tuple[tuple[int, str, bool], ...]
    req_int_cols: tuple[tuple[int, str], ...]
    opt_int_cols: tuple[tuple[int, str], ...]
    json_cols: tuple[tuple[int, str], ...]


_RS_PATTERN_REWRITES = {
    r"^[^\uD800-\uDFFF]*$": None,
    r"^[A-Za-z][A-Za-z0-9_.:-]*$": r"\A[A-Za-z][A-Za-z0-9_.:-]*\n?\z",
    r"^[0-9a-f]{64}$": r"\A[0-9a-f]{64}\n?\z",
    r"^[A-Za-z_][A-Za-z0-9_]*$": r"\A[A-Za-z_][A-Za-z0-9_]*\n?\z",
    r"^\d{4}-\d{2}-\d{2}$": r"\A\d{4}-\d{2}-\d{2}\n?\z",
    r"^(?![A-Za-z]:)(?![/\\])(?!.*(?:^|[/\\])\.\.(?:[/\\]|$))[^\uD800-\uDFFF]+$": (
        r"\A(?![A-Za-z]:)(?![/\\])(?![^\n]*(?:\A|[/\\])\.\.(?:[/\\]|\n?\z))[\s\S]+\z"
    ),
}


def _rewrite_schema_for_rs(node):
    """Translate Python re patterns to equivalent Rust fancy-regex patterns."""
    if isinstance(node, list):
        return [_rewrite_schema_for_rs(v) for v in node]
    if not isinstance(node, dict):
        return node
    out = {}
    for k, v in node.items():
        if k == "pattern" and isinstance(v, str):
            if v not in _RS_PATTERN_REWRITES:
                raise LexiconError(f"unmapped schema regex pattern for native validator: {v!r}")
            mapped = _RS_PATTERN_REWRITES[v]
            if mapped is None:
                continue
            v = mapped
        out[k] = _rewrite_schema_for_rs(v)
    return out


def _is_iso_date(value: str) -> bool:
    """Match jsonschema's Draft 2020-12 date FormatChecker using datetime.date."""
    if not _DATE_RE.fullmatch(value):
        return False
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _deny_retrieve(uri: str):
    raise LexiconError(f"network or unregistered schema ref is forbidden: {uri}")


def _check_no_surrogates(value, context: str = "") -> bool:
    """Verify no lone surrogates exist and return True iff value uses standard JSON types."""
    t = type(value)
    if t is str:
        if not value.isascii() and SURROGATE_RE.search(value):
            suffix = f" in {context}" if context else ""
            raise LexiconError(f"invalid Unicode scalar: lone surrogate{suffix}")
        return True
    if value is None or t is int or t is bool:
        return True
    if t is float:
        return math.isfinite(value)
    if t is list:
        native_ok = True
        for item in value:
            if not _check_no_surrogates(item, context):
                native_ok = False
        return native_ok
    if t is dict:
        native_ok = True
        for key, item in value.items():
            if not _check_no_surrogates(key, context) or type(key) is not str:
                native_ok = False
            if not _check_no_surrogates(item, context):
                native_ok = False
        return native_ok
    if isinstance(value, str):
        if not value.isascii() and SURROGATE_RE.search(value):
            suffix = f" in {context}" if context else ""
            raise LexiconError(f"invalid Unicode scalar: lone surrogate{suffix}")
        return False
    if isinstance(value, (list, tuple)):
        for item in value:
            _check_no_surrogates(item, context)
        return False
    if isinstance(value, dict):
        for key, item in value.items():
            _check_no_surrogates(key, context)
            _check_no_surrogates(item, context)
        return False
    return False


def _reject_json_constant(token: str):
    raise LexiconError(f"invalid JSON constant in CSV cell: {token}")


_JSON_DECODER = json.JSONDecoder(parse_constant=_reject_json_constant)
_JSON_SCAN_ONCE = _JSON_DECODER.scan_once


def _column_spec(col: str, cdef: dict) -> ColumnSpec:
    is_array = cdef.get("type") == "array"
    if col.endswith("_json") or is_array:
        return ColumnSpec(kind="json", nullable=False, is_array=is_array)
    if cdef.get("$ref") == "common.schema.json#/$defs/nullableId":
        return ColumnSpec(kind="str", nullable=True)
    if cdef.get("type") == "integer" or cdef.get("$ref") == "common.schema.json#/$defs/scalarPosition":
        return ColumnSpec(kind="int", nullable=False)
    any_of = cdef.get("anyOf", [])
    nullable = any(opt == {"type": "null"} for opt in any_of)
    if any(opt.get("type") == "integer" for opt in any_of):
        return ColumnSpec(kind="int", nullable=nullable)
    return ColumnSpec(kind="str", nullable=nullable)


def _inline_schema(node, filename, docs, stack=frozenset()):
    """Resolve finite local references once, retaining recursive JSON schemas.

    Validation still uses the same Draft 2020-12 engine and constraints. Bulk
    row checks avoid rebuilding a reference resolver for every scalar column.
    """
    if isinstance(node, list):
        return [_inline_schema(v, filename, docs, stack) for v in node]
    if not isinstance(node, dict):
        return node
    if "$ref" in node:
        name, _, fragment = node["$ref"].partition("#")
        name = name or filename
        key = (name, fragment)
        siblings = {k:v for k,v in node.items() if k != "$ref"}
        if key in stack:
            target = {"$ref":name + "#" + fragment}
        else:
            target = docs[name]
            for part in fragment.lstrip("/").split("/"):
                if part:
                    target = target[part.replace("~1","/").replace("~0","~")]
            target = _inline_schema(target, name, docs, stack | {key})
        return {"allOf":[target,_inline_schema(siblings,filename,docs,stack)]} if siblings else target
    return {k:_inline_schema(v,filename,docs,stack) for k,v in node.items() if k not in {"$id","$schema"}}


@functools.lru_cache(maxsize=1)
def _table_registry() -> dict[str, TableMeta]:
    resources = []
    rs_resources = []
    docs: dict[str, dict] = {}
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        docs[path.name] = doc
        res = DRAFT202012.create_resource(doc)
        resources.append((path.name, res))
        rs_doc = _rewrite_schema_for_rs(doc)
        rs_resources.append((SCHEMA_BASE_URI + path.name, rs_doc))
        if "$id" in doc:
            resources.append((doc["$id"], res))
            if ":" in doc["$id"]:
                rs_resources.append((doc["$id"], rs_doc))
    registry = referencing.Registry(retrieve=_deny_retrieve).with_resources(resources)
    rs_registry = jsonschema_rs.Registry(
        rs_resources,
        draft=jsonschema_rs.Draft202012,
        retriever=_deny_retrieve,
    )

    tables: dict[str, TableMeta] = {}
    for schema_name in SCHEMA_FILES:
        doc = docs[schema_name]
        for table_name, table_def in doc["$defs"].items():
            prop_order = list(table_def["properties"].keys())
            cols = {col: _column_spec(col, cdef) for col, cdef in table_def["properties"].items()}
            col_specs = tuple((col, cols[col]) for col in prop_order)
            inlined = _inline_schema(table_def, schema_name, docs)
            validator = jsonschema.Draft202012Validator(
                inlined,
                registry=registry,
                format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER,
            )
            fast_validator = jsonschema_rs.Draft202012Validator(
                _rewrite_schema_for_rs(inlined),
                base_uri=SCHEMA_BASE_URI + "row.schema.json",
                registry=rs_registry,
                offline=True,
                validate_formats=True,
                formats={"date": _is_iso_date},
            )
            opt_str_cols = []
            int_cols = []
            req_int_cols = []
            opt_int_cols = []
            json_cols = []
            col_modes = []
            for idx, (col, spec) in enumerate(col_specs):
                if spec.kind == "json":
                    json_cols.append((idx, col))
                    col_modes.append((idx, col, 5 if spec.is_array else 4))
                elif spec.kind == "int":
                    int_cols.append((idx, col, spec.nullable))
                    if spec.nullable:
                        opt_int_cols.append((idx, col))
                        col_modes.append((idx, col, 3))
                    else:
                        req_int_cols.append((idx, col))
                        col_modes.append((idx, col, 2))
                elif spec.nullable:
                    opt_str_cols.append((idx, col))
                    col_modes.append((idx, col, 1))
                else:
                    col_modes.append((idx, col, 0))
            tables[table_name] = TableMeta(
                name=table_name,
                fields=prop_order,
                columns=cols,
                col_specs=col_specs,
                expected_keys=frozenset(prop_order),
                validator=validator,
                fast_validator=fast_validator,
                field_tuple=tuple(prop_order),
                n_fields=len(col_specs),
                col_modes=tuple(col_modes),
                opt_str_cols=tuple(opt_str_cols),
                int_cols=tuple(int_cols),
                req_int_cols=tuple(req_int_cols),
                opt_int_cols=tuple(opt_int_cols),
                json_cols=tuple(json_cols),
            )
    return tables


def _require_table(table: str) -> TableMeta:
    meta = _table_registry().get(table)
    if meta is None:
        raise LexiconError(f"unknown lexicon table schema: {table!r}")
    return meta


def fields(table: str) -> list[str]:
    """Return column names for a declared schema table in schema property order."""
    return list(_require_table(table).fields)


def _serialize_cell(col: str, spec: ColumnSpec, value, *, check_surrogates: bool = True) -> str:
    if spec.kind == "json":
        if check_surrogates:
            _check_no_surrogates(value, col)
        if spec.is_array:
            if not isinstance(value, list) or any(
                not isinstance(item, int) or isinstance(item, bool) for item in value
            ):
                raise LexiconError(f"column {col} requires a list of integers")
        try:
            return data_json(value)
        except (TypeError, ValueError) as error:
            raise LexiconError(f"cannot JSON-encode column {col}: {error}") from error
    if value is None:
        if not spec.nullable:
            raise LexiconError(f"required column {col} cannot be null")
        return ""
    if spec.kind == "int":
        if not isinstance(value, int) or isinstance(value, bool):
            raise LexiconError(f"column {col} requires an integer")
        return str(value)
    if not isinstance(value, str):
        raise LexiconError(f"column {col} requires a string")
    if check_surrogates:
        _check_no_surrogates(value, col)
    if spec.nullable and value == "":
        raise LexiconError(f"nullable column {col} cannot contain empty string")
    return value


def _validate_and_serialize_row(meta: TableMeta, row: dict, index_label: str) -> tuple[str, ...]:
    if not isinstance(row, dict):
        raise LexiconError(f"{index_label}: expected dict")
    if type(row) is not dict:
        keys = set(row.keys())
        if keys != meta.expected_keys:
            missing = sorted(meta.expected_keys - keys)
            extra = sorted(keys - meta.expected_keys)
            raise LexiconError(f"{index_label}: column mismatch missing={missing} extra={extra}")
        _check_no_surrogates(row, meta.name)
        if not meta.validator.is_valid(row):
            raise LexiconError(f"{meta.name} schema error at {_format_validation_error(meta.validator, row)}")
        return tuple(_serialize_cell(col, spec, row[col]) for col, spec in meta.col_specs)
    if len(row) != meta.n_fields:
        keys = row.keys()
        missing = sorted(meta.expected_keys - keys)
        extra = sorted(keys - meta.expected_keys)
        raise LexiconError(f"{index_label}: column mismatch missing={missing} extra={extra}")
    native_ok = True
    serialize_fast = True
    cells = [""] * meta.n_fields
    try:
        for idx, col, mode in meta.col_modes:
            value = row[col]
            if mode == 0:
                if type(value) is str:
                    if not value.isascii() and SURROGATE_RE.search(value):
                        raise LexiconError(f"invalid Unicode scalar: lone surrogate in {meta.name}")
                    cells[idx] = value
                else:
                    serialize_fast = False
                    if not _check_no_surrogates(value, meta.name):
                        native_ok = False
            elif mode == 1:
                if value is None:
                    pass
                elif type(value) is str:
                    if not value.isascii() and SURROGATE_RE.search(value):
                        raise LexiconError(f"invalid Unicode scalar: lone surrogate in {meta.name}")
                    if value == "":
                        serialize_fast = False
                    else:
                        cells[idx] = value
                else:
                    serialize_fast = False
                    if not _check_no_surrogates(value, meta.name):
                        native_ok = False
            elif mode == 4:
                if type(value) is str:
                    if not value.isascii() and SURROGATE_RE.search(value):
                        raise LexiconError(f"invalid Unicode scalar: lone surrogate in {meta.name}")
                    cells[idx] = data_json(value)
                elif value is None:
                    cells[idx] = "null"
                else:
                    if not _check_no_surrogates(value, meta.name):
                        native_ok = False
                    try:
                        cells[idx] = data_json(value)
                    except (TypeError, ValueError):
                        serialize_fast = False
            elif mode == 2:
                if type(value) is int:
                    try:
                        cells[idx] = str(value)
                    except ValueError:
                        serialize_fast = False
                else:
                    serialize_fast = False
                    if not _check_no_surrogates(value, meta.name):
                        native_ok = False
            elif mode == 3:
                if value is None:
                    pass
                elif type(value) is int:
                    try:
                        cells[idx] = str(value)
                    except ValueError:
                        serialize_fast = False
                else:
                    serialize_fast = False
                    if not _check_no_surrogates(value, meta.name):
                        native_ok = False
            else:
                if type(value) is list and all(type(item) is int for item in value):
                    try:
                        cells[idx] = data_json(value)
                    except ValueError:
                        serialize_fast = False
                else:
                    serialize_fast = False
                    if not _check_no_surrogates(value, meta.name):
                        native_ok = False
    except KeyError:
        keys = row.keys()
        missing = sorted(meta.expected_keys - keys)
        extra = sorted(keys - meta.expected_keys)
        raise LexiconError(f"{index_label}: column mismatch missing={missing} extra={extra}") from None
    validator = meta.fast_validator if native_ok else meta.validator
    if not validator.is_valid(row):
        raise LexiconError(f"{meta.name} schema error at {_format_validation_error(meta.validator, row)}")
    if serialize_fast:
        return tuple(cells)
    return tuple(_serialize_cell(col, spec, row[col], check_surrogates=False) for col, spec in meta.col_specs)


class TableRowWriter:
    """Streaming schema-validated external-sort CSV writer for one table."""

    def __init__(self, path, table: str, source_root=None, batch_size: int = DEFAULT_SORT_BATCH_SIZE) -> None:
        self.meta = _require_table(table)
        self.count = 0
        self._writer = _ExternalSortWriter(path, self.meta.fields, source_root=source_root, batch_size=batch_size)

    def write_row(self, row: dict) -> None:
        self.count += 1
        self._writer.add_tuple(_validate_and_serialize_row(self.meta, row, f"{self.meta.name} row {self.count}"))

    def write_rows_batch(self, rows: list[dict]) -> None:
        """Validate and serialize a bounded chunk of rows using batch surrogate checks."""
        if not rows:
            return
        try:
            native_flags = native_batch_check_no_surrogates(rows)
        except LexiconError:
            native_flags = None
        if native_flags is None:
            for row in rows:
                self.write_row(row)
            return
        meta = self.meta
        fast_is_valid = meta.fast_validator.is_valid
        full_is_valid = meta.validator.is_valid
        n_fields = meta.n_fields
        expected_keys = meta.expected_keys
        col_modes = meta.col_modes
        col_specs = meta.col_specs
        for row, native_ok in zip(rows, native_flags):
            self.count += 1
            if not native_ok or type(row) is not dict or len(row) != n_fields:
                self._writer.add_tuple(_validate_and_serialize_row(meta, row, f"{meta.name} row {self.count}"))
                continue
            try:
                cells = [""] * n_fields
                serialize_fast = True
                for idx, col, mode in col_modes:
                    value = row[col]
                    if mode == 0:
                        if type(value) is str:
                            cells[idx] = value
                        else:
                            serialize_fast = False
                    elif mode == 1:
                        if value is None:
                            pass
                        elif type(value) is str and value != "":
                            cells[idx] = value
                        else:
                            serialize_fast = False
                    elif mode == 4:
                        if type(value) is str:
                            cells[idx] = data_json(value)
                        elif value is None:
                            cells[idx] = "null"
                        else:
                            try:
                                cells[idx] = data_json(value)
                            except (TypeError, ValueError):
                                serialize_fast = False
                    elif mode == 2:
                        if type(value) is int:
                            try:
                                cells[idx] = str(value)
                            except ValueError:
                                serialize_fast = False
                        else:
                            serialize_fast = False
                    elif mode == 3:
                        if value is None:
                            pass
                        elif type(value) is int:
                            try:
                                cells[idx] = str(value)
                            except ValueError:
                                serialize_fast = False
                        else:
                            serialize_fast = False
                    else:
                        if type(value) is list and all(type(item) is int for item in value):
                            try:
                                cells[idx] = data_json(value)
                            except ValueError:
                                serialize_fast = False
                        else:
                            serialize_fast = False
            except KeyError:
                keys = row.keys()
                missing = sorted(expected_keys - keys)
                extra = sorted(keys - expected_keys)
                raise LexiconError(f"{meta.name} row {self.count}: column mismatch missing={missing} extra={extra}") from None
            if not fast_is_valid(row):
                raise LexiconError(f"{meta.name} schema error at {_format_validation_error(meta.validator, row)}")
            if serialize_fast:
                self._writer.add_tuple(tuple(cells))
            else:
                self._writer.add_tuple(tuple(_serialize_cell(col, spec, row[col], check_surrogates=False) for col, spec in col_specs))

    def finish(self):
        return self._writer.finish()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self._writer.__exit__(exc_type, exc, tb)


def write_rows(path, table: str, decodedRows, source_root=None) -> None:
    """Serialize decoded typed rows to CSV and sort/write atomically via tools.lexicon.write_table."""
    meta = _require_table(table)

    def encode():
        for index, row in enumerate(decodedRows, 1):
            yield _validate_and_serialize_row(meta, row, f"{table} row {index}")

    write_table(path, meta.fields, encode(), source_root=source_root)


def _deserialize_json_cell(col: str, cell: str, *, line_checked: bool = False):
    if not cell:
        raise LexiconError(f"JSON cell {col} must be nonempty")
    if cell == "null":
        return None
    if cell == "true":
        return True
    if cell == "false":
        return False
    if RAW_JSON_CONTROL_RE.search(cell):
        raise LexiconError(f"unescaped raw control or format scalar in JSON cell {col}")
    try:
        if cell[0] not in " \t\n\r":
            try:
                decoded, end = _JSON_SCAN_ONCE(cell, 0)
            except StopIteration:
                decoded = _JSON_DECODER.decode(cell)
            else:
                if end != len(cell):
                    decoded = _JSON_DECODER.decode(cell)
        else:
            decoded = _JSON_DECODER.decode(cell)
    except (ValueError, TypeError) as error:
        raise LexiconError(f"invalid JSON in cell {col}: {error}") from error
    if not line_checked or type(decoded) is not str or "\\u" in cell:
        _check_no_surrogates(decoded, col)
    return decoded


def _deserialize_int_cell(col: str, cell: str, nullable: bool) -> int | None:
    if nullable and cell == "":
        return None
    if cell.isascii() and cell.isdigit() and (len(cell) == 1 or cell[0] != "0"):
        return int(cell)
    if not INT_RE.fullmatch(cell):
        raise LexiconError(f"invalid integer cell in {col}: {cell!r}")
    return int(cell)


def _deserialize_cell(col: str, spec: ColumnSpec, cell: str, *, line_checked: bool = False):
    if not line_checked:
        _check_no_surrogates(cell, col)
    if spec.kind == "json":
        return _deserialize_json_cell(col, cell, line_checked=line_checked)
    if spec.kind == "int":
        return _deserialize_int_cell(col, cell, spec.nullable)
    if spec.nullable and cell == "":
        return None
    return cell


def _checked_lf_lines(handle, name: str):
    iterator = iter(handle)
    first = next(iterator, None)
    if first is None:
        return
    if first.startswith("\ufeff"):
        raise LexiconError(f"UTF-8 BOM is forbidden: {name}")
    if "\r" in first:
        raise LexiconError(f"CRLF/CR line ending is forbidden: {name}:1")
    yield first
    for number, line in enumerate(iterator, 2):
        if "\r" in line:
            raise LexiconError(f"CRLF/CR line ending is forbidden: {name}:{number}")
        yield line


def _format_validation_error(validator: jsonschema.Draft202012Validator, row: dict) -> str:
    errors = sorted(
        validator.iter_errors(row),
        key=lambda err: (tuple(str(part) for part in err.path), err.message),
    )
    err = errors[0]
    location = ".".join(str(part) for part in err.path) or "<row>"
    return f"{location}: {err.message}"


def validate_row(table: str, row: dict) -> None:
    """Validate one decoded row against the offline local jsonschema Registry."""
    meta = _require_table(table)
    native_ok = _check_no_surrogates(row, table)
    validator = meta.fast_validator if native_ok else meta.validator
    if not validator.is_valid(row):
        raise LexiconError(f"{table} schema error at {_format_validation_error(meta.validator, row)}")


def validate_rows_batch(table: str, rows: list[dict], *, collect_errors: bool = False, chunk_size: int = 4096) -> list[tuple[dict, str]]:
    """Validate a list of rows against the offline schema using batch surrogate checking.

    Returns a list of ``(row, error_message)`` pairs when ``collect_errors=True``;
    otherwise raises ``LexiconError`` on the first failing row.
    """
    if not rows:
        return []
    meta = _require_table(table)
    fast_is_valid = meta.fast_validator.is_valid
    full_is_valid = meta.validator.is_valid
    errors: list[tuple[dict, str]] = []
    for start in range(0, len(rows), chunk_size):
        chunk = rows[start : start + chunk_size]
        try:
            native_flags = native_batch_check_no_surrogates(chunk)
        except LexiconError:
            native_flags = None
        if native_flags is None:
            for row in chunk:
                try:
                    validate_row(table, row)
                except LexiconError as exc:
                    if not collect_errors:
                        raise
                    errors.append((row, str(exc)))
            continue
        for row, native_ok in zip(chunk, native_flags):
            is_ok = fast_is_valid(row) if native_ok else full_is_valid(row)
            if not is_ok:
                msg = f"{table} schema error at {_format_validation_error(meta.validator, row)}"
                if not collect_errors:
                    raise LexiconError(msg)
                errors.append((row, msg))
    return errors


def read_rows(path, table: str | None = None):
    """Stream decoded, schema-validated row dicts from a canonical curation CSV file."""
    path = Path(path)
    table_name = path.stem if table is None else table
    meta = _require_table(table_name)

    def _generate():
        n_fields = meta.n_fields
        field_tuple = meta.field_tuple
        opt_str_cols = meta.opt_str_cols
        req_int_cols = meta.req_int_cols
        opt_int_cols = meta.opt_int_cols
        json_cols = meta.json_cols
        fast_is_valid = meta.fast_validator.is_valid
        try:
            with path.open(encoding="utf-8", newline="", buffering=1024 * 1024) as handle:
                reader = csv.reader(_checked_lf_lines(handle, path.name), strict=True)
                header = next(reader, None)
                if header != meta.fields:
                    raise LexiconError(
                        f"invalid CSV header for {table_name} in {path.name}: expected {meta.fields}, got {header}"
                    )
                for row_num, raw_row in enumerate(reader, 2):
                    if len(raw_row) != n_fields:
                        raise LexiconError(
                            f"CSV record width mismatch in {path.name}:{row_num}: expected {n_fields}, got {len(raw_row)}"
                        )
                    decoded = dict(zip(field_tuple, raw_row))
                    for idx, col in opt_str_cols:
                        if raw_row[idx] == "":
                            decoded[col] = None
                    for idx, col in req_int_cols:
                        cell = raw_row[idx]
                        decoded[col] = (
                            int(cell)
                            if cell.isascii() and cell.isdigit() and (len(cell) == 1 or cell[0] != "0")
                            else _deserialize_int_cell(col, cell, False)
                        )
                    for idx, col in opt_int_cols:
                        cell = raw_row[idx]
                        if cell == "":
                            decoded[col] = None
                        elif cell.isascii() and cell.isdigit() and (len(cell) == 1 or cell[0] != "0"):
                            decoded[col] = int(cell)
                        else:
                            decoded[col] = _deserialize_int_cell(col, cell, True)
                    for idx, col in json_cols:
                        cell = raw_row[idx]
                        if cell == "null":
                            decoded[col] = None
                        elif cell == "true":
                            decoded[col] = True
                        elif cell == "false":
                            decoded[col] = False
                        else:
                            decoded[col] = _deserialize_json_cell(col, cell, line_checked=True)
                    if not fast_is_valid(decoded):
                        raise LexiconError(f"{path.name}:{row_num} ({_format_validation_error(meta.validator, decoded)})")
                    yield decoded
        except (csv.Error, UnicodeError) as error:
            raise LexiconError(f"invalid UTF-8/CSV in {path.name}: {error}") from error

    return _generate()


# ---------------------------------------------------------------------------
# Semantic & relational validation (T021-T024)
# ---------------------------------------------------------------------------


def _add_finding(findings: list[dict], code: str, subject_id: str, reason: str, severity: str = "error") -> None:
    findings.append(
        {
            "code": code,
            "severity": severity,
            "reason": reason,
            "subject_id": str(subject_id),
        }
    )


def _index_unique(
    rows: list[dict],
    key: str,
    table_name: str,
    findings: list[dict],
    code: str = "duplicate_id",
) -> tuple[dict[str, dict], set[str]]:
    index: dict[str, dict] = {}
    duplicates: set[str] = set()
    for row in rows:
        val = row.get(key)
        if not isinstance(val, str) or not val:
            _add_finding(findings, "missing_primary_id", str(val or table_name), f"{table_name}: missing {key}")
            continue
        if val in index:
            duplicates.add(val)
            _add_finding(findings, code, val, f"{table_name}: duplicate {key} {val!r}")
        else:
            index[val] = row
    return index, duplicates


def _check_composite_unique(
    rows: list[dict],
    cols: tuple[str, ...],
    table_name: str,
    findings: list[dict],
    code: str,
    subject_col: str | None = None,
) -> None:
    seen: set[tuple] = set()
    for row in rows:
        key = tuple(row.get(c) for c in cols)
        if key in seen:
            subj = row.get(subject_col) if subject_col else "|".join(str(v) for v in key if v is not None)
            _add_finding(findings, code, str(subj or table_name), f"{table_name}: duplicate key {cols}={key!r}")
        else:
            seen.add(key)


def _detect_cycles(adj: dict[str, list[str]]) -> set[str]:
    """Return every node participating in or directly triggering a directed cycle."""
    state: dict[str, int] = {}  # 1 = visiting, 2 = done
    stack: list[str] = []
    in_cycle: set[str] = set()

    def dfs(node: str) -> None:
        state[node] = 1
        stack.append(node)
        for nxt in adj.get(node, ()):
            nxt_state = state.get(nxt, 0)
            if nxt_state == 1:
                idx = stack.index(nxt)
                in_cycle.update(stack[idx:])
            elif nxt_state == 0:
                dfs(nxt)
        stack.pop()
        state[node] = 2

    for start in sorted(adj):
        if state.get(start, 0) == 0:
            dfs(start)
    return in_cycle


def _check_intake_and_accounting(
    tables: dict[str, list[dict]],
    indexes: dict[str, dict[str, dict]],
    findings: list[dict],
) -> None:
    identities = indexes.get("identities", {})
    if "identities" in tables:
        seen_alloc: dict[str, str] = {}
        for row in tables["identities"]:
            alloc = row.get("allocation_key")
            eid = row.get("entity_id", "")
            if alloc in seen_alloc:
                _add_finding(
                    findings,
                    "duplicate_allocation_key",
                    eid,
                    f"identities: allocation_key {alloc!r} conflicts with {seen_alloc[alloc]!r}",
                )
            elif isinstance(alloc, str):
                seen_alloc[alloc] = eid
        for kind, tbl in ENTITY_TABLE_FOR_KIND.items():
            for eid in indexes.get(tbl, {}):
                if eid not in identities:
                    if kind != "assertion":
                        _add_finding(
                            findings,
                            "dangling_reference",
                            eid,
                            f"{tbl}: entity {eid!r} missing from identities",
                        )
                elif identities[eid].get("kind") != kind:
                    _add_finding(
                        findings,
                        "identity_kind_mismatch",
                        eid,
                        f"{tbl}: entity {eid!r} has kind {identities[eid].get('kind')!r} in identities, expected {kind!r}",
                    )

    if "sources" in tables and "snapshots" in tables:
        snaps = indexes["snapshots"]
        for row in tables["sources"]:
            sid = row.get("snapshot_id")
            if sid is not None and sid not in snaps:
                _add_finding(findings, "dangling_reference", row.get("source_id", ""), f"sources: unknown snapshot_id {sid!r}")

    if "source_records" in tables:
        _check_composite_unique(
            tables["source_records"], ("snapshot_id", "ordinal"), "source_records", findings, "duplicate_record_ordinal", "record_id"
        )
        snaps = indexes.get("snapshots", {})
        for row in tables["source_records"]:
            rid = row.get("record_id", "")
            if "snapshots" in tables and row.get("snapshot_id") not in snaps:
                _add_finding(findings, "dangling_reference", rid, f"source_records: unknown snapshot_id {row.get('snapshot_id')!r}")
            start, end = row.get("physical_line_start"), row.get("physical_line_end")
            if isinstance(start, int) and isinstance(end, int) and end < start:
                _add_finding(findings, "invalid_line_span", rid, f"source_records: physical_line_end ({end}) < start ({start})")

    if "dispositions" in tables and "source_records" in tables:
        rec_ids = set(indexes["source_records"].keys())
        disp_ids = set(indexes["dispositions"].keys())
        for missing_rid in sorted(rec_ids - disp_ids):
            _add_finding(findings, "missing_disposition", missing_rid, f"source_records: record {missing_rid!r} lacks a disposition")
        for extra_rid in sorted(disp_ids - rec_ids):
            _add_finding(findings, "dangling_reference", extra_rid, f"dispositions: unknown record_id {extra_rid!r}")

    targets_by_record: dict[str, list[dict]] = {}
    if "record_targets" in tables:
        _check_composite_unique(
            tables["record_targets"], ("record_id", "entity_id", "target_role"), "record_targets", findings, "duplicate_record_target", "record_id"
        )
        for row in tables["record_targets"]:
            rid = row.get("record_id", "")
            eid = row.get("entity_id", "")
            targets_by_record.setdefault(rid, []).append(row)
            if "source_records" in tables and rid not in indexes["source_records"]:
                _add_finding(findings, "dangling_reference", rid, f"record_targets: unknown record_id {rid!r}")
            if "dispositions" in tables and rid not in indexes["dispositions"]:
                _add_finding(findings, "dangling_reference", rid, f"record_targets: record {rid!r} has no disposition")
            if "identities" in tables and eid not in identities:
                _add_finding(findings, "dangling_reference", rid, f"record_targets: unknown entity_id {eid!r}")

    if "dispositions" in tables:
        for row in tables["dispositions"]:
            rid = row.get("record_id", "")
            disp = row.get("disposition")
            targets = targets_by_record.get(rid, [])
            distinct_entities = {t.get("entity_id") for t in targets}
            if disp in {"mapped", "merged"} and len(targets) < 1:
                _add_finding(findings, "missing_record_target", rid, f"dispositions: {disp!r} record requires at least 1 target")
            elif disp == "split" and len(distinct_entities) < 2:
                _add_finding(findings, "insufficient_split_targets", rid, "dispositions: 'split' record requires at least 2 distinct targets")
            elif disp in {"quarantined", "excluded"} and targets:
                _add_finding(
                    findings,
                    "forbidden_targets_on_non_mapped_disposition",
                    rid,
                    f"dispositions: {disp!r} record must have no target mappings",
                )


def _check_entries_and_forms(
    tables: dict[str, list[dict]],
    indexes: dict[str, dict[str, dict]],
    findings: list[dict],
) -> None:
    entries = indexes.get("entries", {})
    forms = indexes.get("forms", {})
    assertions = indexes.get("assertions", {})

    forms_by_entry: dict[str, list[dict]] = {}
    for row in tables.get("forms", ()):
        fid = row.get("form_id", "")
        eid = row.get("entry_id", "")
        forms_by_entry.setdefault(eid, []).append(row)
        if "entries" in tables and eid not in entries:
            _add_finding(findings, "dangling_reference", fid, f"forms: unknown entry_id {eid!r}")
        if "assertions" in tables:
            tid = row.get("text_assertion_id")
            if tid not in assertions:
                _add_finding(findings, "dangling_reference", fid, f"forms: unknown text_assertion_id {tid!r}")
            else:
                asr = assertions[tid]
                if asr.get("subject_kind") != "form" or asr.get("subject_id") != fid:
                    _add_finding(findings, "assertion_ownership_mismatch", fid, f"forms: text_assertion_id {tid!r} not owned by form {fid!r}")
                if row.get("representation") == "written" and row.get("role") == "canonical":
                    if asr.get("value_state") == "known" and (not isinstance(asr.get("value_json"), str) or asr.get("value_json") == ""):
                        _add_finding(findings, "empty_headword", fid, "forms: canonical written headword cannot be empty")
            cid = row.get("convention_assertion_id")
            if cid is not None:
                if cid not in assertions:
                    _add_finding(findings, "dangling_reference", fid, f"forms: unknown convention_assertion_id {cid!r}")
                else:
                    casr = assertions[cid]
                    if casr.get("subject_kind") != "form" or casr.get("subject_id") != fid:
                        _add_finding(
                            findings,
                            "assertion_ownership_mismatch",
                            fid,
                            f"forms: convention_assertion_id {cid!r} not owned by form {fid!r}",
                        )

    for row in tables.get("entries", ()):
        eid = row.get("entry_id", "")
        cfid = row.get("canonical_form_id")
        if cfid is not None and "forms" in tables:
            if cfid not in forms:
                _add_finding(findings, "dangling_reference", eid, f"entries: unknown canonical_form_id {cfid!r}")
            else:
                cform = forms[cfid]
                if cform.get("entry_id") != eid:
                    _add_finding(findings, "canonical_form_wrong_entry", eid, f"entries: canonical_form_id {cfid!r} belongs to another entry")
                elif cform.get("representation") != "written" or cform.get("role") != "canonical":
                    _add_finding(
                        findings,
                        "canonical_form_wrong_role",
                        eid,
                        f"entries: canonical_form_id {cfid!r} must have representation='written' and role='canonical'",
                    )
        pid = row.get("pos_assertion_id")
        if pid is not None and "assertions" in tables:
            if pid not in assertions:
                _add_finding(findings, "dangling_reference", eid, f"entries: unknown pos_assertion_id {pid!r}")
            else:
                pasr = assertions[pid]
                if pasr.get("subject_kind") != "entry" or pasr.get("subject_id") != eid:
                    _add_finding(findings, "assertion_ownership_mismatch", eid, f"entries: pos_assertion_id {pid!r} not owned by entry {eid!r}")

        if "forms" in tables:
            canon_written = [
                f for f in forms_by_entry.get(eid, ()) if f.get("representation") == "written" and f.get("role") == "canonical"
            ]
            if len(canon_written) == 0:
                _add_finding(findings, "missing_canonical_form", eid, f"entries: entry {eid!r} has no canonical written form")
            elif len(canon_written) > 1:
                _add_finding(
                    findings,
                    "multiple_canonical_forms",
                    eid,
                    f"entries: entry {eid!r} has {len(canon_written)} canonical written forms, expected 1",
                )
            elif cfid is not None and cfid in forms and cfid != canon_written[0].get("form_id"):
                _add_finding(
                    findings,
                    "canonical_form_mismatch",
                    eid,
                    f"entries: canonical_form_id {cfid!r} differs from canonical written form {canon_written[0].get('form_id')!r}",
                )


def _check_senses_and_texts(
    tables: dict[str, list[dict]],
    indexes: dict[str, dict[str, dict]],
    findings: list[dict],
) -> None:
    entries = indexes.get("entries", {})
    senses = indexes.get("senses", {})
    texts = indexes.get("texts", {})
    assertions = indexes.get("assertions", {})

    if "senses" in tables:
        parent_adj: dict[str, list[str]] = {}
        for row in tables["senses"]:
            sid = row.get("sense_id", "")
            eid = row.get("entry_id")
            if "entries" in tables and eid not in entries:
                _add_finding(findings, "dangling_reference", sid, f"senses: unknown entry_id {eid!r}")
            pid = row.get("parent_sense_id")
            if pid is not None:
                if pid not in senses:
                    _add_finding(findings, "dangling_reference", sid, f"senses: unknown parent_sense_id {pid!r}")
                else:
                    if senses[pid].get("entry_id") != eid:
                        _add_finding(
                            findings,
                            "sense_parent_wrong_entry",
                            sid,
                            f"senses: parent_sense_id {pid!r} belongs to entry {senses[pid].get('entry_id')!r}, not {eid!r}",
                        )
                    parent_adj.setdefault(sid, []).append(pid)
        for cyclic_sid in sorted(_detect_cycles(parent_adj)):
            _add_finding(findings, "sense_parent_cycle", cyclic_sid, f"senses: sense {cyclic_sid!r} participates in a parent_sense_id cycle")

    if "texts" in tables:
        for row in tables["texts"]:
            tid = row.get("text_id", "")
            okind, oid = row.get("owner_kind"), row.get("owner_id")
            if okind == "entry":
                if ("entries" in tables and oid not in entries) or ("senses" in tables and oid in senses):
                    _add_finding(findings, "text_owner_mismatch", tid, f"texts: entry owner_id {oid!r} does not match an entry")
            elif okind == "sense":
                if ("senses" in tables and oid not in senses) or ("entries" in tables and oid in entries):
                    _add_finding(findings, "text_owner_mismatch", tid, f"texts: sense owner_id {oid!r} does not match a sense")

            if "assertions" in tables:
                aid = row.get("text_assertion_id")
                if aid not in assertions:
                    _add_finding(findings, "dangling_reference", tid, f"texts: unknown text_assertion_id {aid!r}")
                else:
                    asr = assertions[aid]
                    if asr.get("subject_kind") != "text" or asr.get("subject_id") != tid:
                        _add_finding(findings, "assertion_ownership_mismatch", tid, f"texts: text_assertion_id {aid!r} not owned by text {tid!r}")
                    if row.get("component") == "definition" and asr.get("value_state") == "known":
                        if not isinstance(asr.get("value_json"), str) or asr.get("value_json") == "":
                            _add_finding(findings, "empty_definition", tid, "texts: definition text cannot be empty")

            pair_id = row.get("paired_translation_id")
            if pair_id is not None:
                if pair_id not in texts:
                    _add_finding(findings, "dangling_reference", tid, f"texts: unknown paired_translation_id {pair_id!r}")
                elif pair_id == tid:
                    _add_finding(findings, "invalid_paired_translation", tid, "texts: paired_translation_id cannot reference self")
                else:
                    paired = texts[pair_id]
                    if paired.get("component") != "translation":
                        _add_finding(
                            findings,
                            "invalid_paired_translation",
                            tid,
                            f"texts: paired_translation_id {pair_id!r} has component {paired.get('component')!r}, expected 'translation'",
                        )
                    if paired.get("owner_kind") != okind or paired.get("owner_id") != oid:
                        _add_finding(
                            findings,
                            "paired_translation_owner_mismatch",
                            tid,
                            f"texts: paired translation {pair_id!r} belongs to ({paired.get('owner_kind')}, {paired.get('owner_id')!r})",
                        )


def _check_relations(
    tables: dict[str, list[dict]],
    indexes: dict[str, dict[str, dict]],
    dups: dict[str, set[str]],
    findings: list[dict],
) -> None:
    if "relations" not in tables:
        return
    entries = indexes.get("entries", {})
    senses = indexes.get("senses", {})
    relations = indexes["relations"]
    assertions = indexes.get("assertions", {})

    for row in tables["relations"]:
        rid = row.get("relation_id", "")
        for role_label, kind_col, id_col in (("source", "source_kind", "source_id"), ("target", "target_kind", "target_id")):
            ekind = row.get(kind_col)
            eid = row.get(id_col)
            if ekind == "entry":
                if ("entries" in tables and eid not in entries) or ("senses" in tables and eid in senses):
                    _add_finding(
                        findings,
                        "dangling_relation_endpoint",
                        rid,
                        f"relations: {role_label} entry_id {eid!r} not found (spelling-based target guessing is forbidden)",
                    )
                elif eid in dups.get("entries", ()):
                    _add_finding(findings, "non_unique_relation_endpoint", rid, f"relations: {role_label} entry_id {eid!r} is not unique")
            elif ekind == "sense":
                if ("senses" in tables and eid not in senses) or ("entries" in tables and eid in entries):
                    _add_finding(
                        findings,
                        "dangling_relation_endpoint",
                        rid,
                        f"relations: {role_label} sense_id {eid!r} not found (spelling-based target guessing is forbidden)",
                    )
                elif eid in dups.get("senses", ()):
                    _add_finding(findings, "non_unique_relation_endpoint", rid, f"relations: {role_label} sense_id {eid!r} is not unique")

        if "assertions" in tables:
            raid = row.get("relation_code_assertion_id")
            if raid not in assertions:
                _add_finding(findings, "dangling_reference", rid, f"relations: unknown relation_code_assertion_id {raid!r}")
            else:
                asr = assertions[raid]
                if asr.get("subject_kind") != "relation" or asr.get("subject_id") != rid:
                    _add_finding(
                        findings,
                        "assertion_ownership_mismatch",
                        rid,
                        f"relations: relation_code_assertion_id {raid!r} not owned by relation {rid!r}",
                    )

        inv_id = row.get("inverse_relation_id")
        if inv_id is not None:
            if inv_id not in relations:
                _add_finding(findings, "dangling_reference", rid, f"relations: unknown inverse_relation_id {inv_id!r}")
            elif inv_id == rid:
                _add_finding(findings, "invalid_inverse_relation", rid, "relations: inverse_relation_id cannot reference self")
            else:
                inv = relations[inv_id]
                swapped = (
                    inv.get("source_kind") == row.get("target_kind")
                    and inv.get("source_id") == row.get("target_id")
                    and inv.get("target_kind") == row.get("source_kind")
                    and inv.get("target_id") == row.get("source_id")
                )
                back_ok = inv.get("inverse_relation_id") in (None, rid)
                if not (swapped and inv.get("directionality") == row.get("directionality") and back_ok):
                    _add_finding(
                        findings,
                        "incompatible_inverse_relation",
                        rid,
                        f"relations: inverse_relation_id {inv_id!r} has incompatible endpoints, directionality, or inverse link",
                    )


def _check_assertions_evidence_decisions(
    tables: dict[str, list[dict]],
    indexes: dict[str, dict[str, dict]],
    findings: list[dict],
) -> None:
    assertions = indexes.get("assertions", {})
    sources = indexes.get("sources", {})
    records = indexes.get("source_records", {})
    decisions = indexes.get("decisions", {})

    for row in tables.get("assertions", ()):
        aid = row.get("assertion_id", "")
        vstate = row.get("value_state")
        vjson = row.get("value_json")
        if vstate in {"unknown", "not_applicable"} and vjson is not None:
            _add_finding(findings, "invalid_missing_value", aid, f"assertions: value_state {vstate!r} requires null value_json")
        elif vstate == "known" and vjson is None:
            _add_finding(findings, "invalid_missing_value", aid, "assertions: value_state 'known' cannot have null value_json")
        if row.get("property_code") in {"headword", "definition"} and vstate == "known":
            if not isinstance(vjson, str) or vjson == "":
                _add_finding(findings, "empty_required_text", aid, f"assertions: known {row.get('property_code')!r} cannot be empty")
        skind = row.get("subject_kind")
        sid = row.get("subject_id")
        target_table = ENTITY_TABLE_FOR_KIND.get(skind)
        if target_table and target_table in tables and sid not in indexes.get(target_table, {}):
            _add_finding(findings, "dangling_reference", aid, f"assertions: unknown {skind} subject_id {sid!r}")

    supporting_by_assertion: dict[str, list[dict]] = {}
    if "evidence" in tables:
        _check_composite_unique(
            tables["evidence"],
            ("assertion_id", "source_id", "source_record_id", "locator_json", "evidence_role"),
            "evidence",
            findings,
            "duplicate_evidence",
            "assertion_id",
        )
        for row in tables["evidence"]:
            aid = row.get("assertion_id", "")
            supporting_by_assertion.setdefault(aid, []).append(row)
            if "assertions" in tables and aid not in assertions:
                _add_finding(findings, "dangling_reference", aid, f"evidence: unknown assertion_id {aid!r}")
            if "sources" in tables and row.get("source_id") not in sources:
                _add_finding(findings, "dangling_reference", aid, f"evidence: unknown source_id {row.get('source_id')!r}")
            srid = row.get("source_record_id")
            if srid is not None and "source_records" in tables and srid not in records:
                _add_finding(findings, "dangling_reference", aid, f"evidence: unknown source_record_id {srid!r}")

    if "decisions" in tables:
        pred_adj: dict[str, list[str]] = {}
        for row in tables["decisions"]:
            did = row.get("decision_id", "")
            aid = row.get("assertion_id", "")
            if "assertions" in tables:
                if aid not in assertions:
                    _add_finding(findings, "dangling_reference", did, f"decisions: unknown assertion_id {aid!r}")
                else:
                    asr = assertions[aid]
                    if row.get("outcome") == "accepted_auto_source":
                        bad_auto = (
                            asr.get("origin") != "verbatim_source"
                            or asr.get("source_fidelity_state") != "verified"
                            or asr.get("ambiguity_state") != "unambiguous"
                        )
                        if bad_auto:
                            _add_finding(
                                findings,
                                "invalid_auto_acceptance",
                                did,
                                f"decisions: accepted_auto_source forbidden for assertion {aid!r} (origin={asr.get('origin')!r}, fidelity={asr.get('source_fidelity_state')!r}, ambiguity={asr.get('ambiguity_state')!r})",
                            )
                        elif "evidence" in tables and "sources" in tables:
                            has_verified_support = any(
                                ev.get("evidence_role") == "supports"
                                and sources.get(ev.get("source_id"), {}).get("evidence_verification_state") == "verified"
                                and sources.get(ev.get("source_id"), {}).get("reuse_state") == "permitted"
                                for ev in supporting_by_assertion.get(aid, ())
                            )
                            if not has_verified_support:
                                _add_finding(
                                    findings,
                                    "invalid_auto_acceptance",
                                    did,
                                    f"decisions: accepted_auto_source on {aid!r} lacks verified permitted supporting source",
                                )
            pred_id = row.get("predecessor_decision_id")
            if pred_id is not None:
                if pred_id not in decisions:
                    _add_finding(findings, "dangling_reference", did, f"decisions: unknown predecessor_decision_id {pred_id!r}")
                else:
                    if decisions[pred_id].get("assertion_id") != aid:
                        _add_finding(findings, "decision_predecessor_mismatch", did, f"decisions: predecessor {pred_id!r} targets different assertion")
                    pred_adj.setdefault(did, []).append(pred_id)
        for cyclic_did in sorted(_detect_cycles(pred_adj)):
            _add_finding(findings, "decision_cycle", cyclic_did, f"decisions: predecessor chain cycle involving {cyclic_did!r}")


def _check_changes_successors_findings_exceptions(
    tables: dict[str, list[dict]],
    indexes: dict[str, dict[str, dict]],
    findings: list[dict],
) -> None:
    assertions = indexes.get("assertions", {})
    decisions = indexes.get("decisions", {})
    changes = indexes.get("changes", {})
    identities = indexes.get("identities", {})
    records = indexes.get("source_records", {})

    for row in tables.get("changes", ()):
        cid = row.get("change_id", "")
        old_id, new_id = row.get("old_assertion_id"), row.get("new_assertion_id")
        if old_id is None and new_id is None:
            _add_finding(findings, "invalid_change_assertions", cid, "changes: old_assertion_id and new_assertion_id cannot both be null")
        if old_id is not None and new_id is not None and old_id == new_id:
            _add_finding(findings, "invalid_change_assertions", cid, "changes: old_assertion_id and new_assertion_id cannot be identical")
        if "assertions" in tables:
            for ref_id in (old_id, new_id):
                if ref_id is not None:
                    if ref_id not in assertions:
                        _add_finding(findings, "dangling_reference", cid, f"changes: unknown assertion {ref_id!r}")
                    elif assertions[ref_id].get("subject_id") != row.get("subject_id"):
                        _add_finding(findings, "change_subject_mismatch", cid, f"changes: assertion {ref_id!r} belongs to another subject")
        if "decisions" in tables and row.get("decision_id") not in decisions:
            _add_finding(findings, "dangling_reference", cid, f"changes: unknown decision_id {row.get('decision_id')!r}")
        inv_id = row.get("inverse_change_id")
        if inv_id is not None:
            if inv_id not in changes:
                _add_finding(findings, "dangling_reference", cid, f"changes: unknown inverse_change_id {inv_id!r}")
            elif inv_id == cid:
                _add_finding(findings, "invalid_inverse_change", cid, "changes: inverse_change_id cannot reference self")
            else:
                inv = changes[inv_id]
                if (
                    inv.get("subject_id") != row.get("subject_id")
                    or inv.get("old_assertion_id") != new_id
                    or inv.get("new_assertion_id") != old_id
                ):
                    _add_finding(findings, "incompatible_inverse_change", cid, f"changes: inverse_change_id {inv_id!r} is incompatible")

    if "successors" in tables:
        _check_composite_unique(
            tables["successors"], ("retired_id", "successor_id", "role"), "successors", findings, "duplicate_successor", "retired_id"
        )
        succ_adj: dict[str, list[str]] = {}
        for row in tables["successors"]:
            ret_id, succ_id = row.get("retired_id", ""), row.get("successor_id", "")
            succ_adj.setdefault(ret_id, []).append(succ_id)
            if "identities" in tables:
                if ret_id not in identities:
                    _add_finding(findings, "dangling_reference", ret_id, f"successors: unknown retired_id {ret_id!r}")
                else:
                    r_ident = identities[ret_id]
                    if r_ident.get("kind") not in {"entry", "sense"} or r_ident.get("lifecycle") not in {"retired", "merged", "split"}:
                        _add_finding(
                            findings,
                            "invalid_successor_identity",
                            ret_id,
                            f"successors: retired_id {ret_id!r} must be a retired/merged/split entry or sense",
                        )
                if succ_id not in identities:
                    _add_finding(findings, "dangling_reference", ret_id, f"successors: unknown successor_id {succ_id!r}")
                else:
                    s_ident = identities[succ_id]
                    if s_ident.get("kind") not in {"entry", "sense"}:
                        _add_finding(findings, "invalid_successor_identity", ret_id, f"successors: successor_id {succ_id!r} must be entry or sense")
                    elif ret_id in identities and identities[ret_id].get("kind") != s_ident.get("kind"):
                        _add_finding(findings, "successor_kind_mismatch", ret_id, "successors: retired_id and successor_id kinds differ")
        for cyclic_id in sorted(_detect_cycles(succ_adj)):
            _add_finding(findings, "successor_cycle", cyclic_id, f"successors: successor graph cycle involving {cyclic_id!r}")

    for row in tables.get("findings", ()):
        fid = row.get("finding_id", "")
        rid, aid = row.get("record_id"), row.get("assertion_id")
        if rid is None and aid is None:
            _add_finding(findings, "invalid_finding_target", fid, "findings: record_id and assertion_id cannot both be null")
        if rid is not None and "source_records" in tables and rid not in records:
            _add_finding(findings, "dangling_reference", fid, f"findings: unknown record_id {rid!r}")
        if aid is not None and "assertions" in tables and aid not in assertions:
            _add_finding(findings, "dangling_reference", fid, f"findings: unknown assertion_id {aid!r}")
        if row.get("status") in {"resolved", "excluded"} and not row.get("resolution_reason_json"):
            _add_finding(findings, "missing_resolution_reason", fid, f"findings: {row.get('status')!r} finding requires resolution_reason_json")

    if "unicode_exceptions" in tables:
        _check_composite_unique(
            tables["unicode_exceptions"],
            ("assertion_id", "claim_revision_sha256", "value_sha256", "kind", "scalar_position"),
            "unicode_exceptions",
            findings,
            "duplicate_unicode_exception",
            "assertion_id",
        )
        for row in tables["unicode_exceptions"]:
            aid = row.get("assertion_id", "")
            seq = row.get("scalar_sequence", [])
            pos = row.get("scalar_position", -1)
            if "assertions" in tables:
                if aid not in assertions:
                    _add_finding(findings, "dangling_reference", aid, f"unicode_exceptions: unknown assertion_id {aid!r}")
                else:
                    asr = assertions[aid]
                    if row.get("claim_revision_sha256") != asr.get("claim_revision_sha256"):
                        _add_finding(findings, "stale_unicode_exception", aid, f"unicode_exceptions: stale claim_revision_sha256 for {aid!r}")
                    elif asr.get("value_state") != "known" or not isinstance(asr.get("value_json"), str):
                        _add_finding(findings, "unused_unicode_exception", aid, f"unicode_exceptions: assertion {aid!r} has no known string value")
                    else:
                        text = asr["value_json"]
                        expected_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
                        if row.get("value_sha256") != expected_hash:
                            _add_finding(findings, "stale_unicode_exception", aid, f"unicode_exceptions: value_sha256 mismatch for {aid!r}")
                        elif (
                            not seq
                            or not isinstance(pos, int)
                            or pos < 0
                            or pos + len(seq) > len(text)
                            or any(not isinstance(cp, int) or 0xD800 <= cp <= 0xDFFF or cp < 0 or cp > 0x10FFFF for cp in seq)
                            or [ord(ch) for ch in text[pos : pos + len(seq)]] != seq
                        ):
                            _add_finding(
                                findings,
                                "unused_unicode_exception",
                                aid,
                                f"unicode_exceptions: scalar_sequence/position mismatch for {aid!r}",
                            )
                        elif row.get("kind") == "intentional_control" and not any(
                            is_intentional_control(cp) for cp in seq
                        ):
                            _add_finding(
                                findings,
                                "unused_unicode_exception",
                                aid,
                                f"unicode_exceptions: intentional_control on {aid!r} covers no control/format scalar",
                            )
                        elif row.get("kind") == "non_nfc_original":
                            seq_text = "".join(chr(cp) for cp in seq)
                            if native_inspect(text)["is_nfc"] or native_inspect(seq_text)["is_nfc"]:
                                _add_finding(
                                    findings,
                                    "unused_unicode_exception",
                                    aid,
                                    f"unicode_exceptions: non_nfc_original on {aid!r} is already NFC",
                                )
            if "decisions" in tables:
                did = row.get("decision_id", "")
                if did not in decisions:
                    _add_finding(findings, "dangling_reference", aid, f"unicode_exceptions: unknown decision_id {did!r}")
                else:
                    dec = decisions[did]
                    if (
                        dec.get("assertion_id") != aid
                        or dec.get("assertion_revision_sha256") != row.get("claim_revision_sha256")
                        or dec.get("outcome") not in ACCEPTED_OUTCOMES
                    ):
                        _add_finding(
                            findings,
                            "unapproved_unicode_exception",
                            aid,
                            f"unicode_exceptions: decision {did!r} does not accept exact revision of {aid!r}",
                        )


def _check_labels_scopes_pack_members(
    tables: dict[str, list[dict]],
    indexes: dict[str, dict[str, dict]],
    findings: list[dict],
) -> None:
    assertions = indexes.get("assertions", {})
    decisions = indexes.get("decisions", {})
    entries = indexes.get("entries", {})

    labels_by_code: dict[str, dict] = {}
    if "labels" in tables:
        _check_composite_unique(
            tables["labels"], ("registry_id", "registry_version", "code"), "labels", findings, "duplicate_label_code", "code"
        )
        labels_by_reg_code: dict[tuple[str, str, str], dict] = {}
        for row in tables["labels"]:
            rkey = (row.get("registry_id", ""), row.get("registry_version", ""), row.get("code", ""))
            labels_by_reg_code.setdefault(rkey, row)
            labels_by_code.setdefault(row.get("code", ""), row)
        label_adj: dict[str, list[str]] = {}
        for row in tables["labels"]:
            reg_id, reg_ver, code = row.get("registry_id", ""), row.get("registry_version", ""), row.get("code", "")
            pcode = row.get("parent_code")
            if pcode is not None:
                parent = labels_by_reg_code.get((reg_id, reg_ver, pcode))
                if parent is None:
                    _add_finding(findings, "dangling_reference", code, f"labels: unknown parent_code {pcode!r} in registry {reg_id!r}/{reg_ver!r}")
                else:
                    if parent.get("category") != row.get("category"):
                        _add_finding(
                            findings,
                            "label_parent_category_mismatch",
                            code,
                            f"labels: parent {pcode!r} has category {parent.get('category')!r}, expected {row.get('category')!r}",
                        )
                    label_adj.setdefault(f"{reg_id}:{reg_ver}:{code}", []).append(f"{reg_id}:{reg_ver}:{pcode}")
        for cyclic_node in sorted(_detect_cycles(label_adj)):
            _add_finding(findings, "label_parent_cycle", cyclic_node.rsplit(":", 1)[-1], f"labels: cyclic parent_code at {cyclic_node!r}")

    if "scopes" in tables:
        _check_composite_unique(
            tables["scopes"],
            ("subject_kind", "subject_id", "dimension", "state", "label_code"),
            "scopes",
            findings,
            "duplicate_scope",
            "subject_id",
        )
        states_by_subject_dim: dict[tuple[str, str, str], set[str]] = {}
        for row in tables["scopes"]:
            skind, sid = row.get("subject_kind", ""), row.get("subject_id", "")
            dim, state = row.get("dimension", ""), row.get("state", "")
            lcode = row.get("label_code")
            said, did = row.get("supporting_assertion_id"), row.get("decision_id")

            states_by_subject_dim.setdefault((skind, sid, dim), set()).add(state)
            target_table = ENTITY_TABLE_FOR_KIND.get(skind)
            if target_table and target_table in tables and sid not in indexes.get(target_table, {}):
                _add_finding(findings, "dangling_reference", sid, f"scopes: unknown {skind} subject_id {sid!r}")

            if (said is None) != (did is None):
                _add_finding(findings, "partial_scope_backing", sid, "scopes: backing assertion and decision must be provided together")
            if said is not None and "assertions" in tables and said in assertions:
                claim = assertions[said]
                if (claim.get("subject_kind"), claim.get("subject_id")) != (skind, sid):
                    _add_finding(findings, "scope_assertion_owner_mismatch", sid, "scopes: backing assertion belongs to another subject")
                allowed_properties = {f"{dim}_scope", "scope_attestation"}
                if dim == "period":
                    allowed_properties.add("temporal_scope")
                if claim.get("property_code") not in allowed_properties:
                    _add_finding(findings, "scope_assertion_property_mismatch", sid, "scopes: backing assertion property disagrees with dimension")
            if state == "unknown":
                if lcode is not None:
                    _add_finding(findings, "invalid_unknown_scope", sid, f"scopes: unknown {dim!r} scope cannot specify label_code {lcode!r}")

            if state == "unrestricted":
                if lcode is not None:
                    _add_finding(findings, "invalid_unrestricted_scope", sid, "scopes: unrestricted scope cannot specify label_code")
                if said is None or did is None:
                    _add_finding(
                        findings,
                        "unapproved_unrestricted_scope",
                        sid,
                        f"scopes: unrestricted {dim!r} scope requires supporting_assertion_id and accepted decision_id",
                    )
            elif state == "attested":
                if lcode is None:
                    _add_finding(findings, "missing_scope_label", sid, f"scopes: attested {dim!r} scope requires label_code")
                elif "labels" in tables:
                    if lcode not in labels_by_code:
                        _add_finding(findings, "dangling_reference", sid, f"scopes: unknown label_code {lcode!r}")
                    elif labels_by_code[lcode].get("category") != dim:
                        _add_finding(
                            findings,
                            "scope_label_category_mismatch",
                            sid,
                            f"scopes: label {lcode!r} has category {labels_by_code[lcode].get('category')!r}, expected {dim!r}",
                        )
                if said is None or did is None:
                    _add_finding(
                        findings,
                        "unapproved_attested_scope",
                        sid,
                        f"scopes: attested {dim!r} scope requires supporting_assertion_id and accepted decision_id",
                    )

            if said is not None and "assertions" in tables:
                if said not in assertions:
                    _add_finding(findings, "dangling_reference", sid, f"scopes: unknown supporting_assertion_id {said!r}")
                elif assertions[said].get("value_state") != "known":
                    _add_finding(
                        findings,
                        "unapproved_scope_unknown_assertion",
                        sid,
                        f"scopes: supporting_assertion_id {said!r} cannot have value_state {assertions[said].get('value_state')!r}",
                    )
            if did is not None and "decisions" in tables:
                if did not in decisions:
                    _add_finding(findings, "dangling_reference", sid, f"scopes: unknown decision_id {did!r}")
                else:
                    dec = decisions[did]
                    if dec.get("outcome") not in ACCEPTED_OUTCOMES:
                        _add_finding(
                            findings,
                            "unapproved_scope_decision",
                            sid,
                            f"scopes: decision {did!r} has outcome {dec.get('outcome')!r}, expected accepted decision",
                        )
                    elif said is not None and dec.get("assertion_id") != said:
                        _add_finding(
                            findings,
                            "unapproved_scope_decision",
                            sid,
                            f"scopes: decision {did!r} targets assertion {dec.get('assertion_id')!r}, not {said!r}",
                        )
                    elif said is not None and "assertions" in tables and said in assertions:
                        if dec.get("assertion_revision_sha256") != assertions[said].get("claim_revision_sha256"):
                            _add_finding(
                                findings,
                                "stale_scope_decision",
                                sid,
                                f"scopes: decision {did!r} does not match current revision of {said!r}",
                            )

        for (skind, sid, dim), states in sorted(states_by_subject_dim.items()):
            if len(states) > 1:
                _add_finding(
                    findings,
                    "conflicting_scope_states",
                    sid,
                    f"scopes: conflicting states {sorted(states)} for ({skind}, {sid!r}, {dim!r})",
                )

    if "pack_members" in tables:
        _check_composite_unique(
            tables["pack_members"], ("pack_id", "entry_id"), "pack_members", findings, "duplicate_pack_member", "entry_id"
        )
        revs_by_entry: dict[str, set[str]] = {}
        for row in tables["pack_members"]:
            eid = row.get("entry_id", "")
            rev = row.get("included_revision", "")
            revs_by_entry.setdefault(eid, set()).add(rev)
            if "entries" in tables:
                if eid not in entries:
                    _add_finding(findings, "dangling_reference", eid, f"pack_members: unknown entry_id {eid!r}")
                elif entries[eid].get("revision") != rev:
                    _add_finding(findings, "pack_member_revision_mismatch", eid, f"pack_members: revision mismatch for entry {eid!r}")
        for eid, revs in sorted(revs_by_entry.items()):
            if len(revs) > 1:
                _add_finding(findings, "conflicting_pack_revisions", eid, f"pack_members: conflicting revisions across packs for {eid!r}")


def validate_relations(tables: dict[str, list[dict]]) -> list[dict]:
    """Validate structural, relational, scope, disposition, and exception invariants across tables."""
    findings: list[dict] = []
    indexes: dict[str, dict[str, dict]] = {}
    dups: dict[str, set[str]] = {}

    if "identities" in tables:
        indexes["identities"], dups["identities"] = _index_unique(tables["identities"], "entity_id", "identities", findings)

    seen_global_ids: dict[str, str] = {}
    for table_name, id_col in PRIMARY_ID_COLS.items():
        if table_name not in tables:
            continue
        code = "duplicate_disposition" if table_name == "dispositions" else "duplicate_id"
        idx, dup_set = _index_unique(tables[table_name], id_col, table_name, findings, code=code)
        indexes[table_name] = idx
        dups[table_name] = dup_set
        if table_name == "dispositions":
            continue
        for id_val in idx:
            if id_val in seen_global_ids:
                _add_finding(
                    findings,
                    "duplicate_id",
                    id_val,
                    f"global ID collision for {id_val!r} across {seen_global_ids[id_val]} and {table_name}",
                )
            else:
                seen_global_ids[id_val] = table_name

    _check_intake_and_accounting(tables, indexes, findings)
    _check_entries_and_forms(tables, indexes, findings)
    _check_senses_and_texts(tables, indexes, findings)
    _check_relations(tables, indexes, dups, findings)
    _check_assertions_evidence_decisions(tables, indexes, findings)
    _check_changes_successors_findings_exceptions(tables, indexes, findings)
    _check_labels_scopes_pack_members(tables, indexes, findings)

    return sorted(findings, key=lambda item: (item["severity"], item["code"], item["subject_id"], item["reason"]))
