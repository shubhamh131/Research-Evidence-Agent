from langchain_core.prompts import ChatPromptTemplate

from app.models import Chunk, Paper, PaperCard, StudyCard
from app.screening.screen import llm
from app.evidence.citation import quote_found

SYSTEM_TEXT = """
You fill in a study card for one research paper, to answer a question.
Use ONLY the title, abstract and passages given. Do not use outside knowledge.
Rules:
- finding: a RESULT (a comparison, a number or an outcome), not a description of what the study did. The result may come from the abstract or the passages.
- Ignore background statements about other work, such as 'X has replaced Y' in an introduction. Use only what THIS paper tested or found. If this paper did not test the question, set has_finding to false.
- If neither the abstract nor the passages report a result relevant to the question, set has_finding to false and write 'not stated' in the other text fields.
- A verified quote only means the quote exists in the paper text. It does not mean the quote is this paper's own result or that the claim is true.
- answer: answer the question using ONLY this paper's result. Example: question 'Does dropout help?' and result 'dropout lowered accuracy' -> no.
- quote: one sentence copied exactly, word for word, from the abstract or the passages. Empty string if none fits.
- Keep every text field under 30 words.
"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_TEXT),
        (
            "human",
            "Question: {question}\n\nTitle: {title}\n\nAbstract: {abstract}\n\nPassages:\n{passages}",
        ),
    ]
)
card_chain = (prompt | llm.with_structured_output(StudyCard)).with_retry(
    stop_after_attempt=3
)


def make_cards(
    question: str, papers: list[Paper], evidence: list[Chunk]
) -> list[PaperCard]:
    by_paper = {}
    cards = []
    for c in evidence:
        by_paper.setdefault(c.arxiv_id, []).append(c)

    inputs = [
        {
            "question": question,
            "title": p.title,
            "abstract": p.abstract[:900],
            "passages": "\n\n".join(f"- {c.text}" for c in by_paper.get(p.arxiv_id, []))
            or "(none)",
        }
        for p in papers
    ]

    results = card_chain.batch(inputs, config={"max_concurrency": 2})
    for p, r in zip(papers, results):
        source = (
            " ".join(c.text for c in by_paper.get(p.arxiv_id, [])) + " " + p.abstract
        )
        cards.append(
            PaperCard(
                arxiv_id=p.arxiv_id,
                title=p.title,
                card=r,
                quote_verified=quote_found(r.quote, source),
            )
        )
    return cards
