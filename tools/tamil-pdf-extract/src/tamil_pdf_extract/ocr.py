"""Optional page-level OCR draft generation for PDFs with unmapped fonts."""

from __future__ import annotations

import io
import subprocess
from collections.abc import Iterator
from pathlib import Path


def _render_pdf_pages(pdf_path: str | Path, *, dpi: int) -> Iterator[tuple[int, bytes]]:
    try:
        import pypdfium2
    except ImportError as error:
        raise RuntimeError(
            "PDF OCR rendering requires the optional dependencies; "
            "install with uv sync --project tools/tamil-pdf-extract --extra ocr"
        ) from error

    document = pypdfium2.PdfDocument(str(pdf_path))
    try:
        for page_number in range(len(document)):
            page = document[page_number]
            bitmap = page.render(scale=dpi / 72)
            try:
                image = bitmap.to_pil()
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                yield page_number + 1, buffer.getvalue()
            finally:
                bitmap.close()
                page.close()
    finally:
        document.close()


def _recognize_page(
    image_png: bytes,
    *,
    tesseract_executable: str,
    language: str,
) -> str:
    try:
        result = subprocess.run(
            [
                tesseract_executable,
                "stdin",
                "stdout",
                "-l",
                language,
                "--psm",
                "3",
            ],
            input=image_png,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise RuntimeError(f"could not start Tesseract: {error}") from error

    if result.returncode:
        diagnostic = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(
            f"Tesseract failed with exit code {result.returncode}"
            + (f": {diagnostic}" if diagnostic else "")
        )

    try:
        text = result.stdout.decode("utf-8")
    except UnicodeDecodeError as error:
        raise RuntimeError("Tesseract returned invalid UTF-8") from error

    # Keep all recognized scalars, including joiners. Remove only page-ending
    # control characters emitted by Tesseract.
    return text.rstrip("\f\r\n")


def ocr_pdf_to_markdown(
    pdf_path: str | Path,
    *,
    tesseract_executable: str = "tesseract",
    language: str = "tam",
    dpi: int = 300,
) -> str:
    """Return a page-ordered OCR draft; OCR output is not verified text."""

    if not language or any(character.isspace() for character in language):
        raise ValueError("OCR language must be a non-empty Tesseract language code")
    if not 72 <= dpi <= 600:
        raise ValueError("OCR DPI must be between 72 and 600")

    lines = [
        "# OCR transcription draft",
        "",
        f"Source: {Path(pdf_path).name}",
        f"Tesseract language: {language}; render resolution: {dpi} DPI.",
        "",
        "Machine-generated page text for human verification. It is not a",
        "validated transcription. Compare each page against the source PDF.",
        "OCR scalars, including joiners, are preserved as returned by Tesseract.",
        "",
    ]
    for page_number, image_png in _render_pdf_pages(pdf_path, dpi=dpi):
        text = _recognize_page(
            image_png,
            tesseract_executable=tesseract_executable,
            language=language,
        )
        lines.extend(
            [
                f"## PDF page {page_number}",
                "",
                text if text else "_No text recognized._",
                "",
            ]
        )
    return "\n".join(lines)
