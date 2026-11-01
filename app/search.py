import arxiv
import httpx
import re

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


def build_arxiv_query(query: str) -> str:
    words = [
        w for w in re.findall(r"[A-Za-z0-9]+", query) if w.lower() not in STOPWORDS
    ]
    terms = " AND ".join(f"all:{w}" for w in words)
    return f"{ML_CATEGORIES} AND {terms}"


def search_arxiv(query: str, max_results: int = 5) -> list[Paper]:
    client = arxiv.Client()
    search = arxiv.Search(
        query=build_arxiv_query(query),
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    papers = []
    for r in client.results(search=search):
        paper = Paper(
            title=r.title,
            abstract=r.summary.replace("\n", " "),
            authors=[a.name for a in r.authors],
            year=r.published.year,
            url=r.entry_id,
            source=SourcePlatform.ARXIV,
            arxiv_id=r.get_short_id(),
        )
        papers.append(paper)

    return papers
