import json
import logging

from state import PaperState, SectionReview
from utils.llm import llm_client
from prompts import REVIEWER_SYSTEM_PROMPT, REVIEWER_USER_PROMPT

logger = logging.getLogger(__name__)


def reviewer(state: PaperState) -> PaperState:
    current_section = state.get("current_section", "")
    topic = state["topic"]
    content = state.get("sections", {}).get(current_section, "")

    logger.info(f"Running reviewer for section: {current_section}")

    if not content:
        return {**state, "error": f"No content to review for section: {current_section}"}

    outline_data = json.loads(state.get("outline", "{}"))
    chapters = outline_data.get("chapters", [])
    target_chapter = None
    for ch in chapters:
        if ch.get("chapter", "").lower() == current_section.lower():
            target_chapter = ch
            break

    chapter_title = target_chapter["chapter"] if target_chapter else current_section

    user_prompt = REVIEWER_USER_PROMPT.format(
        topic=topic,
        chapter_title=chapter_title,
        content=content
    )

    response = llm_client.structured_generate(
        prompt=user_prompt,
        system_prompt=REVIEWER_SYSTEM_PROMPT,
        output_schema=SectionReview
    )

    if not response.success:
        logger.error(f"Reviewer failed: {response.error}")
        return {**state, "error": f"Reviewer error: {response.error}"}

    review_data = response.content
    review = SectionReview(
        score=review_data.get("score", 0.0),
        decision=review_data.get("decision", "revise"),
        feedback=review_data.get("feedback", ""),
        strengths=review_data.get("strengths", []),
        weaknesses=review_data.get("weaknesses", []),
        suggestions=review_data.get("suggestions", [])
    )

    reviews = state.get("reviews", {})
    reviews[current_section] = review

    logger.info(f"Review completed for {current_section}: score={review.score}, decision={review.decision}")

    return {**state, "reviews": reviews}