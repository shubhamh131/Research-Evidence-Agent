from app.planner import make_plan
from app.collect import collect_papers
from app.screen import screen_papers
from app.prefilter import embed_filter

question = "Are RNNs replaced by transformers?"
papers = collect_papers(make_plan(question))

top = screen_papers(question, papers)

for s in top:
    print(s.relevance, s.paper.year, s.paper.title)
    print("   ", s.reason)
