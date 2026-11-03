from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from app.models import BatchScores, Paper, ScreenedPaper

load_dotenv()

SYSTEM_TEXT = """
You are screening research papers for relevance to a question.
Score each paper from 0 to 5 using only its title and abstract:
- 5: the paper's own experiments directly compare both sides of the question (for example RNN vs transformer on the same task) and report results. Use 5 rarely.
- 3-4: related evidence, but indirect, partial or one-sided (for example a paper that uses a transformer without comparing it to an RNN).
- 1-2: same general topic, but no evidence for the claim.
- 0: unrelated.
Also set direction relative to the question's claim, based only on what the abstract reports.
Give a score for every paper in the batch. Be strict. Keep each reason under 12 words.
"""

llm = ChatGroq(
    model="openai/gpt-oss-20b", temperature=0, max_retries=5, max_tokens=4096
)
prompt = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_TEXT), ("human", "Question: {question}\n\nPapers:\n{papers}")]
)
screener = (prompt | llm.with_structured_output(BatchScores)).with_retry(
    stop_after_attempt=3
)


def screen_papers(
    question: str, papers: list[Paper], top_k: int = 5, batch_size: int = 8
) -> list[ScreenedPaper]:
    # 1. cut the papers into batches
    batches = [papers[i : i + batch_size] for i in range(0, len(papers), batch_size)]

    # 2. build one input per batch
    inputs = [
        {
            "question": question,
            "papers": "\n\n".join(
                f"[{i}] {p.title}\n{p.abstract[:900]}" for i, p in enumerate(b)
            ),
        }
        for b in batches
    ]

    # 3. one call for all batches, at most 3 at the same time
    results = screener.batch(inputs, config={"max_concurrency": 3})

    # 4. pair each batch with its own result
    scored = []
    for batch, result in zip(batches, results):
        for s in result.scores:
            if 0 <= s.index < len(batch):
                scored.append(
                    ScreenedPaper(
                        paper=batch[s.index],
                        relevance=s.relevance,
                        direction=s.direction,
                        reason=s.reason,
                    )
                )

    # 5. best first, but keep room for the opposing side
    scored.sort(key=lambda x: x.relevance, reverse=True)
    n_against = max(1, top_k // 3)
    against = [s for s in scored if s.direction in ("contradicts", "mixed")][:n_against]
    rest = [s for s in scored if s not in against]
    final = against + rest[: top_k - len(against)]
    final.sort(key=lambda x: x.relevance, reverse=True)
    return final
