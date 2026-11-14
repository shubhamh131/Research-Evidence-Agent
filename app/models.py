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
        description="0 = unrelated, 5 = directly compares both sides of the question and reports results.",
    )
    direction: Literal["supports", "contradicts", "mixed", "unclear"] = Field(
        description="Relative to the question's claim: 'supports' if the paper's findings agree with it, 'contradicts' if they go against it, 'mixed' if both, 'unclear' if no clear finding."
    )
    reason: str = Field(description="Max 12 words explaining the score and direction.")


class BatchScores(BaseModel):
    scores: list[PaperScore] = Field(
        description="One score for every paper in the batch."
    )


class ScreenedPaper(BaseModel):
    paper: Paper
    relevance: int
    direction: str
    reason: str


class Chunk(BaseModel):
    arxiv_id: str = Field(description="Id of the paper this chunk comes from.")
    section: str = Field(
        description="Section heading the chunk belongs to, or 'Unknown'."
    )
    text: str = Field(description="The chunk text, about 200 words.")


class StudyCard(BaseModel):
    method: str = Field(
        description="What the study did or tested, in one short sentence."
    )
    setting: str = Field(description="Dataset, task or conditions, or 'not stated'.")
    finding: str = Field(
        description="The main result that bears on the question, in one sentence."
    )
    implication: str = Field(
        description="What this paper's finding implies for the question, in one short sentence."
    )
    answer: Literal["yes", "no", "partly", "unclear"] = Field(
        description="Which way does THIS paper's result lean on the question? 'yes' if it leans toward yes (even for one task or dataset), 'no' if it leans toward no, 'partly' if it shows both, 'unclear' only if the paper reports no result about the question."
    )

    @property
    def direction(self) -> str:
        return {"yes": "supports", "no": "contradicts", "partly": "mixed"}.get(
            self.answer, "unclear"
        )

    quote: str = Field(
        description="One sentence copied exactly, word for word, from the passages, that backs the finding. Empty string if none."
    )
    limitations: str = Field(
        description="Limits the passages state or clearly imply, or 'not stated'."
    )
    has_finding: bool = Field(
        description="False if the passages contain no actual result for the question."
    )


class PaperCard(BaseModel):
    arxiv_id: str
    title: str
    card: StudyCard
    quote_verified: bool = False


class ConflictExplanation(BaseModel):
    explanation: str = Field(
        description="One or two sentences: the likely reason the papers disagree, based only on their setting and method. Say “no clear reason in the evidence” if none is visible."
    )
    factor: Literal[
        "task", "dataset", "model size", "data size", "method", "unclear"
    ] = Field(description="The main factor behind the disagreement")


class Conflict(BaseModel):
    status: Literal["agreement", "conflict", "insufficient"]
    supporting_ids: list[str] = Field(default_factory=list)
    opposing_ids: list[str] = Field(default_factory=list)
    mixed_ids: list[str] = Field(default_factory=list)
    explanation: str = ""
    factor: Literal[
        "task", "dataset", "model size", "data size", "method", "unclear"
    ] = "unclear"
