from app.pipeline import run_pipeline

top, times, counts = run_pipeline("Are RNNs replaced by transformers?", top_k=5)

for rank, s in enumerate(top, start=1):
    print(f"{rank}. [{s.relevance}/5] {s.direction} {s.paper.year} | {s.paper.title}")
    print(f"   {s.reason}")

print()
for stage, seconds in times.items():
    print(f"{stage:8} {seconds:5.1f}s")
print(f"{'total':8} {sum(times.values()):5.1f}s")
print(counts)
