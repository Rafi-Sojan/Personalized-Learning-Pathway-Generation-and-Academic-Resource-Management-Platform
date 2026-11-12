
from types import SimpleNamespace

import pytest

from app.services import document_processing as dp


def test_mixed_pdf_ocr_only_scanned_page(tmp_path, monkeypatch):
    fitz = pytest.importorskip("fitz")

    upload = tmp_path / "mixed.pdf"
    output = tmp_path / "processed.txt"

    document = fitz.open()

    first = document.new_page()
    first.insert_text(
        (72, 72),
        "Unit 1: Introduction to Artificial Intelligence",
    )

    document.new_page()  # Represents a scanned, non-text page.
    document.save(upload)
    document.close()

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

    called = []

    def fake_ocr(path, page_numbers, max_chars):
        called.extend(page_numbers)
        return {2: "Unit 2: Search Algorithms"}

    monkeypatch.setattr(dp, "run_pdf_ocr_pages", fake_ocr)

    dp.process_pdf(upload, output)

    text = output.read_text(encoding="utf-8")

    assert called == [2]
    assert "[[PAGE 1]]" in text
    assert "[[PAGE 2]]" in text
    assert "Introduction to Artificial Intelligence" in text
    assert "Unit 2: Search Algorithms" in text
