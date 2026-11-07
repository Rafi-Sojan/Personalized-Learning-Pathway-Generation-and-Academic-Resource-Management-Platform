"""Bounded text extraction for local preprocessing and offline evaluation."""

from __future__ import annotations

from pathlib import Path


def extract_text(
    path: str | Path,
    *,
    max_bytes: int = 25 * 1024 * 1024,
    max_pages: int = 200,
    max_chars: int = 500_000,
) -> str:
    """Extract page-marked text from a bounded plain-text or PDF source.

    The caller remains responsible for private storage and malware controls. This
    utility rejects encrypted or oversized PDFs, preserves page coordinates, and
    never invokes OCR implicitly; image-only files must use the explicit OCR path.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise ValueError(f"document does not exist: {file_path}")
    if file_path.stat().st_size > max_bytes:
        raise ValueError("document exceeds the configured byte limit")
    if file_path.suffix.lower() in {".txt", ".md", ".csv"}:
        return file_path.read_text(encoding="utf-8", errors="replace")[:max_chars]
    if file_path.suffix.lower() != ".pdf":
        raise ValueError("unsupported document type")
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("PDF extraction requires the backend pypdf dependency") from exc
    try:
        reader = PdfReader(str(file_path), strict=False)
        if reader.is_encrypted:
            raise ValueError("encrypted PDFs are not supported")
        if len(reader.pages) > max_pages:
            raise ValueError("PDF exceeds the configured page limit")
        chunks: list[str] = []
        total = 0
        for page_number, page in enumerate(reader.pages, start=1):
            marker = f"[[PAGE {page_number}]]\n"
            separator_length = 1 if chunks else 0
            remaining = max_chars - total - separator_length - len(marker)
            if remaining <= 0:
                break
            page_text = (page.extract_text() or "")[:remaining]
            chunks.append(f"{marker}{page_text}")
            total += separator_length + len(marker) + len(page_text)
        return "\n".join(chunks)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("PDF could not be read safely") from exc
