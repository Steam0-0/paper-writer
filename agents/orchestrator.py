import json
import logging
from typing import Literal

from state import PaperState, SectionReview, ReviewDecision
from config import review_config

logger = logging.getLogger(__name__)


def should_continue(state: PaperState) -> str:
    """
    条件路由：根据审稿结果决定下一步操作
    """
    current_section = state.get("current_section", "")
    reviews = state.get("reviews", {})
    revision_cycle = state.get("revision_cycle", 0)

    if not current_section:
        return "end"

    review = reviews.get(current_section)
    if not review:
        return "revise"

    if revision_cycle >= review_config.max_revision_cycles:
        logger.warning(f"Max revision cycles ({review_config.max_revision_cycles}) reached for {current_section}")
        return "end"

    if review.decision == ReviewDecision.APPROVE:
        logger.info(f"Section {current_section} approved with score {review.score}")
        return "end"

    if review.decision == ReviewDecision.REVISE:
        logger.info(f"Section {current_section} needs revision (score: {review.score})")
        return "revise"

    return "end"


def route_next_section(state: PaperState) -> Literal["planner", "writer", "end"]:
    """
    路由到下一个章节
    """
    outline_data = json.loads(state.get("outline", "{}"))
    chapters = outline_data.get("chapters", [])
    current_section = state.get("current_section", "")
    sections = state.get("sections", {})

    for idx, ch in enumerate(chapters):
        chapter_name = ch.get("chapter", "")
        if not current_section:
            return "writer"
        if chapter_name.lower() == current_section.lower():
            if idx + 1 < len(chapters):
                return "writer"
            else:
                return "end"

    return "end"


def select_next_section(state: PaperState) -> PaperState:
    """
    选择下一个要写的章节
    """
    outline_data = json.loads(state.get("outline", "{}"))
    chapters = outline_data.get("chapters", [])
    current_section = state.get("current_section", "")
    sections = state.get("sections", {})

    for idx, ch in enumerate(chapters):
        chapter_name = ch.get("chapter", "")
        if chapter_name.lower() == current_section.lower():
            if idx + 1 < len(chapters):
                next_chapter = chapters[idx + 1]
                logger.info(f"Moving to next section: {next_chapter['chapter']}")
                return {**state, "current_section": next_chapter["chapter"], "revision_cycle": 0}
            else:
                logger.info("All sections completed")
                return {**state, "current_section": ""}

    if not chapters:
        return {**state, "error": "No chapters in outline"}

    logger.info(f"Starting with first section: {chapters[0]['chapter']}")
    return {**state, "current_section": chapters[0]["chapter"], "revision_cycle": 0}