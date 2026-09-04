"""Deterministic validation for uploaded notice documents."""
from __future__ import annotations

import io
from dataclasses import dataclass

from pypdf import PdfReader

MAX_PDF_BYTES = 10 * 1024 * 1024


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    code: str | None = None
    message: str | None = None
    reader: PdfReader | None = None


def validate_pdf(content: bytes, filename: str | None, content_type: str | None) -> ValidationResult:
    if content_type != "application/pdf" and not (filename or "").lower().endswith(".pdf"):
        return ValidationResult(False, "invalid_file_type", "Only PDF files are accepted.")
    if len(content) > MAX_PDF_BYTES:
        return ValidationResult(False, "file_too_large", "The PDF exceeds the 10 MB processing limit.")
    if not content:
        return ValidationResult(False, "empty_pdf", "The uploaded PDF is empty.")
    if not content.lstrip().startswith(b"%PDF-"):
        return ValidationResult(False, "invalid_pdf", "The file is not a valid PDF document.")
    try:
        reader = PdfReader(io.BytesIO(content), strict=False)
        if reader.is_encrypted:
            try:
                if reader.decrypt("") == 0:
                    return ValidationResult(False, "password_protected_pdf", "This PDF is password-protected.")
            except Exception:
                return ValidationResult(False, "password_protected_pdf", "This PDF is password-protected.")
        if len(reader.pages) == 0:
            return ValidationResult(False, "empty_pdf", "The PDF has no pages.")
        return ValidationResult(True, reader=reader)
    except Exception:
        return ValidationResult(False, "invalid_pdf", "The PDF could not be read safely.")

