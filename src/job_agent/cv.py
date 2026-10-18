from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader


def extract_cv_text(cv_dir: Path, max_chars: int = 8000) -> str:
    texts: list[str] = []
    for path in sorted(cv_dir.glob("*.pdf")):
        reader = PdfReader(str(path))
        parts = [(page.extract_text() or "") for page in reader.pages]
        texts.append("\n".join(parts))
    combined = "\n\n".join(texts).strip()
    return combined[:max_chars]
