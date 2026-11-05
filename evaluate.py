import json
import re
from pathlib import Path
import time
from app.chain import run
import arxiv


def clean(i):
    return re.sub(r"v\d+$", "", i)


def recall(found_ids, relevant_ids):
    found = {clean(i) for i in found_ids if i}

    return len(found & set(relevant_ids)) / len(relevant_ids)


def explain_missed(missed):
    for r in arxiv.Client().results(arxiv.Search(id_list=list(missed))):
        print("   MISSED:", r.get_short_id(), r.categories, r.title[:60])


questions = json.loads(
    Path(
        "/Users/shubham/Developer/shubham/Research_agent/evals/quetions.json"
    ).read_text()
)

rows = []

for q in questions:
    start = time.time()
    result, times = run(q["question"])

    print(f"\nPapers found for: {q['question']}")
    for paper in result["papers"]:
        print(paper.arxiv_id)

    print(f"LLM-screened arXiv IDs for: {q['question']}")
    for screened in result["top"]:
        print(screened.paper.arxiv_id)

    elapsed = time.time() - start

    row = {
        "question": q["question"],
        "collected": recall([p.arxiv_id for p in result["papers"]], q["relevant_ids"]),
        "filtered": recall(
            [p.arxiv_id for p in result["shortlist"]], q["relevant_ids"]
        ),
        "final": recall([s.paper.arxiv_id for s in result["top"]], q["relevant_ids"]),
        "evidence": recall([c.arxiv_id for c in result["evidence"]], q["relevant_ids"]),
    }
    rows.append(row)
print("\nQUESTION:", q["question"])
collected_ids = {clean(p.arxiv_id) for p in result["papers"]}
missed = set(q["relevant_ids"]) - collected_ids
if missed:
    explain_missed(missed)
    print(
        "   QUERIES:", [qq for sq in result["plan"].sub_questions for qq in sq.queries]
    )

print("\n========== RECALL RESULTS ==========")

for row in rows:
    print(f"\nQuestion: {row['question'][:30]}")
    print(f"Collected: {row['collected']:.2f}")
    print(f"Filtered:  {row['filtered']:.2f}")
    print(f"Final:     {row['final']:.2f}")
    print(f"Evidence:  {row['evidence']:.2f}")
