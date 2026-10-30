from pydantic import BaseModel, Field
from typing import Literal


class SubQuestion(BaseModel):
    question: str = Field(
        description="One specific, searchable research sub-question that is part of answering the original question."
    )
    stance: Literal["supporting", "opposing", "neutral"] = Field(
        description="supporting if this sub-question looks for evidence that agrees with the original question's premise. opposing if it looks for evidence against it or for exceptions. neutral if it only gathers background or comparison."
    )
    queries: list[str] = Field(
        description="1-2 short keyword-style search queries for finding papers on this sub-question. Use technical keywords, not full sentences."
    )


class ResearchPlan(BaseModel):
    original_question: str = Field(
        description="The user's original research question, unchanged."
    )
    sub_questions: list[SubQuestion] = Field(
        description="3-5 sub-questions that together cover the original question. At least one must have stance 'opposing'."
    )
