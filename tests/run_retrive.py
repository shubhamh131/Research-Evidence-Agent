import json
import time
from pathlib import Path

from app.evidence.chunk import make_chunks, split_sections
from app.models import Paper
from app.evidence.pdf import fetch_paper_text
from app.pipeline import run_pipeline
from app.evidence.rerank import rerank
from app.evidence.retrieve import retrieve

question = "Are RNNs replaced by transformers?"
times = {}

# 1. shortlist of 5 papers (saved after the first run)
SNAPSHOT = Path("cache/top_papers.json")
SNAPSHOT.parent.mkdir(exist_ok=True)

t = time.perf_counter()
if SNAPSHOT.exists():
    papers = [Paper(**p) for p in json.loads(SNAPSHOT.read_text())]
else:
    top, _, _ = run_pipeline(question, top_k=5)
    papers = [s.paper for s in top]
    SNAPSHOT.write_text(json.dumps([p.model_dump(mode="json") for p in papers]))
times["shortlist"] = time.perf_counter() - t

# 2. download PDFs and cut them into chunks
t = time.perf_counter()
chunks = []
for p in papers:
    start = time.perf_counter()
    text = fetch_paper_text(p.arxiv_id)
    chunks += make_chunks(p.arxiv_id, split_sections(text))
    if (
        time.perf_counter() - start > 1
    ):  # a real download happened, so be polite to arXiv
        time.sleep(3)
times["pdf+chunk"] = time.perf_counter() - t
print(len(chunks), "chunks from", len(papers), "papers")

# 3. embedding retrieval
t = time.perf_counter()
candidates = retrieve([question], chunks)
times["retrieve"] = time.perf_counter() - t

# 4. cross-encoder rerank
t = time.perf_counter()
final = rerank([question], candidates)
times["rerank"] = time.perf_counter() - t

print("\n--- AFTER RERANK ---")
for c in final:
    print(f"[{c.arxiv_id}] {c.section}")
    print("   ", c.text[:200])

print()
for stage, seconds in times.items():
    print(f"{stage:10} {seconds:6.1f}s")
print(f"{'total':10} {sum(times.values()):6.1f}s")
