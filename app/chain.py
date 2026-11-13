import time

from langchain_core.runnables import RunnableLambda, RunnablePassthrough

from app.collection.collect import collect_papers
from app.evidence import gather_evidence
from app.planner import make_plan
from app.screening.prefilter import embed_filter
from app.screening.screen import screen_papers
from app.cards import make_cards
from langchain_community.cache import SQLiteCache
from langchain_core.globals import set_llm_cache

set_llm_cache(SQLiteCache(database_path="cache/llm.db"))
TIMES = {}
set_llm_cache(SQLiteCache(database_path="cache/llm.db"))


def timed(name, fn):
    def wrapper(x):
        t = time.perf_counter()
        out = fn(x)
        TIMES[name] = time.perf_counter() - t
        return out

    return wrapper


chain = (
    RunnableLambda(lambda q: {"question": q})
    | RunnablePassthrough.assign(plan=timed("plan", lambda x: make_plan(x["question"])))
    | RunnablePassthrough.assign(
        papers=timed("collect", lambda x: collect_papers(x["plan"]))
    )
    | RunnablePassthrough.assign(
        shortlist=timed(
            "embed", lambda x: embed_filter(x["plan"], x["papers"], keep=30)
        )
    )
    | RunnablePassthrough.assign(
        top=timed(
            "screen", lambda x: screen_papers(x["question"], x["shortlist"], top_k=5)
        )
    )
    | RunnablePassthrough.assign(
        evidence=timed(
            "evidence",
            lambda x: gather_evidence(x["plan"], [s.paper for s in x["top"]]),
        )
    )
    | RunnablePassthrough.assign(
        cards=timed(
            "cards",
            lambda x: make_cards(
                x["question"], [s.paper for s in x["top"]], x["evidence"]
            ),
        )
    )
)


def run(question: str):
    TIMES.clear()
    result = chain.invoke(question)
    return result, dict(TIMES)
