def normalize_ocr_text(text: str) -> str:
    """Normalize OCR spacing while retaining line boundaries for syllabus parsing."""
    lines = (" ".join(line.split()) for line in text.replace("\u00ad", "").splitlines())
    return "\n".join(line for line in lines if line)


def run_pdf_ocr(path: str, max_chars: int) -> str:
    """OCR pages from a PDF while enforcing a total extracted-character limit."""
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
        for page_number, page in enumerate(document, start=1):
            pixmap = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
            image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            text = normalize_ocr_text(pytesseract.image_to_string(image))
            marker = f"[[PAGE {page_number}]]\n"
            remaining = max_chars - total - len(marker)
            if remaining <= 0:
                break
            page_text = text[:remaining]
            chunks.append(f"{marker}{page_text}")
            total += len(marker) + len(page_text)
        return "\n".join(chunks)
    finally:
        document.close()
