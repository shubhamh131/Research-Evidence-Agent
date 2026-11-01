import re

from app.models import Paper, ResearchPlan
from app.search import search_arxiv


def _key(paper: Paper) -> str:
    if paper.arxiv_id:
        return re.sub(r"v\d+$", "", paper.arxiv_id)
    return re.sub(r"[^a-z0-9]", "", paper.title.lower())


def collect_papers(plan: ResearchPlan, per_query: int = 10) -> list[Paper]:
    seen: dict[str, Paper] = {}
    for sq in plan.sub_questions:
        for query in sq.queries:
            found = search_arxiv(query, per_query)
            for paper in found:
                seen.setdefault(_key(paper), paper)
    return list(seen.values())
