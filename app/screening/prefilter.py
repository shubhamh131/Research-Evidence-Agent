import numpy as np
from langchain_huggingface import HuggingFaceEmbeddings

from app.models import Paper, ResearchPlan


embedder = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5",
    encode_kwargs={"normalize_embeddings": True},
)


def embed_filter(
    plan: ResearchPlan, papers: list[Paper], keep: int = 30
) -> list[Paper]:
    query_text = []
    query_text.append(plan.original_question)
    for sq in plan.sub_questions:
        query_text.append(sq.question)

    # embedding model take string as input not paper so
    papers_texts = [f"{p.title}. {p.abstract}" for p in papers]

    doc_vecs = np.array(embedder.embed_documents(papers_texts))
    query_vecs = np.array(embedder.embed_documents(query_text))

    scores = doc_vecs @ query_vecs.T
    best = scores.max(axis=1)
    order = np.argsort(best)[::-1][:keep]
    return [papers[i] for i in order]
