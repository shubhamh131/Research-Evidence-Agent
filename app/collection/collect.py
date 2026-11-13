import re
import time
from app.models import Paper, ResearchPlan
from app.collection.search import search_arxiv


def _key(paper: Paper) -> str:
    if paper.arxiv_id:
        return re.sub(r"v\d+$", "", paper.arxiv_id)
    return re.sub(r"[^a-z0-9]", "", paper.title.lower())


def collect_papers(plan: ResearchPlan, per_query: int = 10) -> list[Paper]:
    seen: dict[str, Paper] = {}
    queries = [plan.original_question]
    for sq in plan.sub_questions:
        queries.append(sq.question)
        queries.extend(sq.queries)

    # Planner output can repeat a query across sub-questions. Avoid paying for
    # the same arXiv request more than once while preserving its original form.
    unique_queries = {}
    for query in queries:
        normalized = " ".join(query.lower().split())
        if normalized:
            unique_queries.setdefault(normalized, query)

    for query in unique_queries.values():
        t = time.perf_counter()
        found = search_arxiv(query, per_query)
        print(f"{len(found):3} papers {time.perf_counter() - t:5.1f}s | {query[:60]}")
        for paper in found:
            seen.setdefault(_key(paper), paper)
    return list(seen.values())
