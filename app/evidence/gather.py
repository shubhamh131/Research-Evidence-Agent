import time

from app.evidence.chunk import make_chunks, split_sections
from app.models import Chunk, Paper, ResearchPlan
from app.evidence.pdf import fetch_paper_text
from app.evidence.rerank import rerank
from app.evidence.retrieve import retrieve


def gather_evidence(
    plan: ResearchPlan, papers: list[Paper], per_paper: int = 3
) -> list[Chunk]:
    queries = [plan.original_question] + [sq.question for sq in plan.sub_questions]

    candidates = []
    for p in papers:
        start = time.perf_counter()
        text = fetch_paper_text(p.arxiv_id)
        chunks = make_chunks(p.arxiv_id, split_sections(text))
        if time.perf_counter() - start > 1:
            time.sleep(3)
        if chunks:
            candidates += retrieve(queries, chunks, keep=8)

    return rerank(queries, candidates, per_paper)
