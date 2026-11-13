import hashlib
import json
import re
from pathlib import Path

import arxiv

from app.models import Paper, SourcePlatform

STOPWORDS = {
    "vs",
    "versus",
    "and",
    "or",
    "the",
    "of",
    "in",
    "for",
    "a",
    "an",
    "on",
    "with",
}
ML_CATEGORIES = "(cat:cs.LG OR cat:cs.CL OR cat:cs.AI OR cat:stat.ML)"

SEARCH_CACHE = Path("cache/arxiv_search")
SEARCH_CACHE.mkdir(parents=True, exist_ok=True)


def build_arxiv_query(query: str) -> str:
    words = [
        w for w in re.findall(r"[A-Za-z0-9]+", query) if w.lower() not in STOPWORDS
    ]
    terms = " AND ".join(f"all:{w}" for w in words)
    return f"{ML_CATEGORIES} AND {terms}"


def _search_arxiv_live(query: str, max_results: int = 5) -> list[Paper]:
    client = arxiv.Client()
    search = arxiv.Search(
        query=build_arxiv_query(query),
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    papers = []
    for r in client.results(search):
        papers.append(
            Paper(
                title=r.title,
                abstract=r.summary.replace("\n", " "),
                authors=[a.name for a in r.authors],
                year=r.published.year,
                url=r.entry_id,
                source=SourcePlatform.ARXIV,
                arxiv_id=r.get_short_id(),
            )
        )
    return papers


def search_arxiv(query: str, max_results: int = 5) -> list[Paper]:
    key = hashlib.md5(f"{query}|{max_results}".encode()).hexdigest()
    file = SEARCH_CACHE / f"{key}.json"
    if file.exists():
        return [Paper(**p) for p in json.loads(file.read_text())]

    papers = _search_arxiv_live(query, max_results)
    if papers:
        file.write_text(json.dumps([p.model_dump(mode="json") for p in papers]))
    return papers
