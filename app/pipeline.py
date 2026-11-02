import time


from app.collect import collect_papers
from app.planner import make_plan
from app.prefilter import embed_filter
from app.screen import screen_papers


def run_pipeline(question: str, top_k: int = 5):
    times = {}

    t = time.perf_counter()
    plan = make_plan(question)
    times["plan"] = time.perf_counter() - t

    t = time.perf_counter()
    papers = collect_papers(plan)
    times["collect"] = time.perf_counter() - t

    t = time.perf_counter()
    shortlist = embed_filter(plan, papers, keep=30)
    times["embed"] = time.perf_counter() - t

    t = time.perf_counter()
    top = screen_papers(question, shortlist, top_k=top_k, batch_size=8)
    times["screen"] = time.perf_counter() - t

    counts = {"collected": len(papers), "shortlist": len(shortlist), "final": len(top)}
    return top, times, counts, plan
