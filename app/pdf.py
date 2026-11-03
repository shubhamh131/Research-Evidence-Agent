from pathlib import Path

import httpx
import pymupdf

CACHE = Path("cache/pdf_text")
CACHE.mkdir(parents=True, exist_ok=True)


def fetch_paper_text(arxiv_id: str) -> str:
    file = CACHE / f"{arxiv_id.replace('/', '_')}.txt"
    if file.exists():
        return file.read_text()

    response = httpx.get(
        f"https://arxiv.org/pdf/{arxiv_id}", timeout=30, follow_redirects=True
    )
    response.raise_for_status()
    doc = pymupdf.open(stream=response.content, filetype="pdf")
    text = "\n".join(page.get_text() for page in doc)

    file.write_text(text)
    return text
