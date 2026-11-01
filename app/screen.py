import time

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from app.models import BatchScores, Paper, ScreenedPaper

load_dotenv()

SYSTEM_TEXT = """
You are screening research papers for relevance to a question.
Score each paper from 0 to 5 using only its title and abstract:
- 5: directly tests or compares the question's claim, with evidence.
- 3-4: related evidence, but indirect or partial.
- 1-2: same general topic, but no evidence for the claim.
- 0: unrelated.
Give a score for every paper in the batch. Be strict: a paper that only mentions the topic scores 2 or lower.
"""

llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)
prompt = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_TEXT), ("human", "Question: {question}\n\nPapers:\n{papers}")]
)
screener = prompt | llm.with_structured_output(BatchScores)


def screen_papers(
    question: str, papers: list[Paper], top_k: int = 8, batch_size: int = 12
) -> list[ScreenedPaper]:
    scored = []
    for start in range(0, len(papers), batch_size):
        batch = papers[start : start + batch_size]
        listing = "\n\n".join(
            f"[{i}] {p.title}\n{p.abstract[:900]}" for i, p in enumerate(batch)
        )
        result = screener.invoke({"question": question, "papers": listing})
        for s in result.scores:
            if 0 <= s.index < len(batch):
                scored.append(
                    ScreenedPaper(
                        paper=batch[s.index], relevance=s.relevance, reason=s.reason
                    )
                )
        time.sleep(2)

    scored.sort(key=lambda x: x.relevance, reverse=True)
    return scored[:top_k]
