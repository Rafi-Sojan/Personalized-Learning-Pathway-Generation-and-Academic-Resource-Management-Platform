
from types import SimpleNamespace

import pytest

from app.services import document_processing as dp



def test_mixed_pdf_ocr_only_scanned_page(tmp_path, monkeypatch):
    """Verify that only pages without extractable text receive OCR."""

    fitz = pytest.importorskip("fitz")

    upload = tmp_path / "mixed.pdf"
    output = tmp_path / "processed.txt"

    # Step 1: Create a two-page test PDF.
    document = fitz.open()

    first = document.new_page()
    first.insert_text(
        (72, 72),
        "Unit 1: Introduction to Artificial Intelligence",
    )

    # Page 2 contains no selectable text.
    document.new_page()

    document.save(str(upload))
    document.close()

    # Step 2: Configure processing limits.
    monkeypatch.setattr(
        dp,
        "settings",
        SimpleNamespace(
            max_upload_bytes=25 * 1024 * 1024,
            max_pdf_pages=200,
            max_extracted_text_chars=10000,
            ocr_enabled=True,
        ),
    )

    # Step 3: Mock OCR to avoid requiring Tesseract.
    called: list[int] = []

    def fake_ocr(path, page_numbers, max_chars):
        """Return synthetic OCR text and track selected pages."""
        called.extend(page_numbers)
        return {2: "Unit 2: Search Algorithms"}

    monkeypatch.setattr(
        dp,
        "run_pdf_ocr_pages",
        fake_ocr,
    )

    # Step 4: Process the PDF.
    dp.process_pdf(upload, output)

    text = output.read_text(encoding="utf-8")

    # Step 5: Verify selective OCR.
    assert called == [2]

    # Verify both page markers are preserved.
    assert "[[PAGE 1]]" in text
    assert "[[PAGE 2]]" in text

    # Verify both extraction methods contribute text.
    assert "Introduction to Artificial Intelligence" in text
    assert "Unit 2: Search Algorithms" in text
