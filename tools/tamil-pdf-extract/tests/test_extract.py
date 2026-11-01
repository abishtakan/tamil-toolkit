from __future__ import annotations

import sys
from pathlib import Path

from pypdf import PdfWriter
from pypdf.generic import (
    ArrayObject,
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
    NumberObject,
    TextStringObject,
)

from tamil_pdf_extract import cli
from tamil_pdf_extract import extract_pdf
from tamil_pdf_extract import ocr


def _font(writer: PdfWriter, *, basefont: str, subtype: str = "/Type0", encoding: str = "/Identity-H"):
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject(subtype),
            NameObject("/BaseFont"): NameObject(basefont),
            NameObject("/Encoding"): NameObject(encoding),
        }
    )
    if subtype == "/Type0":
        descendant = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/CIDFontType2"),
                NameObject("/BaseFont"): NameObject(basefont),
                NameObject("/CIDSystemInfo"): DictionaryObject(
                    {
                        NameObject("/Registry"): TextStringObject("Adobe"),
                        NameObject("/Ordering"): TextStringObject("Identity"),
                        NameObject("/Supplement"): NumberObject(0),
                    }
                ),
            }
        )
        font[NameObject("/DescendantFonts")] = ArrayObject([writer._add_object(descendant)])
    return writer._add_object(font)


def _resources(writer: PdfWriter, font_ref, *, xobjects: dict[str, object] | None = None):
    resources = DictionaryObject(
        {
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref}),
        }
    )
    if xobjects:
        resources[NameObject("/XObject")] = DictionaryObject(
            {NameObject(name): reference for name, reference in xobjects.items()}
        )
    return resources


def _write_pdf(
    tmp_path: Path,
    content: bytes,
    *,
    basefont: str = "/AAAAAA+LT-TM-Nila,Bold",
    subtype: str = "/Type0",
    encoding: str = "/Identity-H",
    xobjects: dict[str, object] | None = None,
) -> Path:
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    font_ref = _font(writer, basefont=basefont, subtype=subtype, encoding=encoding)
    page[NameObject("/Resources")] = _resources(writer, font_ref, xobjects=xobjects)
    stream = DecodedStreamObject()
    stream.set_data(content)
    page[NameObject("/Contents")] = writer._add_object(stream)
    path = tmp_path / "fixture.pdf"
    with path.open("wb") as output:
        writer.write(output)
    return path


def test_decodes_all_text_operators_and_joins_tj_fragments(tmp_path):
    path = _write_pdf(
        tmp_path,
        b"BT /F1 12 Tf <0023> Tj <0023> ' 0 0 <0023> \" [<0023> -40 <0026>] TJ ET",
    )

    records = extract_pdf(path, profile="lt-tm")
    runs = [record for record in records if record["record"] == "text"]

    assert [run["operator"] for run in runs] == ["Tj", "'", '"', "TJ"]
    assert [run["text"] for run in runs] == [
        "\u0b9c",
        "\u0b9c",
        "\u0b9c",
        "\u0b9c\u0bc1",
    ]
    assert runs[-1]["codes"] == [0x0023, 0x0026]
    assert runs[-1]["raw_hex"] == "00230026"
    assert all(run["status"] == "decoded" for run in runs)


def test_non_lt_font_is_preserved_without_codec_attempt(tmp_path):
    path = _write_pdf(
        tmp_path,
        b"BT /F1 12 Tf <0041> Tj ET",
        basefont="/Courier",
        subtype="/Type1",
        encoding="/WinAnsiEncoding",
    )

    run = next(record for record in extract_pdf(path, profile="lt-tm") if record["record"] == "text")

    assert run["status"] == "unsupported_font"
    assert run["font"]["basefont"] == "/Courier"
    assert run["raw_hex"] == "0041"
    assert run["text"] is None


