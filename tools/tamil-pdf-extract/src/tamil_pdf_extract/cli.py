"""Command-line entry point for local PDF extraction."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .extract import extract_pdf
from .ocr import ocr_pdf_to_markdown


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract LT-TM Identity-H text runs from a PDF")
    parser.add_argument("pdf", type=Path, help="local PDF file to inspect")
    parser.add_argument("--profile", choices=("lt-tm",), required=True, help="font mapping profile")
    parser.add_argument(
        "--ocr-markdown",
        type=Path,
        help="write an optional, page-numbered Tamil OCR draft to this Markdown path",
    )
    parser.add_argument(
        "--ocr-language",
        default="tam",
        help="installed Tesseract language code for --ocr-markdown (default: tam)",
    )
    parser.add_argument(
        "--ocr-dpi",
        type=int,
        default=300,
        help="PDF render resolution for --ocr-markdown, from 72 to 600 (default: 300)",
    )
    parser.add_argument(
        "--tesseract",
        default="tesseract",
        help="Tesseract executable for --ocr-markdown (default: tesseract on PATH)",
    )
    args = parser.parse_args()

    try:
        records = extract_pdf(args.pdf, profile=args.profile)
        if args.ocr_markdown is not None:
            markdown = ocr_pdf_to_markdown(
                args.pdf,
                tesseract_executable=args.tesseract,
                language=args.ocr_language,
                dpi=args.ocr_dpi,
            )
            args.ocr_markdown.write_text(markdown, encoding="utf-8", newline="\n")
    except (OSError, ValueError) as error:
        print(f"tamil-pdf-extract: {error}", file=sys.stderr)
        return 2
    except RuntimeError as error:
        print(f"tamil-pdf-extract: {error}", file=sys.stderr)
        return 2

    for record in records:
        print(json.dumps(record, ensure_ascii=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
