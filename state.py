from typing import TypedDict, Optional
from pydantic import BaseModel, Field
from enum import Enum


class ReviewDecision(str, Enum):
    APPROVE = "approve"
    REVISE = "revise"
    REJECT = "reject"


class SectionReview(BaseModel):
    score: float = Field(ge=0.0, le=1.0, description="Quality score 0-1")
    decision: ReviewDecision
    feedback: str = Field(description="Detailed feedback for the writer")
    strengths: list[str] = Field(default_factory=list, description="What works well")
    weaknesses: list[str] = Field(default_factory=list, description="What needs improvement")
    suggestions: list[str] = Field(default_factory=list, description="Specific improvement suggestions")


class PaperSection(BaseModel):
    title: str
    content: str
    order: int


class PaperState(TypedDict, total=False):
    topic: str
    outline: str
    sections: dict[str, str]
    current_section: str
    reviews: dict[str, SectionReview]
    revision_cycle: int
    error: Optional[str]


class AgentResponse(BaseModel):
    success: bool
    content: Optional[str] = None
    error: Optional[str] = None


def create_initial_state(topic: str) -> PaperState:
    return PaperState(
        topic=topic,
        outline="",
        sections={},
        current_section="",
        reviews={},
        revision_cycle=0,
        error=None
    )