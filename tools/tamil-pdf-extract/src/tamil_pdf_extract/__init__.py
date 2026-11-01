"""PDF text extraction that delegates LT-TM conversion to the Rust toolkit."""

from .extract import extract_pdf

__all__ = ["extract_pdf"]