def test_unverified_lt_tm_family_is_not_assumed_compatible(tmp_path):
    path = _write_pdf(tmp_path, b"BT /F1 12 Tf <0023> Tj ET", basefont="/AAAAAA+LT-TM-Roja")

    run = next(record for record in extract_pdf(path, profile="lt-tm") if record["record"] == "text")

    assert run["status"] == "unsupported_font"
    assert run["raw_hex"] == "0023"
    assert run["text"] is None


def test_odd_identity_h_byte_is_not_truncated(tmp_path):
    path = _write_pdf(tmp_path, b"BT /F1 12 Tf <002300> Tj ET")

    run = next(record for record in extract_pdf(path, profile="lt-tm") if record["record"] == "text")

    assert run["status"] == "malformed_identity_h"
    assert run["codes"] is None
    assert run["raw_hex"] == "002300"
    assert "odd-length" in run["error"]


def test_surrogate_code_unit_retains_raw_bytes_on_codec_error(tmp_path):
    path = _write_pdf(tmp_path, b"BT /F1 12 Tf <D800> Tj ET")

    run = next(record for record in extract_pdf(path, profile="lt-tm") if record["record"] == "text")

    assert run["status"] == "decode_error"
    assert run["raw_hex"] == "d800"
    assert run["codes"] == [0xD800]
    assert run["error"]


def test_form_uses_its_font_resources_and_page_summary_counts_images(tmp_path):
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    font_ref = _font(writer, basefont="/LT-TM-Narmada")

    form = DecodedStreamObject()
    form.set_data(b"BT /F1 12 Tf <0023> Tj ET")
    form[NameObject("/Type")] = NameObject("/XObject")
    form[NameObject("/Subtype")] = NameObject("/Form")
    form[NameObject("/BBox")] = ArrayObject([NumberObject(0), NumberObject(0), NumberObject(20), NumberObject(20)])
    form[NameObject("/Resources")] = _resources(writer, font_ref)
    form_ref = writer._add_object(form)

    image = DecodedStreamObject()
    image.set_data(b"\x00")
    image[NameObject("/Type")] = NameObject("/XObject")
    image[NameObject("/Subtype")] = NameObject("/Image")
    image[NameObject("/Width")] = NumberObject(1)
    image[NameObject("/Height")] = NumberObject(1)
    image[NameObject("/ColorSpace")] = NameObject("/DeviceGray")
    image[NameObject("/BitsPerComponent")] = NumberObject(8)
    image_ref = writer._add_object(image)

    page[NameObject("/Resources")] = _resources(
        writer,
        font_ref,
        xobjects={"/Fm1": form_ref, "/Im1": image_ref},
    )
    stream = DecodedStreamObject()
    stream.set_data(b"/Fm1 Do /Im1 Do BI /W 1 /H 1 /BPC 8 /CS /G ID \x00 EI")
    page[NameObject("/Contents")] = writer._add_object(stream)
    path = tmp_path / "form.pdf"
    with path.open("wb") as output:
        writer.write(output)

    records = extract_pdf(path, profile="lt-tm")
    run = next(record for record in records if record["record"] == "text")
    summary = next(record for record in records if record["record"] == "page_summary")

    assert run["text"] == "\u0b9c"
    assert run["content_path"] == ["page:1", "form:/Fm1"]
    assert summary["form_xobjects"] == 1
    assert summary["image_xobjects"] == 1
    assert summary["inline_images"] == 1


