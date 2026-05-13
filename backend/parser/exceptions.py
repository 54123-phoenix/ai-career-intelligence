"""Parser-specific exceptions."""

from __future__ import annotations


class ParseError(Exception):
    """Raised when all parsing strategies (LLM + fallback) fail."""


class PDFExtractionError(ParseError):
    """Raised when PDF text extraction fails."""


class SchemaValidationError(ParseError):
    """Raised when parsed data fails Pydantic validation."""
