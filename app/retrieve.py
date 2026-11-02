import numpy as np

from app.models import Chunk
from app.prefilter import embedder


def retrieve(queries: list[str], chunks: list[Chunk], keep: int = 20) -> list[Chunk]:
    chunk_vecs = np.array(embedder.embed_documents([c.text for c in chunks]))
    query_vecs = np.array(embedder.embed_documents(queries))

    scores = chunk_vecs @ query_vecs.T
    best = scores.max(axis=1)

    order = np.argsort(best)[::-1][:keep]
    return [chunks[i] for i in order]
