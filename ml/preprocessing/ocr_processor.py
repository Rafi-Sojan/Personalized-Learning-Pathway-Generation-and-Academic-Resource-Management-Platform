def normalize_ocr_text(text: str) -> str:
    """Normalize OCR spacing while retaining line boundaries for syllabus parsing."""
    lines = (" ".join(line.split()) for line in text.replace("\u00ad", "").splitlines())
    return "\n".join(line for line in lines if line)


def run_pdf_ocr(path: str, max_chars: int) -> str:
    """OCR pages from a PDF while enforcing a total extracted-character limit."""
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


def run_pdf_ocr_pages(
    path: str,
    page_numbers: list[int],
    max_chars: int,
) -> dict[int, str]:
    """OCR selected PDF pages using original 1-based page numbers."""

    if max_chars <= 0 or not page_numbers:
        return {}

    try:
        import fitz
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError(
            "OCR dependencies are missing"
        ) from exc

    results: dict[int, str] = {}
    remaining = max_chars

    with fitz.open(path) as document:
        for page_number in sorted(set(page_numbers)):
            if not 1 <= page_number <= len(document):
                raise ValueError("Invalid OCR page number")

            if remaining <= 0:
                break

            page = document[page_number - 1]

            pixmap = page.get_pixmap(
                matrix=fitz.Matrix(1.5, 1.5),
                alpha=False,
            )

            image = Image.frombytes(
                "RGB",
                (pixmap.width, pixmap.height),
                pixmap.samples,
            )

            text = normalize_ocr_text(
                pytesseract.image_to_string(image)
            )

            text = text[:remaining]
            results[page_number] = text
            remaining -= len(text)

    return results
