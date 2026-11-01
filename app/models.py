from pydantic import BaseModel, Field, HttpUrl
from typing import Literal
from enum import Enum


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


class SourcePlatform(str, Enum):
    """Supported literature repositories and databases."""

    ARXIV = "arxiv"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    GOOGLE_SCHOLAR = "google_scholar"
    PUBMED = "pubmed"
    IEEE = "ieee"
    SCOPUS = "scopus"
    OTHER = "other"


class Paper(BaseModel):
    title: str
    abstract: str = Field(description="The structured abstract component of the paper.")
    authors: list[str] = Field(
        description="The names of the authors in order of contribution."
    )
    year: int | None = Field(
        default=None, description="Publication year, or None if unknown."
    )
    url: HttpUrl = Field(
        description="The primary web link to the paper (e.g., publisher page, arXiv page)."
    )
    source: SourcePlatform = Field(
        description="The repository or index where the metadata was sourced from."
    )
    arxiv_id: str | None = Field(
        default=None,
        description="The unique arXiv identifier (e.g., '1706.03762').",
        examples=["1706.03762", "hep-th/0308182"],
    )


class PaperScore(BaseModel):
    index: int = Field(
        description="The number shown in square brackets before the paper."
    )
    relevance: int = Field(
        ge=0,
        le=5,
        description="0 = unrelated, 5 = directly compares or tests the question's claim with evidence.",
    )
    reason: str = Field(description="One short sentence explaining the score.")


class BatchScores(BaseModel):
    scores: list[PaperScore] = Field(
        description="One score for every paper in the batch."
    )


class ScreenedPaper(BaseModel):
    paper: Paper
    relevance: int
    reason: str
