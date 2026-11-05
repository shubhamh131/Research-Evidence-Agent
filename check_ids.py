import json
import re

import arxiv

questions = json.load(
    open("/Users/shubham/Developer/shubham/Research_agent/evals/quetions.json")
)
ids = [i for q in questions for i in q["relevant_ids"]]

client = arxiv.Client()
search = arxiv.Search(id_list=ids)
titles = {
    re.sub(r"v\d+$", "", r.get_short_id()): r.title for r in client.results(search)
}

for q in questions:
    print(q["question"])
    for i in q["relevant_ids"]:
        print("  ", i, "->", titles.get(i, "NOT FOUND"))
