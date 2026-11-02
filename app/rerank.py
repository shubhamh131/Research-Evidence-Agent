from sentence_transformers import CrossEncoder

from app.models import Chunk

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def rerank(quries: list[str], chunks: list[Chunk], per_paper: int = 3) -> list[Chunk]:
    pairs = [(q, c.text) for c in chunks for q in quries]
    scores = reranker.predict(pairs)

    n = len(quries)
    best = [max(scores[i * n : (i + 1) * n]) for i in range(len(chunks))]
    ranked = sorted(zip(best, chunks), key=lambda x: x[0], reverse=True)

    count = {}
    result = []
    for score, c in ranked:
        if count.get(c.arxiv_id, 0) < per_paper:
            result.append(c)
            count[c.arxiv_id] = count.get(c.arxiv_id, 0) + 1

    return result
