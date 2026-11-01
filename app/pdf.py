import pymupdf
import httpx


def fetch_paper_text(arxiv_id: str) -> str:
    response = httpx.get(
        f"https://arxiv.org/pdf/{arxiv_id}", timeout=30, follow_redirects=True
    )
    response.raise_for_status()
    doc = pymupdf.open(stream=response.content, filetype="pdf")

    return "\n".join(page.get_text() for page in doc)
