from app.models import Conflict, PaperCard
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from app.models import ConflictExplanation

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
    max_retries=5,
    max_tokens=4096,
    reasoning_effort="low",
)

SYSTEM_TEXT = """
You explain why research papers disagree on a question.
You are given short cards: direction, setting, method and finding for each paper.
Rules:
- Use ONLY the cards. Do not use outside knowledge.
- Name the difference between the supporting and the opposing cards that could explain the disagreement (different task, dataset, model size, amount of data, or method).
- If the cards show no clear difference, say 'no clear reason in the evidence' and set factor to 'unclear'.
- Keep the explanation under 40 words.
- The reason must be a difference between the SUPPORTING group and the OPPOSING group, not a difference between papers on the same side.
"""


def classify(cards: list[PaperCard]) -> Conflict:
    supporting_ids = []
    opposing_ids = []
    mixed_ids = []

    for pc in cards:
        if not pc.card.has_finding or not pc.quote_verified:
            continue

        if pc.card.direction == "supports":
            supporting_ids.append(pc.arxiv_id)

        elif pc.card.direction == "contradicts":
            opposing_ids.append(pc.arxiv_id)

        elif pc.card.direction == "mixed":
            mixed_ids.append(pc.arxiv_id)

    decisive_count = len(supporting_ids) + len(opposing_ids)
    if decisive_count < 2:
        status = "insufficient"

    elif supporting_ids and opposing_ids:
        status = "conflict"

    else:
        status = "agreement"

    return Conflict(
        status=status,
        supporting_ids=supporting_ids,
        opposing_ids=opposing_ids,
        mixed_ids=mixed_ids,
    )


def explain_conflict(cards: list[PaperCard]) -> Conflict:
    result = classify(cards)
    if result.status != "conflict":
        return result

    usable_cards = [
        card
        for card in cards
        if card.quote_verified
        and card.card.has_finding
        and card.card.direction in ("supports", "contradicts")
    ]
    side = {"supports": "SUPPORTING", "contradicts": "OPPOSING"}
    lines = [
        f"[{side[pc.card.direction]}] setting: {pc.card.setting} | "
        f"method: {pc.card.method} | finding: {pc.card.finding}"
        for pc in usable_cards
    ]

    card_text = "\n".join(lines)

    prompt = ChatPromptTemplate.from_messages(
        [("system", SYSTEM_TEXT), ("human", "Research cards:\n{card_text}")]
    )

    chain = prompt | llm.with_structured_output(ConflictExplanation).with_retry(
        stop_after_attempt=3
    )

    llm_result = chain.invoke({"card_text": card_text})

    return result.model_copy(
        update={"explanation": llm_result.explanation, "factor": llm_result.factor}
    )
