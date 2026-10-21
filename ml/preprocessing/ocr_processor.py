def normalize_ocr_text(text: str) -> str:
    return " ".join(text.replace("\u00ad", "").split())
