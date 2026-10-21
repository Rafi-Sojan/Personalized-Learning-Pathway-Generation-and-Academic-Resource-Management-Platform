from pathlib import Path


def extract_text(path: str | Path) -> str:
    """Extract text from plain text-like inputs; PDF adapters can be plugged in later."""
    file_path = Path(path)
    if file_path.suffix.lower() in {".txt", ".md", ".csv"}:
        return file_path.read_text(encoding="utf-8")
    raise ValueError("PDF extraction requires a configured PDF provider")