def test_form_cycle_is_counted_and_terminated(tmp_path):
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    font_ref = _font(writer, basefont="/LT-TM-Narmada")

    form = DecodedStreamObject()
    form.set_data(b"/Loop Do")
    form[NameObject("/Type")] = NameObject("/XObject")
    form[NameObject("/Subtype")] = NameObject("/Form")
    form[NameObject("/BBox")] = ArrayObject([NumberObject(0), NumberObject(0), NumberObject(20), NumberObject(20)])
    form[NameObject("/Resources")] = _resources(writer, font_ref)
    form_ref = writer._add_object(form)
    form_resources = form_ref.get_object()[NameObject("/Resources")]
    form_resources[NameObject("/XObject")] = DictionaryObject({NameObject("/Loop"): form_ref})

    page[NameObject("/Resources")] = _resources(
        writer,
        font_ref,
        xobjects={"/Fm1": form_ref},
    )
    stream = DecodedStreamObject()
    stream.set_data(b"/Fm1 Do")
    page[NameObject("/Contents")] = writer._add_object(stream)
    path = tmp_path / "cycle.pdf"
    with path.open("wb") as output:
        writer.write(output)

    summary = next(
        record for record in extract_pdf(path, profile="lt-tm") if record["record"] == "page_summary"
    )

    assert summary["form_xobjects"] == 2
    assert summary["form_cycles"] == 1


def test_rejects_encrypted_pdf(tmp_path):
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.encrypt("secret")
    path = tmp_path / "encrypted.pdf"
    with path.open("wb") as output:
        writer.write(output)

    try:
        extract_pdf(path, profile="lt-tm")
    except ValueError as error:
        assert "encrypted PDFs are not supported" in str(error)
    else:
        raise AssertionError("encrypted PDF was accepted")


def test_rejects_invalid_pdf_with_diagnostic(tmp_path):
    path = tmp_path / "invalid.pdf"
    path.write_bytes(b"not a PDF")

    try:
        extract_pdf(path, profile="lt-tm")
    except ValueError as error:
        assert "could not read PDF" in str(error)
    else:
        raise AssertionError("invalid PDF was accepted")


def test_cli_escapes_decoded_unicode_in_jsonl(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "extract_pdf",
        lambda _path, *, profile: [{"record": "text", "text": "\u0b9c"}],
    )
    monkeypatch.setattr(sys, "argv", ["tamil-pdf-extract", "fixture.pdf", "--profile", "lt-tm"])

    assert cli.main() == 0
    output = capsys.readouterr().out
    assert "\\u0b9c" in output
    assert "\u0b9c" not in output


def test_ocr_markdown_keeps_page_boundaries_and_joiners(monkeypatch, tmp_path):
    zwnj = chr(0x200C)
    zwj = chr(0x200D)
    monkeypatch.setattr(
        ocr,
        "_render_pdf_pages",
        lambda _path, *, dpi: iter([(1, b"page-one"), (2, b"page-two")]),
    )
    monkeypatch.setattr(
        ocr,
        "_recognize_page",
        lambda image, **_kwargs: "text" + zwnj if image == b"page-one" else "text" + zwj,
    )

    markdown = ocr.ocr_pdf_to_markdown(tmp_path / "input.pdf", dpi=300)

    assert "Source: input.pdf" in markdown
    assert "Tesseract language: tam; render resolution: 300 DPI." in markdown
    assert "## PDF page 1\n\n" + "text" + zwnj in markdown
    assert "## PDF page 2\n\n" + "text" + zwj in markdown


def test_ocr_rejects_out_of_range_dpi(tmp_path):
    try:
        ocr.ocr_pdf_to_markdown(tmp_path / "input.pdf", dpi=1000)
    except ValueError as error:
        assert "between 72 and 600" in str(error)
    else:
        raise AssertionError("out-of-range OCR DPI was accepted")


def test_cli_writes_requested_ocr_markdown(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(
        cli,
        "extract_pdf",
        lambda _path, *, profile: [{"record": "page_summary", "page": 1}],
    )
    monkeypatch.setattr(cli, "ocr_pdf_to_markdown", lambda *_args, **_kwargs: "# OCR draft\n")
    output_path = tmp_path / "review.md"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tamil-pdf-extract",
            "fixture.pdf",
            "--profile",
            "lt-tm",
            "--ocr-markdown",
            str(output_path),
        ],
    )

    assert cli.main() == 0
    assert output_path.read_text(encoding="utf-8") == "# OCR draft\n"
    assert '"record":"page_summary"' in capsys.readouterr().out
