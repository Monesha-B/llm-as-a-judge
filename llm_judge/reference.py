"""Extract short trusted reference files; no storage or OCR."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

MAX_BYTES = 2 * 1024 * 1024
MAX_CHARS = 25_000
MAX_PAGES = 20


def extract_reference(name: str, content: bytes) -> str:
    if not isinstance(content, bytes) or not 0 < len(content) <= MAX_BYTES:
        raise ValueError("Reference files must be nonempty and at most 2 MB.")
    extension = Path(name).suffix.lower()
    if extension in {".txt", ".md"}:
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("Text reference must be UTF-8 encoded.") from exc
    elif extension == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(BytesIO(content))
            if len(reader.pages) > MAX_PAGES:
                raise ValueError("PDF reference must not exceed 20 pages.")
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError("Could not read PDF text. Scanned PDFs are not supported.") from exc
    else:
        raise ValueError("Only TXT, MD and text-based PDF are supported.")
    text = text.strip()
    if not text:
        raise ValueError("No selectable text found in the reference file.")
    return text[:MAX_CHARS]
