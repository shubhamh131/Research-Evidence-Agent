from app.planner import make_plan

questions = [
    "Are RNNs replaced by transformers?",
    "tranformers overpassing the RNN",
    "transformers not right choice over the RNN",
]

for q in questions:
    plan = make_plan(q)
    print(plan.model_dump_json(indent=2))
