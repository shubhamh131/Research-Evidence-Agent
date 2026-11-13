from app.planner import make_plan
from app.collection.collect import collect_papers

plan = make_plan("Are RNNs replaced by transformers?")
papers = collect_papers(plan)

print(len(papers), "unique papers")
for p in papers:
    print(p.year, p.source.value, p.title)
