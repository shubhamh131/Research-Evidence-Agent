import arxiv
import httpx

from app.models import Paper, SourcePlatform

S2_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

import os
import time

from dotenv import load_dotenv

load_dotenv()


def _get_with_retry(url: str, params: dict, retries: int = 4) -> httpx.Response:
    headers = {}
    key = os.getenv("S2_API_KEY")
    if key:
        headers["x-api-key"] = key

    for attempt in range(retries):
        response = httpx.get(url, params=params, headers=headers, timeout=20)
        if response.status_code != 429:
            response.raise_for_status()
            return response
        time.sleep(2**attempt)

    response.raise_for_status()


def search_arxiv(query: str, max_results: int = 5) -> list[Paper]:
    client = arxiv.Client()
    search = arxiv.Search(
        query=query, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance
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


def search_semantic_scholar(query: str, limit: int = 5) -> list[Paper]:
    response = httpx.get(
        response=_get_with_retry(
            S2_URL,
            params={
                "query": query,
                "limit": limit,
                "fields": "title,abstract,authors,year,url,externalIds",
            },
        )
    )
    response.raise_for_status()
    items = response.json().get("data", [])

    papers = []
    for item in items:
        paper = Paper(
            title=item["title"],
            abstract=item.get("abstract") or "",
            authors=[a["name"] for a in item["authors"]],
            year=item.get("year"),
            url=item["url"],
            source=SourcePlatform.SEMANTIC_SCHOLAR,
            arxiv_id=(item.get("externalIds") or {}).get("ArXiv"),
        )
        papers.append(paper)

    return papers


def safe_search_s2(query: str, limit: int = 5) -> list[Paper]:
    try:
        return search_semantic_scholar(query, limit)
    except httpx.HTTPError as e:
        print(f"Semantic Scholar failed, continuing without it: {e}")
        return []
