import json
import sys
import time
from pathlib import Path

QUESTION = "Are RNNs replaced by transformers?"
SAVE = Path("cache/last_run.json")
SAVE.parent.mkdir(exist_ok=True)


def show(chunks):
    for c in chunks:
        print(f"[{c.arxiv_id}] {c.section}")
        print("   ", c.text[:200])


def print_times(times):
    print()
    for stage, seconds in times.items():
        print(f"{stage:10} {seconds:6.1f}s")
    print(f"{'total':10} {sum(times.values()):6.1f}s")


mode = sys.argv[1] if len(sys.argv) > 1 else "full"

if mode == "full":
    from app.chain import run

    result, times = run(QUESTION)
    show(result["evidence"])
    print_times(times)

    data = {
        "plan": result["plan"].model_dump(mode="json"),
        "papers": [s.paper.model_dump(mode="json") for s in result["top"]],
    }
    SAVE.write_text(json.dumps(data))

elif mode == "ids":
    if not SAVE.exists():
        sys.exit("No saved run yet. Run `python run.py` first.")
    data = json.loads(SAVE.read_text())
    for paper in data.get("papers", []):
        arxiv_id = paper.get("arxiv_id")
        if arxiv_id:
            print(arxiv_id)

elif mode == "evidence":
    if not SAVE.exists():
        sys.exit("No saved run yet. Run `python run.py` first.")

    from app.evidence import gather_evidence
    from app.models import Paper, ResearchPlan

    data = json.loads(SAVE.read_text())
    plan = ResearchPlan(**data["plan"])
    papers = [Paper(**p) for p in data["papers"]]

    t = time.perf_counter()
    evidence = gather_evidence(plan, papers)
    times = {"evidence": time.perf_counter() - t}

    show(evidence)
    print_times(times)

else:
    sys.exit("Usage: python run.py [full|ids|evidence]")
