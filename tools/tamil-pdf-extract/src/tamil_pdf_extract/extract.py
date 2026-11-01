"""Font-aware text-run extraction for the bounded LT-TM Identity-H profile."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import tamil_toolkit
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from pypdf.generic import (
    ArrayObject,
    ByteStringObject,
    ContentStream,
    DictionaryObject,
    IndirectObject,
    TextStringObject,
)

_BASEFONT_FAMILY = re.compile(r"(?:[A-Z]{6}\+)?(LT-TM-[A-Za-z0-9_.,-]+)\Z")
_VISUALLY_CHECKED_FAMILIES = frozenset(
    {
        "LT-TM-Nehru",
        "LT-TM-Nakkeran",
        "LT-TM-Narmada",
        "LT-TM-Nila,Bold",
        "LT-TM-Sindhu",
    }
)
_TEXT_OPERATORS = {b"Tj", b"TJ", b"'", b'"'}


def _resolve(value: Any) -> Any:
    if isinstance(value, IndirectObject):
        return value.get_object()
    return value


def _name(value: Any) -> str | None:
    value = _resolve(value)
    if value is None:
        return None
    return str(value)


def _string_bytes(value: Any) -> bytes | None:
    if isinstance(value, (ByteStringObject, TextStringObject)):
        return bytes(value.original_bytes)
    return None


def _text_bytes(operands: list[Any], operator: bytes) -> bytes:
    if operator == b"TJ":
        if not operands or not isinstance(operands[-1], ArrayObject):
            return b""
        parts = (_string_bytes(item) for item in operands[-1])
        return b"".join(part for part in parts if part is not None)

    value = operands[-1] if operands else None
    return _string_bytes(value) or b""


def _object_key(reference: Any, obj: Any) -> tuple[Any, ...]:
    if isinstance(reference, IndirectObject):
        return ("ref", reference.idnum, reference.generation)
    return ("obj", id(obj))


def _font(resources: Any, resource_name: str | None) -> dict[str, Any] | None:
    if resource_name is None:
        return None
    resources = _resolve(resources)
    if not isinstance(resources, DictionaryObject):
        return None
    fonts = _resolve(resources.get("/Font"))
    if not isinstance(fonts, DictionaryObject):
        return None
    reference = fonts.get(resource_name)
    font = _resolve(reference)
    if not isinstance(font, DictionaryObject):
        return None

    basefont = _name(font.get("/BaseFont"))
    family = basefont.removeprefix("/") if basefont else ""
    family_match = _BASEFONT_FAMILY.fullmatch(family)
    subtype = _name(font.get("/Subtype"))
    encoding = _name(font.get("/Encoding"))
    return {
        "resource": resource_name,
        "basefont": basefont,
        "subtype": subtype,
        "encoding": encoding,
        "supported": (
            subtype == "/Type0"
            and encoding == "/Identity-H"
            and family_match is not None
            and family_match.group(1) in _VISUALLY_CHECKED_FAMILIES
        ),
    }


def _page_summary(page_number: int) -> dict[str, Any]:
    return {
        "record": "page_summary",
        "page": page_number,
        "text_runs": 0,
        "runs_by_status": {},
        "form_xobjects": 0,
        "image_xobjects": 0,
        "inline_images": 0,
        "form_cycles": 0,
    }


def _count_run(summary: dict[str, Any], status: str) -> None:
    summary["text_runs"] += 1
    counts = summary["runs_by_status"]
    counts[status] = counts.get(status, 0) + 1


def extract_pdf(pdf_path: str | Path, *, profile: str) -> list[dict[str, Any]]:
    """Return ordered text-run and page-summary records from a local PDF.

    The caller must explicitly select ``profile="lt-tm"``. Conversion uses
    the existing Rust-backed ``tamil_toolkit`` dispatcher.
    """

    if profile != "lt-tm":
        raise ValueError("unsupported PDF font profile; supported profile is lt-tm")

    path = Path(pdf_path)
    if not path.is_file():
        raise ValueError(f"PDF path is not a file: {path}")

    try:
        reader = PdfReader(path)
    except PdfReadError as error:
        raise ValueError(f"could not read PDF: {error}") from error
    if reader.is_encrypted:
        raise ValueError("encrypted PDFs are not supported")

    try:
        pages = reader.pages
    except PdfReadError as error:
        raise ValueError(f"could not read PDF pages: {error}") from error

    records: list[dict[str, Any]] = []

    for page_number, page in enumerate(pages, start=1):
        summary = _page_summary(page_number)
        page_records: list[dict[str, Any]] = []

        def walk_stream(
            stream: Any,
            resources: Any,
            content_path: list[str],
            form_stack: frozenset[tuple[Any, ...]],
        ) -> None:
            try:
                operations = ContentStream(stream, reader).operations
            except Exception as error:
                raise ValueError(
                    f"could not parse content stream at {'/'.join(content_path)}: {error}"
                ) from error

            current_font: str | None = None
            font_stack: list[str | None] = []

            for operator_index, (operands, operator) in enumerate(operations):
                if operator == b"q":
                    font_stack.append(current_font)
                    continue
                if operator == b"Q":
                    if font_stack:
                        current_font = font_stack.pop()
                    continue
                if operator == b"Tf":
                    current_font = _name(operands[-2]) if len(operands) >= 2 else None
                    continue
                if operator == b"INLINE IMAGE":
                    summary["inline_images"] += 1
                    continue

                if operator in _TEXT_OPERATORS:
                    font = _font(resources, current_font)
                    raw = _text_bytes(operands, operator)
                    codes: list[int] | None = None
                    error_text: str | None = None
                    decoded: str | None = None
                    is_identity_h = font is not None and font["encoding"] == "/Identity-H"

                    if is_identity_h and len(raw) % 2:
                        status = "malformed_identity_h"
                        error_text = "odd-length byte string for Identity-H font"
                    else:
                        if is_identity_h:
                            codes = [
                                int.from_bytes(raw[offset : offset + 2], "big")
                                for offset in range(0, len(raw), 2)
                            ]
                        if font is None:
                            status = "missing_font"
                            error_text = "no resolvable font resource is selected"
                        elif not font["supported"]:
                            status = "unsupported_font"
                        else:
                            try:
                                decoded = tamil_toolkit.execute(
                                    {"op": "lt_tm_codes_to_unicode", "input": {"codes": codes}}
                                )
                                status = "decoded"
                            except ValueError as error:
                                status = "decode_error"
                                error_text = str(error)

                    run = {
                        "record": "text",
                        "page": page_number,
                        "content_path": list(content_path),
                        "operator_index": operator_index,
                        "operator": operator.decode("ascii"),
                        "font": font,
                        "raw_hex": raw.hex(),
                        "codes": codes,
                        "status": status,
                        "text": decoded,
                        "error": error_text,
                    }
                    _count_run(summary, status)
                    page_records.append(run)
                    continue

                if operator != b"Do" or not operands:
                    continue

                xobject_name = _name(operands[-1])
                resource_dict = _resolve(resources)
                xobjects = (
                    _resolve(resource_dict.get("/XObject"))
                    if isinstance(resource_dict, DictionaryObject)
                    else None
                )
                if not isinstance(xobjects, DictionaryObject) or xobject_name is None:
                    continue
                reference = xobjects.get(xobject_name)
                xobject = _resolve(reference)
                if not isinstance(xobject, DictionaryObject):
                    continue

                subtype = _name(xobject.get("/Subtype"))
                if subtype == "/Image":
                    summary["image_xobjects"] += 1
                elif subtype == "/Form":
                    summary["form_xobjects"] += 1
                    key = _object_key(reference, xobject)
                    if key in form_stack:
                        summary["form_cycles"] += 1
                        continue
                    form_resources = xobject.get("/Resources")
                    if form_resources is None:
                        form_resources = resources
                    walk_stream(
                        xobject,
                        form_resources,
                        [*content_path, f"form:{xobject_name}"],
                        form_stack | {key},
                    )

        page_resources = page.get("/Resources")
        if page_resources is None:
            page_resources = DictionaryObject()
        try:
            page_contents = page.get_contents()
        except PdfReadError as error:
            raise ValueError(f"could not read page {page_number} content: {error}") from error
        if page_contents is not None:
            walk_stream(page_contents, page_resources, [f"page:{page_number}"], frozenset())

        records.extend(page_records)
        records.append(summary)

    return records
