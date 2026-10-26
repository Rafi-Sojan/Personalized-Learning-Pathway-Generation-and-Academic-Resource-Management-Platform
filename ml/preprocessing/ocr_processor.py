def normalize_ocr_text(text: str) -> str:
    return " ".join(text.replace("\u00ad", "").split())


def run_pdf_ocr(path: str, max_chars: int) -> str:
    """OCR image-only PDF pages using the optional Tesseract provider."""
    try:
        import fitz
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("OCR provider is not installed; install backend/requirements-ocr.txt") from exc
    document = fitz.open(path)
    try:
        chunks: list[str] = []
        total = 0
        for page in document:
            pixmap = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
            image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
            text = normalize_ocr_text(pytesseract.image_to_string(image))
            remaining = max_chars - total
            if remaining <= 0:
                break
            chunks.append(text[:remaining])
            total += min(len(text), remaining)
        return "\n".join(chunks)
    finally:
        document.close()
